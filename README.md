# OCR 仪表读数识别系统

基于大语言模型（LLM）的实验室仪表读数自动识别系统，支持多种实验类型的数据采集与管理。

## 功能特性

- **全新 YOLO26x 多目标检测** — 集成旗舰级 YOLO26x 模型，支持高精度多目标定位。
- **自动裁剪与精读** — 系统自动从原始全景图中抠出每个仪器的特写，并送往大模型，显著提升识别率。
- **相机与仪器解耦** — 不再依赖 F0-F8 与特定仪器的硬绑定。单次拍照支持识别图中所有已知仪器（类别 0-8）。
- **手动 NMS 压制** — 针对 E2E 模型特别优化，强制手动 Non-Maximum Suppression，彻底消除重叠框干扰。
- **多仪器检测流水线** — YOLO 自动识别定位 -> 智能裁剪 -> LLM 针对性读数提取，支持单张图片包含多台设备。
- **多仪表类型识别** — 支持运动粘度计、旋转粘度计、表面张力仪等实验室主流仪器。
- **多模态 OCR** — 通过 LMStudio（OpenAI 兼容 API）调用本地视觉大语言模型（如 Qwen2-VL）。
- **实验管理** — 完整支持三种实验类型（运动粘度、表观粘度、表面/界面张力）的流程化采集与 Excel 导出。
- **Mock 相机模式** — 支持读取本地图片目录进行全流程模拟测试。

## 项目结构

```
├── backend/
│   ├── api/main.py              # FastAPI 后端服务 (支持多目标处理逻辑)
│   ├── models/database.py       # SQLite 数据持久化
│   └── services/
│       ├── llm_provider.py      # 多模态 LLM 抽象适配层
│       ├── camera_control.py    # 工业相机触发控制
│       ├── mock_camera.py       # 本地模拟相机服务
│       ├── yolo_detector.py     # YOLO26x 核心引擎 (含手动 NMS 优化)
│       └── multi_instrument_pipeline.py  # 复合检测识别流
├── frontend/                    # Next.js 14 Web 前端
│   └── src/
│       ├── app/page.tsx         # 实验执行主看板
│       └── components/
│           └── ExperimentDetail/# 实验详情 (支持展示裁剪后的仪器特写)
├── models/
│   └── yolo_instrument.pt       # 训练好的 YOLO26x 旗舰权重 (最佳)
├── instrument_reader.py         # 核心识别驱动 (支持 YOLO + 多目标裁剪流)
├── config.py                    # 系统参数配置
└── camera_images/               # 拍照图片与自动生成的 crops/ 裁剪目录
```

## 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r requirements.txt
# 核心依赖: ultralytics (YOLO), torch, torchvision, fastapi, pydantic

# 前端
cd frontend && npm install
```

### 2. 启动 LMStudio 并加载模型

在 LMStudio 中加载 Qwen3.5 多模态模型，启动本地服务器。

### 3. 启动服务

```bash
# 后端 (端口 8001)
./start-backend.sh

# 前端 (端口 3000)
./start-frontend.sh
```

打开 http://localhost:3000 访问系统。

## LLM 模型配置

系统支持两种 LLM 后端，在页面右上角「系统设置」下拉菜单中配置：

| 模式 | 说明 | 配置项 |
|------|------|--------|
| **LMStudio** | 本地 LMStudio 服务 | 服务地址、模型选择（支持自动检测列表） |

配置会持久化到数据库，重启后自动恢复。

## 环境变量

通过 `config.py` 或环境变量设置默认值：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LMSTUDIO_BASE_URL` | `http://127.0.0.1:1234` | LMStudio 服务地址 |
| `LMSTUDIO_MODEL` | `4b` | 默认模型名称 |
| `MODEL_TEMPERATURE` | `0.1` | 模型温度 |
| `MODEL_MAX_TOKENS` | `500` | 最大输出 token 数 |
