import sqlite3

def update_f6_prompt():
    conn = sqlite3.connect('backend/experiments.db')
    cur = conn.cursor()
    
    new_prompt = """这是电动搅拌器（SN: 208721），屏幕显示三行数值：第一行转速 (rotation_speed)、第二行扭矩 (torque)、第三行运行时间 (time)。
请将所有提取的数值作为字符串输出。

【重要】严格按以下 JSON 格式输出，使用中文键名，不要输出任何其他内容：
{"转速": "0", "扭矩": "0", "运行时间": "00:00"}

注意：运行时间字段保留 MM:SS 字符串格式；扭矩可能显示为 00 表示 0N/cm。只输出纯数字文本字符串，不含单位。"""
    
    cur.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (new_prompt, '6'))
    conn.commit()
    conn.close()
    print("F6 Prompt Updated Successfully")

if __name__ == "__main__":
    update_f6_prompt()
