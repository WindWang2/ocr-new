import sqlite3
import json
import os

DB_PATH = r"C:\Users\wangj.KEVIN\projects\ocr-new\backend\experiments.db"

new_config = {
    "provider": "openai_compatible",
    "model_name": "2b-new",
    "base_url": "http://127.0.0.1:8080",
    "temperature": 0.1,
    "max_tokens": 4000
}

def update_config():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure system_config table exists (it should, but just in case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    config_json = json.dumps(new_config)
    cursor.execute(
        "INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)",
        ("llm_config", config_json)
    )
    
    conn.commit()
    conn.close()
    print("LLM Configuration successfully updated in database.")
    print(f"New Base URL: {new_config['base_url']}")

if __name__ == "__main__":
    update_config()
