import pytest
from PIL import Image
import numpy as np
import os
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_clip():
    with patch('backend.services.clip_matcher.CLIPProcessor') as mock_proc, \
         patch('backend.services.clip_matcher.CLIPModel') as mock_model, \
         patch('backend.services.clip_matcher.get_all_templates') as mock_get_templates, \
         patch('backend.services.clip_matcher.os.path.exists') as mock_exists:
        
        # Mock processor
        mock_proc.from_pretrained.return_value = MagicMock()
        
        # Mock model
        mock_model_inst = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_inst
        mock_model_inst.to.return_value = mock_model_inst
        mock_model_inst.eval.return_value = mock_model_inst
        
        # Mock templates
        mock_get_templates.return_value = [
            {
                'instrument_type': 'electronic_balance',
                'name': '电子天枰',
                'example_images_json': '["path/to/img1.jpg"]'
            }
        ]
        
        # Mock exists: False for cache file, True for image file
        def side_effect(p):
            if p == "models/test_clip_cache.json":
                return False
            if p == "path/to/img1.jpg":
                return True
            return False
            
        mock_exists.side_effect = side_effect
        
        yield {
            'processor': mock_proc,
            'model': mock_model,
            'model_inst': mock_model_inst,
            'get_templates': mock_get_templates
        }

def test_clip_matcher_matches_instrument(mock_clip):
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    
    with patch.object(CLIPInstrumentMatcher, '_get_image_embedding') as mock_embed:
        # Mock embedding for cache building
        mock_embed.return_value = [1.0] + [0.0]*511
        
        matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
        
        # Setup model for match_image
        mock_vision_output = MagicMock()
        mock_clip['model_inst'].vision_model.return_value = mock_vision_output
        mock_vision_output.pooler_output = MagicMock()
        
        mock_proj_output = MagicMock()
        mock_clip['model_inst'].visual_projection.return_value = mock_proj_output
        mock_proj_output.__truediv__.return_value = mock_proj_output
        
        # Match query vector exactly with reference vector
        mock_proj_output.cpu.return_value.numpy.return_value = np.array([[1.0] + [0.0]*511])

        img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
        result = matcher.match_image(img)
        
        assert isinstance(result, dict)
        assert result['instrument_type'] == 'electronic_balance'
        assert result['matched'] is True
        assert result['confidence'] > 0.9

def test_clip_matcher_builds_cache():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    
    with patch.object(CLIPInstrumentMatcher, '_get_image_embedding') as mock_embed:
        mock_embed.return_value = [0.1] * 512
        matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
        assert 'electronic_balance' in matcher.embedding_cache

def test_clip_matcher_get_embedding(mock_clip):
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    
    # Mock model features
    mock_feat = MagicMock()
    mock_clip['model_inst'].vision_model.return_value = MagicMock()
    mock_clip['model_inst'].visual_projection.return_value = mock_feat
    mock_feat.__truediv__.return_value = mock_feat
    mock_feat.__getitem__.return_value.cpu.return_value.numpy.return_value.tolist.return_value = [0.1]*512

    matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
    
    with patch('backend.services.clip_matcher.Image.open') as mock_open:
        mock_open.return_value.convert.return_value = Image.fromarray(np.zeros((224,224,3), dtype=np.uint8))
        embedding = matcher._get_image_embedding("some_path.jpg")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 512
