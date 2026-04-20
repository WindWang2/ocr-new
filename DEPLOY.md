# OCR 仪表读数识别系统 部署指南

## 环境要求
- Python 3.10+
- PyTorch 2.4+ (YOLO26x 推理用)
- torchvision (手动 NMS 算子)
- Node.js 18+ (前端)
- 支持硬件相机或模拟相机服务

## 快速部署

### 1. 安装依赖
```bash
# 后端依赖 (建议在 conda 环境中安装)
pip install -r requirements.txt
# 核心依赖: ultralytics (YOLO), torch, torchvision, fastapi, uvicorn
```

### 2. 启动后端服务
```bash
# 默认端口 8001
./start-backend.sh
```

### 3. 启动前端服务
```bash
./start-frontend.sh
```
前端服务运行在 `http://localhost:3000`

## 功能清单
✅ 多相机管理
✅ 实验记录全生命周期管理
✅ **YOLO26x 旗舰级目标检测**（自动识别 9 类仪表 0-8）
✅ **智能自动裁剪 (Auto-Crop)**（提供仪表高清特写供识别）
✅ **跨类别 NMS 消除**（彻底解决 E2E 模型重叠框问题）
✅ 多模态大模型读数精读 (LMStudio/OpenAI 兼容)
✅ 结果导出 Excel (含特写图路径)

## 核心流程

系统现已实现“相机与仪器解耦”：
1. **拍照**：触发相机获取全景 BMP 大图。
2. **检测与分类**：YOLO26x 引擎自动扫描全图，识别所有已知仪器并分类（0-8 对应 F0-F8 模板）。
3. **裁剪**：系统根据检测框自动裁剪出仪器特写，保存在 `camera_images/crops/`。
4. **精读**：将特写图送往大模型，根据分类 ID 匹配 Prompt 进行结构化读数提取。
5. **展示**：前端直接展示裁剪后的高清特写，方便人工校对。

## 配置修改
编辑 `config.py` 修改相关配置：
- LMSTUDIO_BASE_URL: 本地大模型服务地址
- YOLO 权重路径 (默认 models/yolo_instrument.pt)

## 测试验证
```bash
# 运行推理引擎测试
python read_instrument.py demo/1.jpg
```
