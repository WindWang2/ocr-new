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
         patch('backend.services.multi_instrument_pipeline.get_global_provider') as MockProvider, \
         patch('backend.services.multi_instrument_pipeline.DynamicInstrumentLibrary') as MockLib:

        mock_yolo_inst = MagicMock()
        mock_yolo_inst.detect.return_value = [[100.0, 50.0, 300.0, 200.0, 0.95, 1]]
        mock_yolo_inst.crop_instrument.return_value = Image.fromarray(np.zeros((150, 200, 3), dtype=np.uint8))
        MockYOLO.return_value = mock_yolo_inst

        MockCLIP.return_value = MagicMock()
        MockLib.get_camera_prompt.return_value = "dummy_prompt"

        mock_reader_inst = MagicMock()
        mock_reader_inst.mm_reader.analyze_image.return_value = {'weight': 12.34}
        MockReader.return_value = mock_reader_inst

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]['instrument_type'] == 'F1'
        assert results[0]['readings']['weight'] == 12.34

def test_pipeline_skips_unmatched_instruments():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))

    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider') as MockProvider, \
         patch('backend.services.multi_instrument_pipeline.DynamicInstrumentLibrary') as MockLib:

        mock_yolo_inst = MagicMock()
        mock_yolo_inst.detect.return_value = [[100.0, 50.0, 300.0, 200.0, 0.95, 1]]
        mock_yolo_inst.crop_instrument.return_value = img
        MockYOLO.return_value = mock_yolo_inst

        # Return empty prompt should cause the pipeline to skip this detection
        MockLib.get_camera_prompt.return_value = ""

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)

        assert isinstance(results, list)
        assert len(results) == 0

def test_pipeline_data_isolation():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))

    with patch('backend.services.multi_instrument_pipeline.YOLOInstrumentDetector') as MockYOLO, \
         patch('backend.services.multi_instrument_pipeline.CLIPInstrumentMatcher') as MockCLIP, \
         patch('backend.services.multi_instrument_pipeline.InstrumentReader') as MockReader, \
         patch('backend.services.multi_instrument_pipeline.get_global_provider') as MockProvider, \
         patch('backend.services.multi_instrument_pipeline.DynamicInstrumentLibrary') as MockLib:

        mock_yolo_inst = MagicMock()
        # Returns 2 detections of different classes
        mock_yolo_inst.detect.return_value = [
            [0, 0, 100, 100, 0.9, 1], # balance (F1)
            [100, 100, 200, 200, 0.8, 3] # ph_meter (F3)
        ]
        mock_yolo_inst.crop_instrument.return_value = img
        MockYOLO.return_value = mock_yolo_inst

        MockLib.get_camera_prompt.return_value = "dummy_prompt"

        mock_reader_inst = MagicMock()
        # Reader returns "dirty" data with extra fields
        mock_reader_inst.mm_reader.analyze_image.side_effect = [
            {'weight': 10.5, 'ph_value': 7.0}, # balance reading (should only have weight)
            {'ph_value': 6.5, 'weight': 11.0}  # ph reading (should only have ph_value)
        ]
        MockReader.return_value = mock_reader_inst

        pipeline = MultiInstrumentPipeline()
        results = pipeline.process_image(img)

        assert len(results) == 2
        
        # Check isolation
        for res in results:
            if res['instrument_type'] == 'F1':
                assert 'weight' in res['readings']
                assert 'ph_value' not in res['readings']
            if res['instrument_type'] == 'F3':
                assert 'ph_value' in res['readings']
                assert 'weight' not in res['readings']
