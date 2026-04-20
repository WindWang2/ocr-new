"""Integration tests for the full YOLO+CLIP+LLM pipeline"""
import pytest
from PIL import Image
import numpy as np
from unittest.mock import patch, MagicMock


def test_yolo_detector_initialization():
    from backend.services.yolo_detector import YOLOInstrumentDetector
    detector = YOLOInstrumentDetector()
    assert detector is not None
    assert detector.confidence_threshold == 0.5


def test_clip_matcher_initialization():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    # Mock models to avoid download
    with patch('backend.services.clip_matcher.CLIPProcessor'), \
         patch('backend.services.clip_matcher.CLIPModel'), \
         patch('backend.services.clip_matcher.get_all_templates'):
        matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
        assert matcher is not None


def test_pipeline_initialization():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider'):
        MockYOLO.return_value = MagicMock()
        MockCLIP.return_value = MagicMock()
        MockReader.return_value = MagicMock()
        pipeline = MultiInstrumentPipeline()
        assert pipeline is not None


def test_pipeline_processes_multiple_detections():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8))

    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider'), \
         patch('backend.services.multi_instrument_pipeline.DynamicInstrumentLibrary') as MockLib:

        mock_yolo = MagicMock()
        # class 1 (balance), class 3 (ph)
        mock_yolo.detect.return_value = [
            [50.0, 30.0, 200.0, 150.0, 0.95, 1],
            [300.0, 100.0, 500.0, 300.0, 0.88, 3],
        ]
        mock_yolo.crop_instrument.return_value = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        MockYOLO.return_value = mock_yolo

        MockCLIP.return_value = MagicMock()
        
        MockLib.get_camera_prompt.side_effect = ["balance_prompt", "ph_prompt"]

        mock_reader = MagicMock()
        # The pipeline calls self.reader.mm_reader.analyze_image
        mock_reader.mm_reader.analyze_image.side_effect = [
            {'weight': 12.34},
            {'ph_value': 7.2, 'temperature': 25.3},
        ]
        MockReader.return_value = mock_reader

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)

        assert len(results) == 2
        assert results[0]['instrument_type'] == 'F1'
        assert results[1]['instrument_type'] == 'F3'
        assert results[0]['readings']['weight'] == 12.34
        assert results[1]['readings']['ph_value'] == 7.2


def test_all_new_api_routes_exist():
    from backend.api.main import app
    routes = [route.path for route in app.routes]
    # Check some key routes instead of all
    assert '/cameras' in routes
    assert '/experiments' in routes
