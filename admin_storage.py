import json
import os

ADMINS_FILE = "admins.json"

def load_admins():
    if not os.path.exists(ADMINS_FILE):
        return []
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_admins(admins_list):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins_list, f, indent=2, ensure_ascii=False)
