import os
import pandas as pd
from pathlib import Path
from io import BytesIO, StringIO
from google.cloud import storage

# Initialize a single global client (will pick up credentials from the env)
_gcs_client = storage.Client()

def _is_gcs_path(path: str) -> bool:
    return path.startswith("gs://")

def _parse_gcs_path(gcs_path: str):
    # returns (bucket_name, blob_path)
    _, _, bucket_and_blob = gcs_path.partition("gs://")
    bucket_name, _, blob_path = bucket_and_blob.partition("/")
    return bucket_name, blob_path

def _download_to_buffer(gcs_path: str) -> BytesIO:
    bucket_name, blob_path = _parse_gcs_path(gcs_path)
    bucket = _gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    data = blob.download_as_bytes()
    return BytesIO(data)

def _upload_from_buffer(buf: BytesIO, gcs_path: str, content_type: str = "text/csv"):
    bucket_name, blob_path = _parse_gcs_path(gcs_path)
    bucket = _gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(buf.getvalue(), content_type=content_type)

def load_titles_df(path: str) -> pd.DataFrame:
    """Load titles CSV from disk or GCS."""
    if _is_gcs_path(path):
        try:
            buf = _download_to_buffer(path)
            return pd.read_csv(buf).fillna({"title": "", "min_date": "", "max_date": ""})
        except Exception:
            # treat missing blob same as missing file
            return pd.DataFrame(columns=["title", "min_date", "max_date"])
    else:
        p = Path(path)
        if not p.exists():
            return pd.DataFrame(columns=["title", "min_date", "max_date"])
        return pd.read_csv(p)

def save_titles_df(df: pd.DataFrame, path: str):
    """Save titles DataFrame to disk or GCS."""
    if _is_gcs_path(path):
        buf = StringIO()
        df.to_csv(buf, index=False)
        _upload_from_buffer(BytesIO(buf.getvalue().encode()), path)
    else:
        df.to_csv(path, index=False)

def load_csv_db(path: str) -> pd.DataFrame:
    """Load ticket DB CSV from disk or GCS."""
    parse_dates = ["last_update"]
    if _is_gcs_path(path):
        try:
            buf = _download_to_buffer(path)
            return (pd.read_csv(buf, parse_dates=parse_dates)
                    .fillna({"free_tickets": 0, "message": "", "last_update": pd.NaT}))
        except Exception:
            return pd.DataFrame(columns=["link", "free_tickets", "last_update", "message"])
    else:
        if os.path.exists(path):
            return (pd.read_csv(path, parse_dates=parse_dates)
                    .fillna({"free_tickets": 0, "message": "", "last_update": pd.NaT}))
        else:
            return pd.DataFrame(columns=["link", "free_tickets", "last_update", "message"])

def save_csv_db(df: pd.DataFrame, path: str):
    """Save ticket DB DataFrame to disk or GCS."""
    if _is_gcs_path(path):
        buf = StringIO()
        df.to_csv(buf, index=False)
        _upload_from_buffer(BytesIO(buf.getvalue().encode()), path)
    else:
        df.to_csv(path, index=False)
