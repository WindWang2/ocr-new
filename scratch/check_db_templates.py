import sqlite3
import json
import os
from pathlib import Path

db_paths = [
    "experiments.db",
    "backend/database.db",
    "backend/experiments.db",
    "backend/models/database.db"
]

def check_templates(db_path):
    print(f"\n>>> Checking DB: {db_path}")
    if not os.path.exists(db_path):
        print("  File not found.")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instrument_templates'")
        if not cursor.fetchone():
            print("  Table 'instrument_templates' does not exist.")
            return

        cursor.execute("SELECT * FROM instrument_templates WHERE instrument_type IN ('0', '3')")
        rows = cursor.fetchall()
        if not rows:
            print("  No F0 or F3 templates found in this DB.")
        for row in rows:
            d = dict(row)
            print(f"\n  --- Template Type: {d['instrument_type']} ({d['name']}) ---")
            print(f"  Prompt: {d['prompt_template'][:200]}...")
            print(f"  Fields: {d['fields_json']}")
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    for path in db_paths:
        check_templates(path)
