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
        
        # 强制定位到上级目录下的 last.pt
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        self.model_path = model_path or str(project_root.parent / "last.pt")
        
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
        
        img_w, img_h = image.size
        img_area = img_w * img_h

        if len(results.boxes) > 0:
            boxes = results.boxes.xyxy
            scores = results.boxes.conf
            labels = results.boxes.cls
            
            logger.info(f"[DEBUG_YOLO] Raw boxes from model: {len(boxes)}")
            try:
                with open("yolo_debug_raw.log", "a", encoding="utf-8") as f:
                    f.write(f"Raw boxes: {len(boxes)}\n")
                    for b, s, l in zip(boxes, scores, labels):
                        f.write(f"  Class: {int(l)}, Score: {float(s):.3f}, Box: {[float(x) for x in b]}\n")
            except:
                pass
            for b, s, l in zip(boxes, scores, labels):
                logger.info(f"  [DEBUG_YOLO] Class: {int(l)}, Score: {float(s):.3f}, Box: {[float(x) for x in b]}")
            
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
                
                # --- 智能筛选逻辑 ---
                w = x2 - x1
                h = y2 - y1
                area = w * h
                area_ratio = area / img_area
                aspect_ratio = w / h if h > 0 else 0
                
                # 1. 面积过滤：
                # 如果框占了全图 70% 以上且置信度不高，通常是误检的大底座
                if area_ratio > 0.7 and confidence < 0.6:
                    logger.warning(f"跳过过大的疑似背景框: Class {class_id}, Area {area_ratio:.2%}")
                    continue
                
                # 特殊针对 F7: 如果面积占比太小（小于 1%），在 F7 这种大仪表上很可能是误检
                if class_id == 7 and area_ratio < 0.01:
                    logger.warning(f"跳过过小的 F7 误检框: Area {area_ratio:.2%}")
                    continue

                # 2. 极端长宽比过滤：普通仪表通常比例在 0.2 ~ 6.0 之间
                if aspect_ratio > 10.0 or aspect_ratio < 0.1:
                    logger.warning(f"跳过长宽比畸形的框: Class {class_id}, Ratio {aspect_ratio:.2f}")
                    continue

                # 3. 极小噪声过滤
                if area < 400:
                    continue

                # 存储时附带一个几何评分 (用于后期筛选)
                detections.append([x1, y1, x2, y2, confidence, class_id])
                
        # 默认按置信度排序
        detections.sort(key=lambda x: x[4], reverse=True)
        
        # --- 启发式优化：针对特定仪器的多框筛选 ---
        # 对于 F7 (水浴锅)，通常会同时检出“机身”和“屏幕”。
        # 屏幕面积较小且位于机身内部或边缘，我们优先选择较小的框以确保截取到读数。
        if any(d[5] == 7 for d in detections):
            f7_candidates = [d for d in detections if d[5] == 7]
            if len(f7_candidates) > 1:
                # 按面积排序
                f7_candidates.sort(key=lambda x: (x[2]-x[0])*(x[3]-x[1]))
                best_f7 = f7_candidates[0] # 面积最小的
                # 如果这个最小框的置信度还行，就把它推到最前面
                if best_f7[4] > 0.08:
                    detections.remove(best_f7)
                    detections.insert(0, best_f7)
                    logger.info(f"F7 策略生效：优先选择了较小的屏幕框 (Area: {(best_f7[2]-best_f7[0])*(best_f7[3]-best_f7[1]):.0f})")

        return detections

    def crop_instrument(self, image: Image.Image, bbox: List[float], padding: int = 15) -> Image.Image:
        """Crop instrument region from image using bbox with padding."""
        x1, y1, x2, y2 = map(int, bbox[:4])
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.width, x2 + padding)
        y2 = min(image.height, y2 + padding)
        return image.crop((x1, y1, x2, y2))

