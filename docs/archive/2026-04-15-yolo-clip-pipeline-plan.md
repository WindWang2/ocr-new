# YOLO + CLIP 多仪器识别流水线 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现支持单相机多仪器检测的 YOLO+CLIP+LLM 三步流水线，替代原有硬编码相机到仪器的映射。

**Architecture:** 模块化设计分为三个独立服务：YOLO 检测器负责从全图检测仪器区域并输出 bbox，CLIP 匹配器负责将裁剪区域与参考图对比匹配仪器类型，流水线编排器串联三步流程（检测→匹配→读数），最终通过新 API 端点返回多仪器结果。

**Tech Stack:**
- YOLO: ultralytics YOLOv8/YOLO11n
- CLIP: OpenAI CLIP (via transformers or openai-clip package)
- 流水线编排：纯 Python 服务
- API: FastAPI 新增 `/api/read-multi` 端点

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/services/yolo_detector.py` | YOLO 目标检测服务，输出仪器 bbox 列表 |
| `backend/services/clip_matcher.py` | CLIP 嵌入匹配服务，匹配仪器类型并计算置信度 |
| `backend/services/multi_instrument_pipeline.py` | 三步流水线编排，串联检测→匹配→读数 |
| `backend/api/main.py` | 新增 `/api/read-multi` 端点，数据库扩展相机 mode 字段 |
| `backend/models/database.py` | 扩展相机表新增 `mode` 列 (single/multi) |
| `tests/test_yolo_detector.py` | YOLO 检测器单元测试 |
| `tests/test_clip_matcher.py` | CLIP 匹配器单元测试 |
| `tests/test_multi_pipeline.py` | 流水线集成测试 |
| `models/` | 存放 YOLO 权重和 CLIP 嵌入缓存 |

---

## Task 1: 数据库迁移 - 为 cameras 表新增 mode 字段

**Files:**
- Modify: `backend/models/database.py:70-95`
- Test: `tests/test_db_migration.py` (新增)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db_migration.py
def test_camera_table_has_mode_column():
    from backend.models.database import get_connection, get_camera_by_id, add_camera
    # 添加测试相机
    camera_id = add_camera("Test Camera", 99)
    camera = get_camera_by_id(99)
    assert "mode" in camera, "Camera should have mode column after migration"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db_migration.py -v`
Expected: FAIL - AssertionError: "Camera should have mode column after migration"

- [ ] **Step 3: Add database migration for mode column**

在 `backend/models/database.py` 的 `migrations` 列表添加：

```python
migrations = [
    # Version 1: Add new columns to experiments (existing)
    [
        "ALTER TABLE experiments ADD COLUMN type TEXT",
        "ALTER TABLE experiments ADD COLUMN manual_params TEXT",
        "ALTER TABLE experiments ADD COLUMN camera_configs TEXT"
    ],
    # Version 2: Add mode column to cameras for single/multi mode
    [
        "ALTER TABLE cameras ADD COLUMN mode TEXT DEFAULT 'single'"
    ],
]
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_db_migration.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/models/database.py tests/test_db_migration.py
git commit -m "feat(db): add mode column to cameras table for multi-instrument mode"
```

---

## Task 2: 实现 YOLO 目标检测器

**Files:**
- Create: `backend/services/yolo_detector.py`
- Create: `tests/test_yolo_detector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_yolo_detector.py
import pytest
from PIL import Image
import numpy as np

def test_yolo_detector_detects_instruments():
    from backend.services.yolo_detector import YOLOInstrumentDetector
    detector = YOLOInstrumentDetector(confidence_threshold=0.5)
    # Create a dummy test image
    img = Image.fromarray(np.zeros((480, 640, 3), dtype=np.uint8))
    detections = detector.detect(img)
    # Should return a list of bboxes
    assert isinstance(detections, list)
    # Each bbox should have 5 elements: x1, y1, x2, y2, confidence
    for det in detections:
        assert len(det) == 5
        assert all(isinstance(v, (float, int)) for v in det)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_yolo_detector.py::test_yolo_detector_detects_instruments -v`
Expected: FAIL with "No module named 'backend.services.yolo_detector'"

- [ ] **Step 3: Implement YOLOInstrumentDetector**

```python
# backend/services/yolo_detector.py
from typing import List, Tuple
from PIL import Image
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    raise RuntimeError("ultralytics is not installed. Please install: pip install ultralytics")


class YOLOInstrumentDetector:
    """YOLO-based instrument detector.
    Detects instrument regions in a full image, returns list of bounding boxes.
    All output bboxes format: [x1, y1, x2, y2, confidence]
    """

    def __init__(self, model_path: str = None, confidence_threshold: float = 0.5):
        if YOLO is None:
            raise ImportError("ultralytics is required for YOLO detection")
        self.confidence_threshold = confidence_threshold
        # Use default model if not provided
        self.model_path = model_path or "models/yolo_instrument.pt"
        self._load_model()

    def _load_model(self):
        """Load the YOLO model"""
        try:
            self.model = YOLO(self.model_path)
        except FileNotFoundError:
            # If no fine-tuned model exists, use pretrained yolov8n and
            # we'll fine-tune it later. For initial detection framework it's ok
            self.model = YOLO("yolov8n.pt")
            import logging
            logging.warning(f"Fine-tuned model not found at {self.model_path}, using pretrained yolov8n")

    def detect(self, image: Image.Image) -> List[List[float]]:
        """Detect instruments in the given image.
        Returns: List of bboxes: [[x1, y1, x2, y2, confidence], ...]
        """
        results = self.model.predict(image, verbose=False)[0]
        detections = []

        for box in results.boxes:
            confidence = float(box.conf[0])
            if confidence < self.confidence_threshold:
                continue
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            detections.append([x1, y1, x2, y2, confidence])

        # Sort by confidence descending
        detections.sort(key=lambda x: x[4], reverse=True)
        return detections

    def crop_instrument(self, image: Image.Image, bbox: List[float]) -> Image.Image:
        """Crop instrument region from image using bbox."""
        x1, y1, x2, y2 = map(int, bbox[:4])
        # Add small padding around the bbox
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.width, x2 + padding)
        y2 = min(image.height, y2 + padding)
        return image.crop((x1, y1, x2, y2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_yolo_detector.py::test_yolo_detector_detects_instruments -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/yolo_detector.py tests/test_yolo_detector.py
git commit -m "feat(yolo): implement YOLO instrument detector"
```

---

## Task 3: 实现 CLIP 仪器匹配器

**Files:**
- Create: `backend/services/clip_matcher.py`
- Create: `tests/test_clip_matcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_clip_matcher.py
import pytest
from PIL import Image
import numpy as np

def test_clip_matcher_matches_instrument():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    from backend.models.database import get_all_templates

    matcher = CLIPInstrumentMatcher(cache_path="models/clip_cache.json")
    # Create dummy image
    img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    result = matcher.match_image(img)
    # Result structure check
    assert isinstance(result, dict)
    assert "instrument_type" in result
    assert "instrument_name" in result
    assert "confidence" in result
    assert "matched" in result
    assert isinstance(result["matched"], bool)

def test_clip_matcher_builds_cache():
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    matcher = CLIPInstrumentMatcher(cache_path="models/clip_cache.json")
    # Should rebuild cache from templates if missing
    cache = matcher.build_embedding_cache()
    assert isinstance(cache, dict)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_clip_matcher.py -v`
Expected: FAIL with "No module named 'backend.services.clip_matcher'"

- [ ] **Step 3: Implement CLIPInstrumentMatcher**

```python
# backend/services/clip_matcher.py
import json
import os
from typing import Dict, List, Optional, Tuple
from PIL import Image
import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel

from backend.models.database import get_all_templates, get_template


class CLIPInstrumentMatcher:
    """CLIP-based instrument type matcher.
    Compares image embedding against reference image embeddings
    from instrument templates to identify the instrument type.
    """

    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        cache_path: str = "models/clip_cache.json",
        similarity_threshold: float = 0.7,
        device: str = None,
    ):
        self.cache_path = cache_path
        self.similarity_threshold = similarity_threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

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
            with open(self.cache_path, "r") as f:
                self.embedding_cache = json.load(f)
        else:
            self.build_embedding_cache()
            self.save_cache()

    def build_embedding_cache(self) -> Dict:
        """Build embedding cache from all instrument templates in database.
        Each template's example_images are embedded and stored.
        """
        templates = get_all_templates()
        cache = {}

        for tmpl in templates:
            instrument_type = tmpl["instrument_type"]
            example_images = json.loads(tmpl["example_images_json"] or "[]")

            if not example_images:
                continue

            embeddings = []
            for img_path in example_images:
                if os.path.exists(img_path):
                    try:
                        embedding = self._get_image_embedding(img_path)
                        embeddings.append(embedding)
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to embed {img_path}: {e}")

            if embeddings:
                cache[instrument_type] = {
                    "name": tmpl["name"],
                    "embeddings": embeddings,
                    "image_paths": example_images,
                }

        self.embedding_cache = cache
        return cache

    def save_cache(self):
        """Save embedding cache to disk"""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(self.embedding_cache, f, indent=2)

    def _get_image_embedding(self, image_path: str) -> List[float]:
        """Get CLIP embedding for a single image"""
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            # Normalize embedding
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            embedding = image_features[0].cpu().numpy().tolist()

        return embedding

    def match_image(self, image: Image.Image) -> Dict:
        """Match an image against cached reference embeddings.
        Returns the best matching instrument type with confidence.
        """
        if not self.embedding_cache:
            return {
                "matched": False,
                "instrument_type": None,
                "instrument_name": None,
                "confidence": 0.0,
                "reason": "No reference embeddings in cache"
            }

        # Get embedding for query image
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            query_features = self.model.get_image_features(**inputs)
            query_features = query_features / query_features.norm(p=2, dim=-1, keepdim=True)
            query_embedding = query_features[0].cpu().numpy()

        best_match = {
            "matched": False,
            "instrument_type": None,
            "instrument_name": None,
            "confidence": 0.0,
        }

        # Compare with each instrument type's embeddings
        for instr_type, data in self.embedding_cache.items():
            max_sim = 0.0
            for ref_emb in data["embeddings"]:
                ref_emb_np = np.array(ref_emb)
                similarity = float(np.dot(query_embedding, ref_emb_np))
                if similarity > max_sim:
                    max_sim = similarity

            if max_sim > best_match["confidence"]:
                best_match = {
                    "matched": max_sim >= self.similarity_threshold,
                    "instrument_type": instr_type,
                    "instrument_name": data["name"],
                    "confidence": max_sim,
                }

        return best_match

    def invalidate_cache(self):
        """Invalidate and rebuild the entire cache"""
        self.embedding_cache = {}
        self._load_or_build_cache()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_clip_matcher.py -v`
Expected: PASS (embeds correctly)

- [ ] **Step 5: Commit**

```bash
git add backend/services/clip_matcher.py tests/test_clip_matcher.py
git commit -m "feat(clip): implement CLIP instrument matcher"
```

---

## Task 4: 实现多仪器流水线编排

**Files:**
- Create: `backend/services/multi_instrument_pipeline.py`
- Create: `tests/test_multi_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_multi_pipeline.py
import pytest
from PIL import Image
import numpy as np

def test_pipeline_runs_full_detection():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    pipeline = MultiInstrumentPipeline()
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))
    results = pipeline.process_image(img)
    assert isinstance(results, list)
    for result in results:
        assert "bbox" in result
        assert "instrument_type" in result
        assert "clip_confidence" in result
        assert "readings" in result

def test_pipeline_returns_empty_for_no_detections():
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    pipeline = MultiInstrumentPipeline()
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))
    # With high confidence threshold, no detections
    pipeline.yolo_detector.confidence_threshold = 0.99
    results = pipeline.process_image(img)
    assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_multi_pipeline.py -v`
Expected: FAIL with "No module named ..."

- [ ] **Step 3: Implement MultiInstrumentPipeline**

```python
# backend/services/multi_instrument_pipeline.py
from typing import List, Dict, Optional
from PIL import Image

from backend.services.yolo_detector import YOLOInstrumentDetector
from backend.services.clip_matcher import CLIPInstrumentMatcher
from backend.services.llm_provider import get_global_provider
from instrument_reader import InstrumentReader
from backend.models.database import get_template


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
        clip_cache_path: str = "models/clip_cache.json",
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
        """Full pipeline processing:
        - Detect instruments with YOLO
        - Crop each bbox
        - Match with CLIP
        - Read with LLM if matched
        Returns list of detection results.
        """
        # Step 1: YOLO detection
        detections = self.yolo_detector.detect(image)
        results = []

        for det in detections:
            x1, y1, x2, y2, yolo_conf = det

            # Step 2: Crop and CLIP match
            cropped = self.yolo_detector.crop_instrument(image, det)
            clip_result = self.clip_matcher.match_image(cropped)

            if not clip_result["matched"]:
                # Skip low confidence matches
                continue

            # Step 3: LLM reading if we have a match
            reading_result = self._read_instrument(
                cropped,
                clip_result["instrument_type"]
            )

            result = {
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "instrument_type": clip_result["instrument_type"],
                "instrument_name": clip_result["instrument_name"],
                "clip_confidence": float(clip_result["confidence"]),
                "yolo_confidence": float(yolo_conf),
                "readings": reading_result.get("readings", {}),
                "read_success": reading_result.get("success", False),
                "read_error": reading_result.get("error"),
                "read_confidence": reading_result.get("confidence"),
            }
            results.append(result)

        return results

    def _read_instrument(self, image: Image.Image, instrument_type: str) -> Dict:
        """Read instrument using LLM based on template"""
        template = get_template(instrument_type)
        if not template:
            return {
                "success": False,
                "error": f"No template found for {instrument_type}",
                "readings": {},
            }

        prompt = template["prompt_template"]
        try:
            parsed = self.reader.mm_reader.analyze_image(
                image,
                prompt,
                call_type="read"
            )
            if "error" in parsed:
                return {
                    "success": False,
                    "error": parsed["error"],
                    "readings": {},
                }
            return {
                "success": True,
                "readings": parsed,
                "confidence": parsed.get("confidence", 0.8),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "readings": {},
            }

    def rebuild_clip_cache(self):
        """Rebuild CLIP embedding cache after template changes"""
        self.clip_matcher.invalidate_cache()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_multi_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/multi_instrument_pipeline.py tests/test_multi_pipeline.py
git commit -m "feat(pipeline): implement multi-instrument processing pipeline"
```

---

## Task 5: 新增 /api/read-multi API 端点

**Files:**
- Modify: `backend/api/main.py`
- Test: test via manual API call or add `tests/test_api_read_multi.py`

- [ ] **Step 1: Add request/response Pydantic models**

Add to `backend/api/main.py` after existing request models:

```python
class ReadMultiRequest(BaseModel):
    image_path: Optional[str] = None
    camera_id: Optional[int] = None

class DetectionResult(BaseModel):
    bbox: List[float]
    instrument_type: str
    instrument_name: str
    clip_confidence: float
    read_success: bool
    readings: Optional[Dict] = None
    read_confidence: Optional[float] = None
    read_error: Optional[str] = None

class ReadMultiResponse(BaseModel):
    success: bool
    detections: List[DetectionResult]
    detail: Optional[str] = None
```

- [ ] **Step 2: Add the endpoint handler**

Add to `backend/api/main.py` after `/experiments/{exp_id}/run-test`:

```python
@app.post("/api/read-multi")
def read_multi_instruments(body: ReadMultiRequest):
    """Multi-instrument reading endpoint.
    Detects, classifies, and reads all instruments in the image.
    If camera_id provided but no image_path, captures from camera first.
    """
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    from PIL import Image

    full_image_path = body.image_path
    image = None

    # If no image_path but camera_id, capture from camera first
    if not full_image_path and body.camera_id is not None:
        mock_enabled = get_config("mock_camera_enabled", default=False)
        image_dir = get_config("image_dir", default=None) or None
        try:
            if mock_enabled:
                from backend.services.mock_camera import MockCameraClient
                client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir)
                success, result = client.capture_image()
            else:
                from backend.services.camera_control import CameraClient
                camera_config = Config.get_camera_config()
                if image_dir:
                    camera_config["image_dir"] = image_dir
                client = CameraClient(camera_id=body.camera_id, config=camera_config)
                success, result = client.capture_image()
        except Exception as e:
            logger.error(f"Camera {body.camera_id} capture failed: {e}")
            return {"success": False, "detections": [], "detail": f"Capture failed: {str(e)}"}

        if not success:
            return {"success": False, "detections": [], "detail": result.get("error", "Capture failed")}

        full_image_path = result.get("image_path")
        if not full_image_path:
            return {"success": False, "detections": [], "detail": "No image captured"}

    # Open the image
    try:
        assert full_image_path is not None
        image = Image.open(full_image_path).convert("RGB")
    except Exception as e:
        return {"success": False, "detections": [], "detail": f"Cannot open image: {str(e)}"}

    # Run the pipeline
    try:
        pipeline = MultiInstrumentPipeline()
        detections = pipeline.process_image(image)
        return {
            "success": True,
            "detections": detections,
        }
    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        return {"success": False, "detections": [], "detail": f"Processing failed: {str(e)}"}
```

- [ ] **Step 3: Write test**

```python
# tests/test_api_read_multi.py
def test_read_multi_endpoint_exists():
    from backend.api.main import app
    # Check that route exists in app
    routes = [route.path for route in app.routes]
    assert "/api/read-multi" in routes
```

- [ ] **Step 4: Run test to verify**

Run: `python -m pytest tests/test_api_read_multi.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/main.py tests/test_api_read_multi.py
git commit -m "feat(api): add /api/read-multi endpoint for multi-instrument reading"
```

---

## Task 6: Update requirements.txt with new dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add dependencies**

```
# Add to requirements.txt
ultralytics>=8.0.0
transformers>=4.30.0
torch>=2.0.0
pillow>=9.0.0
```

- [ ] **Step 2: Verify**

Run: `pip check`
Expected: No conflicts

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore(deps): add ultralytics and transformers for YOLO+CLIP"
```

---

## Task 7: Extend camera creation API to support mode field

**Files:**
- Modify: `backend/api/main.py`, `backend/models/database.py`

- [ ] **Step 1: Update CameraCreate Pydantic model**

In `backend/api/main.py`, update `CameraCreate`:

```python
class CameraCreate(BaseModel):
    name: str
    camera_id: int
    control_host: Optional[str] = "127.0.0.1"
    control_port: Optional[int] = None
    mode: Optional[str] = "single"  # "single" or "multi"
```

- [ ] **Step 2: Update add_camera call in create_camera endpoint**

In `create_camera` endpoint:

```python
try:
    camera_id_db = add_camera(
        name=camera.name,
        camera_id=camera.camera_id,
        control_host=camera.control_host,
        control_port=camera.control_port,
        mode=camera.mode or "single",
    )
    return {"success": True, "camera_id": camera_id_db, "message": "相机添加成功"}
```

- [ ] **Step 3: Update add_camera function in database.py**

In `backend/models/database.py`, update function signature and INSERT:

```python
def add_camera(name: str, camera_id: int, control_host: str = "127.0.0.1",
               control_port: int = None, mode: str = "single") -> int:
    """添加相机"""
    if control_port is None:
        control_port = 9000 + camera_id

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cameras (name, camera_id, control_host, control_port, mode) VALUES (?, ?, ?, ?, ?)",
        (name, camera_id, control_host, control_port, mode)
    )
    conn.commit()
    camera_id_db = cursor.lastrowid
    conn.close()
    return camera_id_db
```

- [ ] **Step 4: Update get_cameras and get_camera_by_id to include mode**

Already returns all columns, so no change needed - it will be included automatically.

- [ ] **Step 5: Test**

```python
# tests/test_camera_mode.py
def test_add_camera_with_mode():
    from backend.models.database import add_camera, get_camera_by_id
    camera_id = 100
    add_camera("Test Multi Camera", camera_id, mode="multi")
    camera = get_camera_by_id(camera_id)
    assert camera["mode"] == "multi"
```

Run: `python -m pytest tests/test_camera_mode.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/main.py backend/models/database.py tests/test_camera_mode.py
git commit -m "feat(camera): add mode field support for multi-instrument cameras"
```

---

## Task 8: Add cache rebuild endpoint

**Files:**
- Modify: `backend/api/main.py`

- [ ] **Step 1: Add endpoint**

```python
@app.post("/api/rebuild-clip-cache")
def rebuild_clip_cache():
    """Rebuild CLIP embedding cache after template/reference image changes"""
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    try:
        pipeline = MultiInstrumentPipeline()
        pipeline.rebuild_clip_cache()
        return {"success": True, "message": "CLIP cache rebuilt successfully"}
    except Exception as e:
        logger.error(f"Failed to rebuild CLIP cache: {e}")
        return {"success": False, "detail": str(e)}
```

- [ ] **Step 2: Test**

Run: `python -m pytest tests/test_api_read_multi.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/api/main.py
git commit -m "feat(api): add endpoint to rebuild CLIP cache"
```

---

## Task 9: Integration test of full pipeline

**Files:**
- Create: `tests/test_full_pipeline_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_full_pipeline_integration.py
import pytest
from PIL import Image
import numpy as np

def test_full_pipeline_integration():
    from backend.services.yolo_detector import YOLOInstrumentDetector
    from backend.services.clip_matcher import CLIPInstrumentMatcher
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline

    # Test that all components initialize correctly
    detector = YOLOInstrumentDetector()
    assert detector is not None

    matcher = CLIPInstrumentMatcher()
    assert matcher is not None

    pipeline = MultiInstrumentPipeline()
    assert pipeline is not None

    # Test processing on dummy image
    img = Image.fromarray(np.zeros((640, 480, 3), dtype=np.uint8))
    results = pipeline.process_image(img)
    # Should not crash, returns list
    assert isinstance(results, list)
```

- [ ] **Step 2: Run test**

Run: `python -m pytest tests/test_full_pipeline_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_full_pipeline_integration.py
git commit -m "test: add full pipeline integration test"
```

---

## 验收标准

- [ ] 所有单元测试通过
- [ ] `/api/read-multi` 端点可调用，返回正确格式
- [ ] YOLO 能检测出多个仪器框
- [ ] CLIP 能正确匹配仪器类型
- [ ] LLM 对每个匹配到的仪器正确读数
- [ ] 支持 existing templates 的 example_images 作为参考图
- [ ] CLIP 缓存可重建

---

## 后续优化任务（P2/P3）

- P2: 前端添加相机模式选择 UI
- P2: 前端添加多仪器结果展示
- P2: 独立参考图管理 UI（脱离 templates）
- P3: YOLO fine-tuning 脚本和工具链
- P3: 批量标注工具
