@echo off
chcp 65001 >nul
title 实验室仪表OCR系统 - 一键部署与运行
color 0B

echo ===================================================
echo     实验室仪表 OCR 识别系统 - 自动部署与运行环境
echo ===================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并添加到系统 PATH。
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+ 并添加到系统 PATH。
    pause
    exit /b 1
)

echo [1/3] 检查并安装后端依赖 (Python)...
if not exist "backend_env" (
    echo 创建 Python 虚拟环境...
    python -m venv backend_env
)
call backend_env\Scripts\activate.bat
pip install -r requirements.txt
pip install uvicorn fastapi
echo 后端依赖就绪。
echo.

echo [2/3] 检查并安装前端依赖 (Node.js)...
cd frontend
if not exist "node_modules" (
    echo 正在安装 npm 依赖，请稍候...
    call npm install
)
cd ..
echo 前端依赖就绪。
echo.

echo [3/3] 启动系统服务...

:: 启动后端
echo 启动后端服务 (端口 8001)...
start "OCR Backend API" cmd /c "call backend_env\Scripts\activate.bat && set PYTHONPATH=%cd% && python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001"

:: 启动前端
echo 启动前端界面 (端口 3000)...
start "OCR Frontend Web" cmd /c "cd frontend && npm run dev"

echo.
echo ===================================================
echo 系统已成功启动！
echo.
echo 前端访问地址: http://localhost:3000
echo 后端 API 文档: http://localhost:8001/docs
echo.
echo 注意：如果需要使用高性能大模型(Qianfan-OCR)，请确保 llama-server 已在后台运行。
echo ===================================================
pause
