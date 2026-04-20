"""Multi-instrument detection pipeline: YOLO -> CLIP -> LLM"""
import logging
from typing import List, Dict, Optional
from PIL import Image

from backend.services.yolo_detector import YOLOInstrumentDetector
from backend.services.clip_matcher import CLIPInstrumentMatcher
from backend.services.llm_provider import get_global_provider
from backend.models.database import get_template
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from instrument_reader import InstrumentReader

logger = logging.getLogger(__name__)


import re
from instrument_reader import InstrumentReader, DynamicInstrumentLibrary

logger = logging.getLogger(__name__)


class MultiInstrumentPipeline:
    """Updated multi-instrument reading pipeline:
    1. YOLO detects and classifies all instruments (class_id 0-8)
    2. System crops each instrument area
    3. LLM reads values for each specific instrument using matched prompts
    """

    def __init__(
        self,
        yolo_model_path: str = None,
        yolo_conf_threshold: float = 0.1, # Lower threshold for better sensitivity
    ):
        self.yolo_detector = YOLOInstrumentDetector(
            model_path=yolo_model_path,
            confidence_threshold=yolo_conf_threshold,
            iou_threshold=0.15,
            agnostic_nms=True
        )
        self.reader = InstrumentReader(provider=get_global_provider())

    def process_image(self, image: Image.Image) -> List[Dict]:
        """Full pipeline: detect -> identify via YOLO class -> read"""
        detections = self.yolo_detector.detect(image)
        results = []

        # 字段白名单，确保数据隔离
        WHITELIST = {
            0: ['mode', 'current_speed', 'total_time', 'remaining_time', 'seg1_speed', 'seg2_speed', 'seg3_speed'],
            1: ['weight'],
            2: ['weight'],
            3: ['ph_value', 'temperature', 'pts'],
            4: ['content_mg_l', 'transmittance', 'absorbance', 'test_value', 'blank_value'],
            5: ['tension', 'temperature', 'upper_density', 'lower_density', 'rise_speed', 'fall_speed'],
            6: ['rotation_speed', 'torque', 'time'],
            7: ['temperature', 'time'],
            8: ['actual_reading', 'max_reading', 'min_reading', 'rotation_speed', 'apparent_viscosity']
        }

        for det in detections:
            x1, y1, x2, y2, yolo_conf, class_id = det
            class_id = int(class_id)
            camera_name = f"F{class_id}"
            
            cropped = self.yolo_detector.crop_instrument(image, det, padding=15)
            
            # 直接通过 YOLO 类别获取 Prompt
            prompt = DynamicInstrumentLibrary.get_camera_prompt(camera_name)
            if not prompt:
                logger.warning(f"No prompt found for class {class_id} (mapped to {camera_name})")
                continue

            try:
                # 调用大模型读取
                raw_readings = self.reader.mm_reader.analyze_image(cropped, prompt, call_type='read')
                
                # 应用白名单过滤，彻底解决“天平出pH”问题
                allowed_fields = WHITELIST.get(class_id, [])
                filtered_readings = {}
                if not isinstance(raw_readings, dict):
                    raw_readings = {}
                    
                for k, v in raw_readings.items():
                    if k in allowed_fields and v is not None:
                        filtered_readings[k] = v

                result = {
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'instrument_type': camera_name,
                    'class_id': class_id,
                    'yolo_confidence': float(yolo_conf),
                    'readings': filtered_readings, # 只返回该仪器的合法字段
                    'read_success': 'error' not in raw_readings,
                    'read_error': raw_readings.get('error'),
                }
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to read instrument {camera_name}: {e}")

        return results

    def _read_instrument(self, image: Image.Image, instrument_type: str) -> Dict:
        # This method is now legacy, using direct reading in process_image
        pass

    def rebuild_clip_cache(self):
        """Rebuild CLIP embedding cache after template changes"""
        self.clip_matcher.invalidate_cache()
