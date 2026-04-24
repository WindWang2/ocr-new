# OCR 实验室仪表读数识别系统 (New Architecture)

基于 **YOLOv8 + GLM-OCR** 的高性能实验室仪表读数自动识别系统。采用“以仪器为中心”的配置架构，支持复杂环境下的多目标检测与精准 OCR。

## 核心架构

1. **YOLO 目标定位**：采用训练好的 `last.pt` 权重，识别 9 类仪器 (Class 0-8)。
2. **智能裁切流**：系统根据 YOLO 定位自动抠图，消除背景干扰。
3. **GLM-OCR 视觉识别**：利用本地 GPU 加速的 GLM-OCR 模型，对特写图进行精准读数提取。
4. **中央配置驱动**：所有仪器的路由、提示词、后处理逻辑统一由 `backend/instrument_configs.py` 管理。

## 功能特性

- **仪器-相机解耦**：支持在 `instrument_configs.py` 中自由映射仪器到任意相机。
- **强制 ID 匹配**：请求 F1 时，即使 YOLO 误认，系统也会强制套用 F1 的专业提示词，确保业务逻辑准确。
- **高精度 Prompt 模板**：针对天平、水质仪、粘度计等专门优化了提示词，包含小数点纠偏逻辑。
- **本地 GPU 加速**：在 `ocr_backend` 环境下运行，充分利用 1080 Ti 的推理能力。

## 项目结构

```
├── backend/
│   ├── instrument_configs.py    # 【核心】中央配置文件 (路由、Prompt、后处理)
│   ├── api/main.py              # FastAPI 后端服务
│   └── services/
│       ├── llm_provider.py      # GLM-OCR 适配层
│       └── yolo_detector.py     # YOLOv8 推理引擎
├── instrument_reader.py         # 核心逻辑类 (协调 YOLO 裁切与 OCR 识别)
├── PROJECT_CONTEXT.md           # 项目环境与路由备忘录
├── start_backend.ps1            # 后端启动脚本 (Windows)
├── start_frontend.bat           # 前端启动脚本
└── camera_images/               # 原始图片与 crops/ 裁切缓存
```

## 快速开始

### 1. 环境准备
确保已安装 Conda，并激活环境：
```powershell
conda activate ocr_backend
```

### 2. 配置说明
修改 `backend/instrument_configs.py` 来对齐硬件：
- `yolo_cls_id`: YOLO 模型的类别 (0-8 对应 F0-F8)。
- `camera_id`: 物理相机编号。
- `prompt`: 针对该仪器的专用指令。
- `post_process`: 后处理逻辑标识 (如 `decimal_correction_2`)。

### 3. 启动系统
```powershell
# 启动后端 (默认端口 8001)
.\start_backend.ps1

# 启动前端 (默认端口 3000)
.\start_frontend.bat
```

## 开发者备忘录

- **环境**: `ocr_backend` (Python 3.10+)
- **GPU 推理**: GLM-OCR 默认使用 `cuda`。
- **调试**: 查看 `backend.log` 搜索 `[DEBUG RAW LLM]` 获取大模型原始 JSON 输出。
