import sqlite3
import json

def update_f5_with_f_value():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the new prompt
    f5_prompt = """这是表界面张力仪控制屏幕。
请读取屏幕上显示的以下七个参数数值，并将它们作为字符串输出：
1. 张力 (tension)：屏幕右侧显示的"表/界面张力"数值，单位 mN/m。可能带有负号，通常有3位小数。
2. 温度 (temperature)："温度"下方的数值。若显示 N/A 则为 null。
3. 上层密度 (upper_density)："上层密度"右侧的数值，单位 g/cm3。
4. 下层密度 (lower_density)："下层密度"右侧的数值，单位 g/cm3。
5. 上升速度 (rise_speed)："上升速度"右侧的数值，单位 mm/min。
6. 下降速度 (fall_speed)："下降速度"右侧的数值，单位 mm/min。
7. F值 (f_value)：屏幕右下角 "F 值" 文字右侧的数值（通常在 - 和 + 按钮之间）。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为纯数字字符串输出。不要照抄示例里的 0！
{"张力": "填入张力数值", "温度": "填入温度数值", "上层密度": "填入数字", "下层密度": "填入数字", "上升速度": "填入数字", "下降速度": "填入数字", "F值": "填入数字"}

注意：
- 只输出纯数字的文本字符串，绝对不要包含任何字母或单位。必须输出屏幕上真实的数字作为文本。
- 如果某个值由于未测量而显示为空白或 N/A，请将其值设为 null（不要加引号）。
- 屏幕上的 F: - / + 是按钮操作，不是数值的正负号，请勿混淆。"""

    # Define the new fields JSON
    f5_fields = [
        {"name": "tension", "label": "张力", "unit": "mN/m"},
        {"name": "temperature", "label": "温度", "unit": "°C"},
        {"name": "upper_density", "label": "上层密度", "unit": "g/cm³"},
        {"name": "lower_density", "label": "下层密度", "unit": "g/cm³"},
        {"name": "rise_speed", "label": "上升速度", "unit": "mm/min"},
        {"name": "fall_speed", "label": "下降速度", "unit": "mm/min"},
        {"name": "f_value", "label": "F值", "unit": ""}
    ]

    # Update the database
    cursor.execute("UPDATE instrument_templates SET prompt_template = ?, fields_json = ? WHERE instrument_type = '5'", 
                 (f5_prompt, json.dumps(f5_fields, ensure_ascii=False)))
    
    # Also update constants.py whitelist if necessary?
    # backend/models/constants.py has 5: ['tension', 'temperature', 'upper_density', 'lower_density', 'rise_speed', 'fall_speed']
    # I should add 'f_value' there too.

    conn.commit()
    conn.close()
    print("F5 Prompt and Fields updated successfully with F-value.")

if __name__ == "__main__":
    update_f5_with_f_value()
