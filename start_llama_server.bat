@echo off
title Llama-Server (Qwen 2B Multimodal)
echo Starting Local LLM Server...
echo Model: ..\2B-new\Qwen3.5-2B.Q4_K_M.gguf
echo MMProj: ..\2B-new\mmproj-BF16.gguf
echo.

"..\llama-cpp\llama-server.exe" -m "..\2B-new\Qwen3.5-2B.Q4_K_M.gguf" --mmproj "..\2B-new\mmproj-BF16.gguf" -ngl -1 --host 127.0.0.1 --port 8080 -c 4096

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server failed to start.
    echo Please check if GPU drivers/CUDA 12.4 are installed.
    pause
)
