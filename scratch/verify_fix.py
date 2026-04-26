import requests
import json

BASE_URL = "http://localhost:8001"

def test_instrument_centric_capture():
    # 假设实验 ID 为 1，相机 ID 为 0，仪器 ID 为 7 (水浴锅)
    # 在实际环境中需要确保后端正在运行
    payload = {
        "camera_id": 0,
        "target_instrument_id": 0,
        "field_key": "speed"
    }
    
    print(f"Testing capture with payload: {payload}")
    try:
        # 尝试获取一个存在的实验 ID
        res = requests.get(f"{BASE_URL}/experiments")
        exps = res.json().get("experiments", [])
        if not exps:
            print("No experiments found to test with.")
            return
        
        exp_id = exps[0]["id"]
        print(f"Using experiment ID: {exp_id}")
        
        response = requests.post(f"{BASE_URL}/experiments/{exp_id}/capture", json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        image_path = response.json().get("image_path", "")
        if "crops" in image_path:
            print("SUCCESS: Captured image is already a crop!")
        else:
            print("NOTICE: Captured image is still a full image. (This might happen if YOLO failed to detect)")

    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_instrument_centric_capture()
