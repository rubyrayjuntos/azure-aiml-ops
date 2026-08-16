from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

NUMERIC_COLS = ["x1", "x2"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("snapshot_baseline")
    parser.add_argument(
        "--reference-data", required=True, help="Path to the training dataset (parquet dir)"
    )
    parser.add_argument("--model-info", required=True, help="register.py's --output path")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--container", default="monitoring")
    return parser.parse_args()


def compute_reference_stats(frame: pd.DataFrame) -> dict:
    stats: dict = {"numeric": {}}
    for column in NUMERIC_COLS:
        stats["numeric"][column] = {
            "mean": float(frame[column].mean()),
            "std": float(frame[column].std()),
            "values_sample": frame[column].sample(min(500, len(frame)), random_state=42).tolist(),
        }
    return stats


def main() -> None:
    args = parse_args()
    model_info_path = Path(args.model_info) / "model-info.json"
    model_info = json.loads(model_info_path.read_text(encoding="utf-8"))
    if model_info.get("registered") is not True:
        print("register.py declined to promote this candidate; skipping baseline snapshot.")
        return

    reference = pd.read_parquet(Path(args.reference_data) / "data.parquet")
    stats = compute_reference_stats(reference)
    payload = {
        "model_name": args.model_name,
        "model_version": model_info["model_version"],
        "training_run_id": os.environ.get("AZUREML_RUN_ID", "unknown"),
        "captured_at": datetime.now(UTC).isoformat(),
        "row_count": len(reference),
        "stats": stats,
    }

    credential = DefaultAzureCredential(
        managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID")
    )
    blob_service = BlobServiceClient(
        account_url=f"https://{args.storage_account}.blob.core.windows.net",
        credential=credential,
    )
    blob_client = blob_service.get_blob_client(
        container=args.container, blob="monitoring/baseline/reference.json"
    )
    blob_client.upload_blob(json.dumps(payload, indent=2), overwrite=True)
    print(
        f"Baseline snapshot written to {args.container}/monitoring/baseline/reference.json "
        f"({payload['row_count']} rows, model version {payload['model_version']})."
    )


if __name__ == "__main__":
    main()
