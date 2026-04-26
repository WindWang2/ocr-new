from PIL import Image, ImageEnhance
import os

def debug_enhance():
    img_path = r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F7\000_224306.jpg"
    img = Image.open(img_path)
    # Box 1 for F6: [61.1, 64.6, 117.9, 137.2]
    # Padding 40
    bbox = [61.1, 64.6, 117.9, 137.2]
    padding = 40
    x1, y1, x2, y2 = map(int, bbox[:4])
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(img.width, x2 + padding)
    y2 = min(img.height, y2 + padding)
    crop = img.crop((x1, y1, x2, y2))
    
    # Enhancement
    enhancer = ImageEnhance.Brightness(crop)
    crop = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Contrast(crop)
    crop = enhancer.enhance(1.5)
    
    save_path = r"C:\Users\wangj.KEVIN\projects\ocr-new\scratch\f6_enhanced_debug.png"
    crop.save(save_path)
    print(f"Enhanced crop saved to {save_path}")

if __name__ == "__main__":
    debug_enhance()
