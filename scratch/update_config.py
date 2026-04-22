import sqlite3
import json
import os

db_path = 'backend/experiments.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT value FROM system_config WHERE key=?', ('llm_config',))
    row = c.fetchone()
    
    if row:
        config = json.loads(row[0])
    else:
        config = {
            "provider": "local_vlm",
            "model_name": "GLM-OCR",
            "base_url": "C:\\Users\\wangj.KEVIN\\projects\\GLM-OCR",
            "temperature": 0.0
        }
    
    config['max_tokens'] = 2048
    c.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('llm_config', json.dumps(config)))
    conn.commit()
    print(f"Database updated: max_tokens set to 2048. Current config: {config}")
    conn.close()
else:
    print("Database not found")
