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


class MultiInstrumentPipeline:
    """Three-stage multi-instrument reading pipeline:
    1. YOLO detects all instrument bounding boxes
    2. CLIP matches each cropped box to instrument type
    3. LLM reads the value for each matched instrument
    """

    def __init__(
        self,
        yolo_model_path: str = None,
        yolo_conf_threshold: float = 0.5,
        clip_cache_path: str = 'models/clip_cache.json',
        clip_sim_threshold: float = 0.7,
    ):
        self.yolo_detector = YOLOInstrumentDetector(
            model_path=yolo_model_path,
            confidence_threshold=yolo_conf_threshold,
        )
        self.clip_matcher = CLIPInstrumentMatcher(
            cache_path=clip_cache_path,
            similarity_threshold=clip_sim_threshold,
        )
        self.reader = InstrumentReader(provider=get_global_provider())

    def process_image(self, image: Image.Image) -> List[Dict]:
        """Full pipeline: detect -> match -> read"""
        detections = self.yolo_detector.detect(image)
        results = []

        for det in detections:
            x1, y1, x2, y2, yolo_conf = det
            cropped = self.yolo_detector.crop_instrument(image, det)
            clip_result = self.clip_matcher.match_image(cropped)

            if not clip_result.get('matched'):
                logger.info(f'Skipped detection (CLIP not matched, conf={clip_result.get("confidence", 0):.2f})')
                continue

            reading_result = self._read_instrument(cropped, clip_result['instrument_type'])

            result = {
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'instrument_type': clip_result['instrument_type'],
                'instrument_name': clip_result.get('instrument_name', ''),
                'clip_confidence': float(clip_result.get('confidence', 0)),
                'yolo_confidence': float(yolo_conf),
                'readings': reading_result.get('readings', {}),
                'read_success': reading_result.get('success', False),
                'read_error': reading_result.get('error'),
            }
            results.append(result)

        return results

    def _read_instrument(self, image: Image.Image, instrument_type: str) -> Dict:
        """Read instrument using LLM based on template"""
        template = get_template(instrument_type)
        if not template:
            return {'success': False, 'error': f'No template for {instrument_type}', 'readings': {}}

        prompt = template.get('prompt_template', '')
        try:
            parsed = self.reader.mm_reader.analyze_image(image, prompt, call_type='read')
            if 'error' in parsed:
                return {'success': False, 'error': parsed['error'], 'readings': {}}
            return {'success': True, 'readings': parsed}
        except Exception as e:
            return {'success': False, 'error': str(e), 'readings': {}}

    def rebuild_clip_cache(self):
        """Rebuild CLIP embedding cache after template changes"""
        self.clip_matcher.invalidate_cache()
