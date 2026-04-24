import sqlite3
import json

def update_f8_prompt():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    f8_prompt = """这是六速旋转粘度计控制屏幕。屏幕展示了一个包含八行数据的表格。
请精准提取每一行右侧对应的数值，并将它们作为字符串输出：

1. 实时读数 (actual_reading)："实时读数"右侧的数字。
2. 最大读数 (max_reading)："最大读数"右侧的数字（例如 0.03）。
3. 最小读数 (min_reading)："最小读数"右侧的数字（可能带负号，例如 -0.03）。
4. 转速 (rotation_speed)："转速"右侧的数字，单位 RPM。
5. 剪切速率 (shear_rate)："剪切速率"右侧的数字，单位 s-1。
6. 剪切应力 (shear_stress)："剪切应力"右侧的数字，单位 Pa。
7. 表观粘度 (apparent_viscosity)："表观粘度"右侧的数字，单位 mpa.s。
8. 5秒平均值 (avg_5s)："5秒平均值"右侧的数字，单位 mpa.s。

【重要】严格按以下 JSON 格式输出，使用中文键名，所有的数值必须用双引号包裹作为纯数字字符串输出。不要照抄示例里的数字！
{"实时读数": "0", "最大读数": "0.03", "最小读数": "-0.03", "转速": "0", "剪切速率": "0", "剪切应力": "0", "表观粘度": "0", "5秒平均值": "0"}

注意：
- 只输出纯数字的文本字符串，绝对不要包含任何字母或单位（如 RPM, Pa, mpa.s）。
- 如果数值为 0，请务必输出 "0" 字符串。
- 绝不要输出 Markdown 代码块，不要有任何解释性文字。"""

    f8_fields = [
        {"name": "actual_reading", "label": "实时读数", "unit": ""},
        {"name": "max_reading", "label": "最大读数", "unit": ""},
        {"name": "min_reading", "label": "最小读数", "unit": ""},
        {"name": "rotation_speed", "label": "转速", "unit": "RPM"},
        {"name": "shear_rate", "label": "剪切速率", "unit": "s⁻¹"},
        {"name": "shear_stress", "label": "剪切应力", "unit": "Pa"},
        {"name": "apparent_viscosity", "label": "表观粘度", "unit": "mPa·s"},
        {"name": "avg_5s", "label": "5秒平均值", "unit": "mPa·s"}
    ]

    cursor.execute("UPDATE instrument_templates SET prompt_template = ?, fields_json = ? WHERE instrument_type = '8'", 
                 (f8_prompt, json.dumps(f8_fields, ensure_ascii=False)))
    
    conn.commit()
    conn.close()
    print("F8 (Rotational Viscometer) Prompt and Fields updated successfully.")

if __name__ == "__main__":
    update_f8_prompt()
