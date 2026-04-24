import sqlite3
import json

def update():
    conn = sqlite3.connect('backend/experiments.db')
    cursor = conn.cursor()

    # F3 PH Meter
    f3_prompt = (
        "这是 PH 计（酸度计）的液晶屏幕。\n"
        "请读取屏幕上最大的三个数字：\n"
        "1. ph_value: 屏幕中间最大的数字，通常带 2 位或 3 位小数（如 7.01 或 4.005）。\n"
        "2. temperature: 屏幕下方带 °C 或 MTC 字样的数字（如 25.0）。\n"
        "3. pts: 屏幕下方百分号旁的数字（通常为 100.0 或 98.5）。\n\n"
        "【重要】严格按以下 JSON 格式输出，不要输出任何其他内容：\n"
        "{\"ph_value\": 0.00, \"temperature\": 0.0, \"pts\": 0.0}\n\n"
        "注意：只输出纯数字 JSON，不要含单位，无法读取设为 null。"
    )
    
    f3_fields = [
        {"name": "ph_value", "label": "PH值", "unit": ""},
        {"name": "temperature", "label": "温度", "unit": "°C"},
        {"name": "pts", "label": "PTS", "unit": "%"}
    ]

    cursor.execute('UPDATE instrument_templates SET prompt_template = ?, fields_json = ? WHERE instrument_type = "3"', 
                 (f3_prompt, json.dumps(f3_fields, ensure_ascii=False)))

    # F0 Mixer
    f0_prompt = (
        "这是超级吴英混调器控制屏幕。\n"
        "你需要判断是自动还是手动模式，并提取数值。\n\n"
        "【自动模式识别】：左侧菜单栏 \"自动模式\" 选项高亮时。\n"
        "提取：seg1_speed, seg1_time, seg2_speed, seg2_time, seg3_speed, seg3_time, total_time, remaining_time, current_segment, current_speed。\n\n"
        "【手动模式识别】：左侧菜单栏 \"手动模式\" 选项高亮时。\n"
        "屏幕中央有表格：\n"
        "- high_speed: \"高速\"行的转速\n"
        "- high_time: \"高速\"行的设置时间\n"
        "- low_speed: \"低速\"行的转速\n"
        "- low_time: \"低速\"行的时间\n"
        "- current_speed: 下方实时转速\n\n"
        "【重要】严格按以下格式输出 JSON：\n"
        "自动：{\"mode\": \"auto\", \"current_speed\": 0, \"remaining_time\": 0}\n"
        "手动：{\"mode\": \"manual\", \"high_speed\": 0, \"high_time\": 0, \"low_speed\": 0, \"low_time\": 0, \"current_speed\": 0}\n\n"
        "只输出 JSON，不要输出 Markdown 块或解释。"
    )
    
    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = "0"', (f0_prompt,))

    conn.commit()
    conn.close()
    print("Database templates updated.")

if __name__ == "__main__":
    update()
