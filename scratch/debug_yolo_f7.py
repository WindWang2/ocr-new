import sys
from pathlib import Path
from PIL import Image

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.yolo_detector import YOLOInstrumentDetector

def test_yolo():
    detector = YOLOInstrumentDetector()
    img_path = r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F7\000_224311.jpg"
    img = Image.open(img_path)
    detections = detector.detect(img)
    
    print(f"Detections for {img_path}:")
    for i, det in enumerate(detections):
        x1, y1, x2, y2, conf, cid = det
        print(f"{i}: Class {cid}, Conf {conf:.3f}, Box [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]")

if __name__ == "__main__":
    test_yolo()
