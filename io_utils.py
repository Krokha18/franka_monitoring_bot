import os

import pandas as pd
from pathlib import Path

def load_titles_df(file_path):
    if not Path(file_path).exists():
        return pd.DataFrame(columns=["title", "min_date", "max_date"])
    return pd.read_csv(file_path)

def save_titles_df(df, file_path):
    df.to_csv(file_path, index=False)

def load_csv_db(path):
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["last_update"]).fillna({"free_tickets": 0, "message": "", "last_update": pd.NaT})
    else:
        return pd.DataFrame(columns=["link", "free_tickets", "last_update", "message"])

def save_csv_db(df, path):
    df.to_csv(path, index=False)
