from __future__ import annotations

import argparse
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.linear_model import LogisticRegression


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-data", required=True)
    parser.add_argument("--model-output", required=True)
    args = parser.parse_args()
    frame = pd.read_parquet(Path(args.train_data) / "data.parquet")
    model = LogisticRegression(random_state=42).fit(frame[["x1", "x2"]], frame["target"])
    output = Path(args.model_output)
    output.mkdir(parents=True, exist_ok=True)
    mlflow.sklearn.save_model(model, output)
    mlflow.log_param("training_rows", len(frame))


if __name__ == "__main__":
    main()
