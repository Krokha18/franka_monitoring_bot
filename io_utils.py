import os
import json

import pandas as pd
from pathlib import Path

def load_titles_df(file_path):
    if not Path(file_path).exists():
        return pd.DataFrame(columns=["title", "min_date", "max_date"])
    return pd.read_csv(file_path)

def save_titles_df(df, file_path):
    df.to_csv(file_path, index=False)


def load_db(db_file):
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_db(db, db_file):
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
