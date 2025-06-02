import pandas as pd
from io_utils import load_titles_df, save_titles_df

DATE_FMT = "%Y-%m-%d"

def list_titles(path: str):
    return load_titles_df(path)

def add_title(path: str, title: str, min_date=None, max_date=None):
    df = load_titles_df(path)
    if title in df["title"].values:
        return False
    new_row = pd.DataFrame([{"title": title, "min_date": min_date, "max_date": max_date}])
    df = pd.concat([df, new_row], ignore_index=True)
    save_titles_df(df, path)
    return True

def remove_title(path: str, title: str):
    df = load_titles_df(path)
    if title not in df["title"].values:
        return False
    df = df[df["title"] != title]
    save_titles_df(df, path)
    return True

def update_title(path: str, title: str, min_date=None, max_date=None):
    df = load_titles_df(path)
    if title not in df["title"].values:
        return False
    df.loc[df["title"] == title, "min_date"] = min_date
    df.loc[df["title"] == title, "max_date"] = max_date
    save_titles_df(df, path)
    return True
