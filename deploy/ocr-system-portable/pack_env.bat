@echo off
title 打包运行环境到便携包
chcp 65001 >nul
color 0B

echo ======================================================
echo    正在将当前机器的 Python 和 Node.js 打包进便携包
echo ======================================================

set "BASE_DIR=%~dp0"
set "CONDA_ENV=C:\Users\wangj.KEVIN\.conda\envs\ocr_backend"

echo [1/2] 正在复制 Python 环境 (约 3-5 GB, 请耐心等待)...
xcopy "%CONDA_ENV%" "%BASE_DIR%bin\python" /E /I /Y /Q

echo [2/2] 正在复制 Node.js 环境...
for /f "delims=" %%i in ('where node.exe') do set "NODE_PATH=%%i"
if defined NODE_PATH (
    xcopy "%NODE_PATH%\.." "%BASE_DIR%bin\node" /E /I /Y /Q
) else (
    echo [错误] 当前机器未找到 node.exe
)

echo ======================================================
echo 打包完成！
echo 您现在可以将整个 ocr-system-portable 文件夹拷贝到任何新机器上。
echo 新机器上无需安装任何依赖，直接双击 run.bat 即可运行。
echo ======================================================
pause
