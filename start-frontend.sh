#!/bin/bash
# 启动前端开发服务器
cd $(dirname "$0")/frontend
echo "启动前端 (端口 3000)..."
npm run dev
