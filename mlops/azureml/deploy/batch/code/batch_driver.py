from __future__ import annotations

import os
from pathlib import Path

import mlflow
import pandas as pd


def init() -> None:
    global model
    model = mlflow.pyfunc.load_model(os.environ["AZUREML_MODEL_DIR"])


def run(mini_batch: list[str]) -> pd.DataFrame:
    frames = [pd.read_csv(Path(path)) for path in mini_batch]
    frame = pd.concat(frames, ignore_index=True)
    required = ["x1", "x2"]
    if any(column not in frame for column in required):
        raise ValueError(f"batch input must contain {required}")
    result = frame.copy()
    result["prediction"] = model.predict(frame[required])
    return result
