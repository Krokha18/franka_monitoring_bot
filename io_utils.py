import os
import pandas as pd
from pathlib import Path
from io import BytesIO, StringIO
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

def _is_gcs_path(path: str) -> bool:
    return isinstance(path, str) and path.startswith("gs://")

def _get_gcs_client():
    try:
        return storage.Client()
    except DefaultCredentialsError:
        # локально без creds — повертаємо None, будемо падати вже у функціях на локальному шляху
        return None

def load_titles_df(path: str) -> pd.DataFrame:
    if _is_gcs_path(path):
        client = _get_gcs_client()
        if client is None:
            raise RuntimeError("GCS credentials not found. Set up ADC or GOOGLE_APPLICATION_CREDENTIALS.")
        bucket_name, blob_path = path[5:].split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        if not blob.exists():
            return pd.DataFrame(columns=["title","min_date","max_date"])
        data = blob.download_as_bytes()
        return pd.read_csv(BytesIO(data), parse_dates=['min_date',"max_date"])
    else:
        p = Path(path)
        if not p.exists():
            return pd.DataFrame(columns=["title","min_date","max_date"])
        return pd.read_csv(p)

def save_titles_df(df: pd.DataFrame, path: str):
    if _is_gcs_path(path):
        client = _get_gcs_client()
        if client is None:
            raise RuntimeError("GCS credentials not found. Set up ADC or GOOGLE_APPLICATION_CREDENTIALS.")
        bucket_name, blob_path = path[5:].split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        out = df.to_csv(index=False).encode()
        blob.upload_from_string(out, content_type="text/csv")
    else:
        df.to_csv(path, index=False)

def load_csv_db(path: str) -> pd.DataFrame:
    if _is_gcs_path(path):
        client = _get_gcs_client()
        if client is None:
            raise RuntimeError("GCS credentials not found. Set up ADC or GOOGLE_APPLICATION_CREDENTIALS.")
        bucket_name, blob_path = path[5:].split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        if not blob.exists():
            return pd.DataFrame(columns=["link","free_tickets","last_update","message"])
        data = blob.download_as_bytes()
        return pd.read_csv(BytesIO(data), parse_dates=["last_update"])\
                 .fillna({"free_tickets":0, "message":"", "last_update": pd.NaT})
    else:
        if os.path.exists(path):
            return pd.read_csv(path, parse_dates=["last_update"])\
                     .fillna({"free_tickets":0, "message":"", "last_update": pd.NaT})
        return pd.DataFrame(columns=["link","free_tickets","last_update","message"])

def save_csv_db(df: pd.DataFrame, path: str):
    if _is_gcs_path(path):
        client = _get_gcs_client()
        if client is None:
            raise RuntimeError("GCS credentials not found. Set up ADC or GOOGLE_APPLICATION_CREDENTIALS.")
        bucket_name, blob_path = path[5:].split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        out = df.to_csv(index=False).encode()
        blob.upload_from_string(out, content_type="text/csv")
    else:
        df.to_csv(path, index=False)
