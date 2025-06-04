import pandas as pd
from io_utils import load_titles_df, save_titles_df

def add_title(path: str, user_id: int, title: str, min_date, max_date) -> bool:
    df = load_titles_df(path)
    # Перевірка, чи цей user вже має такий title
    if ((df["user_id"] == user_id) & (df["title"] == title)).any():
        return False
    new_row = pd.DataFrame([{
        "user_id": user_id,
        "title": title,
        "min_date": min_date,
        "max_date": max_date
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_titles_df(df, path)
    return True

def remove_title(path: str, user_id: int, title: str) -> bool:
    df = load_titles_df(path)
    cond = (df["user_id"] == user_id) & (df["title"] == title)
    if not cond.any():
        return False
    df = df[~cond]
    save_titles_df(df, path)
    return True

def update_title(path: str, user_id: int, title: str, min_date, max_date) -> bool:
    df = load_titles_df(path)
    cond = (df["user_id"] == user_id) & (df["title"] == title)
    if not cond.any():
        return False
    df.loc[cond, "min_date"] = min_date
    df.loc[cond, "max_date"] = max_date
    save_titles_df(df, path)
    return True

def list_titles(path: str, user_id: int) -> pd.DataFrame:
    df = load_titles_df(path)
    return df[df["user_id"] == user_id].copy()
