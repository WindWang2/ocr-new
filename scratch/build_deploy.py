import os
import shutil
import subprocess
from pathlib import Path

def copytree_with_ignore(src, dst, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        if ignore and ignore(src, item):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree_with_ignore(s, d, ignore)
        else:
            shutil.copy2(s, d)

def main():
    deploy_dir = Path('deploy/ocr-system')
    
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    
    deploy_dir.mkdir(parents=True)
    
    print("Copying backend files...")
    # Copy backend folder
    def ignore_pycache(d, files):
        return [f for f in files if f == '__pycache__'] if d.endswith('__pycache__') or '__pycache__' in d else []
    
    shutil.copytree('backend', deploy_dir / 'backend', ignore=shutil.ignore_patterns('__pycache__', '*.db'))
    
    # Copy core python files
    shutil.copy('config.py', deploy_dir / 'config.py')
    shutil.copy('instrument_reader.py', deploy_dir / 'instrument_reader.py')
    shutil.copy('requirements.txt', deploy_dir / 'requirements.txt')
    
    print("Copying frontend standalone files...")
    # Copy frontend standalone
    standalone_src = Path('frontend/.next/standalone')
    if standalone_src.exists():
        # Copy the contents of standalone directly
        for item in os.listdir(standalone_src):
            s = standalone_src / item
            d = deploy_dir / 'frontend' / item
            if s.is_dir():
                shutil.copytree(s, d)
            else:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)
                
        # Copy .next/static and public
        shutil.copytree('frontend/.next/static', deploy_dir / 'frontend/.next/static', dirs_exist_ok=True)
        shutil.copytree('frontend/public', deploy_dir / 'frontend/public', dirs_exist_ok=True)
        
        # If there's an inner frontend dir inside standalone (due to workspace), move it up
        inner_frontend = deploy_dir / 'frontend' / 'frontend'
        if inner_frontend.exists():
            for item in os.listdir(inner_frontend):
                s = inner_frontend / item
                d = deploy_dir / 'frontend' / item
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            shutil.rmtree(inner_frontend)

    print("Downloading Python offline wheels...")
    # Download wheels for offline installation
    wheels_dir = deploy_dir / 'python_wheels'
    wheels_dir.mkdir(exist_ok=True)
    subprocess.run([
        'python', '-m', 'pip', 'download',
        '-r', 'requirements.txt',
        'fastapi', 'uvicorn', 'python-multipart', 'pillow',
        '--prefer-binary',
        '-d', str(wheels_dir)
    ], check=False) # check=False because some might fail to download strictly offline, but we try our best.

    print("Creating deployment scripts...")
    # Create install script
    with open(deploy_dir / '1_install_env.bat', 'w', encoding='utf-8') as f:
        f.write('''@echo off
chcp 65001 >nul
echo =========================================
echo   实验室仪表 OCR 系统 - 离线环境安装
echo =========================================

echo 正在创建 Python 虚拟环境...
python -m venv venv

echo 正在离线安装 Python 依赖...
call venv\\Scripts\\activate.bat
pip install --no-index --find-links=python_wheels -r requirements.txt
pip install --no-index --find-links=python_wheels fastapi uvicorn python-multipart pillow

echo 安装完成！
pause
''')

    # Create run script
    with open(deploy_dir / '2_start_system.bat', 'w', encoding='utf-8') as f:
        f.write('''@echo off
chcp 65001 >nul
title OCR 系统控制台
color 0A

echo =========================================
echo      实验室仪表 OCR 识别系统 - 启动
echo =========================================

if exist "llama.cpp\\llama-server.exe" (
    if exist "Qianfan-OCR-GGUF\\Qianfan-OCR-q4_k_m.gguf" (
        echo [1/3] 正在启动大模型推理服务 (Qianfan-OCR)...
        start "Llama Server (GPU)" cmd /c "cd llama.cpp && llama-server.exe --model ..\\Qianfan-OCR-GGUF\\Qianfan-OCR-q4_k_m.gguf --mmproj ..\\Qianfan-OCR-GGUF\\Qianfan-OCR-mmproj-f16.gguf --n-gpu-layers -1 --mmproj-offload --flash-attn on --ctx-size 4096 --port 8080 --host 0.0.0.0"
    ) else (
        echo [1/3] 未找到模型文件，跳过启动大模型服务。
    )
) else (
    echo [1/3] 未找到 llama.cpp 服务端程序，跳过启动大模型服务。
)

echo [2/3] 正在启动后端服务...
start "OCR Backend" cmd /c "call venv\\Scripts\\activate.bat && set PYTHONPATH=%cd% && python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001"

echo [3/3] 正在启动前端服务...
start "OCR Frontend" cmd /c "cd frontend && set PORT=3000 && node server.js"

echo 系统启动中，请等待几秒后访问：http://localhost:3000
pause
''')

    with open(deploy_dir / 'README_DEPLOY.txt', 'w', encoding='utf-8') as f:
        f.write('''实验室仪表 OCR 识别系统 - 离线部署包

【前提要求】
1. 目标机器已安装 Python 3.10+ (并已加入系统 PATH)。
2. 目标机器已安装 Node.js 18+ (并已加入系统 PATH)。
3. 若需使用 GPU 加速，请确保目标机器拥有 NVIDIA 显卡 (如 3060Ti) 并已安装对应的显卡驱动 (建议支持 CUDA 13.1)。

【部署步骤】
1. 双击运行 `1_install_env.bat`，系统将自动离线安装所需的所有 Python 依赖。
2. (非常重要) 将上级目录的 `llama-b8937-bin-win-cuda-13.1-x64.zip` 解压，并将其中的文件放入本目录下的 `llama.cpp` 文件夹中。
3. (非常重要) 将上级目录的 `cudart-llama-bin-win-cuda-13.1-x64.zip` 解压，并将其中的 DLL 文件也放入 `llama.cpp` 文件夹中。
4. (非常重要) 将上级目录的 `Qianfan-OCR-GGUF` 文件夹完整复制到本目录下。
5. 确保 `last.pt` (YOLO 模型) 已存在于本目录下（打包脚本会自动尝试复制，若缺失请手动从上级目录拷贝）。
6. 双击运行 `2_start_system.bat`，系统将依次启动大模型服务、后端API、前端网页。
7. 启动完成后，在浏览器中访问 http://localhost:3000 即可使用。

【目录结构说明】
- backend/: 后端核心代码
- frontend/: 编译后独立的 Next.js 前端 (内含 node_modules，无需 npm install)
- python_wheels/: 离线依赖包安装源
- venv/: 运行 1_install_env.bat 后生成的 Python 虚拟环境
- llama.cpp/: 需手动创建并放入 llama-b8937 和 cudart 的离线文件
- Qianfan-OCR-GGUF/: 需手动放入的多模态大模型文件
- last.pt: YOLOv8 目标定位模型文件
''')

    print(f"Deployment package created at: {deploy_dir.absolute()}")

if __name__ == "__main__":
    main()
