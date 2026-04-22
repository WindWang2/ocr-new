import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.getcwd())

from instrument_reader import InstrumentReader

reader = InstrumentReader()
crop_path = r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F8\crops\000_153245_crop_F8_153246.jpg"

print(f"Final Inspection of: {crop_path}")

if os.path.exists(crop_path):
    # 彻底放松提示词，让模型自由发挥
    prompt = "Look at this image extremely carefully. It is a crop of an industrial instrument. Tell me EXACTLY what you see. Is there a digital screen? If so, what digits are displayed? Include the decimal point if visible."
    
    # analyze_image 会处理所有的消息格式转换
    response = reader.mm_reader.analyze_image(crop_path, prompt, call_type="final_audit")
    print(f"\nModel Verdict: {response}\n")
else:
    print("Crop image not found.")
