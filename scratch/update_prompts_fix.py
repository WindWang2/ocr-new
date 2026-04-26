import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def update_templates():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 更新 D5 (Type 5) 提示词 - 移除 0.013 示例
    prompt_d5 = r'''这是表界面张力仪控制屏幕。请忽略左侧的大黑框（曲线图区域），只关注右侧的文字列表。

按照从上到下的顺序，精准读取每一行右侧对应的数值（必须作为字符串输出）：
1. 张力 (tension)："表/界面张力"右侧的数字，必须包含所有位小数。
2. 温度 (temperature)："温度"右侧的数值。如果显示 "N/A"，务必输出 null（不加引号）。
3. 上层密度 (upper_density)："上层密度"右侧的数字。
4. 下层密度 (lower_density)："下层密度"右侧的数字。
5. 上升速度 (rise_speed)："上升速度"右侧的数字。
6. 下降速度 (fall_speed)："下降速度"右侧的数字。
7. F值 (f_value)：屏幕右下角底部，"F 值" 文字右侧的数字（通常在 - 和 + 两个圆形按钮中间）。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为纯数字字符串输出。
{"张力": "0.000", "温度": null, "上层密度": "0.000", "下层密度": "0.000", "上升速度": "0", "下降速度": "0", "F值": "0.0"}

注意：
- 严禁输出任何单位（如 mN/m, °C, g/cm3, mm/min），只提取纯数字文本。
- 如果某项数值为 0，请务必输出 "0" 而不是单位。
- 绝不要输出 Markdown 代码块，不要有任何解释性文字。'''
    
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d5, '5'))

    # 更新 D1 (Type 1) 提示词 - 彻底移除占位符文字
    prompt_d1 = r'''这是电子分析天平1号，读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，使用中文键名，不要输出任何其他内容。读取到的数字必须作为字符串（带双引号）输出：
{"重量": "40.33"}

注意：
1. 仔细辨认小数点位置（LED数码管上小数点非常细小，通常在最后两位数字之前）。
2. 只输出纯数字的文本字符串，不含单位。严禁输出 "读取到的数字" 或 "填入数字" 这种提示文字，必须输出你看到的真实数字。'''
    
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d1, '1'))

    conn.commit()
    conn.close()
    print("D1, D5 提示词模板已更新，已移除数值示例。")

if __name__ == "__main__":
    update_templates()
