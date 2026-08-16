from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import mlflow
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


def init() -> None:
    global model
    model = mlflow.pyfunc.load_model(os.environ["AZUREML_MODEL_DIR"])

    global blob_service, monitoring_container
    storage_account = os.environ.get("MONITORING_STORAGE_ACCOUNT")
    monitoring_container = os.environ.get("MONITORING_CONTAINER", "monitoring")
    if storage_account:
        credential = DefaultAzureCredential(
            managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID")
        )
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=credential,
        )
    else:
        blob_service = None


def run(mini_batch: list[str]) -> pd.DataFrame:
    frames = [pd.read_csv(Path(path)) for path in mini_batch]
    frame = pd.concat(frames, ignore_index=True)
    required = ["x1", "x2"]
    if any(column not in frame for column in required):
        raise ValueError(f"batch input must contain {required}")
    result = frame.copy()
    result["prediction"] = model.predict(frame[required])

    if blob_service is not None:
        try:
            log_frame = result.copy()
            log_frame["logged_at"] = datetime.now(UTC).isoformat()
            now = datetime.now(UTC)
            blob_path = (
                f"monitoring/inference-log/batch/{now:%Y}/{now:%m}/{now:%d}/{uuid.uuid4()}.parquet"
            )
            blob_client = blob_service.get_blob_client(
                container=monitoring_container, blob=blob_path
            )
            blob_client.upload_blob(log_frame.to_parquet(index=False), overwrite=True)
        except Exception:
            logger.exception("Inference logging failed (non-fatal)")

    return result
