"""
中央仪器配置文件：以仪器为核心，记录所有关联元数据。
以后仪器统一称为 D0, D1... D8；相机统一称为 F0, F1... F8。
"""

INSTRUMENT_CONFIGS = {
    "D0": {
        "name": "吴英混调器",
        "yolo_cls_id": 0,
        "camera_id": 0,  # 对应物理相机 F0
        "prompt": "Identify the mixer speed and status. Output JSON: {'speed': 0, 'status': 'running/stopped'}.",
        "post_process": None
    },
    "D1": {
        "name": "电子天平1",
        "yolo_cls_id": 1,
        "camera_id": 3,  # 对应物理相机 F3
        "prompt": "这是电子分析天平1号（SN: 53662），读取屏幕显示的重量数值。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"weight\": 0.00}\n\n注意：\n1. 仔细辨认小数点位置（LED数码管上小数点非常细小，通常在最后两位数字之前）。\n2. 请务必确认小数点！如果你看到 4033，请根据常识判断它应该是 40.33。\n3. 数值单位为g，只输出纯数字不含单位。",
        "post_process": "decimal_correction_2"
    },
    "D2": {
        "name": "电子天平2",
        "yolo_cls_id": 2,
        "camera_id": 3,  # 对应物理相机 F3
        "prompt": "这是电子分析天平2号（SN: 230199），读取屏幕显示的重量数值。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"weight\": 0.00}\n\n注意：\n1. 仔细辨认小数点位置。\n2. 请务必确认小数点！如果你看到 4033，请根据常识判断它应该是 40.33。\n3. 数值单位为g，只输出纯数字不含单位。",
        "post_process": "decimal_correction_2"
    },
    "D3": {
        "name": "PH计",
        "yolo_cls_id": 3,
        "camera_id": 3,  # 对应物理相机 F3
        "prompt": "这是一个台式PH计。请从屏幕中提取以下数值：\n1. 第一行显示的数字是 PH值 (ph_value)，例如 6.73。\n2. 第二行左侧显示的数字是 温度 (temperature)，例如 25.0。\n3. 第二行右侧带有百分号(%)的数字是 PTS (pts)，通常为 100.0。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"ph_value\": 0.00, \"temperature\": 0.0, \"pts\": 100.0}",
        "post_process": None
    },
    "D4": {
        "name": "水质检测仪",
        "yolo_cls_id": 4,
        "camera_id": 5,  # 对应物理相机 F5
        "prompt": "这是一个多参数水质检测仪。请读取屏幕上显示的所有指标：\n1. 电导率 (Conductivity, 包含单位如 μS/cm 或 mS/cm)\n2. TDS (包含单位如 mg/L 或 g/L)\n3. 盐度 (Salinity, PSU 或 ppt)\n4. 电阻率 (Resistivity, MΩ·cm)\n5. 温度 (Temp, °C)\n\n【重要】严格按以下格式输出 JSON，不要有任何解释：\n{\"conductivity\": 0.0, \"cond_unit\": \"uS/cm\", \"tds\": 0.0, \"salinity\": 0.0, \"resistivity\": 0.0, \"temp\": 0.0}",
        "post_process": None
    },
    "D5": {
        "name": "表界面张力仪",
        "yolo_cls_id": 5,
        "camera_id": 5,  # 对应物理相机 F5
        "prompt": "这是一个表界面张力仪。请读取主屏幕上的张力值 and 温度：\n1. 张力值 (Surface Tension, 单位 mN/m)\n2. 温度 (Temp, 单位 °C)\n\n【重要】严格按以下格式输出 JSON：\n{\"tension\": 0.00, \"temp\": 0.0}",
        "post_process": None
    },
    "D6": {
        "name": "搅拌器",
        "yolo_cls_id": 6,
        "camera_id": 7,  # 对应物理相机 F7
        "prompt": "这是一个电动搅拌器。屏幕显示三行数值：\n1. 第一行是大字显示的当前转速 (rotation_speed)，单位 RPM。这是一个整数，通常为三位或四位数（例如 1110），且没有小数点。\n2. 第二行是扭矩 (torque)，单位 N/cm。\n3. 第三行是运行时间 (time)，格式通常为 MM:SS。\n\n【重要】严格按以下JSON格式输出，不要输出任何其他内容：\n{\"rotation_speed\": 0, \"torque\": 0.0, \"time\": \"00:00\"}\n\n注意：rotation_speed 必须是整数，请仔细辨认末尾的数字，不要遗漏。只输出一行JSON。",
        "post_process": None,
        "preprocessing": {
            "sharpen": 1.5,
            "contrast": 1.2
        }
    },
    "D7": {
        "name": "水浴锅",
        "yolo_cls_id": 7,
        "camera_id": 7,  # 对应物理相机 F7
        "prompt": "这是一个恒温水浴锅。请读取屏幕显示的设定温度和当前实际温度 (°C)。\n\n输出 JSON：{\"set_temp\": 0.0, \"current_temp\": 0.0}",
        "post_process": None
    },
    "D8": {
        "name": "粘度计",
        "yolo_cls_id": 8,
        "camera_id": 8,  # 对应物理相机 F8
        "prompt": "这是一个旋转粘度计。请读取屏幕上所有的关键参数：\n1. 粘度值 (Viscosity, 单位 cP 或 mPa.s)\n2. 扭矩百分比 (Torque %)\n3. 转速 (Speed, RPM)\n4. 转子型号 (Spindle, 如 LV-1, 62号等)\n5. 温度 (Temp, °C)\n\n【重要】严格按以下格式输出 JSON：\n{\"viscosity\": 0.0, \"torque_pct\": 0.0, \"speed_rpm\": 0, \"spindle\": \"\", \"temp\": 0.0}",
        "post_process": None
    }
}

def get_config_by_d_id(d_id: str):
    """根据仪器 ID (D0-D8) 获取配置"""
    return INSTRUMENT_CONFIGS.get(d_id)

def get_config_by_yolo_id(yolo_id: int):
    """根据 YOLO 类别 ID 获取配置"""
    for d_id, cfg in INSTRUMENT_CONFIGS.items():
        if cfg["yolo_cls_id"] == yolo_id:
            return cfg
    return None
