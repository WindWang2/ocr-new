import sqlite3

def update_f7_prompt_final():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the even more robust prompt for F7
    f7_prompt = """这是水浴锅（SN: 37844）的控制屏幕。
屏幕上有两行数字：
1. 温度 (temperature)：位于屏幕上方（通常是红色的数字）。请精准读取，并记住：该数字的最后一位始终是小数位。例如：看到 248 请读作 "24.8"；看到 375 请读作 "37.5"。
2. 时间 (time)：位于屏幕下方。请读作整数分钟。例如：看到 789 请读作 "789"。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为文本字符串输出。不要照抄示例里的数字！
{"温度": "填入读取到的温度", "时间": "填入读取到的时间"}

注意：
- 只输出纯数字构成的文本字符串，绝对不要包含任何字母或单位。
- 必须严格执行“温度最后一位是小数”的转换规则。
- 如果某个位置没有数字，请填入 null（不带引号）。
- 绝不要输出 Markdown 代码块，不要有任何解释。"""

    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '7'", (f7_prompt,))
    
    conn.commit()
    conn.close()
    print("F7 (Water Bath) Prompt finalized with strict non-placeholder guidance.")

if __name__ == "__main__":
    update_f7_prompt_final()
