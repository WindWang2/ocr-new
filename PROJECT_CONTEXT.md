# Project Context (Final Alignment)

## Python Environment
- **Conda Environment**: `ocr_backend`
- **Backend Entry**: `backend.api.main:app`
- **Default Port**: 8001
- **GPU Status**: NVIDIA 1080 Ti (using CUDA)

## Instrument-to-Camera Master Mapping
This mapping is defined in `backend/instrument_configs.py`. 
**注意：仪器命名为 D0-D8，物理相机命名为 F0-F8。**

| Instrument (仪器) | Name | YOLO Cls | Camera (相机) | Post-Process |
| :--- | :--- | :--- | :--- | :--- |
| **D0** | 吴英混调器 | 0 | F0 | - |
| **D1** | 电子天平 1 | 1 | F3 | decimal_correction_2 |
| **D2** | 电子天平 2 | 2 | F3 | decimal_correction_2 |
| **D3** | PH 计 | 3 | F3 | - |
| **D4** | 水质检测仪 | 4 | F5 | - |
| **D5** | 表界面张力仪 | 5 | F5 | - |
| **D6** | 搅拌器 | 6 | F7 | - |
| **D7** | 水浴锅 | 7 | F7 | - |
| **D8** | 粘度计 | 8 | F8 | - |

## Key Logic
- **YOLO First**: All OCR tasks (except direct camera read) perform YOLO detection first.
- **Forced Context**: When requesting instrument `DX`, the system forces the usage of `DX` prompt and post-processing, even if YOLO misidentifies the class ID, as long as a bounding box is found.
- **Logging**: Detailed multimodal traces are marked with `[DEBUG RAW LLM]` and `[DEBUG_CROP]`.
