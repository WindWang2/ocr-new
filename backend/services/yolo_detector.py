"""YOLO-based instrument detector."""
import logging
from typing import List
from PIL import Image

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logger = logging.getLogger(__name__)


class YOLOInstrumentDetector:
    """YOLO-based instrument detector.
    Detects instrument regions in a full image, returns list of bounding boxes.
    All output bboxes format: [x1, y1, x2, y2, confidence]
    """

    def __init__(self, model_path: str = None, confidence_threshold: float = 0.5):
        if YOLO is None:
            raise ImportError("ultralytics is required for YOLO detection")
        self.confidence_threshold = confidence_threshold
        self.model_path = model_path or "models/yolo_instrument.pt"
        self._load_model()

    def _load_model(self):
        """Load the YOLO model"""
        import os
        if os.path.exists(self.model_path):
            self.model = YOLO(self.model_path)
        else:
            # Fallback to pretrained yolov8n
            self.model = YOLO("yolov8n.pt")
            logger.warning(f"Fine-tuned model not found at {self.model_path}, using pretrained yolov8n")

    def detect(self, image: Image.Image) -> List[List[float]]:
        """Detect instruments in the given image.
        Returns: List of bboxes: [[x1, y1, x2, y2, confidence], ...]
        """
        results = self.model.predict(image, verbose=False)[0]
        detections = []
        for box in results.boxes:
            confidence = float(box.conf[0])
            if confidence < self.confidence_threshold:
                continue
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            detections.append([x1, y1, x2, y2, confidence])
        detections.sort(key=lambda x: x[4], reverse=True)
        return detections

    def crop_instrument(self, image: Image.Image, bbox: List[float]) -> Image.Image:
        """Crop instrument region from image using bbox."""
        x1, y1, x2, y2 = map(int, bbox[:4])
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.width, x2 + padding)
        y2 = min(image.height, y2 + padding)
        return image.crop((x1, y1, x2, y2))
