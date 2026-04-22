import sqlite3
import json
import os

db_path = r'c:\Users\wangj.KEVIN\projects\ocr-new\backend\experiments.db'

templates = [
    {
        "type": "0", "name": "超级吴英混调度器", 
        "fields_json": json.dumps([
            {"name": "mode", "label": "模式", "unit": ""},
            {"name": "current_speed", "label": "当前转速", "unit": "转"},
            {"name": "total_time", "label": "总时长", "unit": "S"},
            {"name": "remaining_time", "label": "剩余时长", "unit": "S"},
            {"name": "seg1_speed", "label": "段一转速", "unit": "转"},
            {"name": "seg2_speed", "label": "段二转速", "unit": "转"},
            {"name": "seg3_speed", "label": "段三转速", "unit": "转"}
        ]),
        "keywords_json": json.dumps(["mixer", "control", "吴英混"]),
        "prompt_template": """这是超级吴英混调器（SN: 258795）控制屏幕。请先判断当前是自动模式还是手动模式（看左侧菜单哪个选项高亮），然后读取对应数值。

自动模式字段：seg1_speed(段一转速,转)、seg1_time(段一时间,S)、seg2_speed(段二转速,转)、seg2_time(段二时间,S)、seg3_speed(段三转速,转)、seg3_time(段三时间,S)、total_time(总时长,S)、remaining_time(剩余时长,S)、current_segment(当前段数)、current_speed(当前转速,转)

手动模式：屏幕中间有一个表格，列标题为"转速(转)"和"时间(S)"，两行分别为"高速"和"低速"。从表格中读取：
- high_speed = "高速"行、"转速(转)"列的数字
- high_time = "高速"行、"时间(S)"列的数字
- low_speed = "低速"行、"转速(转)"列的数字
- low_time = "低速"行、"时间(S)"列的数字
表格下方还有：remaining_time(剩余时间,S)、current_speed(当前转速,转)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
自动模式：{"mode": "auto", "seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0}
手动模式：{"mode": "manual", "high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0}

只输出一行JSON，数值为纯数字不含单位，无法读取的值设为null。"""
    },
    {
        "type": "1", "name": "天平 1", 
        "fields_json": json.dumps([{"name": "weight", "label": "重量", "unit": "g"}]),
        "keywords_json": json.dumps(["balance", "weight", "scale"]),
        "prompt_template": """这是电子天枰1号（SN: 53662），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g，只输出纯数字不含单位。"""
    },
    {
        "type": "2", "name": "天平 2", 
        "fields_json": json.dumps([{"name": "weight", "label": "重量", "unit": "g"}]),
        "keywords_json": json.dumps(["balance", "weight", "scale"]),
        "prompt_template": """这是电子天枰2号（SN: 230199），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g，只输出纯数字不含单位。"""
    },
    {
        "type": "3", "name": "PH 仪", 
        "fields_json": json.dumps([
            {"name": "ph_value", "label": "PH值", "unit": ""},
            {"name": "temperature", "label": "温度", "unit": "°C"},
            {"name": "pts", "label": "PTS", "unit": "%"}
        ]),
        "keywords_json": json.dumps(["ph", "meter", "acidity"]),
        "prompt_template": """这是PH仪（SN: 176585），读取屏幕上的三个数值：pH值(ph_value)、温度(temperature,°C,MTC)、PTS值(pts,%PTS)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"ph_value": 0.00, "temperature": 0.0, "pts": 0.0}

注意：pH值通常带2位小数，温度带1位小数，PTS通常为100.0。只输出一行JSON，数值不含单位，无法读取设为null。"""
    },
    {
        "type": "4", "name": "水质检测仪", 
        "fields_json": json.dumps([
            {"name": "content_mg_l", "label": "含量", "unit": "mg/L"},
            {"name": "transmittance", "label": "透光度", "unit": "%"},
            {"name": "absorbance", "label": "吸光度", "unit": ""},
            {"name": "test_value", "label": "检测值", "unit": ""},
            {"name": "blank_value", "label": "空白值", "unit": ""}
        ]),
        "keywords_json": json.dumps(["water", "quality", "analyzer"]),
        "prompt_template": """这是水质检测仪（SN: 43373），检测总硬度。请先判断当前是高量程还是低量程模式，然后读取屏幕显示的所有数值。

读数字段：当前量程模式(mode)、检测日期(date)、空白值(blank_value)、检测值(test_value)、吸光度(absorbance)、含量mg/L(content_mg_l)、透光度%(transmittance)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"mode": "high", "date": "", "blank_value": 0, "test_value": 0, "absorbance": 0.000, "content_mg_l": 0.00, "transmittance": 0.0}

注意：mode字段为"high"（高量程）或"low"（低量程），date字段为字符串（格式xxxx-xx-xx xx:xx:xx），其他字段为数值，无法读取设为null。只输出一行JSON。"""
    },
    {
        "type": "5", "name": "表界面张力仪", 
        "fields_json": json.dumps([
            {"name": "tension", "label": "张力值", "unit": "mN/m"},
            {"name": "temperature", "label": "温度", "unit": "°C"},
            {"name": "upper_density", "label": "上层密度", "unit": "g/cm3"},
            {"name": "lower_density", "label": "下层密度", "unit": "g/cm3"},
            {"name": "rise_speed", "label": "上升速度", "unit": "mm/min"},
            {"name": "fall_speed", "label": "下降速度", "unit": "mm/min"}
        ]),
        "keywords_json": json.dumps(["tension", "meter", "surface"]),
        "prompt_template": """这是表界面张力仪（SN: 101663），读取屏幕上的六个数值：表/界面张力(tension,nN/m)、温度(temperature,°C)、上层密度(upper_density,g/cm3)、下层密度(lower_density,g/cm3)、上升速度(rise_speed,mm/min)、下降速度(fall_speed,mm/min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"tension": 0.000, "temperature": 0.0, "upper_density": 0.000, "lower_density": 0.000, "rise_speed": 0, "fall_speed": 0}

注意：张力通常带3位小数，可能为负数；温度若显示N/A则设为null；F值旁的-/+是按钮不是正负号。只输出一行JSON，数值不含单位。"""
    },
    {
        "type": "6", "name": "电动搅拌器", 
        "fields_json": json.dumps([
            {"name": "rotation_speed", "label": "转速", "unit": "rpm"},
            {"name": "torque", "label": "扭矩", "unit": "N/cm"},
            {"name": "time", "label": "运行时间", "unit": ""}
        ]),
        "keywords_json": json.dumps(["stirrer", "electric", "mixer"]),
        "prompt_template": """这是电动搅拌器（SN: 208721），屏幕显示三行数值：第一行转速(rotation_speed,rpm)、第二行张力(torque,N/cm)、第三行时间(time,XX:XX)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"rotation_speed": 0, "torque": 0, "time": "00:00"}

注意：time字段保留MM:SS字符串格式；torque可能显示为00表示0N/cm。只输出一行JSON，数值不含单位。"""
    },
    {
        "type": "7", "name": "水浴锅", 
        "fields_json": json.dumps([
            {"name": "temperature", "label": "温度", "unit": "°C"},
            {"name": "time", "label": "时间", "unit": "min"}
        ]),
        "keywords_json": json.dumps(["water", "bath", "temp"]),
        "prompt_template": """这是水浴锅（SN: 37844），读取屏幕显示的温度(temperature,°C)和定时时间(time,min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"temperature": 0.0, "time": 0}

注意：TEMP标签下方为温度（通常带1位小数，LED数码管小数点很小，如"17.3"），TIME标签下方为时间（整数分钟）。只输出一行JSON，数值不含单位。"""
    },
    {
        "type": "8", "name": "6速旋转粘度计", 
        "fields_json": json.dumps([
            {"name": "actual_reading", "label": "实时读数", "unit": ""},
            {"name": "max_reading", "label": "最大读数", "unit": ""},
            {"name": "min_reading", "label": "最小读数", "unit": ""},
            {"name": "rotation_speed", "label": "转速", "unit": "RPM"},
            {"name": "apparent_viscosity", "label": "粘度", "unit": "mPa·s"}
        ]),
        "keywords_json": json.dumps(["viscosity", "viscometer"]),
        "prompt_template": """这是6速旋转粘度计（SN: 106833），读取屏幕上的八个数值：实施读数(actual_reading)、最大读数(max_reading)、最小读数(min_reading)、转速(rotation_speed,RPM)、剪切速率(shear_rate,S-1)、剪切应力(shear_stress,Pa)、表观粘度(apparent_viscosity,mpa.s)、5秒平均值(avg_5s,mpa.s)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 0.000, "apparent_viscosity": 0.0, "avg_5s": 0.0}

只输出一行JSON，数值不含单位，无法读取设为null。"""
    }
]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

for t in templates:
    cur.execute('''
        INSERT INTO instrument_templates (instrument_type, name, fields_json, keywords_json, prompt_template)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(instrument_type) DO UPDATE SET
            name=excluded.name,
            fields_json=excluded.fields_json,
            keywords_json=excluded.keywords_json,
            prompt_template=excluded.prompt_template
    ''', (t["type"], t["name"], t["fields_json"], t["keywords_json"], t["prompt_template"]))
    print(f"Synced template: {t['name']} (ID {t['type']})")

conn.commit()
conn.close()
print("Instrument templates sync complete.")
