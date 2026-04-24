"""
中央仪器配置文件：以仪器为核心，记录所有关联元数据。
"""

INSTRUMENT_CONFIGS = {
    "F0": {
        "name": "吴英混调器",
        "yolo_cls_id": 0,
        "camera_id": 0,
        "prompt": "Identify the mixer speed and status. Output JSON: {'speed': 0, 'status': 'running/stopped'}.",
        "post_process": None
    },
    "F1": {
        "name": "电子天平1",
        "yolo_cls_id": 1,
        "camera_id": 3,
        "prompt": "这是电子分析天平1号（SN: 53662），读取屏幕显示的重量数值。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"weight\": 0.00}\n\n注意：\n1. 仔细辨认小数点位置（LED数码管上小数点非常细小，通常在最后两位数字之前）。\n2. 请务必确认小数点！如果你看到 4033，请根据常识判断它应该是 40.33。\n3. 数值单位为g，只输出纯数字不含单位。",
        "post_process": "decimal_correction_2"
    },
    "F2": {
        "name": "电子天平2",
        "yolo_cls_id": 2,
        "camera_id": 3,
        "prompt": "这是电子分析天平2号（SN: 230199），读取屏幕显示的重量数值。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"weight\": 0.00}\n\n注意：\n1. 仔细辨认小数点位置。\n2. 请务必确认小数点！如果你看到 4033，请根据常识判断它应该是 40.33。\n3. 数值单位为g，只输出纯数字不含单位。",
        "post_process": "decimal_correction_2"
    },
    "F3": {
        "name": "PH计",
        "yolo_cls_id": 3,
        "camera_id": 3,
        "prompt": "这是一个台式PH计，读取主屏幕显示的PH值和温度（如果可见）。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"ph\": 0.00, \"temp\": 25.0}",
        "post_process": None
    },
    "F4": {
        "name": "水质检测仪",
        "yolo_cls_id": 4,
        "camera_id": 5,
        "prompt": "这是一个多参数水质检测仪。请读取屏幕上显示的所有指标：\n1. 电导率 (Conductivity, 包含单位如 μS/cm 或 mS/cm)\n2. TDS (包含单位如 mg/L 或 g/L)\n3. 盐度 (Salinity, PSU 或 ppt)\n4. 电阻率 (Resistivity, MΩ·cm)\n5. 温度 (Temp, °C)\n\n【重要】严格按以下格式输出 JSON，不要有任何解释：\n{\"conductivity\": 0.0, \"cond_unit\": \"uS/cm\", \"tds\": 0.0, \"salinity\": 0.0, \"resistivity\": 0.0, \"temp\": 0.0}",
        "post_process": None
    },
    "F5": {
        "name": "表界面张力仪",
        "yolo_cls_id": 5,
        "camera_id": 5,
        "prompt": "这是一个表界面张力仪。请读取主屏幕上的张力值和温度：\n1. 张力值 (Surface Tension, 单位 mN/m)\n2. 温度 (Temp, 单位 °C)\n\n【重要】严格按以下格式输出 JSON：\n{\"tension\": 0.00, \"temp\": 0.0}",
        "post_process": None
    },
    "F6": {
        "name": "搅拌器",
        "yolo_cls_id": 6,
        "camera_id": 7,
        "prompt": "这是一个电动搅拌器。请识别屏幕显示的设定转速和当前转速 (RPM)。\n\n输出 JSON：{\"set_speed\": 0, \"current_speed\": 0}",
        "post_process": None
    },
    "F7": {
        "name": "水浴锅",
        "yolo_cls_id": 7,
        "camera_id": 7,
        "prompt": "这是一个恒温水浴锅。请读取屏幕显示的设定温度和当前实际温度 (°C)。\n\n输出 JSON：{\"set_temp\": 0.0, \"current_temp\": 0.0}",
        "post_process": None
    },
    "F8": {
        "name": "粘度计",
        "yolo_cls_id": 8,
        "camera_id": 8,
        "prompt": "这是一个旋转粘度计。请读取屏幕上所有的关键参数：\n1. 粘度值 (Viscosity, 单位 cP 或 mPa.s)\n2. 扭矩百分比 (Torque %)\n3. 转速 (Speed, RPM)\n4. 转子型号 (Spindle, 如 LV-1, 62号等)\n5. 温度 (Temp, °C)\n\n【重要】严格按以下格式输出 JSON：\n{\"viscosity\": 0.0, \"torque_pct\": 0.0, \"speed_rpm\": 0, \"spindle\": \"\", \"temp\": 0.0}",
        "post_process": None
    }
}

def get_config_by_f_id(f_id: str):
    return INSTRUMENT_CONFIGS.get(f_id)

def get_config_by_yolo_id(yolo_id: int):
    for f_id, cfg in INSTRUMENT_CONFIGS.items():
        if cfg["yolo_cls_id"] == yolo_id:
            return cfg
    return None
