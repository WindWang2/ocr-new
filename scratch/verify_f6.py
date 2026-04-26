import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8001"

def test_f6_reading():
    print("Testing F6 (Stirrer) Reading...")
    
    # 0. 寻找有效的实验 ID
    try:
        exp_list_res = requests.get(f"{BASE_URL}/experiments")
        exp_list = exp_list_res.json().get("experiments", [])
        if not exp_list:
            print("Error: No experiments found in database.")
            return
        exp_id = exp_list[0]["id"]
        print(f"Using experiment ID: {exp_id}")
    except Exception as e:
        print(f"Failed to fetch experiment list: {e}")
        return

    # 1. 寻找测试图片
    image_dir = "camera_images/F6"
    if not os.path.exists(image_dir):
        image_dir = "C:/Users/wangj.KEVIN/Downloads/更换镜头后-测试20260415/更换镜头后-测试20260415/F6"
    
    if not os.path.exists(image_dir):
        print("Error: Could not find F6 test images.")
        return

    images = sorted(Path(image_dir).glob("*.jpg"), key=os.path.getmtime, reverse=True)
    if not images:
        print("Error: No images in F6 directory.")
        return
    
    img_path = str(images[0])
    print(f"Using image: {img_path}")

    # 2. 模拟前端调用 /run-test
    payload = {
        "field_key": "F6_stirrer",
        "target_instrument_id": 6,
        "image_path": os.path.abspath(img_path),
        "precise": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/experiments/{exp_id}/run-test", json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("\nOCR Results:")
        print(json.dumps(result.get("all_ocr", {}), indent=2, ensure_ascii=False))
        
        all_ocr = result.get("all_ocr", {})
        time_val = all_ocr.get("运行时间") or all_ocr.get("time")
        
        if time_val:
            print(f"\nSUCCESS: Time value found: {time_val}")
            if ":" in str(time_val):
                print("SUCCESS: Time format preserved as string with colon.")
            else:
                print("WARNING: Time format is NOT preserved (lost colon).")
        else:
            print("\nERROR: Time field not found in OCR results.")
                
        print("\nPrimary Reading:")
        print(f"Reading: {result.get('readings', [])}")
        
    except Exception as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_f6_reading()
