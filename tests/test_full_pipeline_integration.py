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
    matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
    assert matcher is not None


def test_pipeline_initialization():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO,          patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP,          patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader,          patch('backend.services.multi_instrument_pipeline.get_global_provider'):
        MockYOLO.return_value = MagicMock()
        MockCLIP.return_value = MagicMock()
        MockReader.return_value = MagicMock()
        pipeline = MultiInstrumentPipeline()
        assert pipeline is not None


def test_pipeline_processes_multiple_detections():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8))

    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO,          patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP,          patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader,          patch('backend.services.multi_instrument_pipeline.get_global_provider'):

        mock_yolo = MagicMock()
        mock_yolo.detect.return_value = [
            [50.0, 30.0, 200.0, 150.0, 0.95],
            [300.0, 100.0, 500.0, 300.0, 0.88],
        ]
        mock_yolo.crop_instrument.return_value = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        MockYOLO.return_value = mock_yolo

        mock_clip = MagicMock()
        mock_clip.match_image.side_effect = [
            {'matched': True, 'instrument_type': 'electronic_balance', 'instrument_name': '电子天枰', 'confidence': 0.92},
            {'matched': True, 'instrument_type': 'ph_meter', 'instrument_name': 'PH仪', 'confidence': 0.88},
        ]
        MockCLIP.return_value = mock_clip

        mock_reader = MagicMock()
        mock_reader.mm_reader.analyze_image.side_effect = [
            {'weight': 12.34},
            {'ph_value': 7.2, 'temperature': 25.3},
        ]
        MockReader.return_value = mock_reader

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)

        assert len(results) == 2
        assert results[0]['instrument_type'] == 'electronic_balance'
        assert results[1]['instrument_type'] == 'ph_meter'


def test_all_new_api_routes_exist():
    from backend.api.main import app
    routes = [route.path for route in app.routes]
    assert '/api/read-multi' in routes
    assert '/api/rebuild-clip-cache' in routes
