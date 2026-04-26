import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def update_d5_adaptive_prompt():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # D5 - 张力仪自适应 Prompt
    prompt_d5 = r'''这是表界面张力仪屏幕。该仪器有两种显示模式，请先观察右侧列表的文字标签再提取。

【模式识别与提取规则】
1. 观察右侧文字列表：
   - 如果列表包含 "上层密度" 和 "下层密度"，说明是 6行模式。
   - 如果列表直接从 "温度" 跳到 "上升速度"，说明是 5行模式，此时通常屏幕最下方中央会有 "F 值"。

2. 请提取以下所有可能的字段，如果图中不存在某项，请务必返回 null（不带引号）：
   - 张力 (tension): "表/界面张力" 右侧数字。
   - 温度 (temperature): "温度" 右侧数值，显示 N/A 则为 null。
   - 上层密度 (upper_density): 如果存在，提取右侧数字。
   - 下层密度 (lower_density): 如果存在，提取右侧数字。
   - 上升速度 (rise_speed): "上升速度" 右侧数字。
   - 下降速度 (fall_speed): "下降速度" 右侧数字。
   - F值 (f_value): 仅在 5行模式下存在，位于屏幕最下方两个圆形按钮中间。

【重要】禁止复读示例，严禁输出Markdown。
必须严格输出一行 JSON，使用中文键名：
{"张力": "数字", "温度": "数字/null", "上层密度": "数字/null", "下层密度": "数字/null", "上升速度": "数字", "下降速度": "数字", "F值": "数字/null"}'''

    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d5, '5'))
    
    conn.commit()
    conn.close()
    print("D5 提示词已更新为自适应模式：支持 5行/6行 界面自动切换。")

if __name__ == "__main__":
    update_d5_adaptive_prompt()
