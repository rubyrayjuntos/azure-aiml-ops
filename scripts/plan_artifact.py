#!/usr/bin/env python3
"""Create and verify the R1 Terraform plan review artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

SCHEMA_VERSION = "1.0"
EXPECTED_FILES = {
    "r1.tfplan",
    "r1.tfplan.sha256",
    "r1-plan.sanitized.json",
    "r1-plan.sanitized.json.sha256",
    "approval-metadata.json",
    "artifact-manifest.v1.json",
}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "client_secret",
    "code",
    "password",
    "sig",
    "signature",
    "skoid",
    "skt",
    "sp",
    "sv",
    "token",
}
SENSITIVE_FIELD_KEYS = {
    "access_key",
    "account_key",
    "client_secret",
    "connection_string",
    "password",
    "primary_access_key",
    "primary_connection_string",
    "sas_token",
    "secret_value",
    "secondary_access_key",
    "secondary_connection_string",
}
REDACTED = "<redacted:sensitive>"
DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAXIMUM_PLAN_AGE_HOURS = 720


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def _write_digest(path: Path, digest: str, target: str) -> None:
    path.write_text(f"{digest}  {target}\n", encoding="utf-8", newline="\n")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON object contains a duplicate key")
        result[key] = value
    return result


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def _mask(value: Any, sensitive: Any) -> Any:
    if sensitive is True:
        return REDACTED
    if isinstance(value, dict) and isinstance(sensitive, dict):
        return {key: _mask(item, sensitive.get(key)) for key, item in value.items()}
    if isinstance(value, list) and isinstance(sensitive, list):
        return [
            _mask(item, sensitive[index] if index < len(sensitive) else None)
            for index, item in enumerate(value)
        ]
    return value


def _sanitize(node: Any, parent_key: str = "") -> Any:
    if parent_key.lower() in SENSITIVE_FIELD_KEYS:
        return REDACTED
    if isinstance(node, list):
        return [_sanitize(item, parent_key) for item in node]
    if not isinstance(node, dict):
        return node

    result = deepcopy(node)
    for value_key, sensitive_key in (
        ("values", "sensitive_values"),
        ("before", "before_sensitive"),
        ("after", "after_sensitive"),
    ):
        if value_key in result and sensitive_key in result:
            result[value_key] = _mask(result[value_key], result[sensitive_key])
    if result.get("sensitive") is True:
        for key in ("before", "after"):
            if key in result:
                result[key] = REDACTED
    return {key: _sanitize(value, key) for key, value in result.items()}


def _assert_no_credentials(node: Any) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in SENSITIVE_FIELD_KEYS and value != REDACTED:
                raise ValueError("sanitized plan contains an unredacted sensitive field")
            _assert_no_credentials(value)
        return
    if isinstance(node, list):
        for value in node:
            _assert_no_credentials(value)
        return
    if not isinstance(node, str) or node == REDACTED:
        return
    lowered = node.lower()
    if "defaultendpointsprotocol=" in lowered or "accountkey=" in lowered:
        raise ValueError("sanitized plan contains a credential-bearing value")
    parsed = urlsplit(node)
    if parsed.scheme and (parsed.username is not None or parsed.password is not None):
        raise ValueError("sanitized plan contains a credential-bearing URI")
    if parsed.scheme and any(
        key.lower() in SENSITIVE_QUERY_KEYS for key, _ in parse_qsl(parsed.query)
    ):
        raise ValueError("sanitized plan contains a credential-bearing URI")


def _action_summary(plan: dict[str, Any]) -> dict[str, int]:
    summary = {
        "create": 0,
        "update": 0,
        "replace": 0,
        "delete": 0,
        "read": 0,
        "no_op": 0,
    }
    for change in plan.get("resource_changes", []):
        actions = change.get("change", {}).get("actions", [])
        if actions == ["create"]:
            summary["create"] += 1
        elif actions == ["update"]:
            summary["update"] += 1
        elif "create" in actions and "delete" in actions:
            summary["replace"] += 1
        elif actions == ["delete"]:
            summary["delete"] += 1
        elif actions == ["read"]:
            summary["read"] += 1
        elif actions == ["no-op"]:
            summary["no_op"] += 1
        else:
            raise ValueError("Terraform plan contains an unsupported action sequence")
    return summary


def _terraform_version(terraform_dir: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["terraform", f"-chdir={terraform_dir}", "version", "-json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    return {
        "terraform_version": payload["terraform_version"],
        "provider_selections": dict(sorted(payload.get("provider_selections", {}).items())),
    }


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("artifact timestamp is missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("artifact timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _state_identity(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if not raw.strip():
        return {"exists": False, "lineage": None, "serial": None, "digest": _sha256(path)}
    payload = _read_json(path)
    if payload == {"state_absent": True}:
        return {"exists": False, "lineage": None, "serial": None, "digest": _sha256(path)}
    lineage = payload.get("lineage") if isinstance(payload, dict) else None
    serial = payload.get("serial") if isinstance(payload, dict) else None
    if not isinstance(lineage, str) or not lineage or not isinstance(serial, int):
        raise ValueError("Terraform state snapshot lacks lineage or serial")
    return {"exists": True, "lineage": lineage, "serial": serial, "digest": _sha256(path)}


def _validated_deployment_governance(project_root: Path) -> dict[str, str]:
    plan_path = project_root / ".azure/deployment-plan.md"
    status_path = project_root / ".azure/validate-status.json"
    plan_text = plan_path.read_text(encoding="utf-8")
    if not re.search(r"^> \*\*Status:\*\* Validated\s*$", plan_text, re.MULTILINE):
        raise ValueError("deployment plan status is not Validated")
    if "Not yet executed" in plan_text or "Not yet validated" in plan_text:
        raise ValueError("deployment plan validation proof is incomplete")
    validation_status = _read_json(status_path)
    if validation_status != {"completedStep": "UpdateStatus"}:
        raise ValueError("Azure validation workflow is incomplete")
    return {
        "deployment_plan_digest": _sha256(plan_path),
        "validation_status_digest": _sha256(status_path),
    }


def create(args: argparse.Namespace) -> None:
    root = Path(args.artifact_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    plan_path = Path(args.plan).resolve()
    raw_path = Path(args.raw_json).resolve()
    if plan_path.parent != root:
        raise ValueError("binary plan must be in the artifact directory")
    raw = _read_json(raw_path)
    sanitized = _sanitize(raw)
    _assert_no_credentials(sanitized)

    sanitized_path = root / "r1-plan.sanitized.json"
    _write_json(sanitized_path, sanitized)
    plan_digest = _sha256(plan_path)
    json_digest = _sha256(sanitized_path)
    _write_digest(root / "r1.tfplan.sha256", plan_digest, "r1.tfplan")
    _write_digest(
        root / "r1-plan.sanitized.json.sha256",
        json_digest,
        "r1-plan.sanitized.json",
    )

    receipt = _read_json(Path(args.generation_receipt))
    for field in ("platform_source_commit", "platform_package_digest"):
        if field not in receipt:
            raise ValueError("generation receipt lacks immutable platform provenance")
    governance = _validated_deployment_governance(Path(args.generation_receipt).resolve().parent)
    approval = {
        "approval_contract_version": SCHEMA_VERSION,
        "source_commit": args.source_commit,
        "platform_source_commit": receipt["platform_source_commit"],
        "platform_package_digest": receipt["platform_package_digest"],
        **governance,
        "generation_id": receipt["generation_id"],
        "manifest_digest": receipt["manifest_digest"],
        "resolved_plan_digest": receipt["resolved_plan_digest"],
        "target_environment": args.environment,
        "terraform_plan_digest": plan_digest,
        "sanitized_plan_digest": json_digest,
        "plan_run_id": args.run_id,
        "plan_run_attempt": args.run_attempt,
        "plan_requested_by": args.actor,
        "plan_producer": "github-actions",
        "independent_human_reviewer_required": False,
    }
    approval_path = root / "approval-metadata.json"
    _write_json(approval_path, approval)

    terraform_dir = Path(args.terraform_dir).resolve()
    versions = _terraform_version(terraform_dir)
    files = {
        name: _sha256(root / name)
        for name in sorted(EXPECTED_FILES - {"artifact-manifest.v1.json"})
    }
    created_at = datetime.now(UTC)
    state_identity = _state_identity(Path(args.state_snapshot).resolve())
    manifest = {
        "artifact_manifest_schema_version": SCHEMA_VERSION,
        "created_at": created_at.isoformat(),
        "expires_at": (created_at + timedelta(days=args.retention_days)).isoformat(),
        "maximum_plan_age_hours": args.maximum_plan_age_hours,
        "expected_files": sorted(EXPECTED_FILES),
        "files": files,
        "source_commit": args.source_commit,
        "platform_source_commit": receipt["platform_source_commit"],
        "platform_package_digest": receipt["platform_package_digest"],
        **governance,
        "platform_version": receipt["platform_version"],
        "generation_id": receipt["generation_id"],
        "manifest_digest": receipt["manifest_digest"],
        "resolved_plan_digest": receipt["resolved_plan_digest"],
        "template_digest": receipt["template_digest"],
        "generated_files_digest": receipt["generated_files_digest"],
        "dependency_constraints_digest": receipt["dependency_constraints_digest"],
        "plan_run_id": args.run_id,
        "plan_run_attempt": args.run_attempt,
        "tenant_id": args.tenant_id,
        "subscription_id": args.subscription_id,
        "target_environment": args.environment,
        "backend": {
            "resource_group": args.backend_resource_group,
            "storage_account": args.backend_storage_account,
            "container": args.backend_container,
            "state_key": args.state_key,
            "state": state_identity,
        },
        "terraform": {
            **versions,
            "lock_file_digest": _sha256(terraform_dir / ".terraform.lock.hcl"),
        },
        "terraform_plan_digest": plan_digest,
        "sanitized_plan_digest": json_digest,
        "action_summary": _action_summary(sanitized),
    }
    _write_json(root / "artifact-manifest.v1.json", manifest)
    raw_path.unlink(missing_ok=True)
    verify_artifact(root)


def _read_digest(path: Path, expected_name: str) -> str:
    match = re.fullmatch(r"(sha256:[0-9a-f]{64})  ([^\n]+)\n?", path.read_text(encoding="utf-8"))
    if not match or match.group(2) != expected_name:
        raise ValueError("artifact digest file is malformed")
    return match.group(1)


def verify_artifact(
    root: Path,
    *,
    expected_run_id: str | None = None,
    expected_run_attempt: str | None = None,
    expected_environment: str | None = None,
    reviewed_plan_digest: str | None = None,
    reviewed_json_digest: str | None = None,
    expected_tenant_id: str | None = None,
    expected_subscription_id: str | None = None,
    current_state_snapshot: Path | None = None,
    project_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    if actual_files != EXPECTED_FILES:
        raise ValueError("reviewed artifact contents do not match schema 1.0")
    manifest = _read_json(root / "artifact-manifest.v1.json")
    if manifest.get("artifact_manifest_schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported artifact manifest schema")
    if manifest.get("expected_files") != sorted(EXPECTED_FILES):
        raise ValueError("artifact manifest file list does not match schema 1.0")
    expected_digests = manifest.get("files")
    if not isinstance(expected_digests, dict) or set(expected_digests) != EXPECTED_FILES - {
        "artifact-manifest.v1.json"
    }:
        raise ValueError("artifact manifest digest set does not match schema 1.0")
    for name, expected in expected_digests.items():
        if _sha256(root / name) != expected:
            raise ValueError("artifact file digest mismatch")

    plan_digest = _sha256(root / "r1.tfplan")
    json_path = root / "r1-plan.sanitized.json"
    json_digest = _sha256(json_path)
    sanitized = _read_json(json_path)
    _assert_no_credentials(sanitized)
    approval = _read_json(root / "approval-metadata.json")
    checked_at = (now or datetime.now(UTC)).astimezone(UTC)
    created_at = _parse_timestamp(manifest.get("created_at"))
    expires_at = _parse_timestamp(manifest.get("expires_at"))
    maximum_age = manifest.get("maximum_plan_age_hours")
    if not isinstance(maximum_age, int) or maximum_age <= 0:
        raise ValueError("artifact maximum plan age is invalid")
    checks = {
        "created_not_future": created_at <= checked_at,
        "not_expired": checked_at <= expires_at,
        "within_maximum_age": checked_at - created_at <= timedelta(hours=maximum_age),
        "plan_digest_file": _read_digest(root / "r1.tfplan.sha256", "r1.tfplan") == plan_digest,
        "json_digest_file": _read_digest(
            root / "r1-plan.sanitized.json.sha256", "r1-plan.sanitized.json"
        )
        == json_digest,
        "manifest_plan_digest": manifest.get("terraform_plan_digest") == plan_digest,
        "manifest_json_digest": manifest.get("sanitized_plan_digest") == json_digest,
        "manifest_action_summary": manifest.get("action_summary") == _action_summary(sanitized),
        "approval_version": approval.get("approval_contract_version") == SCHEMA_VERSION,
        "approval_plan_digest": approval.get("terraform_plan_digest") == plan_digest,
        "approval_json_digest": approval.get("sanitized_plan_digest") == json_digest,
        "approval_generation": approval.get("generation_id") == manifest.get("generation_id"),
        "approval_commit": approval.get("source_commit") == manifest.get("source_commit"),
        "approval_platform_commit": approval.get("platform_source_commit")
        == manifest.get("platform_source_commit"),
        "approval_platform_package": approval.get("platform_package_digest")
        == manifest.get("platform_package_digest"),
        "approval_deployment_plan": approval.get("deployment_plan_digest")
        == manifest.get("deployment_plan_digest"),
        "approval_validation_status": approval.get("validation_status_digest")
        == manifest.get("validation_status_digest"),
        "approval_environment": approval.get("target_environment")
        == manifest.get("target_environment"),
        "approval_run": approval.get("plan_run_id") == manifest.get("plan_run_id"),
        "approval_attempt": approval.get("plan_run_attempt") == manifest.get("plan_run_attempt"),
        "source_commit": bool(re.fullmatch(r"[0-9a-f]{40}", manifest.get("source_commit", ""))),
        "generation_id": bool(
            re.fullmatch(r"sha256:[0-9a-f]{64}", manifest.get("generation_id", ""))
        ),
        "tenant_id": bool(re.fullmatch(r"[0-9a-fA-F-]{36}", manifest.get("tenant_id", ""))),
        "subscription_id": bool(
            re.fullmatch(r"[0-9a-fA-F-]{36}", manifest.get("subscription_id", ""))
        ),
        "platform_source_commit": bool(
            re.fullmatch(r"[0-9a-f]{40}", manifest.get("platform_source_commit", ""))
        ),
        "platform_package_digest": bool(
            re.fullmatch(r"sha256:[0-9a-f]{64}", manifest.get("platform_package_digest", ""))
        ),
        "deployment_plan_digest": bool(
            re.fullmatch(r"sha256:[0-9a-f]{64}", manifest.get("deployment_plan_digest", ""))
        ),
        "validation_status_digest": bool(
            re.fullmatch(r"sha256:[0-9a-f]{64}", manifest.get("validation_status_digest", ""))
        ),
    }
    if expected_run_id is not None:
        checks["expected_run"] = manifest.get("plan_run_id") == expected_run_id
    if expected_run_attempt is not None:
        checks["expected_attempt"] = manifest.get("plan_run_attempt") == expected_run_attempt
    if expected_environment is not None:
        checks["expected_environment"] = manifest.get("target_environment") == expected_environment
    if reviewed_plan_digest is not None:
        checks["reviewed_plan_digest"] = reviewed_plan_digest.lower() == plan_digest
    if reviewed_json_digest is not None:
        checks["reviewed_json_digest"] = reviewed_json_digest.lower() == json_digest
    if expected_tenant_id is not None:
        checks["expected_tenant"] = (
            manifest.get("tenant_id", "").lower() == expected_tenant_id.lower()
        )
    if expected_subscription_id is not None:
        checks["expected_subscription"] = (
            manifest.get("subscription_id", "").lower() == expected_subscription_id.lower()
        )
    if current_state_snapshot is not None:
        checks["backend_state_unchanged"] = (
            manifest.get("backend", {}).get("state") == _state_identity(current_state_snapshot)
        )
    if project_root is not None:
        governance = _validated_deployment_governance(project_root)
        for key, value in governance.items():
            checks[f"governance_{key}"] = manifest.get(key) == value
        receipt = _read_json(project_root / "generation-receipt.json")
        for key in (
            "platform_version",
            "generation_id",
            "manifest_digest",
            "resolved_plan_digest",
            "template_digest",
            "generated_files_digest",
            "dependency_constraints_digest",
            "platform_source_commit",
            "platform_package_digest",
        ):
            checks[f"receipt_{key}"] = manifest.get(key) == receipt.get(key)
        backend = (
            project_root / "infra/terraform" / f"backend-{manifest['target_environment']}.hcl"
        ).read_text(encoding="utf-8")
        backend_keys = {
            "resource_group": "resource_group_name",
            "storage_account": "storage_account_name",
            "container": "container_name",
            "state_key": "key",
        }
        for key, backend_key in backend_keys.items():
            value = manifest["backend"][key]
            checks[f"backend_{key}"] = bool(
                re.search(
                    rf'^\s*{re.escape(backend_key)}\s*=\s*"{re.escape(value)}"\s*$',
                    backend,
                    re.MULTILINE,
                )
            )
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError("artifact verification failed: " + ", ".join(failed))
    return manifest


def verify(args: argparse.Namespace) -> None:
    manifest = verify_artifact(
        Path(args.artifact_dir).resolve(),
        expected_run_id=args.run_id,
        expected_run_attempt=args.run_attempt,
        expected_environment=args.environment,
        reviewed_plan_digest=args.plan_digest,
        reviewed_json_digest=args.json_digest,
        expected_tenant_id=args.tenant_id,
        expected_subscription_id=args.subscription_id,
        current_state_snapshot=(
            Path(args.current_state_snapshot).resolve() if args.current_state_snapshot else None
        ),
        project_root=Path(args.project_root).resolve() if args.project_root else None,
    )
    if args.github_output:
        output = Path(os.environ["GITHUB_OUTPUT"])
        approval = _read_json(Path(args.artifact_dir).resolve() / "approval-metadata.json")
        with output.open("a", encoding="utf-8") as stream:
            for key in (
                "source_commit",
                "platform_source_commit",
                "platform_package_digest",
                "deployment_plan_digest",
                "validation_status_digest",
                "generation_id",
                "manifest_digest",
                "resolved_plan_digest",
            ):
                stream.write(f"{key}={manifest[key]}\n")
            stream.write(f"plan_requested_by={approval['plan_requested_by']}\n")
            stream.write(f"plan_digest={manifest['terraform_plan_digest']}\n")
            stream.write(f"json_digest={manifest['sanitized_plan_digest']}\n")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create")
    for name in (
        "artifact-dir",
        "terraform-dir",
        "plan",
        "raw-json",
        "generation-receipt",
        "source-commit",
        "run-id",
        "run-attempt",
        "actor",
        "tenant-id",
        "subscription-id",
        "environment",
        "backend-resource-group",
        "backend-storage-account",
        "backend-container",
        "state-key",
        "state-snapshot",
    ):
        create_parser.add_argument(f"--{name}", required=True)
    create_parser.set_defaults(handler=create)
    create_parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    create_parser.add_argument(
        "--maximum-plan-age-hours", type=int, default=DEFAULT_MAXIMUM_PLAN_AGE_HOURS
    )
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--artifact-dir", required=True)
    verify_parser.add_argument("--run-id")
    verify_parser.add_argument("--run-attempt")
    verify_parser.add_argument("--environment")
    verify_parser.add_argument("--plan-digest")
    verify_parser.add_argument("--json-digest")
    verify_parser.add_argument("--tenant-id")
    verify_parser.add_argument("--subscription-id")
    verify_parser.add_argument("--current-state-snapshot")
    verify_parser.add_argument("--project-root")
    verify_parser.add_argument("--github-output", action="store_true")
    verify_parser.set_defaults(handler=verify)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (
        KeyError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        raise SystemExit(f"plan artifact validation failed: {error}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
