# OCR 仪表读数识别系统 部署指南

## 环境要求
- Python 3.8+
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
