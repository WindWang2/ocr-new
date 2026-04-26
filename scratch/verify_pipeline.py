"""验证新流水线：原图 -> 1/3 YOLO -> 3x bbox -> 原图裁剪 -> 600px -> 单文件"""
import requests, json
from pathlib import Path
from PIL import Image

# 1. 测试 capture 接口
print("=" * 60)
print("测试 /capture 接口（F7 仪器）")
print("=" * 60)

r = requests.post(
    "http://localhost:8001/experiments/27/capture",
    json={"camera_id": 7, "target_instrument_id": 7, "field_key": "temperature"}
)
resp = r.json()
print(f"返回: {json.dumps(resp, indent=2, ensure_ascii=False)}")

if resp.get("success"):
    crop_path = resp["image_path"]
    print(f"\n裁剪图相对路径: {crop_path}")
    
    # 验证图片可以通过 /images 访问
    img_r = requests.get(f"http://localhost:8001/images/{crop_path}")
    print(f"HTTP 状态: {img_r.status_code}, 大小: {len(img_r.content)} bytes")
    
    # 验证文件系统上的裁剪图
    base_dir = Path(r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415")
    full_path = base_dir / crop_path.replace("/", "\\")
    if full_path.exists():
        img = Image.open(full_path)
        print(f"裁剪图实际尺寸: {img.size[0]}x{img.size[1]}")
        print(f"文件大小: {full_path.stat().st_size / 1024:.1f} KB")
        
        # 验证最长边是否为 600
        max_dim = max(img.size)
        if max_dim <= 600:
            print(f"✅ 最长边 = {max_dim}px (≤600)")
        else:
            print(f"❌ 最长边 = {max_dim}px (超过600!)")
    
    # 验证没有多余的 display/recognition 子目录
    crops_dir = full_path.parent
    has_display = (crops_dir / "display").exists()
    has_recognition = (crops_dir / "recognition").exists()
    print(f"\n是否存在 display 子目录: {has_display}")
    print(f"是否存在 recognition 子目录: {has_recognition}")
    if not has_display and not has_recognition:
        print("✅ 无多余中间文件目录")
    
    # 检查 crops 目录中的文件
    print(f"\ncrops 目录内容 ({crops_dir}):")
    for f in sorted(crops_dir.iterdir()):
        if f.is_file():
            print(f"  {f.name}  ({f.stat().st_size / 1024:.1f} KB)")
        elif f.is_dir():
            print(f"  [DIR] {f.name}/")

print("\n" + "=" * 60)
print("完成")
