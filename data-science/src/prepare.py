from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--train-output", required=True)
    parser.add_argument("--test-output", required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    required = {"x1", "x2", "target"}
    if set(frame.columns) != required:
        raise ValueError(f"training data must contain exactly {sorted(required)}")
    if frame.isna().any().any():
        raise ValueError("training data cannot contain null values")
    train, test = train_test_split(
        frame, test_size=0.25, random_state=42, stratify=frame["target"]
    )
    for destination, data in ((args.train_output, train), (args.test_output, test)):
        path = Path(destination)
        path.mkdir(parents=True, exist_ok=True)
        data.to_parquet(path / "data.parquet", index=False)


if __name__ == "__main__":
    main()
