# OCR 实验室仪表读数识别系统 (V1.2 Architecture)

基于 **YOLOv8 + Qianfan-OCR (llama.cpp 加速)** 的高性能实验室仪表读数自动识别平台。本系统专为离线部署和复杂的工业暗光环境设计，提供从目标定位到全量化数值提取的端到端解决方案。

## 核心架构升级

1. **大模型视觉算力卸载 (GPU)**：
   - 彻底废弃了缓慢的 Python 运行时加载，全面转向 C++ 原生的 `llama-server` (CUDA 13.1 编译版)。
   - **mmproj (视觉组件)** 和 LLM 层全量 Offload 至 NVIDIA Tensor Core。单张复杂仪表图片（如 D0 混调器 11 个字段）处理时间从 50s+ 缩短至 **5~8 秒**。
2. **零 Padding 紧凑裁剪**：
   - 优化了 YOLOv8 的后处理逻辑，精准提取纯净的仪表屏幕（BBox 零填充），最大程度减少背景干扰。
3. **暗光自适应旋转引擎 (OpenCV)**：
   - 针对 D4 (水质仪) 等容易横置摆放的设备，底层内置 CLAHE 暗光增强与 Canny 边缘密度探测算法，自动执行 90° 顺逆时针旋转纠正，确保大模型始终读取正向屏幕。
4. **全动态 Prompt 模板引擎**：
   - 彻底实行“去数值化”和“布局感知”提示词策略，杜绝大模型在暗光或黑屏（关机）状态下的“数字幻觉”复读。
5. **React/Next.js 全栈控制台**：
   - 提供 5 大定制化核心实验（表观黏度、表面/界面张力、运动粘度、水质矿化度、pH值）的结构化表单。
   - 内置全流程 SVG 交互式实验操作指导，支持一键 Excel 原始记录导出及纯水张力均值自动核算。

## 离线部署方案 (Windows)

系统支持一键打包与离线部署，专为无外网的实验室环境设计。

### 1. 环境前提
- **OS**: Windows 10/11
- **硬件**: 推荐 NVIDIA 3060 Ti (8GB) 或以上显卡
- **基础依赖**: 需提前安装 Python 3.10+ 和 Node.js 18+

### 2. 快速部署步骤
1. 将 `deploy/ocr-system/` 拷贝至目标机器。
2. 按目录内的 `README_DEPLOY.txt` 指引，将 `llama-b8937-bin-win-cuda-13.1-x64` 和 `Qianfan-OCR-GGUF` 放入指定位置。
3. 确保 `last.pt` (YOLO 模型) 在系统根目录。
4. 双击 `1_install_env.bat`，脚本将从本地 `python_wheels` 自动无网安装环境。
5. 双击 `2_start_system.bat`，系统将自动并行拉起 `llama-server`、`FastAPI` 和 `Next.js` 服务。

## 服务访问

- **前端控制台**: `http://localhost:3000`
- **后端 API 文档**: `http://localhost:8001/docs`
- **大模型 RPC 监控**: `http://localhost:8080/health`
