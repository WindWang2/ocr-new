import sqlite3

def update_f7_prompt():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f7_prompt = """这是水浴锅（SN: 37844）的控制屏幕。
请读取屏幕上显示的两个数值，并将它们作为字符串输出：
1. 温度 (temperature)：屏幕上方的数字（通常为红色或较大的数字）。注意：该数字的最后一位始终是小数位（例如：看到 375 应该读作 "37.5"；看到 250 应该读作 "25.0"）。
2. 时间 (time)：屏幕下方的数字，单位为分钟（整数）。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为字符串输出：
{"温度": "37.5", "时间": "30"}

注意：
- 只输出纯数字构成的文本字符串，不要含单位。
- 必须严格遵守“温度最后一位是小数”的规则。
- 绝不要输出 Markdown 代码块，不要有任何解释性文字。"""

    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '7'", (f7_prompt,))
    
    conn.commit()
    conn.close()
    print("F7 (Water Bath) Prompt updated with decimal point rules.")

if __name__ == "__main__":
    update_f7_prompt()
