import os
from pathlib import Path

# 使用正斜杠避免转义问题
base_path = Path("C:/Users/wangj.KEVIN/Downloads/更换镜头后-测试20260415/更换镜头后-测试20260415")

print(f"Auditing path: {base_path}")

if not base_path.exists():
    print("Error: Base path not found.")
    # 尝试模糊搜索下载目录
    for p in Path("C:/Users/wangj.KEVIN/Downloads").glob("*20260415*"):
        print(f" - Found alternative: {p}")
else:
    for cam_dir in sorted(base_path.glob("F*")):
        if cam_dir.is_dir():
            files = sorted(cam_dir.glob("*.jpg"), key=os.path.getmtime, reverse=True)
            if files:
                print(f"Camera {cam_dir.name}: {len(files)} images. Latest: {files[0].name}")
            else:
                print(f"Camera {cam_dir.name}: Empty.")
