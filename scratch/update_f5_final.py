import sqlite3
import json

def update_f5_final():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f5_prompt = """这是表界面张力仪控制屏幕。请忽略左侧的大黑框（曲线图区域），只关注右侧的文字列表。

按照从上到下的顺序，精准读取每一行右侧对应的数值：
1. 张力 (tension)："表/界面张力"右侧的数字（例如 0.013），必须包含所有位小数。
2. 温度 (temperature)："温度"右侧的数值。如果显示 "N/A"，务必输出 null（不加引号）。
3. 上层密度 (upper_density)："上层密度"右侧的数字（例如 0.000），不要和下面的速度混淆。
4. 下层密度 (lower_density)："下层密度"右侧的数字（例如 1.000）。
5. 上升速度 (rise_speed)："上升速度"右侧的数字（例如 10）。
6. 下降速度 (fall_speed)："下降速度"右侧的数字（例如 10）。
7. F值 (f_value)：屏幕右下角底部，"F 值" 文字右侧的数字（通常在 - 和 + 两个圆形按钮中间，例如 5.0）。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为纯数字字符串输出。
{"张力": "0.013", "温度": null, "上层密度": "0.000", "下层密度": "1.000", "上升速度": "10", "下降速度": "10", "F值": "5.0"}

注意：
- 严禁输出任何单位（如 mN/m, °C, g/cm3, mm/min），只提取纯数字文本。
- 如果某项数值为 0，请务必输出 "0" 而不是单位。
- 绝不要输出 Markdown 代码块，不要有任何解释性文字。"""

    f5_fields = [
        {"name": "tension", "label": "张力", "unit": "mN/m"},
        {"name": "temperature", "label": "温度", "unit": "°C"},
        {"name": "upper_density", "label": "上层密度", "unit": "g/cm³"},
        {"name": "lower_density", "label": "下层密度", "unit": "g/cm³"},
        {"name": "rise_speed", "label": "上升速度", "unit": "mm/min"},
        {"name": "fall_speed", "label": "下降速度", "unit": "mm/min"},
        {"name": "f_value", "label": "F值", "unit": ""}
    ]

    cursor.execute("UPDATE instrument_templates SET prompt_template = ?, fields_json = ? WHERE instrument_type = '5'", 
                 (f5_prompt, json.dumps(f5_fields, ensure_ascii=False)))
    
    conn.commit()
    conn.close()
    print("F5 Prompt finalized with strict visual position guidance.")

if __name__ == "__main__":
    update_f5_final()
