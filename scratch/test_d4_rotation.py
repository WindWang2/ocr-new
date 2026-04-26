import cv2
import numpy as np
import os

def determine_rotation(image_path):
    print(f"Analyzing {os.path.basename(image_path)}...")
    img_array = np.fromfile(image_path, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Failed to load image.")
        return None

    h, w = img.shape
    
    # 缩小图像以加快处理速度并减少噪点
    scale = 600 / max(h, w)
    small_img = cv2.resize(img, (int(w * scale), int(h * scale)))
    sh, sw = small_img.shape

    # 1. 增强对比度 (CLAHE) 应对暗光情况
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced_img = clahe.apply(small_img)

    # 2. 边缘检测
    edges = cv2.Canny(enhanced_img, 50, 150)

    # 3. 将图像分为左右两半，计算边缘像素的密度
    left_half = edges[:, :sw//2]
    right_half = edges[:, sw//2:]

    left_density = np.sum(left_half > 0)
    right_density = np.sum(right_half > 0)

    print(f"  Left edge density: {left_density}")
    print(f"  Right edge density: {right_density}")

    # 屏幕区域（包含大量文字和图形边缘）通常会有更高的边缘密度
    # 正常视角下，屏幕在下方。如果目前横放，屏幕在左侧则机器底部在左，需顺时针(270度或-90度)
    # 屏幕在右侧则机器底部在右，需逆时针(90度)
    
    # 我们期望白板在上，屏幕在下。
    # 假设图像横置，屏幕在左（边缘密度左>右） -> 屏幕在底部意味着向左旋转了90度 -> 需要顺时针旋转90度（也就是ROTATE_90_CLOCKWISE）
    # 屏幕在右（边缘密度右>左） -> 屏幕在底部意味着向右旋转了90度 -> 需要逆时针旋转90度（也就是ROTATE_90_COUNTERCLOCKWISE）

    if left_density > right_density:
        print("  Screen detected on the LEFT.")
        print("  Action: Rotate 90 degrees CLOCKWISE.")
        return cv2.ROTATE_90_CLOCKWISE
    else:
        print("  Screen detected on the RIGHT.")
        print("  Action: Rotate 90 degrees COUNTERCLOCKWISE.")
        return cv2.ROTATE_90_COUNTERCLOCKWISE

def test_images():
    images = [
        r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\20260422112556581_F5-I0_OK.bmp", # 明亮
        r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\20260422110348871_F5-I0_OK.bmp", # 正常
        r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\20260422112023634_F5-I0_OK.bmp"  # 暗光
    ]

    for img_path in images:
        if os.path.exists(img_path):
            rotation = determine_rotation(img_path)
        else:
            print(f"File not found: {img_path}")

if __name__ == "__main__":
    test_images()
