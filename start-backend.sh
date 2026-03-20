#!/bin/bash
# 启动后端 API 服务
cd ~/projects/ocr-new
echo "启动后端 API (端口 8000)..."
source .venv/bin/activate
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
