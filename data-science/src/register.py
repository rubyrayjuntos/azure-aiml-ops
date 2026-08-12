from __future__ import annotations

import argparse
import json
from pathlib import Path

import mlflow
import mlflow.sklearn


def should_register(decision: dict) -> bool:
    return decision.get("promote") is True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-input", required=True)
    parser.add_argument("--decision-input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    decision = json.loads(
        (Path(args.decision_input) / "promotion-decision.json").read_text(encoding="utf-8")
    )
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    if not should_register(decision):
        (output / "model-info.json").write_text(
            json.dumps({"registered": False, "decision": decision}, sort_keys=True),
            encoding="utf-8",
        )
        return
    model = mlflow.sklearn.load_model(args.model_input)
    with mlflow.start_run(nested=True) as run:
        mlflow.sklearn.log_model(model, artifact_path="model")
        registered = mlflow.register_model(f"runs:/{run.info.run_id}/model", args.model_name)
    (output / "model-info.json").write_text(
        json.dumps(
            {
                "registered": True,
                "model_name": args.model_name,
                "model_version": str(registered.version),
                "run_id": run.info.run_id,
                "decision": decision,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
