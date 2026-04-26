import sqlite3
import json
import os

db_path = os.path.join("backend", "experiments.db")

def check_config():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM system_config WHERE key = 'llm_config'")
        row = cursor.fetchone()
        if row:
            print(f"llm_config: {row['value']}")
        else:
            print("llm_config not found in system_config table")
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_config()
