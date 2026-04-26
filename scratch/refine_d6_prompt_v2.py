import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def refine_d6_prompt():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # D6 - 扭矩搅拌器：更科学的边缘识别指令
    prompt_d6 = r'''这是电动搅拌器屏幕。

【识别任务】
请按照以下三个区域，从上到下精准提取数值：

1. 顶部主区域：提取转速 (rotation_speed)。
   - 【核心准则】请从屏幕数字显示区的“最左侧边缘”开始读数。
   - 特别注意：第一位数字如果是“1”，它非常细窄且靠左，千万不要把它当成边框而漏掉。
   - 完整读取看到的每一个数字，不要主观推测位数。

2. 中间区域：提取扭矩 (torque)。
   - 通常为两位数（如 00）。

3. 底部区域：提取运行时间 (time)。
   - 格式为 MM:SS（如 00:10）。

【输出要求】
- 必须严格输出单行 JSON，使用中文键名。
- 禁止输出单位，禁止复读示例。

JSON 示例：
{"转速": "1110", "扭矩": "00", "运行时间": "00:10"}'''

    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d6, '6'))
    
    conn.commit()
    conn.close()
    print("D6 提示词已精修：转向“从左边缘开始扫描”的视觉策略。")

if __name__ == "__main__":
    refine_d6_prompt()
