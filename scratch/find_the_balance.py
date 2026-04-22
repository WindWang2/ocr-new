import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.getcwd())

from instrument_reader import InstrumentReader
from config import Config

# 屏蔽杂乱日志
import logging
logging.getLogger("instrument_reader").setLevel(logging.ERROR)

reader = InstrumentReader()
base_path = Path("C:/Users/wangj.KEVIN/Downloads/更换镜头后-测试20260415/更换镜头后-测试20260415")

target_cams = ["F0", "F1", "F3", "F5", "F7", "F8"]

print("--- DESCRIPTIVE AUDIT START ---")

for cam in target_cams:
    cam_dir = base_path / cam
    if not cam_dir.exists(): continue
    
    files = sorted(cam_dir.glob("*.jpg"), key=os.path.getmtime, reverse=True)
    if not files: continue
    
    img_path = str(files[0])
    
    prompt = "Describe the main instrument in this image. Is it an electronic scale, a mixer, or a pH meter? Mention any visible numbers or labels."
    
    try:
        # 使用 analyze_image，它会自动处理 local_vlm 的调用
        result = reader.mm_reader.analyze_image(img_path, prompt, call_type="describe")
        print(f"[{cam}] Description: {result}")
    except Exception as e:
        print(f"[{cam}] ERROR: {e}")

print("--- DESCRIPTIVE AUDIT END ---")
