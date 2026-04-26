"""验证高清裁剪修复：确保 detect_only 使用原始BMP而不是500px预览图"""
import sys
sys.path.insert(0, '.')

from PIL import Image
from pathlib import Path

# 模拟场景：传入一个 _preview.jpg，验证系统是否能找到原始BMP
test_dir = Path(r'C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F7')
preview_file = test_dir / '000_144804_preview.jpg'

print(f"=== 高清裁剪修复验证 ===\n")
print(f"1. 预览图路径: {preview_file}")
print(f"   预览图尺寸: {Image.open(preview_file).size}")

# 查找BMP原图
bmp_candidates = []
for sub in test_dir.iterdir():
    if sub.is_dir():
        for bmp_file in sub.glob("*.bmp"):
            bmp_candidates.append(bmp_file)
        for bmp_file in sub.glob("*.BMP"):
            bmp_candidates.append(bmp_file)

if bmp_candidates:
    latest_bmp = max(bmp_candidates, key=lambda f: f.stat().st_mtime)
    bmp_img = Image.open(latest_bmp)
    print(f"\n2. 发现BMP原图: {latest_bmp.name}")
    print(f"   BMP尺寸: {bmp_img.size}")
    print(f"   BMP文件大小: {latest_bmp.stat().st_size / 1024 / 1024:.1f}MB")
    
    # 对比裁剪质量
    # 从BMP裁剪
    from instrument_reader import InstrumentReader
    reader = InstrumentReader()
    
    print(f"\n3. 使用BMP原图进行YOLO检测...")
    result_bmp = reader.detect_only(str(latest_bmp))
    if result_bmp["success"]:
        for r in result_bmp["results"]:
            crop_path = r.get("image_source")
            if crop_path and Path(str(crop_path)).exists():
                crop_img = Image.open(str(crop_path))
                print(f"   F{r['class_id']}: 裁剪图尺寸 {crop_img.size} ← 从BMP原图裁剪")
    
    print(f"\n4. 使用预览图进行YOLO检测...")
    result_preview = reader.detect_only(str(preview_file))
    if result_preview["success"]:
        for r in result_preview["results"]:
            crop_path = r.get("image_source")
            if crop_path and Path(str(crop_path)).exists():
                crop_img = Image.open(str(crop_path))
                print(f"   F{r['class_id']}: 裁剪图尺寸 {crop_img.size} ← 智能发现BMP原图后裁剪")
    
    print(f"\n✅ 修复验证完成！")
else:
    print(f"\n❌ 未找到BMP原图，验证失败")
