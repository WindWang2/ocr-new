import sys
sys.path.insert(0, '.')
from pathlib import Path
from PIL import Image
import torch
import torchvision.ops as ops
from ultralytics import YOLO

test_dir = Path(r'C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F6')
bmp_candidates = list(test_dir.rglob("*.bmp")) + list(test_dir.rglob("*.BMP"))
latest_bmp = max(bmp_candidates, key=lambda f: f.stat().st_mtime)

print(f"BMP: {latest_bmp}")
img_bmp = Image.open(latest_bmp).convert("RGB")
img_small = img_bmp.resize((500, 375), Image.Resampling.LANCZOS)
img_small.save("test_f6_small.jpg", "JPEG", quality=85)
img_jpg = Image.open("test_f6_small.jpg")

print(f"Small JPG size: {img_jpg.size}")

# Test with YOLO directly through API
import requests
import json
print("Running capture to generate fallback, then trying YOLO...")

