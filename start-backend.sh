#!/bin/bash
# 启动后端 API 服务
cd ~/github/ocr-new
echo "启动后端 API (端口 8765)..."
~/miniconda3/envs/sglang/bin/uvicorn api_server:app --host 0.0.0.0 --port 8765 --reload
