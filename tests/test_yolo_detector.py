import pytest
from PIL import Image
import numpy as np

def test_yolo_detector_detects_instruments():
    from backend.services.yolo_detector import YOLOInstrumentDetector
    detector = YOLOInstrumentDetector(confidence_threshold=0.5)
    # Create a dummy test image
    img = Image.fromarray(np.zeros((480, 640, 3), dtype=np.uint8))
    detections = detector.detect(img)
    # Should return a list of bboxes
    assert isinstance(detections, list)
    # Each bbox should have 5 elements: x1, y1, x2, y2, confidence
    for det in detections:
        assert len(det) == 5
        assert all(isinstance(v, (float, int)) for v in det)

def test_yolo_detector_crop_instrument():
    from backend.services.yolo_detector import YOLOInstrumentDetector
    detector = YOLOInstrumentDetector()
    img = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
    bbox = [100.0, 50.0, 300.0, 200.0, 0.9]
    cropped = detector.crop_instrument(img, bbox)
    assert isinstance(cropped, Image.Image)
    # Cropped should be smaller than original
    assert cropped.width <= img.width
    assert cropped.height <= img.height
