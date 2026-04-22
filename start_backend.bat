@echo off
setlocal
echo [Backend] 正在启动 OCR 实验服务 API (强制使用 ocr_backend 环境)...

:: 环境变量设置
set PYTHONNOUSERSITE=1
set AUTO_START_LLAMA=true

:: 使用绝对路径以确保环境正确，防止被全局 Python 干扰
set ENV_PYTHON=C:\Users\wangj.KEVIN\.conda\envs\ocr_backend\python.exe

if not exist "%ENV_PYTHON%" (
    echo [ERROR] 未找到环境 Python: %ENV_PYTHON%
    echo 请检查 Conda 环境 ocr_backend 是否安装。
    pause
    exit /b 1
)

echo [Backend] 使用环境: %ENV_PYTHON%

:: 启动 Uvicorn (使用 -m 以确保加载环境内的包)
"%ENV_PYTHON%" -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001 --reload --reload-dir backend

if %ERRORLEVEL% neq 0 (
    echo [ERROR] 后端启动失败。
    pause
)
