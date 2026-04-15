import pytest
from PIL import Image
import numpy as np
from unittest.mock import patch, MagicMock

def test_pipeline_process_image_returns_list():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))

    # Mock YOLO to return one detection
    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider') as MockProvider:

        mock_yolo_inst = MagicMock()
        mock_yolo_inst.detect.return_value = [[100.0, 50.0, 300.0, 200.0, 0.95]]
        mock_yolo_inst.crop_instrument.return_value = Image.fromarray(np.zeros((150, 200, 3), dtype=np.uint8))
        MockYOLO.return_value = mock_yolo_inst

        mock_clip_inst = MagicMock()
        mock_clip_inst.match_image.return_value = {
            'matched': True,
            'instrument_type': 'electronic_balance',
            'instrument_name': '电子天枰',
            'confidence': 0.92,
        }
        MockCLIP.return_value = mock_clip_inst

        mock_reader_inst = MagicMock()
        mock_reader_inst.mm_reader.analyze_image.return_value = {'weight': 12.34}
        MockReader.return_value = mock_reader_inst

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)

        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert 'bbox' in r
        assert 'instrument_type' in r
        assert 'clip_confidence' in r
        assert r['instrument_type'] == 'electronic_balance'

def test_pipeline_returns_empty_for_no_detections():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))

    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider') as MockProvider:

        mock_yolo_inst = MagicMock()
        mock_yolo_inst.detect.return_value = []
        MockYOLO.return_value = mock_yolo_inst

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)
        assert results == []

def test_pipeline_skips_unmatched_instruments():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))

    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider') as MockProvider:

        mock_yolo_inst = MagicMock()
        mock_yolo_inst.detect.return_value = [[100.0, 50.0, 300.0, 200.0, 0.95]]
        mock_yolo_inst.crop_instrument.return_value = img
        MockYOLO.return_value = mock_yolo_inst

        mock_clip_inst = MagicMock()
        mock_clip_inst.match_image.return_value = {
            'matched': False,
            'instrument_type': None,
            'instrument_name': None,
            'confidence': 0.3,
        }
        MockCLIP.return_value = mock_clip_inst

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)
        assert results == []
