import sqlite3

def fix_f5_prompt():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f5_prompt = """这是表界面张力仪控制屏幕。
请读取屏幕上显示的以下六个参数数值，并将它们作为字符串输出：
1. 张力 (tension)：屏幕上方最大的数字，单位 mN/m。可能带有负号，通常有3位小数。
2. 温度 (temperature)：带 °C 单位的数值。若显示 N/A 则为 null。
3. 上层密度 (upper_density)：单位 g/cm3。
4. 下层密度 (lower_density)：单位 g/cm3。
5. 上升速度 (rise_speed)：单位 mm/min。通常在屏幕右下角，如 10。
6. 下降速度 (fall_speed)：单位 mm/min。通常在屏幕右下角，如 10。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为纯数字字符串输出。不要照抄示例里的 0！
{"张力": "填入张力数值", "温度": "填入温度数值", "上层密度": "填入数字", "下层密度": "填入数字", "上升速度": "填入数字", "下降速度": "填入数字"}

注意：
- 只输出纯数字的文本字符串，绝对不要包含任何字母或单位。必须输出屏幕上真实的数字作为文本。
- 如果某个值由于未测量而显示为空白或 N/A，请将其值设为 null（不要加引号）。
- 屏幕上的 F: - / + 是按钮操作，不是数值的正负号，请勿混淆。"""

    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '5'", (f5_prompt,))
    conn.commit()
    conn.close()
    print("F5 Prompt updated to prevent hallucination of zeros.")

if __name__ == "__main__":
    fix_f5_prompt()
