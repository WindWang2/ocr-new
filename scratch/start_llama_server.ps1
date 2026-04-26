# 启动 llama-server.exe 脚本 (GPU 加速增强版)
$LlamaDir = "C:\Users\wangj.KEVIN\projects\llama-b8929-bin-win-cuda-12.4-x64"
$ModelPath = "C:\Users\wangj.KEVIN\projects\Qianfan-OCR-GGUF\Qianfan-OCR-q4_k_m.gguf"
$MmprojPath = "C:\Users\wangj.KEVIN\projects\Qianfan-OCR-GGUF\Qianfan-OCR-mmproj-f16.gguf"

Write-Host "Starting llama-server with Qianfan-OCR (GPU Vision Enabled)..." -ForegroundColor Cyan

& "$LlamaDir\llama-server.exe" `
    --model $ModelPath `
    --mmproj $MmprojPath `
    --n-gpu-layers -1 `
    --mmproj-offload `
    --flash-attn on `
    --ctx-size 4096 `
    --port 8080 `
    --host 0.0.0.0
