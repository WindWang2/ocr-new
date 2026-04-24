import sqlite3

def fix_balance_prompts():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f1_prompt = """这是电子分析天平1号（SN: 53662），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，使用中文键名，不要输出任何其他内容：
{"重量": 填入你看到的数字}

注意：
1. 仔细辨认小数点位置（LED数码管上小数点非常细小，通常在最后两位数字之前）。
2. 如果看到 4033，请根据常识判断它应该是 40.33。如果屏幕显示 84.2，则输出 84.2。
3. 数值单位为g，只输出纯数字不含单位，不要照抄模板里的文字。"""

    f2_prompt = """这是电子天平2号（SN: 230199），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，使用中文键名，不要输出任何其他内容：
{"重量": 填入你看到的数字}

注意：
1. 仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g。
2. 只输出纯数字不含单位。绝对不要照抄模板里的文字，必须输出屏幕上真实的数字。"""

    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '1'", (f1_prompt,))
    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '2'", (f2_prompt,))
    
    conn.commit()
    conn.close()
    print("F1 and F2 Prompts updated to prevent 0.00 hallucination.")

if __name__ == "__main__":
    fix_balance_prompts()
