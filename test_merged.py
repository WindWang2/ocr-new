"""
合并识别+读数为单次调用的测试脚本
用法: python test_merged.py <模型名> <图片路径> [图片路径 ...]
示例: python test_merged.py 2b-new demo/1.jpg
环境变量: LMSTUDIO_BASE_URL=http://192.168.31.127:1234
"""

import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

MERGED_PROMPT = """识别图片中的仪器类型，并同时读取所有数值，一次输出完整结果。

【识别规则】（按优先级顺序判断）
1. 屏幕出现"空白值"、"检测值"、"吸光度"、"透光度"任意字样 → water_quality_meter
2. 中间表格有"段一"、"段二"、"段三"三行 → wuying_mixer_auto（不要看左侧菜单，只看表格行标签）
3. 中间表格有"高速"、"低速"两行 → wuying_mixer_manual（不要看左侧菜单，只看表格行标签）
4. 看到pH/PTS字样 → ph_meter
5. 看到TEMP和TIME两个标签 → temperature_controller
6. 看到张力/密度(g/cm3)/上升速度/下降速度 → surface_tension_meter
7. 看到rpm/N.cm/扭矩 → torque_stirrer
8. 看到剪切速率/表观粘度 → viscometer_6speed
9. 看到重量(g)的LED数码管显示 → electronic_balance

【输出格式】根据识别结果，从下面选一个对应格式，只输出一行JSON：

electronic_balance:    {"instrument_type": "electronic_balance", "weight": 0.00}
ph_meter:              {"instrument_type": "ph_meter", "ph_value": 0.00, "temperature": 0.0, "pts": 0.0}
wuying_mixer_auto:     {"instrument_type": "wuying_mixer_auto", "mode": "auto", "seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0}
wuying_mixer_manual:   {"instrument_type": "wuying_mixer_manual", "mode": "manual", "high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0}
temperature_controller:{"instrument_type": "temperature_controller", "temperature": 0.0, "time": 0}
   注意：温度为LED数码管显示，小数点很小容易漏看，通常带1位小数（如"17.3"不是"173"）
water_quality_meter:   {"instrument_type": "water_quality_meter", "test_item": "", "date": "", "blank_value": 0, "test_value": 0, "absorbance": 0.000, "content_mg_l": 0.00, "transmittance": 0.0}
   注意：content_mg_l只填数字（如0.0），不含"mg/L"；transmittance只填数字（如99.54），不含"%"
surface_tension_meter: {"instrument_type": "surface_tension_meter", "tension": 0.000, "temperature": 0.0, "upper_density": 0.000, "lower_density": 0.000, "rise_speed": 0, "fall_speed": 0, "f_value": 0.0}
torque_stirrer:        {"instrument_type": "torque_stirrer", "rotation_speed": 0, "torque": 0, "time": "00:00"}
viscometer_6speed:     {"instrument_type": "viscometer_6speed", "actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 0.000, "apparent_viscosity": 0.0, "avg_5s": 0.0}

【重要】只输出一行平铺JSON，不要嵌套，不要任何其他内容，无法读取的值设为null。
"""


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    model = sys.argv[1]
    images = sys.argv[2:]

    from instrument_reader import MultimodalModelReader
    reader = MultimodalModelReader(model_name=model)

    for img_path in images:
        if not Path(img_path).exists():
            print(f"[跳过] 文件不存在: {img_path}")
            continue

        print(f"\n{'='*50}")
        print(f"图片: {img_path}  模型: {model}  (单次调用)")
        print(f"{'='*50}")

        result = reader.analyze_image(img_path, MERGED_PROMPT, call_type="merged")

        if "error" in result:
            print(f"  失败: {result['error']}")
            continue

        instrument_type = result.get("instrument_type", "未知")
        print(f"  仪器类型: {instrument_type}")
        print(f"  完整结果:")
        print("  " + json.dumps(result, ensure_ascii=False, indent=2).replace("\n", "\n  "))


if __name__ == "__main__":
    main()
