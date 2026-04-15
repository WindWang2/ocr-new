# OCR 仪表读数识别系统 部署指南

## 环境要求
- Python 3.8+
- PyTorch 2.0+ (YOLO+CLIP 推理用)
- Node.js 18+ (前端)
- 支持硬件相机或模拟相机服务

## 快速部署

### 1. 安装依赖
```bash
# 后端依赖
pip install -r requirements.txt --break-system-packages

# 前端依赖 (可选，仅需运行前端时安装)
cd frontend
npm install
```

### 2. 启动后端服务
```bash
./start-backend.sh
```
后端服务运行在 `http://0.0.0.0:8001`

### 3. 启动前端服务 (可选)
```bash
./start-frontend.sh
```
前端服务运行在 `http://localhost:3000`

## 接口文档
访问 `http://localhost:8001/docs` 查看完整的Swagger API文档

## 功能清单
✅ 多相机管理（增删改查）
✅ 实验创建与执行（支持单/多相机模式）
✅ 拍照自动OCR识别仪表读数
✅ 实验结果存储与查询
✅ 单相机模式兼容
✅ 部分失败容错机制
✅ 可视化前端界面
✅ YOLO 目标检测多仪器定位
✅ CLIP 嵌入匹配仪器类型
✅ 多仪器流水线编排

## 多仪器模式

相机支持两种模式：
- **single** — 传统单仪器模式，直接对整张图片进行 OCR 识别
- **multi** — 多仪器模式，使用 YOLO+CLIP+LLM 三步流水线：
  1. YOLO 目标检测检测出图片中所有仪器区域并裁剪
  2. CLIP 对每个检测区域进行嵌入，匹配最相似的仪器类型
  3. 对每个仪器区域调用 LLM 提取读数

### 多仪器模式 API

- `POST /api/read-multi` — 多仪器批量识别接口，接收图片，返回所有仪器的类型和识别结果
- `POST /api/rebuild-clip-cache` — 重新生成 CLIP 仪器描述嵌入缓存，修改仪器配置后需调用更新

## 配置修改
编辑 `config.py` 修改相关配置：
- 相机控制端口
- LMStudio 模型地址
- 存储路径等

## 测试验证
```bash
# 运行全量测试
pytest tests/ -v
```

## 健康检查
```bash
curl http://localhost:8001/health
```
返回成功则服务正常运行
