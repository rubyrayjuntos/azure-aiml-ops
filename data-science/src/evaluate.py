from __future__ import annotations

import argparse
import json
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.metrics import f1_score


def promotion_decision(
    candidate: float, champion: float | None, minimum_improvement: float
) -> dict:
    promote = champion is None or candidate >= champion + minimum_improvement
    return {
        "promote": promote,
        "metric": "f1",
        "candidate_metric": candidate,
        "champion_metric": champion,
        "minimum_improvement": minimum_improvement,
        "reason": (
            "no_champion"
            if champion is None
            else ("improved" if promote else "not_improved")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-input", required=True)
    parser.add_argument("--test-data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--champion-metric", type=float, default=-1.0)
    parser.add_argument("--minimum-improvement", type=float, default=0.01)
    args = parser.parse_args()
    model = mlflow.sklearn.load_model(args.model_input)
    frame = pd.read_parquet(Path(args.test_data) / "data.parquet")
    score = float(f1_score(frame["target"], model.predict(frame[["x1", "x2"]])))
    mlflow.log_metric("test_f1", score)
    champion_metric = args.champion_metric if args.champion_metric >= 0 else None
    decision = promotion_decision(score, champion_metric, args.minimum_improvement)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "promotion-decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
