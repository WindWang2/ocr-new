@echo off
title WANGJ-OCR 仪表识别系统 - 启动中心 (高性能版)
:: 必须使用 ANSI 编码保存此文件以防止乱码
chcp 936 >nul
color 0B

set "BASE_DIR=%~dp0"
:: 去掉末尾可能存在的反斜杠
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"

:: 路径转换：将反斜杠转换为正斜杠，解决 llama-server 路径识别问题
set "GGUF_MODEL=%BASE_DIR%\models\exp-ocr\exp-ocr-q4_k_m.gguf"
set "GGUF_MMPROJ=%BASE_DIR%\models\exp-ocr\exp-ocr-mmproj-f16.gguf"
set "MODEL_UNIX=%GGUF_MODEL:\=/%"
set "MMPROJ_UNIX=%GGUF_MMPROJ:\=/%"

set "LLAMA_BIN=%BASE_DIR%\bin\llama-cpp\llama-server.exe"
set "PYTHON_CMD=%BASE_DIR%\bin\python\python.exe"

echo ======================================================
echo    WANGJ-OCR 系统启动中心 (Portable V1.3)
echo ======================================================

:: 1. 启动算力后端
echo [1/3] 正在加载 GPU 加速后端...
if exist "%LLAMA_BIN%" (
    start "Llama Server" cmd /c ""%LLAMA_BIN%" -m "%MODEL_UNIX%" --mmproj "%MMPROJ_UNIX%" -ngl -1 --mmproj-offload --flash-attn on --ctx-size 4096 --port 8080 --host 0.0.0.0"
) else (
    echo [错误] 未找到 llama-server.exe
)

:: 2. 启动 API 后端
echo [2/3] 正在启动 API 逻辑服务...
set "PYTHONPATH=%BASE_DIR%"
start "OCR Backend" cmd /c "cd /d "%BASE_DIR%" && "%PYTHON_CMD%" -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001"

:: 3. 启动 Web 前端
echo [3/3] 正在启动前端控制台...
if exist "%BASE_DIR%\frontend\server.js" (
    start "OCR Frontend" cmd /c "cd /d "%BASE_DIR%\frontend" && ..\bin\node\node.exe server.js"
) else (
    echo [提示] 正在使用开发模式启动前端...
    start "OCR Frontend" cmd /c "cd /d "%BASE_DIR%\frontend" && npm run dev"
)

echo.
echo 系统启动成功！
echo 访问地址: http://localhost:3000
echo ======================================================
pause
