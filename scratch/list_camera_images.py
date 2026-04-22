import os
import sys
from pathlib import Path

# 添加项目路径到 PYTHONPATH
sys.path.append(os.getcwd())

from config import Config

print(f"IMAGE_DIR from config: {Config.IMAGE_DIR}")
base_path = Path(Config.IMAGE_DIR)

if not base_path.exists():
    print(f"Error: Path {base_path} does not exist.")
    sys.exit(1)

for cam_dir in sorted(base_path.glob("F*")):
    if cam_dir.is_dir():
        files = sorted(cam_dir.glob("*.jpg"), key=os.path.getmtime, reverse=True)
        if files:
            print(f"Camera {cam_dir.name}: {files[0].name} (Size: {os.path.getsize(files[0])} bytes)")
        else:
            print(f"Camera {cam_dir.name}: No images found.")
