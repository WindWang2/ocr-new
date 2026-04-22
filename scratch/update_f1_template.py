import sqlite3
import json

db_path = "backend/experiments.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

new_prompt = """这是电子分析天平1号（SN: 53662），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：
1. 仔细辨认小数点位置（LED数码管上小数点非常细小，通常在最后两位数字之前）。
2. 请务必确认小数点！如果看到 4033，请根据常识判断它应该是 40.33。
3. 数值单位为g，只输出纯数字不含单位。"""

cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '1'", (new_prompt,))
conn.commit()
conn.close()
print("F1 模板更新成功！")
