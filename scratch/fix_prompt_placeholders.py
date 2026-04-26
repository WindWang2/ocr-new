import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def fix_all_prompts_placeholders():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # D0 - 混调器：改用具体的数字示例，防止模型复读“数字”二字
    prompt_d0 = r'''这是超级吴菌混调器的控制屏幕。请先根据左侧菜单高亮状态判断模式。

【模式判定】
- 左侧第一个按钮 (A) 高亮：自动模式。
- 左侧第二个按钮 (手形) 高亮：手动模式。

【提取指南】
1. 自动模式：提取屏幕上方三个表格（段一、段二、段三）中“转速(转)”和“时间(S)”下方的数字。
2. 手动模式：提取上方两个表格（高速、低速）中“转速(转)”和“时间(S)”下方的数字。
3. 共有：提取“剩余时长”或“剩余时间”右侧数字，以及“当前转速”右侧数字。

【重要】严禁输出“数字”、“填入”等文字。必须输出你看到的真实数值，如果看不清或不存在，请输出 null。
输出 JSON 格式示例（以自动模式为例）：
{"模式": "自动", "段一转速": "10000", "段一时间": "20", "段二转速": "16000", "段二时间": "20", "段三转速": "22000", "段三时间": "20", "剩余时长": "1", "当前转速": "0"}'''

    # D5 - 张力仪：同样移除“数字”占位符
    prompt_d5 = r'''这是表界面张力仪屏幕。
1. 6行模式：包含上层密度、下层密度。
2. 5行模式：不含密度，底部有“F 值”。

【要求】精准提取标签右侧数值。严禁输出“数字”占位符，严禁输出单位。看不到则填 null。
JSON 格式示例：
{"张力": "0.000", "温度": null, "上层密度": "0.000", "下层密度": "1.000", "上升速度": "10", "下降速度": "10", "F值": "5.0"}'''

    # D1/D2 - 天平
    prompt_d_scale = r'''这是电子天平。读取屏幕中心的数字，注意识别微小的小数点。
JSON 格式：
{"重量": "40.33"}
(注意：必须输出你观察到的真实数字，严禁复读示例值)'''

    # 批量更新
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d0, '0'))
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d5, '5'))
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d_scale, '1'))
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d_scale, '2'))
    
    conn.commit()
    conn.close()
    print("Prompt 占位符污染已修复：移除了‘数字’字样，改用具体格式指引。")

if __name__ == "__main__":
    fix_all_prompts_placeholders()
