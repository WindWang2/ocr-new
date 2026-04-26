import sqlite3
import json

db_path = 'backend/experiments.db'
conn = sqlite3.connect(db_path)

# New prompt for F6
new_prompt = """这是一个电动搅拌器。屏幕显示三行数值：
1. 第一行是大字显示的当前转速 (rotation_speed)，单位 RPM。这是一个整数，通常为三位或四位数（例如 1110），且没有小数点。
2. 第二行是扭矩 (torque)，单位 N/cm。
3. 第三行是运行时间 (time)，格式通常为 MM:SS。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"rotation_speed": 0, "torque": 0.0, "time": "00:00"}

注意：rotation_speed 必须是整数，请仔细辨认末尾的数字，不要遗漏。只输出一行JSON。"""

# Update prompt in DB
conn.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?", (new_prompt, '6'))

# Update fields in DB if needed (to match the prompt keys)
# Current keys in DB for F6 were rotation_speed, torque, time in the seed data
conn.commit()
conn.close()
print("Stirrer (F6) template updated successfully.")
