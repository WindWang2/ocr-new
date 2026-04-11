# Instrument OCR Recognition System Optimization Design

## 1. Overview
This design document addresses the core challenges in the current Instrument OCR Recognition system, focusing on improving accuracy, performance, and extensibility. The three main pillars of this optimization are addressing model output instability, optimizing fallback/routing to bypass unnecessary LLM calls, and implementing UI-driven templating to eliminate hardcoded configurations.

## 2. Goals
- **Accuracy (A):** Mitigate model output instability (hallucinations, parsing errors, missed decimals/signs) using structured outputs and validation rules.
- **Performance (B):** Implement fallback/routing optimization to avoid full LLM calls for simple screens, falling back to LLMs only when necessary.
- **Extensibility (C):** Build a UI-driven templating system for adding new instruments, moving away from hardcoded prompts and configurations in `instrument_reader.py`.

## 3. Architecture & Approaches

### 3.1. Accuracy: Mitigating Model Output Instability
The current approach relies on complex regex and JSON parsing to extract data from raw text responses.
**Approach:** Structured Output Enforcement & Validation Engine
- **Structured Outputs (JSON Mode/Tools):** Modify the API calls to the LLM (OpenAI compatible) to enforce JSON output natively if the model supports it (`response_format={"type": "json_object"}`). Provide explicit JSON schemas for each instrument type.
- **Robust Parsing Pipeline:** If the model doesn't support strict JSON mode, standardize the extraction logic using a robust library (e.g., `pydantic` for schema validation and coercion).
- **Validation Rules Engine:** Add configurable validation rules (min/max bounds, expected data types, required fields) per instrument. If a reading violates a rule, trigger a retry or flag it for manual review instead of silently saving garbage data.

### 3.2. Performance: Fallback/Routing Optimization
Currently, the multi-modal LLM is heavily utilized, which is slow and resource-intensive.
**Approach:** Multi-Tier Recognition Strategy
- **Tier 1 (Fast & Cheap):** For simple digital displays (e.g., electronic balances, simple temperature controllers), use a lightweight, traditional OCR engine (like PaddleOCR or Tesseract) combined with standard regex extraction rules.
- **Tier 2 (Heavy & Accurate):** For complex, multi-field screens (e.g., 6-speed viscometer) or when Tier 1 fails to extract values matching the validation rules, route the request to the multi-modal LLM.
- **Implementation:** Introduce a router layer in `InstrumentReader` that checks the instrument's configuration to determine the initial tier.

### 3.3. Extensibility: UI-Driven Templating
Instrument types, prompts, and keywords are currently hardcoded in `instrument_reader.py`.
**Approach:** Database-Driven Instrument Templates
- **Database Schema:** Create a new table/collection `instrument_templates` storing:
  - Instrument Name & ID
  - Fields (name, label, unit, type, validation rules)
  - Identification Keywords (for routing)
  - LLM Prompt Template (with variables for few-shot injection if needed)
  - Default Tier Routing (Tier 1 vs. Tier 2)
- **Backend API:** Implement CRUD endpoints (`/templates`) for managing these configurations.
- **Frontend UI:** Build a "Template Management" screen where users can visually define fields, expected formats, and keywords.
- **Refactoring:** Modify `InstrumentLibrary` to load its configuration dynamically from the database instead of static dictionaries.

## 4. Implementation Plan (High-Level)

### Phase 1: Extensibility (The Foundation)
1.  **Database Migration:** Add tables for `instrument_templates` and `template_fields`.
2.  **API Development:** Create CRUD endpoints for templates in `main.py`.
3.  **Refactor `InstrumentReader`:** Update it to fetch prompts, fields, and keywords from the database instead of `InstrumentLibrary`.
4.  **Frontend Management UI:** Build the UI to add/edit these templates.

### Phase 2: Accuracy
1.  **Integrate `pydantic`:** Define strict schemas for LLM outputs based on the dynamic templates.
2.  **Update LLM Calls:** Attempt to use JSON mode where supported.
3.  **Implement Validation:** Apply the validation rules defined in the templates to the extracted values.

### Phase 3: Performance
1.  **Integrate Lightweight OCR:** Add a fallback OCR engine (e.g., a simple wrapper around an existing OCR tool or API).
2.  **Routing Logic:** Update the `InstrumentReader` to try Tier 1 extraction first based on template configuration.

## 5. Security & Error Handling
- Invalid JSON from LLMs will be caught by Pydantic and flagged for retry/manual entry.
- Template creation must validate field types to prevent injection into the dynamic prompts.

## 6. Testing Strategy
- **Unit Tests:** Test the dynamic prompt generation and Pydantic validation logic.
- **Integration Tests:** Test the fallback routing (Tier 1 -> Tier 2) using mock OCR and LLM responses.
- **E2E Tests:** End-to-end test of creating a template via API and successfully extracting data using that template.