"""
方案C测试：glm-ocr 提取文字 → 关键词规则识别仪器类型 → 模型读数
用法: python test_ocr_identify.py <读数模型> <图片路径> [图片路径 ...]
示例: python test_ocr_identify.py 2b-new demo/1.jpg demo/1-2.jpg
环境变量: LMSTUDIO_BASE_URL=http://192.168.31.127:1234
"""

import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

# 关键词规则：按优先级排列
KEYWORD_RULES = [
    # 优先级最高：水质检测仪特征词唯一
    ("water_quality_meter",  ["空白值", "检测值", "吸光度", "透光度"]),
    # 混调器：只看表格行标签
    ("wuying_mixer_auto",    ["段一", "段二", "段三"]),
    ("wuying_mixer_manual",  ["高速", "低速"]),
    # 其他仪器
    ("ph_meter",             ["PTS", "MTC", "pH"]),
    ("surface_tension_meter",["表/界面张力", "上升速度", "下降速度"]),
    ("torque_stirrer",       ["N.cm", "rpm"]),
    ("viscometer_6speed",    ["剪切速率", "表观粘度"]),
    ("temperature_controller",["TEMP", "TIME"]),
    ("electronic_balance",   ["g"]),  # 兜底
]

def identify_by_keywords(ocr_text: str) -> str:
    """根据 OCR 文字用关键词规则识别仪器类型"""
    for instrument_type, keywords in KEYWORD_RULES:
        if all(kw in ocr_text for kw in keywords):
            return instrument_type
    return "unknown"

def get_ocr_text(image_path: str, ocr_model: str, base_url: str) -> str:
    """用 OCR 模型提取图片文字"""
    import base64
    import httpx
    from PIL import Image
    import io

    img = Image.open(image_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    payload = {
        "model": ocr_model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "识别图片中所有文字，原样输出，不要解释。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
        ]}],
        "max_tokens": 500,
        "temperature": 0.0,
    }
    r = httpx.post(f"{base_url}/v1/chat/completions", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def get_unit(instrument_type: str, field: str) -> str:
    from instrument_reader import InstrumentLibrary
    return InstrumentLibrary.INSTRUMENTS.get(instrument_type, {}).get("unit", {}).get(field, "")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    read_model = sys.argv[1]
    images = sys.argv[2:]

    import os
    base_url = os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")
    ocr_model = "glm-ocr"

    from instrument_reader import MultimodalModelReader, InstrumentLibrary
    read_reader = MultimodalModelReader(model_name=read_model)

    for img_path in images:
        if not Path(img_path).exists():
            print(f"[跳过] 文件不存在: {img_path}")
            continue

        print(f"\n{'='*50}")
        print(f"图片: {img_path}")
        print(f"{'='*50}")

        # 步骤1：OCR 提取文字
        print(f"[步骤1] OCR提取文字 ({ocr_model})...")
        try:
            ocr_text = get_ocr_text(img_path, ocr_model, base_url)
            print(f"  OCR内容: {ocr_text[:120].replace(chr(10), ' ')}{'...' if len(ocr_text)>120 else ''}")
        except Exception as e:
            print(f"  OCR失败: {e}")
            continue

        # 步骤2：关键词规则识别
        instrument_type = identify_by_keywords(ocr_text)
        instrument_name = InstrumentLibrary.INSTRUMENTS.get(instrument_type, {}).get("name", instrument_type)
        print(f"[步骤2] 关键词匹配: {instrument_type} ({instrument_name})")

        if instrument_type == "unknown":
            print(f"  未匹配到任何仪器类型")
            print(f"  完整OCR文字:\n{ocr_text}")
            continue

        # 步骤3：模型读数（附带OCR文字作为参考）
        print(f"[步骤3] 读取数值 ({read_model})...")
        read_result = read_reader.read_instrument(img_path, instrument_type, ocr_text=ocr_text)

        if "error" in read_result:
            print(f"  失败: {read_result['error']}")
            continue

        print(f"  读数 (带单位):")
        for k, v in read_result.items():
            if v is not None:
                unit = get_unit(instrument_type, k)
                unit_str = f" {unit}" if unit else ""
                print(f"    {k}: {v}{unit_str}")


if __name__ == "__main__":
    main()
