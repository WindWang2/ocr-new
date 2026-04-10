# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime

image_dir = Path(r"E:\维视视觉\2.原图\仪器界面数据读取-测试")
camera_dir = image_dir / "F0"
today_dir = camera_dir / datetime.now().strftime("%Y%m%d")

print("image_dir exists:", image_dir.exists())
print("camera_dir exists:", camera_dir.exists())
print("today_dir:", today_dir)
print("today_dir exists:", today_dir.exists())

if camera_dir.exists():
    print("\nF0 subdirs:")
    for d in sorted(camera_dir.iterdir()):
        if d.is_dir():
            print(" ", d.name)

if today_dir.exists():
    print(f"\nFiles in {today_dir}:")
    for f in sorted(today_dir.iterdir())[:10]:
        print(" ", f.name)
else:
    print("\ntoday_dir not found, listing latest dir files:")
    if camera_dir.exists():
        dirs = sorted([d for d in camera_dir.iterdir() if d.is_dir()], reverse=True)
        if dirs:
            latest = dirs[0]
            print(f"Latest dir: {latest}")
            for f in sorted(latest.iterdir())[:10]:
                print(" ", f.name)
