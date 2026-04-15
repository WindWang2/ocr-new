import pytest
from PIL import Image
import numpy as np
import os

def test_clip_matcher_matches_instrument():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
    # Create dummy image
    img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    result = matcher.match_image(img)
    # Result structure check
    assert isinstance(result, dict)
    assert 'instrument_type' in result
    assert 'instrument_name' in result
    assert 'confidence' in result
    assert 'matched' in result
    assert isinstance(result['matched'], bool)

def test_clip_matcher_builds_cache():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
    cache = matcher.build_embedding_cache()
    assert isinstance(cache, dict)

def test_clip_matcher_get_embedding():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    matcher = CLIPInstrumentMatcher(cache_path='models/test_clip_cache.json')
    # Create a temp image to test embedding extraction
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        img.save(f.name)
        embedding = matcher._get_image_embedding(f.name)
        os.unlink(f.name)
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(v, float) for v in embedding)
