import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def upgrade_d6_prompt():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # D6 - 扭矩搅拌器深度加固 Prompt
    prompt_d6 = r'''这是电动搅拌器屏幕，请精准提取三行数值。

【提取逻辑】
1. 第一行（大字）：当前转速 (rotation_speed)。
   - 【极其重要】仔细辨认数字的第一位！转速通常是四位数（例如 1110, 2000），严禁漏掉开头的数字。
   - 必须完整输出看到的每一位数字。
2. 第二行（中字）：扭矩 (torque)。
   - 通常显示为两位数（如 00 或 01）。
3. 第三行（下层）：运行时间 (time)。
   - 格式严格为 MM:SS（如 00:10）。

【要求】
- 严禁抄袭示例数值。
- 严禁输出任何占位符文字。
- 必须严格输出单行 JSON，键名使用中文。

JSON 格式示例：
{"转速": "1110", "扭矩": "00", "运行时间": "00:10"}'''

    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d6, '6'))
    
    conn.commit()
    conn.close()
    print("D6 提示词已升级：强化了对四位数转速的识别指令。")

if __name__ == "__main__":
    upgrade_d6_prompt()
