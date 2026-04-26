import sqlite3
import json

db_path = 'backend/experiments.db'
conn = sqlite3.connect(db_path)

new_prompt = """这是一个台式PH计。请从屏幕中提取以下数值：
1. 第一行显示的数字是 PH值 (ph_value)，例如 6.73。
2. 第二行左侧显示的数字是 温度 (temperature)，例如 25.0。
3. 第二行右侧带有百分号(%)的数字是 PTS (pts)，通常为 100.0。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"ph_value": 0.00, "temperature": 0.0, "pts": 100.0}

注意：只输出一行JSON，数值不含单位，无法读取设为null。"""

# Update prompt
conn.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?", (new_prompt, '3'))

# Check if we should rename pts to pth or add it
row = conn.execute("SELECT fields_json FROM instrument_templates WHERE instrument_type = ?", ('3',)).fetchone()
if row:
    fields = json.loads(row[0])
    updated = False
    for f in fields:
        if f['name'] == 'pts':
            f['label'] = 'PTH' 
            updated = True
    if updated:
        conn.execute("UPDATE instrument_templates SET fields_json = ? WHERE instrument_type = ?", (json.dumps(fields), '3'))

conn.commit()
conn.close()
print("PH meter (F3) template updated successfully.")
