import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def update_d0_prompt():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # D0 - 混调器深度优化 Prompt
    prompt_d0 = r'''这是超级吴菌混调器的控制屏幕。请先通过左侧菜单栏判断运行模式，再根据布局提取数值。

【第一步：模式判定】
查看屏幕左侧垂直排列的四个大按钮：
- 如果第一个按钮（带有 (A) 标志和“自动”字样）处于高亮/激活状态，当前为【自动模式】。
- 如果第二个按钮（带有手形标志和“手动”字样）处于高亮/激活状态，当前为【手动模式】。

【第二步：根据布局提取数值】

1. 如果是【自动模式】：
   - 提取屏幕上方三个表格（段一、段二、段三）中“转速(转)”和“时间(S)”下方的数字。
   - 提取中间行的“剩余时长(S)”右侧数字。
   - 提取底部的“当前转速(转)”右侧数字。
   字段：mode: "自动", seg1_speed, seg1_time, seg2_speed, seg2_time, seg3_speed, seg3_time, remaining_time, current_speed。

2. 如果是【手动模式】：
   - 提取屏幕上方两个表格（高速、低速）中“转速(转)”和“时间(S)”下方的数字。
   - 提取底部的“剩余时间(S)”和“当前转速(转)”中间的数字。
   字段：mode: "手动", high_speed, high_time, low_speed, low_time, remaining_time, current_speed。

【要求】
- 严禁抄袭占位符或示例，必须输出你观察到的真实数字字符串。
- 严禁输出 Markdown 代码块。
- 必须严格输出一行 JSON。

JSON 格式示例（键名使用中文）：
{"模式": "自动/手动", "段一转速": "数字", "段一时间": "数字", "段二转速": "数字", "段二时间": "数字", "段三转速": "数字", "段三时间": "数字", "剩余时长": "数字", "当前转速": "数字"}
(如果是手动模式，请相应调整键名为：高速转速、高速时间、低速转速、低速时间等)'''

    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d0, '0'))
    
    conn.commit()
    conn.close()
    print("D0 提示词已更新：强化了自动/手动模式的视觉布局判定逻辑。")

if __name__ == "__main__":
    update_d0_prompt()
