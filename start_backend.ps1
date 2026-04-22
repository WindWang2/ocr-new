# OCR Backend Startup Script (PowerShell)
$ErrorActionPreference = "Stop"
Write-Host "[Backend] 正在启动 OCR 实验服务 API..." -ForegroundColor Cyan

# Environment Variables
$env:PYTHONNOUSERSITE = "1"
$env:AUTO_START_LLAMA = "true"

# Environment Python Path
$EnvPython = "C:\Users\wangj.KEVIN\.conda\envs\ocr_backend\python.exe"

if (-not (Test-Path $EnvPython)) {
    Write-Host "[ERROR] 未找到环境 Python: $EnvPython" -ForegroundColor Red
    exit 1
}

Write-Host "[Backend] 使用环境: $EnvPython" -ForegroundColor Green

# Start Uvicorn
$env:PYTHONPATH = (Get-Location).Path
$Uvicorn = "C:\Users\wangj.KEVIN\.conda\envs\ocr_backend\Scripts\uvicorn.exe"
& $Uvicorn backend.api.main:app --host 0.0.0.0 --port 8001 --reload
