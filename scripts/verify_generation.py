from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

RECEIPT_NAME = "generation-receipt.json"
MUTABLE_GOVERNANCE_PATHS = {
    ".azure/deployment-plan.md",
    ".azure/validate-status.json",
}
IGNORED_RUNTIME_PARTS = {
    ".git",
    ".terraform",
    ".pytest_cache",
    ".ruff_cache",
    ".local-runs",
    "__pycache__",
    "build",
    "dist",
    "mlruns",
    "mlartifacts",
    "mlflow.db",
}


def is_runtime_path(path: Path) -> bool:
    return any(
        part in IGNORED_RUNTIME_PARTS or part.endswith(".egg-info") for part in path.parts
    )


def digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def digest_json(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return digest_bytes(canonical.encode("utf-8"))


def generated_files_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in root.rglob("*") if file.is_file()):
        relative_path = path.relative_to(root)
        relative = relative_path.as_posix()
        if relative == RECEIPT_NAME:
            continue
        if relative in MUTABLE_GOVERNANCE_PATHS:
            continue
        if is_runtime_path(relative_path):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def verify(root: Path) -> dict[str, Any]:
    receipt = json.loads((root / RECEIPT_NAME).read_text(encoding="utf-8"))
    actual_files_digest = generated_files_digest(root)
    source_manifest = yaml.safe_load(
        (root / "platform/source-manifest.yaml").read_text(encoding="utf-8")
    )
    resolved_plan = json.loads(
        (root / "platform/resolved-plan.json").read_text(encoding="utf-8")
    )
    expected = {
        "generated_files_digest": actual_files_digest,
        "manifest_digest": digest_json(source_manifest),
        "resolved_plan_digest": digest_json(resolved_plan),
        "dependency_constraints_digest": digest_bytes((root / "constraints.txt").read_bytes()),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ValueError(f"generation receipt {field} mismatch")
    generation_identity = {
            "platform_version": receipt["platform_version"],
            "manifest_digest": expected["manifest_digest"],
            "resolved_plan_digest": expected["resolved_plan_digest"],
            "template_digest": receipt["template_digest"],
            "generated_files_digest": actual_files_digest,
    }
    if not re.fullmatch(r"[0-9a-f]{40}", receipt.get("platform_source_commit", "")):
        raise ValueError("generation receipt platform source commit is invalid")
    if not re.fullmatch(
        r"sha256:[0-9a-f]{64}", receipt.get("platform_package_digest", "")
    ):
        raise ValueError("generation receipt platform package digest is invalid")
    generation_identity["platform_source_commit"] = receipt["platform_source_commit"]
    generation_identity["platform_package_digest"] = receipt["platform_package_digest"]
    expected_generation_id = digest_json(generation_identity)
    if receipt.get("generation_id") != expected_generation_id:
        raise ValueError("generation receipt generation_id mismatch")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()
    receipt = verify(args.root)
    result = {
        key: receipt[key]
        for key in ("generation_id", "manifest_digest", "resolved_plan_digest")
    }
    if args.github_output:
        output = Path(os.environ["GITHUB_OUTPUT"])
        with output.open("a", encoding="utf-8") as stream:
            for key, value in result.items():
                stream.write(f"{key}={value}\n")
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
