import sys
sys.path.insert(0, '.')
from pathlib import Path
from PIL import Image
from backend.services.yolo_detector import YOLOInstrumentDetector

test_dir = Path(r'C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F6')
bmp_candidates = list(test_dir.rglob("*.bmp")) + list(test_dir.rglob("*.BMP"))
latest_bmp = max(bmp_candidates, key=lambda f: f.stat().st_mtime)

print(f"BMP: {latest_bmp}")
img = Image.open(latest_bmp)
print(f"Original size: {img.size}")

detector = YOLOInstrumentDetector(confidence_threshold=0.1, iou_threshold=0.15)

# 1. Test 1/3 scale
small_img = img.resize((img.size[0]//3, img.size[1]//3), Image.Resampling.LANCZOS)
print(f"Small size (1/3): {small_img.size}")
dets = detector.detect(small_img)
print(f"Detections at 1/3: {dets}")

# 2. Test full scale
print(f"Full size: {img.size}")
dets_full = detector.detect(img)
print(f"Detections at full: {dets_full}")

# 3. Test fixed 500px scale (what was previously used)
max_size = 500
w, h = img.size
scale = max_size / max(w, h)
fixed_img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
print(f"Fixed size (500px): {fixed_img.size}")
dets_fixed = detector.detect(fixed_img)
print(f"Detections at 500px: {dets_fixed}")
