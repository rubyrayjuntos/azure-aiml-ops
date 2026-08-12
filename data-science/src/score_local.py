from __future__ import annotations

import argparse
from pathlib import Path

import mlflow
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-input", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    required = ["x1", "x2"]
    if any(column not in frame for column in required):
        raise ValueError(f"scoring input must contain {required}")
    model = mlflow.pyfunc.load_model(args.model_input)
    result = frame.copy()
    result["prediction"] = model.predict(frame[required])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)


if __name__ == "__main__":
    main()
