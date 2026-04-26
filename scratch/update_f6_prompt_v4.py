import sqlite3

def update_f6_prompt_v4():
    conn = sqlite3.connect('backend/experiments.db')
    cur = conn.cursor()
    
    # 增加对 7 段码识别的提示，并强调时间格式
    new_prompt = """这是电动搅拌器的控制屏幕。屏幕上有三行 LED 7段数码管显示的数字：
第一行：转速 (rotation_speed)，单位 rpm。
第二行：扭矩 (torque)，单位 N.cm。
第三行：运行时间 (time)，格式必须为 MM:SS。

【特别注意】
1. 识别 1 和 7：请仔细辨别。如果只有一根竖线则为 1，有横折则为 7。
2. 时间格式：必须完整输出 MM:SS。即使分钟是 0，也要输出 00:SS（例如 00:10 而不是 10）。

【输出要求】
严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为文本字符串输出。
{"转速": "填入实际数值", "扭矩": "填入实际数值", "运行时间": "填入实际数值"}

注意：
- 只输出纯数字（或时间格式）的文本字符串，不含单位。
- 扭矩如果显示 00，请读作 "0"。
- 绝不要输出 Markdown 代码块，不要有任何解释性文字。"""
    
    cur.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (new_prompt, '6'))
    conn.commit()
    conn.close()
    print("F6 Prompt V4 Updated Successfully")

if __name__ == "__main__":
    update_f6_prompt_v4()
