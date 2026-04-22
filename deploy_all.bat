@echo off
title OCR System - One-Click Deployment
setlocal

echo ===================================================
echo   OCR Instrument Identification System - Deployment
echo ===================================================
echo.

:: 1. Start Llama Server (Obsolete - Now using native local_vlm)
:: echo [1/3] Starting Local Llama Server (Port 8080)...
:: start "Llama-Server" cmd /c start_llama_server.bat
:: ping 127.0.0.1 -n 8 > nul

:: 2. Start Backend API (Using PowerShell to ensure environment safety)
echo [2/3] Starting Backend API (Port 8001)...
start "Backend-API" powershell -ExecutionPolicy Bypass -File start_backend.ps1
ping 127.0.0.1 -n 5 > nul

:: 3. Start Frontend UI
echo [3/3] Starting Frontend UI (Port 3000)...
start "Frontend-UI" cmd /c start_frontend.bat

echo.
echo ===================================================
echo   Deployment Started Successfully!
echo ===================================================
echo.
echo Service Endpoints:
echo - Frontend: http://localhost:3000
echo - Backend:  http://localhost:8001/docs
echo - Llama:    http://localhost:8080/status
echo.
pause
