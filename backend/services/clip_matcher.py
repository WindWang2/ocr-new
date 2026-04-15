"""CLIP-based instrument type matcher."""
import json
import logging
import os
from typing import Dict, List, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False

from backend.models.database import get_all_templates, get_template


class CLIPInstrumentMatcher:
    """CLIP-based instrument type matcher.
    Compares image embedding against reference image embeddings
    from instrument templates to identify the instrument type.
    """

    def __init__(
        self,
        model_name: str = 'openai/clip-vit-base-patch32',
        cache_path: str = 'models/clip_cache.json',
        similarity_threshold: float = 0.7,
        device: str = None,
    ):
        if not HAS_CLIP:
            raise ImportError('transformers and torch are required for CLIP matching')
        self.cache_path = cache_path
        self.similarity_threshold = similarity_threshold
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        # Load CLIP model and processor
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

        # Load or build embedding cache
        self.embedding_cache: Dict = {}
        self._load_or_build_cache()

    def _load_or_build_cache(self):
        """Load existing cache from disk or build it from database templates"""
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r') as f:
                self.embedding_cache = json.load(f)
        else:
            self.build_embedding_cache()
            self.save_cache()

    def build_embedding_cache(self) -> Dict:
        """Build embedding cache from all instrument templates in database."""
        templates = get_all_templates()
        cache = {}
        for tmpl in templates:
            instrument_type = tmpl['instrument_type']
            example_images = json.loads(tmpl.get('example_images_json') or '[]')
            if not example_images:
                continue
            embeddings = []
            valid_paths = []
            for img_path in example_images:
                if os.path.exists(img_path):
                    try:
                        embedding = self._get_image_embedding(img_path)
                        embeddings.append(embedding)
                        valid_paths.append(img_path)
                    except Exception as e:
                        logger.warning(f'Failed to embed {img_path}: {e}')
            if embeddings:
                cache[instrument_type] = {
                    'name': tmpl.get('name', instrument_type),
                    'embeddings': embeddings,
                    'image_paths': valid_paths,
                }
        self.embedding_cache = cache
        return cache

    def save_cache(self):
        """Save embedding cache to disk"""
        os.makedirs(os.path.dirname(self.cache_path) or '.', exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self.embedding_cache, f, indent=2)

    def _get_image_embedding(self, image_path: str) -> List[float]:
        """Get CLIP embedding for a single image"""
        image = Image.open(image_path).convert('RGB')
        inputs = self.processor(images=image, return_tensors='pt').to(self.device)
        with torch.no_grad():
            outputs = self.model.vision_model(**inputs)
            image_features = self.model.visual_projection(outputs.pooler_output)
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            embedding = image_features[0].cpu().numpy().tolist()
        return embedding

    def match_image(self, image: Image.Image) -> Dict:
        """Match an image against cached reference embeddings."""
        if not self.embedding_cache:
            return {
                'matched': False,
                'instrument_type': None,
                'instrument_name': None,
                'confidence': 0.0,
                'reason': 'No reference embeddings in cache',
            }
        inputs = self.processor(images=image, return_tensors='pt').to(self.device)
        with torch.no_grad():
            outputs = self.model.vision_model(**inputs)
            query_features = self.model.visual_projection(outputs.pooler_output)
            query_features = query_features / query_features.norm(p=2, dim=-1, keepdim=True)
            query_embedding = query_features.cpu().numpy()

        best_match = {
            'matched': False,
            'instrument_type': None,
            'instrument_name': None,
            'confidence': 0.0,
        }
        for instr_type, data in self.embedding_cache.items():
            max_sim = 0.0
            for ref_emb in data['embeddings']:
                ref_emb_np = np.array(ref_emb)
                similarity = float(np.dot(query_embedding, ref_emb_np))
                if similarity > max_sim:
                    max_sim = similarity
            if max_sim > best_match['confidence']:
                best_match = {
                    'matched': max_sim >= self.similarity_threshold,
                    'instrument_type': instr_type,
                    'instrument_name': data['name'],
                    'confidence': max_sim,
                }
        return best_match

    def invalidate_cache(self):
        """Invalidate and rebuild the entire cache"""
        self.embedding_cache = {}
        self._load_or_build_cache()
