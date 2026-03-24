"""
仪器读数识别系统
使用 LMStudio 本地部署多模态模型（OpenAI 兼容 API）
相机配置来源：相机.xlsx
"""

import os
import base64
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)


class InstrumentLibrary:
    """通用仪器库定义 - 支持多种常见仪器类型"""

    INSTRUMENTS = {
        "electronic_balance": {
            "name": "电子天平/分析天平",
            "attributes": ["weight"],
            "unit": {"weight": "g"},
            "description": "电子或分析天平，用于测量质量，精度通常0.01g-0.0001g",
            "decimal_places": {"weight": 2},
            "display_type": "LCD/LED数码管",
            "keywords": ["天平", "balance", "称重", "质量"]
        },
        "ph_meter": {
            "name": "pH计/酸度计",
            "attributes": ["ph_value", "temperature", "pts"],
            "unit": {"ph_value": "", "temperature": "°C", "pts": "%PTS"},
            "description": "数字pH计，测量溶液酸碱度，显示温度和PTS值",
            "decimal_places": {"ph_value": 2, "temperature": 1, "pts": 1},
            "display_type": "LCD背光屏",
            "keywords": ["pH", "酸度", "酸碱度", "PH计", "MTC", "INESA"]
        },
        "wuying_mixer_auto": {
            "name": "超级吴英混调器（自动模式）",
            "attributes": ["seg1_speed", "seg1_time", "seg2_speed", "seg2_time", "seg3_speed", "seg3_time", "total_time", "remaining_time", "current_segment", "current_speed"],
            "unit": {"seg1_speed": "转", "seg1_time": "S", "seg2_speed": "转", "seg2_time": "S", "seg3_speed": "转", "seg3_time": "S", "total_time": "S", "remaining_time": "S", "current_segment": "", "current_speed": "转"},
            "description": "超级吴英混调器自动模式，屏幕显示段一/段二/段三的转速和时间、总时长、剩余时长、当前段数和当前转速",
            "decimal_places": {"seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0},
            "display_type": "触摸式液晶屏",
            "keywords": ["吴英", "混调器", "自动", "段一", "段二", "段三", "转速(转)", "时间(S)"]
        },
        "wuying_mixer_manual": {
            "name": "超级吴英混调器（手动模式）",
            "attributes": ["high_speed", "high_time", "low_speed", "low_time", "remaining_time", "current_speed"],
            "unit": {"high_speed": "转", "high_time": "S", "low_speed": "转", "low_time": "S", "remaining_time": "S", "current_speed": "转"},
            "description": "超级吴英混调器手动模式，屏幕显示高速转速与时间、低速转速与时间、剩余时间和当前转速",
            "decimal_places": {"high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0},
            "display_type": "触摸式液晶屏",
            "keywords": ["吴英", "混调器", "手动", "高速", "低速", "转速(转)", "时间(S)"]
        },
        "temperature_controller": {
            "name": "温度控制设备",
            "attributes": ["temperature", "time"],
            "unit": {"temperature": "°C", "time": "min"},
            "description": "恒温培养箱、水浴锅、干燥箱等温度控制设备，可能显示温度和定时时间",
            "decimal_places": {"temperature": 1, "time": 0},
            "display_type": "LED数码管/LCD",
            "keywords": ["温度", "恒温", "培养箱", "水浴", "干燥箱", "TEMP", "TIME"]
        },
        "water_quality_meter": {
            "name": "水质检测仪",
            "attributes": ["date", "blank_value", "test_value", "absorbance", "content_mg_l", "transmittance", "mode"],
            "unit": {"date": "", "blank_value": "", "test_value": "", "absorbance": "", "content_mg_l": "mg/L", "transmittance": "%", "mode": ""},
            "description": "水质检测仪，检测总硬度（高量程或低量程），显示检测日期、空白值、检测值、吸光度、含量、透光度",
            "decimal_places": {"date": 0, "blank_value": 3, "test_value": 3, "absorbance": 3, "content_mg_l": 2, "transmittance": 1, "mode": 0},
            "display_type": "彩色液晶屏",
            "keywords": ["水质", "检测仪", "总硬度", "高量程", "低量程", "硬度"]
        },
        "surface_tension_meter": {
            "name": "表界面张力仪",
            "attributes": ["tension", "temperature", "upper_density", "lower_density", "rise_speed", "fall_speed"],
            "unit": {"tension": "mN/m", "temperature": "°C", "upper_density": "g/cm³", "lower_density": "g/cm³", "rise_speed": "mm/min", "fall_speed": "mm/min"},
            "description": "表界面张力测量仪，显示张力值、温度、上下层密度、升降速度",
            "decimal_places": {"tension": 3, "temperature": 1, "upper_density": 3, "lower_density": 3, "rise_speed": 0, "fall_speed": 0},
            "display_type": "触摸屏",
            "keywords": ["表面张力", "界面张力", "张力仪", "上升速度", "下降速度"]
        },
        "torque_stirrer": {
            "name": "扭矩搅拌器",
            "attributes": ["rotation_speed", "torque", "time"],
            "unit": {"rotation_speed": "rpm", "torque": "N.cm", "time": ""},
            "description": "扭矩搅拌器，屏幕显示三行数值：上方rpm转速、中间N.cm扭矩、下方时间",
            "decimal_places": {"rotation_speed": 0, "torque": 0, "time": 0},
            "display_type": "LED数码管/LCD",
            "keywords": ["扭矩", "搅拌", "N.cm", "rpm", "转速", "扭矩单位"]
        },
        "viscometer_6speed": {
            "name": "6速旋转粘度计",
            "attributes": ["actual_reading", "max_reading", "min_reading", "rotation_speed", "shear_rate", "shear_stress", "apparent_viscosity", "avg_5s"],
            "unit": {"actual_reading": "", "max_reading": "", "min_reading": "", "rotation_speed": "RPM", "shear_rate": "S-1", "shear_stress": "Pa", "apparent_viscosity": "mPa.s", "avg_5s": "mPa.s"},
            "description": "6速旋转粘度计，显示实施读数、最大/最小读数、转速、剪切速率、剪切应力、表观粘度、5秒平均值",
            "decimal_places": {"actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 3, "apparent_viscosity": 1, "avg_5s": 1},
            "display_type": "彩色液晶屏",
            "keywords": ["粘度计", "6速", "旋转粘度"]
        },
        "unknown": {
            "name": "未知仪器",
            "attributes": ["value"],
            "unit": {"value": ""},
            "description": "未能识别的仪器类型，尝试读取显示的数值",
            "decimal_places": {"value": 2},
            "display_type": "未知",
            "keywords": []
        }
    }

    # 相机编号到仪器的映射（来源：相机.xlsx）
    # F0: 超级吴英混调器（自动/手动两种模式）
    # F1: 电子天枰1号  F2: 电子天枰2号
    # F3: PH仪  F4: 水质检测仪  F5: 表界面张力仪
    # F6: 电动搅拌器  F7: 水浴锅  F8: 6速旋转粘度计
    CAMERA_PROMPTS = {
        "F0": """这是超级吴英混调器控制屏幕。请先判断当前是自动模式还是手动模式（看左侧菜单哪个选项高亮），然后读取对应数值。

自动模式字段：seg1_speed(段一转速,转)、seg1_time(段一时间,S)、seg2_speed(段二转速,转)、seg2_time(段二时间,S)、seg3_speed(段三转速,转)、seg3_time(段三时间,S)、total_time(总时长,S)、remaining_time(剩余时长,S)、current_segment(当前段数)、current_speed(当前转速,转)

手动模式：屏幕中间有一个表格，列标题为"转速(转)"和"时间(S)"，两行分别为"高速"和"低速"。从表格中读取：
- high_speed = "高速"行、"转速(转)"列的数字
- high_time = "高速"行、"时间(S)"列的数字
- low_speed = "低速"行、"转速(转)"列的数字
- low_time = "低速"行、"时间(S)"列的数字
表格下方还有：remaining_time(剩余时间,S)、current_speed(当前转速,转)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：

自动模式：{"instrument_type": "wuying_mixer_auto", "readings": {"seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0}, "confidence": 0.95}
手动模式：{"instrument_type": "wuying_mixer_manual", "readings": {"high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0}, "confidence": 0.95}

只输出一行JSON，数值为纯数字不含单位，无法读取的值设为null。
""",

        "F1": """这是电子天枰1号，读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "electronic_balance", "readings": {"weight": 0.00}, "confidence": 0.95}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g。只输出一行JSON，数值不含单位。
""",

        "F2": """这是电子天枰2号，读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "electronic_balance", "readings": {"weight": 0.00}, "confidence": 0.95}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g。只输出一行JSON，数值不含单位。
""",

        "F3": """这是PH仪，读取屏幕上的三个数值：pH值(ph_value)、温度(temperature,°C)、PTS值(pts,%PTS)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "ph_meter", "readings": {"ph_value": 0.00, "temperature": 0.0, "pts": 0.0}, "confidence": 0.95}

注意：pH值通常带2位小数，温度带1位小数，PTS通常为100.0。只输出一行JSON，数值不含单位，无法读取设为null。
""",

        "F4": """这是水质检测仪，检测总硬度。请先判断当前是高量程还是低量程模式，然后读取屏幕显示的所有数值。

读数字段：检测日期(date)、空白值(blank_value)、检测值(test_value)、吸光度(absorbance)、含量mg/L(content_mg_l)、透光度%(transmittance)、当前量程模式(mode)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "water_quality_meter", "readings": {"date": "", "blank_value": 0, "test_value": 0, "absorbance": 0.000, "content_mg_l": 0.00, "transmittance": 0.0, "mode": "high"}, "confidence": 0.95}

注意：date字段为字符串（格式xxxx-xx-xx xx:xx:xx），mode字段为"high"（高量程）或"low"（低量程），其他字段为数值，无法读取设为null。只输出一行JSON。
""",

        "F5": """这是表界面张力仪，读取屏幕上的六个数值：表/界面张力(tension,nN/m)、温度(temperature,°C)、上层密度(upper_density,g/cm3)、下层密度(lower_density,g/cm3)、上升速度(rise_speed,mm/min)、下降速度(fall_speed,mm/min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "surface_tension_meter", "readings": {"tension": 0.000, "temperature": 0.0, "upper_density": 0.000, "lower_density": 0.000, "rise_speed": 0, "fall_speed": 0}, "confidence": 0.95}

注意：张力通常带3位小数，可能为负数；温度若显示N/A则设为null；F值旁的-/+是按钮不是正负号。只输出一行JSON，数值不含单位。
""",

        "F6": """这是电动搅拌器，屏幕显示三行数值：第一行转速(rotation_speed,rpm)、第二行张力(torque,N/cm)、第三行时间(time)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "torque_stirrer", "readings": {"rotation_speed": 0, "torque": 0, "time": "00:00"}, "confidence": 0.95}

注意：time字段保留MM:SS字符串格式；torque可能显示为00表示0N/cm。只输出一行JSON，数值不含单位。
""",

        "F7": """这是水浴锅，读取屏幕显示的温度(temperature,°C)和定时时间(time,min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "temperature_controller", "readings": {"temperature": 0.0, "time": 0}, "confidence": 0.95}

注意：TEMP标签下方为温度（通常带1位小数，LED数码管小数点很小，如"17.3"），TIME标签下方为时间（整数分钟）。只输出一行JSON，数值不含单位。
""",

        "F8": """这是6速旋转粘度计，读取屏幕上的八个数值：实施读数(actual_reading)、最大读数(max_reading)、最小读数(min_reading)、转速(rotation_speed,RPM)、剪切速率(shear_rate,S-1)、剪切应力(shear_stress,Pa)、表观粘度(apparent_viscosity,mpa.s)、5秒平均值(avg_5s,mpa.s)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "viscometer_6speed", "readings": {"actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 0.000, "apparent_viscosity": 0.0, "avg_5s": 0.0}, "confidence": 0.95}

只输出一行JSON，数值不含单位，无法读取设为null。
""",
    }

    # 相机名称到仪器类型的映射（用于结果的 instrument_name 字段）
    CAMERA_INSTRUMENT_NAMES = {
        "F0": "超级吴英混调器",
        "F1": "电子天枰1号",
        "F2": "电子天枰2号",
        "F3": "PH仪",
        "F4": "水质检测仪",
        "F5": "表界面张力仪",
        "F6": "电动搅拌器",
        "F7": "水浴锅",
        "F8": "6速旋转粘度计",
    }

    @classmethod
    def get_camera_prompt(cls, camera_name: str) -> str:
        """根据相机名称（F0-F8）获取专用读取prompt"""
        return cls.CAMERA_PROMPTS.get(camera_name.upper(), "")

    @classmethod
    def get_instrument_prompt(cls, instrument_type: str) -> str:
        """获取特定仪器的读取prompt（简洁版，适配4B小模型）"""
        prompts = {
            "electronic_balance": """这是电子天平，读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "electronic_balance", "readings": {"weight": 0.00}, "confidence": 0.95}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g。只输出一行JSON，数值不含单位。
""",

            "ph_meter": """这是PH仪，读取屏幕上的三个数值：pH值(ph_value)、温度(temperature,°C)、PTS值(pts,%PTS)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "ph_meter", "readings": {"ph_value": 0.00, "temperature": 0.0, "pts": 0.0}, "confidence": 0.95}

注意：pH值通常带2位小数，温度带1位小数，PTS通常为100.0。只输出一行JSON，数值不含单位，无法读取设为null。
""",

            "wuying_mixer_auto": """这是超级吴英混调器控制屏幕，当前为自动模式。读取段一/段二/段三的转速和时间、总时长、剩余时长、当前段数和当前转速。

字段：seg1_speed(段一转速,转)、seg1_time(段一时间,S)、seg2_speed(段二转速,转)、seg2_time(段二时间,S)、seg3_speed(段三转速,转)、seg3_time(段三时间,S)、total_time(总时长,S)、remaining_time(剩余时长,S)、current_segment(当前段数)、current_speed(当前转速,转)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：

{"instrument_type": "wuying_mixer_auto", "readings": {"seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0}, "confidence": 0.95}

只输出一行JSON，数值为纯数字不含单位，无法读取的值设为null。
""",

            "wuying_mixer_manual": """这是超级吴英混调器手动模式屏幕。屏幕中间有一个表格，列标题为"转速(转)"和"时间(S)"，两行分别为"高速"和"低速"。从表格中读取：
- high_speed = "高速"行、"转速(转)"列的数字
- high_time = "高速"行、"时间(S)"列的数字
- low_speed = "低速"行、"转速(转)"列的数字
- low_time = "低速"行、"时间(S)"列的数字
表格下方还有：remaining_time(剩余时间,S)、current_speed(当前转速,转)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：

{"instrument_type": "wuying_mixer_manual", "readings": {"high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0}, "confidence": 0.95}

只输出一行JSON，数值为纯数字不含单位，无法读取的值设为null。
""",

            "temperature_controller": """这是温度控制设备（水浴锅），读取屏幕显示的温度(temperature,°C)和定时时间(time,min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "temperature_controller", "readings": {"temperature": 0.0, "time": 0}, "confidence": 0.95}

注意：TEMP标签下方为温度（通常带1位小数，LED数码管小数点很小），TIME标签下方为时间（整数分钟）。只输出一行JSON，数值不含单位。
""",

            "water_quality_meter": """这是水质检测仪，检测总硬度。请先判断当前是高量程还是低量程模式，然后读取屏幕显示的所有数值。

读数字段：检测日期(date)、空白值(blank_value)、检测值(test_value)、吸光度(absorbance)、含量mg/L(content_mg_l)、透光度%(transmittance)、当前量程模式(mode)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "water_quality_meter", "readings": {"date": "", "blank_value": 0, "test_value": 0, "absorbance": 0.000, "content_mg_l": 0.00, "transmittance": 0.0, "mode": "high"}, "confidence": 0.95}

注意：date字段为字符串（格式xxxx-xx-xx xx:xx:xx），mode字段为"high"或"low"，其他字段为数值，无法读取设为null。只输出一行JSON。
""",

            "surface_tension_meter": """这是表界面张力仪，读取屏幕上的数值：张力(tension,mN/m)、温度(temperature,°C)、上层密度(upper_density,g/cm3)、下层密度(lower_density,g/cm3)、上升速度(rise_speed,mm/min)、下降速度(fall_speed,mm/min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "surface_tension_meter", "readings": {"tension": 0.000, "temperature": 0.0, "upper_density": 0.000, "lower_density": 0.000, "rise_speed": 0, "fall_speed": 0}, "confidence": 0.95}

注意：张力通常带3位小数，可能为负数；温度若显示N/A则设为null。只输出一行JSON，数值不含单位。
""",

            "torque_stirrer": """这是电动搅拌器，屏幕显示三行数值：第一行转速(rotation_speed,rpm)、第二行扭矩(torque,N/cm)、第三行时间(time)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "torque_stirrer", "readings": {"rotation_speed": 0, "torque": 0, "time": "00:00"}, "confidence": 0.95}

注意：time字段保留MM:SS字符串格式；torque可能显示为00表示0N/cm。只输出一行JSON，数值不含单位。
""",

            "viscometer_6speed": """这是6速旋转粘度计，读取屏幕上的八个数值：实施读数(actual_reading)、最大读数(max_reading)、最小读数(min_reading)、转速(rotation_speed,RPM)、剪切速率(shear_rate,S-1)、剪切应力(shear_stress,Pa)、表观粘度(apparent_viscosity,mpa.s)、5秒平均值(avg_5s,mpa.s)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"instrument_type": "viscometer_6speed", "readings": {"actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 0.000, "apparent_viscosity": 0.0, "avg_5s": 0.0}, "confidence": 0.95}

只输出一行JSON，数值不含单位，无法读取设为null。
""",
        }
        return prompts.get(instrument_type, "")

    @classmethod
    def identify_instrument_prompt(cls) -> str:
        """获取仪器类型识别的prompt（仅限相机对应的9种仪器）"""
        prompt = """识别图片中的仪器类型，从以下选项中选择最匹配的一个：

- electronic_balance: 电子天平/分析天平 - 读取屏幕显示的重量数值(g)
- ph_meter: pH计/酸度计 - 读取pH值、温度(°C)、PTS值
- wuying_mixer_auto: 超级吴英混调器（自动模式）- 屏幕显示段一/段二/段三的转速和时间
- wuying_mixer_manual: 超级吴英混调器（手动模式）- 屏幕显示高速/低速的转速和时间
- temperature_controller: 温度控制设备(水浴锅等) - 显示温度(°C)和定时时间(min)
- water_quality_meter: 水质检测仪 - 检测总硬度，显示日期、空白值、检测值、吸光度、含量、透光度
- surface_tension_meter: 表界面张力仪 - 显示张力、温度、密度、升降速度
- torque_stirrer: 扭矩搅拌器 - 显示rpm转速、N.cm扭矩、时间
- viscometer_6speed: 6速旋转粘度计 - 显示实施读数、最大/最小读数、转速、剪切速率、剪切应力、表观粘度

【重要】你必须严格按照以下JSON格式输出，不要输出任何其他内容（不要分析、不要解释、不要思考过程）：

{"instrument_type": "选中的仪器类型标识", "confidence": 0.95}

输出要求：
1. 只输出一行JSON，不要有其他任何文字
2. 不要使用Markdown代码块
3. 不要输出分析过程
4. instrument_type 必须是上述9个选项之一

"""

        return prompt


class MultimodalModelReader:
    """多模态大模型读取器（LMStudio 后端）"""

    def __init__(self, model_name: str = None, base_url: str = None, provider=None):
        """
        初始化模型
        Args:
            model_name: 模型名称，默认从配置读取
            base_url: API地址，默认从配置读取
            provider: LLM Provider 实例（可选，传入时忽略 model_name/base_url）
        """
        if provider is not None:
            self._provider = provider
            self.model_name = provider.model_name
            self.base_url = ""
        else:
            self.base_url = base_url or Config.LMSTUDIO_BASE_URL
            self.model_name = model_name or Config.LMSTUDIO_MODEL

            from backend.services.llm_provider import create_provider, LLMConfig
            self._provider = create_provider(LLMConfig(
                provider=Config.DEFAULT_LLM_PROVIDER,
                model_name=self.model_name,
                base_url=self.base_url,
            ))

        logger.info("使用 LLM 后端, 模型: %s", self.model_name)

    def analyze_image(self, image_path: str, prompt: str, call_type: str = "unknown") -> Dict[str, Any]:
        """使用多模态模型分析图片

        Args:
            image_path: 图片路径
            prompt: 提示词
            call_type: 调用类型（identify/read），用于保存调试文件
        """
        try:
            # 读取图片，非 JPEG/PNG 格式（如 BMP）先转换为 JPEG
            suffix = Path(image_path).suffix.lower()
            if suffix not in ('.jpg', '.jpeg', '.png'):
                from PIL import Image
                import io
                img = Image.open(image_path).convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95)
                image_data = buf.getvalue()
            else:
                with open(image_path, "rb") as f:
                    image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # 调用 LLM Provider
            result_text = self._provider.chat(
                messages=[{"role": "user", "content": prompt}],
                images=[base64_image],
                temperature=Config.MODEL_TEMPERATURE,
                max_tokens=Config.MODEL_MAX_TOKENS,
            )
            logger.debug("模型原始响应: %s", result_text[:500] if len(result_text) > 500 else result_text)

            parsed = self._parse_json_response(result_text)
            if "error" in parsed:
                logger.warning("JSON解析失败，原始响应: %s", result_text)

            # 保存响应到JSON文件（调试用）
            self._save_response_debug(image_path, call_type, prompt, result_text, parsed)

            return parsed
        except Exception as e:
            logger.error("多模态模型分析失败: %s", e)
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """解析JSON响应（支持嵌套JSON、Markdown代码块）"""
        # 清理文本
        text = text.strip()

        # 移除省略号 ...
        text = re.sub(r',\s*\.\.\.\s*', '', text)
        text = re.sub(r'\.\.\.', '', text)

        # 尝试提取 Markdown 代码块中的 JSON
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block_match:
            json_text = code_block_match.group(1).strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass

        try:
            # 先尝试直接解析整个文本
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        try:
            # 提取最外层的 JSON 对象（支持嵌套大括号）
            start = text.find('{')
            if start == -1:
                logger.warning("响应中未找到JSON对象: %s", text[:200])
                return {"error": "响应中未找到JSON对象", "raw_text": text}

            depth = 0
            # 优先从后往前找最后一个完整的JSON对象
            for i in range(len(text) - 1, start - 1, -1):
                if text[i] == '}':
                    # 从start到i检查是否是完整JSON
                    json_str = text[start:i + 1]
                    # 验证大括号匹配
                    depth_check = 0
                    valid = True
                    for c in json_str:
                        if c == '{':
                            depth_check += 1
                        elif c == '}':
                            depth_check -= 1
                            if depth_check < 0:
                                valid = False
                                break
                    if valid and depth_check == 0:
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            pass

            # 如果上面失败，使用原来的方法
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        json_str = text[start:i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.warning("JSON解析错误: %s, JSON内容: %s", e, json_str[:200])
                            return {"error": f"JSON解析错误: {e}", "raw_text": text}
            logger.warning("JSON对象未正确闭合: %s", text[:200])
            return {"error": "JSON对象未正确闭合", "raw_text": text}
        except Exception as e:
            logger.error("解析响应时发生异常: %s", e)
            return {"error": str(e), "raw_text": text}

    def _save_response_debug(self, image_path: str, call_type: str, prompt: str, raw_response: str, parsed: Dict):
        """保存大模型响应到JSON文件（调试用）"""
        from datetime import datetime

        try:
            # 创建json目录
            json_dir = Path("json")
            json_dir.mkdir(exist_ok=True)

            # 生成文件名：图片名_调用类型_时间戳.json
            image_name = Path(image_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{image_name}_{call_type}_{timestamp}.json"
            filepath = json_dir / filename

            # 构建保存数据
            data = {
                "timestamp": datetime.now().isoformat(),
                "image_path": str(image_path),
                "call_type": call_type,
                "model": self.model_name,
                "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                "raw_response": raw_response,
                "parsed_response": parsed
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("响应已保存到: %s", filepath)
        except Exception as e:
            logger.warning("保存调试JSON失败: %s", e)

    def identify_instrument(self, image_path: str) -> Dict[str, Any]:
        """识别仪器类型"""
        prompt = InstrumentLibrary.identify_instrument_prompt()
        return self.analyze_image(image_path, prompt, call_type="identify")

    def read_instrument(self, image_path: str, instrument_type: str) -> Dict[str, Any]:
        """读取仪器数值"""
        prompt = InstrumentLibrary.get_instrument_prompt(instrument_type)
        return self.analyze_image(image_path, prompt, call_type="read")


class InstrumentReader:
    """仪器读数主类 - 仅使用多模态模型"""

    def __init__(self, model_name: str = None, provider=None):
        """
        初始化仪器读数系统
        Args:
            model_name: 多模态模型名称，默认从配置读取
            provider: LLM Provider 实例（可选）
        """
        logger.info("初始化仪器读数系统...")
        if provider is not None:
            logger.info("后端: %s", provider.provider_type)
            logger.info("模型: %s", provider.model_name)
            self.mm_reader = MultimodalModelReader(provider=provider)
        else:
            logger.info("后端: LMStudio")
            logger.info("模型: %s", model_name or Config.LMSTUDIO_MODEL)
            self.mm_reader = MultimodalModelReader(model_name=model_name)

        logger.info("系统初始化完成！")

    @staticmethod
    def _extract_camera_name(image_path: str) -> Optional[str]:
        """
        从图片路径或文件名中提取相机名称（F0-F8）。
        支持路径格式：
          - .../F0/20260314/xxx.jpg
          - .../xxx_F0-I0_OK.jpg
          - .../camera_0/xxx.jpg  → F0
        """
        path_str = str(image_path)

        # 从文件名提取：xxx_F0-I0_OK.jpg
        fname_match = re.search(r'_([Ff]\d)-[Ii]\d', path_str)
        if fname_match:
            return fname_match.group(1).upper()

        # 从目录名提取：.../F0/...
        dir_match = re.search(r'[\\/]([Ff]\d)[\\/]', path_str)
        if dir_match:
            return dir_match.group(1).upper()

        # 从 camera_N 目录提取：.../camera_0/...
        cam_num_match = re.search(r'camera[_\-](\d)', path_str, re.IGNORECASE)
        if cam_num_match:
            return f"F{cam_num_match.group(1)}"

        return None

    def read_instrument(self, image_path: str, camera_name: str = None) -> Dict[str, Any]:
        """
        读取仪器读数。
        若能确定相机名称（F0-F8），直接使用相机专用prompt（单步）；
        否则退回两步识别流程。

        Args:
            image_path: 图片路径
            camera_name: 可选，相机名称如 "F0"。为 None 时自动从路径推断。
        Returns:
            包含识别结果的字典
        """
        logger.info("处理图片: %s", image_path)

        # 尝试确定相机名称
        if camera_name is None:
            camera_name = self._extract_camera_name(image_path)

        if camera_name and camera_name.upper() in InstrumentLibrary.CAMERA_PROMPTS:
            return self._read_by_camera(image_path, camera_name.upper())
        else:
            return self._read_by_identification(image_path)

    def _read_by_camera(self, image_path: str, camera_name: str) -> Dict[str, Any]:
        """使用相机专用prompt直接读取（单步，跳过识别）"""
        logger.info("相机 %s: 使用专用prompt直接读取", camera_name)

        prompt = InstrumentLibrary.get_camera_prompt(camera_name)
        parsed = self.mm_reader.analyze_image(image_path, prompt, call_type="read")

        if "error" in parsed:
            return {"success": False, "error": f"数值读取失败: {parsed['error']}"}

        instrument_type = parsed.get("instrument_type", camera_name.lower())
        instrument_name = InstrumentLibrary.CAMERA_INSTRUMENT_NAMES.get(camera_name, camera_name)
        readings = parsed.get("readings", {})

        result = {
            "success": True,
            "instrument_type": instrument_type,
            "instrument_name": instrument_name,
            "camera_name": camera_name,
            "type_confidence": 1.0,
            "readings": readings,
            "confidence": parsed.get("confidence", 0.9),
            "method": "camera_direct",
        }

        for attr, value in readings.items():
            if value is not None:
                logger.info("  %s: %s", attr, value)

        return result

    def _read_by_identification(self, image_path: str) -> Dict[str, Any]:
        """两步识别流程：先识别仪器类型，再读取数值"""
        # 步骤1: 识别仪器类型
        logger.info("步骤1: 使用多模态模型识别仪器类型...")
        identification = self.mm_reader.identify_instrument(image_path)

        if "error" in identification:
            return {
                "success": False,
                "error": f"仪器类型识别失败: {identification['error']}"
            }

        instrument_type = identification.get("instrument_type", "unknown")
        type_confidence = identification.get("confidence", 0)
        logger.info("识别结果: %s (置信度: %s)", instrument_type, type_confidence)

        # 步骤2: 读取数值
        logger.info("步骤2: 使用多模态模型读取数值...")
        mm_readings = self.mm_reader.read_instrument(image_path, instrument_type)

        if "error" in mm_readings:
            return {
                "success": False,
                "error": f"数值读取失败: {mm_readings['error']}"
            }

        instrument_info = InstrumentLibrary.INSTRUMENTS.get(instrument_type, {})
        result = {
            "success": True,
            "instrument_type": instrument_type,
            "instrument_name": instrument_info.get("name", "未知仪器"),
            "type_confidence": type_confidence,
            "readings": mm_readings.get("readings", {}),
            "confidence": mm_readings.get("confidence", 0.9),
            "method": "multimodal"
        }

        if result["readings"]:
            for attr, value in result["readings"].items():
                if value is not None and instrument_type in InstrumentLibrary.INSTRUMENTS:
                    unit = InstrumentLibrary.INSTRUMENTS[instrument_type]["unit"].get(attr, "")
                    logger.info("  %s: %s %s", attr, value, unit)

        return result

    def batch_read(self, image_dir: str) -> list:
        """批量读取仪器"""
        image_dir = Path(image_dir)
        image_files = []
        for ext in Config.IMAGE_EXTENSIONS:
            image_files.extend(image_dir.glob(f"*{ext}"))
            image_files.extend(image_dir.glob(f"*{ext.upper()}"))

        results = []
        for image_file in image_files:
            result = self.read_instrument(str(image_file))
            result["image_file"] = image_file.name
            results.append(result)

        return results


def main():
    """主函数"""
    reader = InstrumentReader()

    demo_dir = Path("demo")
    if demo_dir.exists():
        print("\n" + "="*60)
        print("开始批量读取demo文件夹中的仪器")
        print("="*60)

        results = reader.batch_read(str(demo_dir))

        print("\n" + "="*60)
        print("读取完成！结果汇总：")
        print("="*60)

        for result in results:
            print(f"\n图片: {result.get('image_file', 'unknown')}")
            print(f"仪器类型: {result.get('instrument_name', 'unknown')}")
            print(f"识别方法: {result.get('method', 'unknown')}")
            if result["success"]:
                for attr, value in result.get("readings", {}).items():
                    if value is not None:
                        instrument_type = result.get("instrument_type", "")
                        if instrument_type in InstrumentLibrary.INSTRUMENTS:
                            unit = InstrumentLibrary.INSTRUMENTS[instrument_type]["unit"].get(attr, "")
                            print(f"  {attr}: {value} {unit}")
    else:
        print("demo文件夹不存在，请确保路径正确")


if __name__ == "__main__":
    main()
