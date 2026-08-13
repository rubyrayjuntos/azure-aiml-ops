from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str], *, root: Path) -> None:
    subprocess.run(command, cwd=root, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".local-runs/current")
    parser.add_argument("--champion-metric", type=float, default=-1.0)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / args.output
    if output.exists():
        raise ValueError(f"local output must not already exist: {output}")
    output.mkdir(parents=True)
    os.environ["MLFLOW_TRACKING_URI"] = f"sqlite:///{(output / 'mlflow.db').resolve()}"
    source = root / "data-science" / "src"
    operation_id = "local-lifecycle"
    evidence = [
        sys.executable,
        "scripts/emit_evidence.py",
        "--local-root",
        str(output / "evidence"),
        "--operation-id",
        operation_id,
        "--provider",
        "local",
        "--capability",
        "ml",
        "--operation",
        "local_lifecycle",
        "--source-run-id",
        operation_id,
    ]
    run([*evidence, "--state", "started", "--source-sequence", "0"], root=root)
    try:
        run(
            [
                sys.executable,
                str(source / "prepare.py"),
                "--input",
                "data/train.csv",
                "--train-output",
                str(output / "train"),
                "--test-output",
                str(output / "test"),
            ],
            root=root,
        )
        run(
            [
                sys.executable,
                str(source / "train.py"),
                "--train-data",
                str(output / "train"),
                "--model-output",
                str(output / "model"),
            ],
            root=root,
        )
        run(
            [
                sys.executable,
                str(source / "evaluate.py"),
                "--model-name",
                "azure-ai-ml-ops-model",
                "--model-input",
                str(output / "model"),
                "--test-data",
                str(output / "test"),
                "--output",
                str(output / "evaluation"),
                "--champion-metric",
                str(args.champion_metric),
            ],
            root=root,
        )
        run(
            [
                sys.executable,
                str(source / "package_model.py"),
                "--model-input",
                str(output / "model"),
                "--decision-input",
                str(output / "evaluation"),
                "--output",
                str(output / "package"),
            ],
            root=root,
        )
        package = json.loads(
            (output / "package" / "package-info.json").read_text(encoding="utf-8")
        )
        if package["packaged"]:
            run(
                [
                    sys.executable,
                    str(source / "score_local.py"),
                    "--model-input",
                    str(output / "package" / "model"),
                    "--input",
                    "data/batch.csv",
                    "--output",
                    str(output / "predictions.csv"),
                ],
                root=root,
            )
    except Exception:
        run([*evidence, "--state", "failed", "--source-sequence", "1"], root=root)
        raise
    run([*evidence, "--state", "succeeded", "--source-sequence", "1"], root=root)
    print(output)


if __name__ == "__main__":
    main()
