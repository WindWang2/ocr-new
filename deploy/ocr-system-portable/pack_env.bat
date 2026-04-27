@echo off
title WANGJ-OCR 环境打包向导 (环境绿化)
chcp 936 >nul
color 0E

echo ======================================================
echo    WANGJ-OCR 便携包打包工具
echo    作用：将当前电脑的 Python 和 Node 环境拷贝进包内
echo ======================================================

set "BASE_DIR=%~dp0"

:: --- 配置源环境路径 (根据您的机器修改) ---
set "CONDA_ENV=C:\Users\wangj.KEVIN\.conda\envs\ocr_backend"

echo [1/2] 正在绿化 Python 环境...
if exist "%CONDA_ENV%" (
    echo 正在从 %CONDA_ENV% 复制文件，这可能需要几分钟...
    xcopy "%CONDA_ENV%" "%BASE_DIR%bin\python" /E /I /Y /Q
) else (
    echo [错误] 找不到指定的 Conda 环境: %CONDA_ENV%
    echo 请在 pack_env.bat 中修改 CONDA_ENV 变量指向正确的环境路径。
)

echo [2/2] 正在绿化 Node.js 环境...
for /f "delims=" %%i in ('where node.exe') do set "NODE_PATH=%%i"
if defined NODE_PATH (
    echo 正在从 %NODE_PATH% 所在目录复制 Node 环境...
    xcopy "%NODE_PATH%\.." "%BASE_DIR%bin\node" /E /I /Y /Q
) else (
    echo [错误] 当前系统未安装 Node.js，无法打包。
)

echo ======================================================
echo 打包任务结束！
echo 如果上述步骤无报错，bin 目录下现在应包含完整的运行环境。
echo 您现在可以将整个文件夹拷贝到任何新机器上。
echo ======================================================
pause
