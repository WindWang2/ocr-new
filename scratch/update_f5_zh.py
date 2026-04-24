import sqlite3

def update_f5_prompt():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f5_prompt = """这是表界面张力仪控制屏幕。
请读取屏幕上显示的以下六个参数数值：
1. 张力 (tension)：屏幕上方最大的数字，单位 mN/m。可能带有负号，通常有3位小数。
2. 温度 (temperature)：带 °C 单位的数值。若显示 N/A 则为 null。
3. 上层密度 (upper_density)：单位 g/cm3。
4. 下层密度 (lower_density)：单位 g/cm3。
5. 上升速度 (rise_speed)：单位 mm/min。
6. 下降速度 (fall_speed)：单位 mm/min。

【重要】严格按以下 JSON 格式输出，使用中文键名，不要输出任何其他内容（不要Markdown代码块，不要解释）：
{"张力": 0.000, "温度": 0.0, "上层密度": 0.000, "下层密度": 0.000, "上升速度": 0, "下降速度": 0}

注意：
- 只输出纯数字 JSON，绝对不要包含任何字母或单位。
- 如果某个值由于未测量而显示为空白或 N/A，请将其值设为 null。
- 屏幕上的 F: - / + 是按钮操作，不是数值的正负号，请勿混淆。"""

    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '5'", (f5_prompt,))
    conn.commit()
    conn.close()
    print("F5 Prompt updated successfully with Chinese keys.")

if __name__ == "__main__":
    update_f5_prompt()
