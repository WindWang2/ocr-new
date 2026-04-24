# Project Context (Final Alignment)

## Python Environment
- **Conda Environment**: `ocr_backend`
- **Backend Entry**: `backend.api.main:app`
- **Default Port**: 8001
- **GPU Status**: NVIDIA 1080 Ti (using CUDA)

## Instrument-to-Camera Master Mapping
This mapping is defined in `backend/instrument_configs.py`:

| Instrument | Name | YOLO Cls | Camera ID | Post-Process |
| :--- | :--- | :--- | :--- | :--- |
| **F0** | 吴英混调器 | 0 | 0 | - |
| **F1** | 电子天平 1 | 1 | 3 | decimal_correction_2 |
| **F2** | 电子天平 2 | 2 | 3 | decimal_correction_2 |
| **F3** | PH 计 | 3 | 3 | - |
| **F4** | 水质检测仪 | 4 | 5 | - |
| **F5** | 表界面张力仪 | 5 | 5 | - |
| **F6** | 搅拌器 | 6 | 7 | - |
| **F7** | 水浴锅 | 7 | 7 | - |
| **F8** | 粘度计 | 8 | 8 | - |

## Key Logic
- **YOLO First**: All OCR tasks (except direct camera read) perform YOLO detection first.
- **Forced Context**: When requesting instrument `X`, the system forces the usage of `FX` prompt and post-processing, even if YOLO misidentifies the class ID, as long as a bounding box is found.
- **Logging**: Detailed multimodal traces are marked with `[DEBUG RAW LLM]` and `[DEBUG_CROP]`.
