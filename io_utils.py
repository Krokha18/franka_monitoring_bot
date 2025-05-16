import os
import json

def load_titles(titles_file):
    if os.path.exists(titles_file):
        with open(titles_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_titles(titles, titles_file):
    with open(titles_file, "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False, indent=4)


def load_db(db_file):
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_db(db, db_file):
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
