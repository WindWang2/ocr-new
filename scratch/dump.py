import sqlite3
import json

db_path = 'backend/experiments.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT instrument_type, name, prompt_template FROM instrument_templates WHERE instrument_type IN ('0', '1', '2', '3') ORDER BY instrument_type")
rows = cursor.fetchall()

result = {}
for row in rows:
    f_id = f"F{row['instrument_type']}"
    result[f_id] = {
        "name": row['name'],
        "prompt": row['prompt_template']
    }

with open('scratch/dump.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

conn.close()
