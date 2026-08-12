from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlsplit, urlunsplit

TERMINAL = {"succeeded", "failed", "skipped"}
EVENT_IDENTITY_VERSION = "1.0"
EVENT_IDENTITY_FIELDS = (
    "project", "environment", "provider", "capability", "operation", "operation_id",
    "source_run_id", "source_sequence",
)
SENSITIVE = ("secret", "password", "token", "credential", "connection_string", "raw_data", "prompt")
APPROVED_ARTIFACT_URI_SCHEMES = {"azure", "azureml", "https"}
SENSITIVE_QUERY_PARAMETERS = {
    "access_token", "api_key", "apikey", "client_secret", "code", "credential", "key",
    "password", "secret", "sig", "se", "sp", "sv", "skt", "skoid", "token",
}


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def event_identity(
    provider: str,
    capability: str,
    operation: str,
    operation_id: str,
    source_run_id: str,
    source_sequence: int,
) -> str:
    return canonical(
        [
            "azure-ai-ml-ops",
            "dev",
            provider,
            capability,
            operation,
            operation_id,
            source_run_id,
            str(source_sequence),
        ]
    )


def validate_artifact_uri(value: str) -> str:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("artifact URI contains control characters")
    parsed = urlsplit(value)
    lowered = value.lower()
    if "defaultendpointsprotocol=" in lowered or "accountkey=" in lowered:
        raise ValueError("artifact URI must not contain a connection string")
    scheme = parsed.scheme.lower()
    if scheme not in APPROVED_ARTIFACT_URI_SCHEMES:
        raise ValueError("artifact URI scheme is not approved")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("artifact URI must not contain user information")
    if parsed.query:
        names = {name.lower() for name, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        if names & SENSITIVE_QUERY_PARAMETERS:
            raise ValueError("artifact URI must not contain credential-bearing parameters")
        raise ValueError("artifact URI must be an unsigned canonical reference")
    if parsed.fragment:
        raise ValueError("artifact URI must not contain a fragment")
    if scheme == "https" and not parsed.hostname:
        raise ValueError("HTTPS artifact URI requires a host")
    if scheme in {"azure", "azureml"} and not (parsed.netloc or parsed.path):
        raise ValueError("artifact URI requires a resource path")
    return urlunsplit((scheme, parsed.netloc, parsed.path, "", ""))


def parse_artifact(value: str) -> dict:
    kind, separator, uri = value.partition("=")
    if not separator or not kind or not uri:
        raise argparse.ArgumentTypeError("artifact must use kind=uri")
    try:
        normalized = validate_artifact_uri(uri)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None
    return {"kind": kind, "uri": normalized}


def reject_sensitive_keys(value: object, path: str = "metadata") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(part in key.lower() for part in SENSITIVE):
                raise ValueError(f"sensitive metadata key is not allowed: {path}.{key}")
            reject_sensitive_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_sensitive_keys(item, f"{path}[{index}]")


def main() -> None:
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    parser = argparse.ArgumentParser()
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument(
        "--state",
        choices=["started", "running", "succeeded", "failed", "skipped"],
        required=True,
    )
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-sequence", type=int, required=True)
    parser.add_argument("--artifact", type=parse_artifact, action="append", default=[])
    parser.add_argument("--metadata", default="{}")
    args = parser.parse_args()
    metadata = json.loads(args.metadata)
    reject_sensitive_keys(metadata)
    now = datetime.now(UTC)
    identity = event_identity(
        args.provider,
        args.capability,
        args.operation,
        args.operation_id,
        args.source_run_id,
        args.source_sequence,
    )
    event_id = digest(identity)
    event = {
        "schema_version": "1.0",
        "event_identity_version": EVENT_IDENTITY_VERSION,
        "event_id": event_id,
        "operation_id": args.operation_id,
        "project": "azure-ai-ml-ops",
        "environment": "dev",
        "provider": args.provider,
        "capability": args.capability,
        "operation": args.operation,
        "state": args.state,
        "source_run_id": args.source_run_id,
        "source_sequence": args.source_sequence,
        "occurred_at": now.isoformat(),
        "recorded_at": now.isoformat(),
        "artifact_references": args.artifact,
        "metadata": metadata,
    }
    event["payload_digest"] = digest(canonical(event))
    name = f"v1/azure-ai-ml-ops/dev/{now:%Y/%m/%d}/{args.operation_id}/{event_id}.json"
    service = BlobServiceClient(
        account_url=f"https://{args.storage_account}.blob.core.windows.net",
        credential=DefaultAzureCredential(),
    )
    client = service.get_blob_client("platform-evidence", name)
    payload = canonical(event)
    try:
        client.upload_blob(payload, overwrite=False)
    except Exception:
        if client.download_blob().readall().decode() != payload:
            raise
    if args.state in TERMINAL:
        receipt = {
            "schema_version": "1.0",
            "project": "azure-ai-ml-ops",
            "environment": "dev",
            "operation_id": args.operation_id,
            "terminal_event_id": event_id,
            "state": args.state,
            "artifact_references": args.artifact,
        }
        receipt_client = service.get_blob_client(
            "platform-evidence", f"receipts/{args.operation_id}/receipt.json"
        )
        receipt_payload = canonical(receipt)
        try:
            receipt_client.upload_blob(receipt_payload, overwrite=False)
        except Exception:
            if receipt_client.download_blob().readall().decode() != receipt_payload:
                raise
    print(event_id)


if __name__ == "__main__":
    main()
