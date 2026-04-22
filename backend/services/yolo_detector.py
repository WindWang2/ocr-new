import os
import logging
from typing import List
from PIL import Image
import torchvision.ops as ops
import torch

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logger = logging.getLogger(__name__)


class YOLOInstrumentDetector:
    """YOLO-based instrument detector.
    Detects instrument regions in a full image, returns list of bounding boxes.
    All output bboxes format: [x1, y1, x2, y2, confidence, class_id]
    """

    def __init__(self, model_path: str = None, confidence_threshold: float = 0.1, iou_threshold: float = 0.45, agnostic_nms: bool = True):
        if YOLO is None:
            raise ImportError("ultralytics is required for YOLO detection")
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.agnostic_nms = agnostic_nms
        
        # 强制定位到项目根目录下的 models 文件夹
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        self.model_path = model_path or r"C:\Users\wangj.KEVIN\projects\last.pt"
        
        if not os.path.exists(self.model_path):
            logger.warning(f"指定模型未找到: {self.model_path}, 尝试备选路径...")
            fallback = project_root / "yolov8n.pt"
            if fallback.exists():
                self.model_path = str(fallback)
            else:
                self.model_path = "yolov8n.pt" # 自动下载

        logger.info(f"YOLO 加载模型: {self.model_path} (阈值: {self.confidence_threshold})")
        self._load_model()

    def _load_model(self):
        """Load the YOLO model"""
        import os
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        if os.path.exists(self.model_path):
            self.model = YOLO(self.model_path)
        else:
            # Fallback to pretrained yolov8n
            self.model = YOLO("yolov8n.pt")
            logger.warning(f"Fine-tuned model not found at {self.model_path}, using pretrained yolov8n")
        
        self.model.to(device)
        logger.info(f"YOLO 运行设备: {device}")

    def detect(self, image: Image.Image) -> List[List[float]]:
        """Detect instruments in the given image.
        Returns: List of bboxes: [[x1, y1, x2, y2, confidence, class_id], ...]
        """
        results = self.model.predict(image, verbose=False, conf=self.confidence_threshold)[0]
        detections = []
        
        if len(results.boxes) > 0:
            boxes = results.boxes.xyxy
            scores = results.boxes.conf
            labels = results.boxes.cls
            
            # Apply manual NMS to suppress overlapping boxes from End-to-End models
            if self.agnostic_nms:
                keep = ops.nms(boxes, scores, self.iou_threshold)
            else:
                keep = ops.batched_nms(boxes, scores, labels, self.iou_threshold)
                
            filtered_boxes = boxes[keep]
            filtered_scores = scores[keep]
            filtered_labels = labels[keep]
            
            for box, score, label in zip(filtered_boxes, filtered_scores, filtered_labels):
                x1, y1, x2, y2 = map(float, box)
                confidence = float(score)
                class_id = int(label)
                detections.append([x1, y1, x2, y2, confidence, class_id])
                
        detections.sort(key=lambda x: x[4], reverse=True)
        return detections

    def crop_instrument(self, image: Image.Image, bbox: List[float], padding: int = 15) -> Image.Image:
        """Crop instrument region from image using bbox with padding."""
        x1, y1, x2, y2 = map(int, bbox[:4])
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.width, x2 + padding)
        y2 = min(image.height, y2 + padding)
        return image.crop((x1, y1, x2, y2))

