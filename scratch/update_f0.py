import sqlite3

def update_f0_prompt():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f0_prompt = """这是超级吴英混调器控制屏幕。
你需要判断当前是自动还是手动模式，并提取屏幕上对应的数值。

【自动模式识别】：左侧菜单栏标有 "自动" 的选项（通常带有一个 (A) 图标）处于高亮/被选中状态时。
此时屏幕中央上方会显示“段一”、“段二”、“段三”三个表格。
请提取以下数值（只输出纯数字）：
- 模式 (mode): "自动" (固定填这个中文字符串)
- 段一转速 (seg1_speed): "段一"表格中"转速(转)"下方的数值
- 段一时间 (seg1_time): "段一"表格中"时间(S)"下方的数值
- 段二转速 (seg2_speed): "段二"表格中"转速(转)"下方的数值
- 段二时间 (seg2_time): "段二"表格中"时间(S)"下方的数值
- 段三转速 (seg3_speed): "段三"表格中"转速(转)"下方的数值
- 段三时间 (seg3_time): "段三"表格中"时间(S)"下方的数值
- 总共时长 (total_time): "总共时长(S)"右侧的数值
- 剩余时长 (remaining_time): "剩余时长(S)"右侧的数值
- 当前段数 (current_segment): "当前段数"右侧的数值
- 当前转速 (current_speed): "当前转速(转)"右侧的数值

【手动模式识别】：左侧菜单栏标有 "手动" 的选项（带有一个手指标志）处于高亮/被选中状态时。
屏幕中央会显示“高速”和“低速”的表格，请提取：
- 模式 (mode): "手动" (固定填这个中文字符串)
- 高速转速 (high_speed): "高速"行的转速
- 高速时间 (high_time): "高速"行的设置时间
- 低速转速 (low_speed): "低速"行的转速
- 低速时间 (low_time): "低速"行的时间
- 当前转速 (current_speed): 下方实时转速

【重要】严格按以下格式输出 JSON，使用中文键名，无法读取的设为 null：
自动模式示例：{"模式": "自动", "段一转速": 10000, "段一时间": 20, "段二转速": 16000, "段二时间": 20, "段三转速": 22000, "段三时间": 20, "总共时长": 60, "剩余时长": 1, "当前段数": 1, "当前转速": 0}
手动模式示例：{"模式": "手动", "高速转速": 0, "高速时间": 0, "低速转速": 0, "低速时间": 0, "当前转速": 0}

注意：
- 只输出纯数字 JSON（除了“模式”字段），绝对不要包含任何单位（如 转、S 等）。
- 绝不要输出 Markdown 代码块，不要解释你的推理过程。"""

    cursor.execute("UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = '0'", (f0_prompt,))
    conn.commit()
    conn.close()
    print("F0 Prompt updated successfully with detailed layout instructions.")

if __name__ == "__main__":
    update_f0_prompt()
