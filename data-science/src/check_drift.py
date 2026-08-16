from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from scipy.stats import ks_2samp

NUMERIC_COLS = ["x1", "x2"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("check_drift")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--container", default="monitoring")
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument(
        "--min-rows", type=int, default=30,
        help="Minimum recent inference rows before running tests at all",
    )
    parser.add_argument(
        "--fdr-alpha", type=float, default=0.05, help="Benjamini-Hochberg FDR level"
    )
    parser.add_argument(
        "--ks-effect-threshold", type=float, default=0.1,
        help="Minimum KS D-statistic to count as practically significant",
    )
    parser.add_argument(
        "--min-drifted-features", type=int, default=1,
        help="How many features must clear both gates before DRIFT_DETECTED fires",
    )
    parser.add_argument(
        "--report-output", default=None, help="Optional path to write a JSON report"
    )
    return parser.parse_args()


def load_baseline(blob_service: BlobServiceClient, container: str) -> dict | None:
    client = blob_service.get_blob_client(
        container=container, blob="monitoring/baseline/reference.json"
    )
    if not client.exists():
        return None
    return json.loads(client.download_blob().readall())


def load_recent_inference_data(
    blob_service: BlobServiceClient, container: str, lookback_days: int
) -> pd.DataFrame | None:
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    prefix = "monitoring/inference-log/"
    container_client = blob_service.get_container_client(container)
    frames = []
    for blob in container_client.list_blobs(name_starts_with=prefix):
        if blob.last_modified is not None and blob.last_modified < cutoff:
            continue
        data = container_client.download_blob(blob.name).readall()
        frames.append(pd.read_parquet(BytesIO(data)))
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def benjamini_hochberg(p_values: dict[str, float], alpha: float) -> set[str]:
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    total = len(items)
    if total == 0:
        return set()
    largest_k = 0
    for index, (_, p_value) in enumerate(items, start=1):
        if p_value <= (index / total) * alpha:
            largest_k = index
    return {name for name, _ in items[:largest_k]}


def check_numeric_drift(baseline_numeric: dict, recent: pd.DataFrame) -> dict:
    results = {}
    for column, reference in baseline_numeric.items():
        if column not in recent.columns:
            continue
        sample = recent[column].dropna()
        if len(sample) == 0:
            continue
        statistic, p_value = ks_2samp(reference["values_sample"], sample)
        results[column] = {"statistic": float(statistic), "p_value": float(p_value)}
    return results


def main() -> int:
    args = parse_args()
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID")
    )
    blob_service = BlobServiceClient(
        account_url=f"https://{args.storage_account}.blob.core.windows.net",
        credential=credential,
    )

    baseline = load_baseline(blob_service, args.container)
    if baseline is None:
        print("No baseline found yet - no model has been promoted since monitoring was added.")
        print("MONITORING_STATUS=NOT_READY")
        return 0

    recent = load_recent_inference_data(blob_service, args.container, args.lookback_days)
    row_count = 0 if recent is None else len(recent)
    if row_count < args.min_rows:
        print(
            f"Only {row_count} inference rows in the last {args.lookback_days} days "
            f"(minimum {args.min_rows}) - too few for a statistically meaningful comparison."
        )
        print("MONITORING_STATUS=INSUFFICIENT_DATA")
        return 0

    numeric_results = check_numeric_drift(baseline["stats"]["numeric"], recent)
    p_values = {
        f"numeric:{column}": result["p_value"] for column, result in numeric_results.items()
    }
    significant_after_correction = benjamini_hochberg(p_values, args.fdr_alpha)

    drifted_features = [
        column
        for column, result in numeric_results.items()
        if f"numeric:{column}" in significant_after_correction
        and result["statistic"] >= args.ks_effect_threshold
    ]

    report = {
        "baseline_model_version": baseline.get("model_version"),
        "baseline_captured_at": baseline["captured_at"],
        "inference_rows_compared": row_count,
        "numeric": numeric_results,
        "significant_after_fdr_correction": sorted(significant_after_correction),
        "drifted_features": drifted_features,
    }

    if args.report_output:
        with open(args.report_output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    print(json.dumps(report, indent=2))
    status = "DRIFT_DETECTED" if len(drifted_features) >= args.min_drifted_features else "HEALTHY"
    print(f"MONITORING_STATUS={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
