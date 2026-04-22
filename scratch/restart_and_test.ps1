# 强杀旧进程
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process uvicorn* -ErrorAction SilentlyContinue | Stop-Process -Force

# 启动后端并重定向
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File start_backend.ps1" -WorkingDirectory "c:\Users\wangj.KEVIN\projects\ocr-new" -RedirectStandardOutput backend.log -RedirectStandardError backend_err.log

Write-Host "Waiting for backend to start and model to load (20s)..."
Start-Sleep -Seconds 20

# 触发 F1 识别测试
$body = @{ field_key = "F1"; target_instrument_id = 1 } | ConvertTo-Json
Write-Host "Triggering OCR test for F1..."
try {
    $res = Invoke-RestMethod -Uri http://127.0.0.1:8001/experiments/8/run-test -Method Post -Body $body -ContentType "application/json"
    $res | ConvertTo-Json
} catch {
    Write-Error "Request failed: $_"
}

Start-Sleep -Seconds 5
Write-Host "--- LAST 100 LINES OF BACKEND.LOG ---"
Get-Content backend.log -Tail 100
