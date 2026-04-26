from PIL import Image
import os

path = r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F7\000_115001.jpg"
if os.path.exists(path):
    img = Image.open(path)
    print(f"Size: {img.size}")
    print(f"Format: {img.format}")
else:
    print("File not found")
