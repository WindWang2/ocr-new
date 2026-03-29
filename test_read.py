"""
仪器读数测试脚本（两步：识别 → 读数）
用法: python test_read.py <识别模型> <读数模型> <图片路径> [图片路径 ...]
示例: python test_read.py 2b ocr demo/1.jpg
      python test_read.py 2b-new ocr demo/1.jpg demo/2.jpg
环境变量: LMSTUDIO_BASE_URL=http://192.168.31.127:1234
"""

import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)


def get_unit(instrument_type: str, field: str) -> str:
    from instrument_reader import InstrumentLibrary
    return InstrumentLibrary.INSTRUMENTS.get(instrument_type, {}).get("unit", {}).get(field, "")


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    identify_model = sys.argv[1]
    read_model = sys.argv[2]
    images = sys.argv[3:]

    from instrument_reader import MultimodalModelReader

    identify_reader = MultimodalModelReader(model_name=identify_model)
    read_reader = MultimodalModelReader(model_name=read_model)

    for img_path in images:
        if not Path(img_path).exists():
            print(f"[跳过] 文件不存在: {img_path}")
            continue

        print(f"\n{'='*50}")
        print(f"图片: {img_path}  识别模型: {identify_model}  读数模型: {read_model}")
        print(f"{'='*50}")

        # 第一步：识别仪器类型
        print(f"[步骤1] 识别仪器类型 ({identify_model})...")
        identify_result = identify_reader.identify_instrument(img_path)

        if "error" in identify_result:
            print(f"  失败: {identify_result['error']}")
            continue

        instrument_type = identify_result.get("instrument_type")
        confidence = identify_result.get("confidence", "?")
        from instrument_reader import InstrumentLibrary
        instrument_name = InstrumentLibrary.INSTRUMENTS.get(instrument_type, {}).get("name", instrument_type)
        print(f"  仪器类型: {instrument_type}")
        print(f"  仪器名称: {instrument_name}")
        print(f"  置信度:   {confidence}")

        # 第二步：读取数值
        print(f"[步骤2] 读取数值 ({read_model})...")
        read_result = read_reader.read_instrument(img_path, instrument_type)

        if "error" in read_result:
            print(f"  失败: {read_result['error']}")
            continue

        print(f"  读数 (原始JSON):")
        print("  " + json.dumps(read_result, ensure_ascii=False, indent=2).replace("\n", "\n  "))
        print(f"  读数 (带单位):")
        for k, v in read_result.items():
            if v is not None:
                unit = get_unit(instrument_type, k)
                unit_str = f" {unit}" if unit else ""
                print(f"    {k}: {v}{unit_str}")


if __name__ == "__main__":
    main()
