# OCR Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement UI-driven templates with example images, structured outputs via Pydantic, and a fallback OCR routing strategy to optimize accuracy, performance, and extensibility.

**Architecture:** We will introduce a new SQLite table `instrument_templates` to store instrument configurations (including few-shot example image references). A frontend UI will allow CRUD operations. The `InstrumentReader` will be refactored to fetch these templates dynamically. We will then wrap the multi-modal LLM calls with Pydantic for validation, and finally introduce a lightweight OCR tier for simple displays.

**Tech Stack:** Python, FastAPI, SQLite, Pydantic, Next.js, TailwindCSS

---

## Phase 1: Database and API for Templates

### Task 1: Database Migration for Instrument Templates

**Files:**
- Modify: `backend/models/database.py`

- [ ] **Step 1: Write the schema definition**
In `backend/models/database.py`, modify the `init_db` function to create the `instrument_templates` table.
```python
def init_db():
    # ... existing connection logic ...
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instrument_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instrument_type TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        prompt_template TEXT,
        fields_json TEXT NOT NULL,
        keywords_json TEXT NOT NULL,
        example_images_json TEXT,
        default_tier INTEGER DEFAULT 2,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
```

- [ ] **Step 2: Write CRUD functions for templates**
Add helper functions to `backend/models/database.py`.
```python
import json

def get_all_templates():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instrument_templates")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_template(instrument_type):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instrument_templates WHERE instrument_type = ?", (instrument_type,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_template(instrument_type, name, description, prompt_template, fields, keywords, example_images=None, default_tier=2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO instrument_templates (instrument_type, name, description, prompt_template, fields_json, keywords_json, example_images_json, default_tier)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(instrument_type) DO UPDATE SET
        name=excluded.name,
        description=excluded.description,
        prompt_template=excluded.prompt_template,
        fields_json=excluded.fields_json,
        keywords_json=excluded.keywords_json,
        example_images_json=excluded.example_images_json,
        default_tier=excluded.default_tier
    ''', (instrument_type, name, description, prompt_template, json.dumps(fields), json.dumps(keywords), json.dumps(example_images or []), default_tier))
    conn.commit()
    conn.close()
```

- [ ] **Step 3: Commit**
```bash
git add backend/models/database.py
git commit -m "feat(db): add instrument_templates schema and CRUD functions"
```

### Task 2: API Endpoints for Templates

**Files:**
- Modify: `backend/api/main.py`

- [ ] **Step 1: Define Pydantic Models for Template API**
Add near the other Pydantic models in `backend/api/main.py`.
```python
class TemplateField(BaseModel):
    name: str
    label: str
    unit: Optional[str] = ""
    type: str = "float"

class InstrumentTemplateCreate(BaseModel):
    instrument_type: str
    name: str
    description: Optional[str] = ""
    prompt_template: str
    fields: List[TemplateField]
    keywords: List[str]
    example_images: Optional[List[str]] = []
    default_tier: int = 2
```

- [ ] **Step 2: Implement Endpoints**
```python
from backend.models.database import get_all_templates, get_template, upsert_template

@app.get("/templates")
def list_templates():
    templates = get_all_templates()
    for t in templates:
        t['fields'] = json.loads(t['fields_json'])
        t['keywords'] = json.loads(t['keywords_json'])
        t['example_images'] = json.loads(t['example_images_json'] or '[]')
    return {"success": True, "templates": templates}

@app.post("/templates")
def create_or_update_template(body: InstrumentTemplateCreate):
    upsert_template(
        instrument_type=body.instrument_type,
        name=body.name,
        description=body.description,
        prompt_template=body.prompt_template,
        fields=[f.dict() for f in body.fields],
        keywords=body.keywords,
        example_images=body.example_images,
        default_tier=body.default_tier
    )
    return {"success": True, "message": "Template saved"}
```

- [ ] **Step 3: Commit**
```bash
git add backend/api/main.py
git commit -m "feat(api): add instrument templates endpoints"
```

## Phase 2: Refactoring `InstrumentReader` & Integrating Pydantic

### Task 3: Load Configuration from DB instead of Hardcoding

**Files:**
- Modify: `instrument_reader.py`

- [ ] **Step 1: Replace Static Prompts with DB Call**
In `instrument_reader.py`, replace `InstrumentLibrary` with a dynamic version.
```python
from backend.models.database import get_all_templates, get_template
import json

class DynamicInstrumentLibrary:
    @classmethod
    def get_template(cls, instrument_type):
        t = get_template(instrument_type)
        if t:
            t['fields'] = json.loads(t['fields_json'])
            t['keywords'] = json.loads(t['keywords_json'])
            t['example_images'] = json.loads(t['example_images_json'] or '[]')
        return t

    @classmethod
    def get_all(cls):
        templates = get_all_templates()
        for t in templates:
            t['fields'] = json.loads(t['fields_json'])
            t['keywords'] = json.loads(t['keywords_json'])
            t['example_images'] = json.loads(t['example_images_json'] or '[]')
        return templates

    @classmethod
    def identify_by_ocr_keywords(cls, ocr_text: str) -> str:
        templates = cls.get_all()
        for t in templates:
            if all(kw in ocr_text for kw in t['keywords']):
                return t['instrument_type']
        return "unknown"

    @classmethod
    def get_instrument_prompt(cls, instrument_type: str) -> str:
        t = cls.get_template(instrument_type)
        if t:
            return t['prompt_template']
        return ""
```
Replace usages of `InstrumentLibrary` in `InstrumentReader` with `DynamicInstrumentLibrary`.

- [ ] **Step 2: Commit**
```bash
git add instrument_reader.py
git commit -m "refactor(ocr): replace hardcoded config with dynamic db template queries"
```

### Task 4: Enforce JSON Validation with Pydantic

**Files:**
- Modify: `instrument_reader.py`

- [ ] **Step 1: Implement Dynamic Pydantic Model Creation**
```python
from pydantic import create_model, Field

def get_pydantic_model_for_instrument(instrument_type: str):
    t = DynamicInstrumentLibrary.get_template(instrument_type)
    if not t:
        return None
    fields_config = t.get('fields', [])
    model_fields = {}
    for f in fields_config:
        model_fields[f['name']] = (float, Field(default=None, description=f['label']))
    
    DynamicModel = create_model(f'{instrument_type}Model', **model_fields)
    return DynamicModel
```

- [ ] **Step 2: Validate LLM output**
Modify `_parse_json_response` in `MultimodalModelReader` to accept a Pydantic model class and validate the parsed JSON.
```python
    def _validate_with_pydantic(self, parsed_json: dict, instrument_type: str) -> dict:
        model_class = get_pydantic_model_for_instrument(instrument_type)
        if not model_class:
            return parsed_json
        try:
            validated = model_class(**parsed_json)
            return validated.dict()
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}", "raw_parsed": parsed_json}
```
Update `analyze_image` to accept `instrument_type` and call validation if applicable.

- [ ] **Step 3: Commit**
```bash
git add instrument_reader.py
git commit -m "feat(ocr): add pydantic validation for instrument readings"
```

## Phase 3: Few-Shot Example Injection

### Task 5: Support Example Images in LLM Provider

**Files:**
- Modify: `backend/services/llm_provider.py`
- Modify: `instrument_reader.py`

- [ ] **Step 1: Update API signature to pass multiple images**
Ensure `chat` method in LLM provider implementations accepts a list of base64 images, mapping them properly to the payload for multimodal models.

- [ ] **Step 2: Append examples in `analyze_image`**
```python
    def analyze_image(self, image_path: str, prompt: str, call_type: str = "unknown", instrument_type: str = None) -> dict:
        # Load base image
        import io
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        base64_images = [base64.b64encode(buf.getvalue()).decode('utf-8')]

        if instrument_type:
            template = DynamicInstrumentLibrary.get_template(instrument_type)
            if template and template.get('example_images'):
                for ex_path in template['example_images']:
                    try:
                        ex_img = Image.open(ex_path).convert("RGB")
                        ex_buf = io.BytesIO()
                        ex_img.save(ex_buf, format="JPEG", quality=95)
                        base64_images.append(base64.b64encode(ex_buf.getvalue()).decode('utf-8'))
                    except Exception as e:
                        logger.warning(f"Failed to load example image {ex_path}: {e}")

        # ... Call provider with base64_images list ...
```

- [ ] **Step 3: Commit**
```bash
git add backend/services/llm_provider.py instrument_reader.py
git commit -m "feat(ocr): support few-shot example images in llm requests"
```

## Phase 4: Frontend UI for Template Management

### Task 6: Template Management Screen

**Files:**
- Create: `frontend/src/app/templates/page.tsx`
- Create: `frontend/src/components/TemplateManagement/TemplateEditor.tsx`

- [ ] **Step 1: Fetch and List Templates**
Fetch from `/templates` API and render a list view of available instruments.

- [ ] **Step 2: Template Editor Form**
Build a form with fields for `instrument_type`, `name`, `description`, `prompt_template`.
Add a dynamic list builder for `fields` and `keywords`.
Add an image upload component for `example_images` that posts to an image upload API and stores the returned path in the `example_images` array.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/app/templates/ frontend/src/components/TemplateManagement/
git commit -m "feat(ui): add template management screen"
```
