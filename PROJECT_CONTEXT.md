# Project Context (V1.2 Alignment)

## Infrastructure Environment
- **Target OS**: Windows 10/11 (Offline/Air-gapped deployment supported)
- **Backend Framework**: Python (FastAPI + Uvicorn)
- **Frontend Framework**: Node.js (React + Next.js)
- **Hardware Acceleration**: NVIDIA 3060 Ti / 1080 Ti (using CUDA 13.1 via `llama.cpp`)
- **Default Ports**:
  - `3000`: Frontend Dashboard
  - `8001`: Backend Core API
  - `8080`: `llama-server` (Qianfan-OCR GGUF Model)

## Core Technologies
- **Target Detection**: `ultralytics` YOLOv8 (`last.pt`) with custom area, confidence, and center-distance weighting to suppress background noise.
- **Computer Vision**: OpenCV (`cv2`) for dynamic rotation logic (CLAHE + Canny Edge Density) for horizontal cameras (like D4).
- **Vision-Language Model**: InternVL/Qianfan-OCR (Q4_K_M quantized) executed via `llama-server` with `--mmproj-offload` for max GPU utilization.

## Instrument Master Map
The 9 core instruments (`D0` to `D8`) are managed via dynamic prompt templates stored in the `experiments.db` SQLite database.

| Instrument | Focus & Fixes Applied in V1.2 | Target Camera |
| :--- | :--- | :--- |
| **D0** (混调器) | Adaptive layout detection (Auto/Manual mode) via highlighted button tracking. | F0 |
| **D1** (天平1) | Strict zero-padding crop. Removed numerical prompt placeholders. | F3 |
| **D2** (天平2) | Strict zero-padding crop. Removed numerical prompt placeholders. | F3 |
| **D3** (pH计) | Consolidated pH & Temperature into a single snapshot. | F3 |
| **D4** (水质仪) | Auto OpenCV rotation (Detects screen left/right). Strict `null` fallback on black/powered-off screen. | F5 |
| **D5** (张力仪) | Adaptive 5-line / 6-line detection. Excel export now supports multi-water surface tension averaging. | F5 |
| **D6** (扭矩搅拌) | Forced "left-edge scanning" to prevent truncating the first narrow '1' in 4-digit RPMs. | F7 |
| **D7** (水浴锅) | YOLO multi-box suppression (forces picking the smallest internal screen box). | F7 |
| **D8** (粘度计) | Apparent viscosity `100r/min` target binding and automated backend average calculations. | F8 |

*Note: The Kinematic Viscosity experiment does not use D0-D8 for OCR, as it relies on manual stopwatch timing for glass capillaries.*