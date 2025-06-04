import datetime
import pandas as pd
from pathlib import Path
from typing import Optional


def _path_exists(path: str) -> bool:
    if path.startswith("gs://"):
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            return fs.exists(path)
        except Exception:
            return False
    return Path(path).exists()


def read_csv_with_dates(
    path: str,
    parse_dates: Optional[list[str]] = None,
    default_cols: Optional[dict] = None,
) -> pd.DataFrame:
    parse_dates = parse_dates or []
    default_cols = default_cols or {}

    # Мапа Python-типів до pandas dtype
    type_map = {
        str: 'string',
        int: 'int64',
        float: 'float64',
        bool: 'bool',
        pd.Timestamp: 'datetime64[ns]',
        datetime.datetime: 'datetime64[ns]',
        datetime.date: 'datetime64[ns]',
        type(None): 'object',  # якщо значення None
    }

    if not _path_exists(path):
        df = pd.DataFrame(columns=default_cols.keys())
        for col, default_val in default_cols.items():
            val_type = type(default_val)
            dtype = type_map.get(val_type, 'object')
            df[col] = pd.Series(dtype=dtype)
        return df

    df = pd.read_csv(path)

    for col in parse_dates:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df


def save_csv(df: pd.DataFrame, path: str):
    if 'user_id' in df.columns:
        df.sort_values(by=['user_id'], inplace=True)
    df.to_csv(path, index=False)


def load_titles_df(path: str) -> pd.DataFrame:
    return read_csv_with_dates(
        path,
        parse_dates=["min_date", "max_date"],
        default_cols={"user_id": str, "title": str, "min_date": pd.NaT, "max_date": pd.NaT},
    )


def save_titles_df(df: pd.DataFrame, path: str):
    save_csv(df, path)


def load_csv_db(path: str) -> pd.DataFrame:
    df = read_csv_with_dates(
        path,
        parse_dates=["last_update"],
        default_cols={"user_id":str, "link": str, "free_tickets":int, "last_update": pd.NaT, "message": str},
    )
    return df.fillna({
        "free_tickets": 0,
        "message": "",
        "last_update": pd.NaT
    })


def save_csv_db(df: pd.DataFrame, path: str):
    save_csv(df, path)


def load_card_df(path: str) -> pd.DataFrame:
    return read_csv_with_dates(
        path,
        parse_dates=["datetime"],
        default_cols={"card_id": str, "datetime": pd.NaT, "status": str},
    )


def save_card_df(df: pd.DataFrame, path: str):
    save_csv(df, path)
