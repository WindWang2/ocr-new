# OCR 仪表读数识别系统

基于大语言模型（LLM）的实验室仪表读数自动识别系统，支持多种实验类型的数据采集与管理。

## 功能特性

- **多仪表类型识别** — 支持运动粘度计、旋转粘度计、表面张力仪等 17 种实验室仪器
- **多模态 OCR** — 通过 LMStudio（OpenAI 兼容 API）调用视觉语言模型进行仪表读数识别
- **LLM 模型切换** — 前端下拉菜单实时切换模型，支持本地 LMStudio 和远程 OpenAI 兼容服务
- **实验管理** — 三种实验类型（运动粘度、表观粘度、表面/界面张力），支持创建、执行、导出 Excel
- **Mock 相机模式** — 读取本地图片进行 OCR 测试，无需连接真实相机
- **连接状态指示** — Settings 按钮实时显示 LLM 服务连接状态

## 项目结构

```
├── backend/
│   ├── api/main.py              # FastAPI 后端服务 (端口 8001)
│   ├── models/database.py       # SQLite 数据模型
│   └── services/
│       ├── llm_provider.py      # LLM 抽象层 (OpenAI 兼容)
│       ├── camera_control.py    # 真实相机 TCP 客户端
│       └── mock_camera.py       # Mock 相机 (本地图片 OCR)
├── frontend/                    # Next.js 14 前端
│   └── src/
│       ├── app/page.tsx         # 主页面
│       ├── components/
│       │   ├── SettingsPanel/   # 系统设置 (LLM 模型选择)
│       │   ├── ExperimentDetail/# 实验详情与拍照识别
│       │   └── CreateExperiment/# 实验创建向导
│       ├── lib/api.ts           # 后端 API 客户端
│       └── types/index.ts       # TypeScript 类型定义
├── instrument_reader.py         # OCR 核心引擎 (两步识别: 仪器分类 → 读数提取)
├── config.py                    # 系统默认配置
├── camera_images/F0~F8/         # Mock 相机图片目录
├── start-backend.sh             # 启动后端
└── start-frontend.sh            # 启动前端
```

## 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r requirements.txt

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
