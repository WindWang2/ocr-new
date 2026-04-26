import sqlite3

def update_f6_prompt_v2():
    conn = sqlite3.connect('backend/experiments.db')
    cur = conn.cursor()
    
    new_prompt = """这是电动搅拌器的控制屏幕。屏幕上有三行 LED 数字：
1. 第一行：转速 (rotation_speed)，单位 rpm。请读取最上方的数字。
2. 第二行：扭矩 (torque)，单位 N.cm。请读取中间的数字。
3. 第三行：运行时间 (time)，格式为 MM:SS。请读取最下方的数字。

请精准读取当前屏幕显示的这三个数值。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为文本字符串输出。不要照抄示例！
{"转速": "填入读取到的转速", "扭矩": "填入读取到的扭矩", "运行时间": "填入读取到的时间"}

注意：
- 只输出纯数字（或时间格式）的文本字符串，绝对不要包含任何字母或单位（如 rpm, N.cm）。
- 扭矩如果显示 00，请读作 "0"。
- 时间必须保留 MM:SS 格式。
- 绝不要输出 Markdown 代码块，不要有任何解释性文字。"""
    
    cur.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (new_prompt, '6'))
    conn.commit()
    conn.close()
    print("F6 Prompt V2 Updated Successfully")

if __name__ == "__main__":
    update_f6_prompt_v2()
