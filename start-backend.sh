#!/bin/bash
# 启动后端 API 服务
cd $(dirname "$0")
echo "启动后端 API (端口 8001)..."
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001 --reload
