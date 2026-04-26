@echo off
title OCR 智能监控系统 - 纯绿化独立运行版 (RTX 3060 Ti)
chcp 65001 >nul
color 0A

:: 获取当前批处理所在的绝对路径
set "BASE_DIR=%~dp0"

:: 二进制执行文件路径
set "LLAMA_BIN=%BASE_DIR%bin\llama-cpp\llama-server.exe"
set "PYTHON_BIN=%BASE_DIR%bin\python\python.exe"
set "NODE_BIN=%BASE_DIR%bin\node\node.exe"

:: 模型文件路径
set "MODEL_PATH=%BASE_DIR%models\exp-ocr\exp-ocr-q4_k_m.gguf"
set "MMPROJ_PATH=%BASE_DIR%models\exp-ocr\exp-ocr-mmproj-f16.gguf"

echo ======================================================
echo    OCR 实验室系统 - 无依赖免安装版 (双击即用)
echo ======================================================

:: --- 端口清理逻辑 ---
echo [0/3] 正在检查端口占用情况...

set "PORTS=8080 8001 3000"
for %%P in (%PORTS%) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
        echo [清理] 端口 %%P 被进程 %%a 占用，正在强制结束...
        taskkill /F /PID %%a >nul 2>&1
    )
)
timeout /t 1 /nobreak >nul

:: 1. 启动大模型视觉算力核心
echo [1/3] 正在加载算力后端 (GPU 硬件加速)...
if exist "%LLAMA_BIN%" (
    if exist "%MODEL_PATH%" (
        start "Llama Server (GPU)" cmd /c ""%LLAMA_BIN%" --model "%MODEL_PATH%" --mmproj "%MMPROJ_PATH%" --n-gpu-layers -1 --mmproj-offload --flash-attn on --ctx-size 4096 --port 8080 --host 0.0.0.0"
    ) else (
        echo [错误] 未在 models\exp-ocr 中找到模型文件！
    )
) else (
    echo [错误] 未找到 %LLAMA_BIN%！
)

:: 2. 启动 API 逻辑后端
echo [2/3] 正在启动 API 逻辑服务...
set "PYTHONPATH=%BASE_DIR%"
if exist "%PYTHON_BIN%" (
    start "OCR Backend" cmd /c "cd /d "%BASE_DIR%" && "%PYTHON_BIN%" -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001"
) else (
    echo [错误] 未找到内置 Python 环境: %PYTHON_BIN%
)

:: 3. 启动 Web 前端控制台
echo [3/3] 正在启动 Web 前端控制台...
if exist "%NODE_BIN%" (
    if exist "%BASE_DIR%frontend\server.js" (
        start "OCR Frontend" cmd /c "cd /d "%BASE_DIR%frontend" && "%NODE_BIN%" server.js"
    ) else (
        echo [错误] 未找到 frontend\server.js
    )
) else (
    echo [错误] 未找到内置 Node.js: %NODE_BIN%
)

echo ======================================================
echo 系统启动指令已下发！
echo 访问地址: http://localhost:3000
echo ======================================================
pause
