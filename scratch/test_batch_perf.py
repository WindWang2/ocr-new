import base64
import requests
import time
import os

API_URL = "http://localhost:8080/v1/chat/completions"

# 准备三张不同的测试图
test_images = [
    {
        "name": "D0 Mixer",
        "path": r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F0\20260418\crops\20260418170647791_F0-I0_OK_crop_F0_184851.png",
        "prompt": "这是实验室混料机屏幕，提取运行模式、各段转速和时间、总时长。输出JSON。"
    },
    {
        "name": "D1 Scale",
        "path": r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F3\20260418\crops\20260418170647791_F3-I0_OK_crop_F1_182228.png",
        "prompt": "这是电子天平，提取重量数值。输出JSON。"
    },
    {
        "name": "D5 Tension",
        "path": r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F5\20260418\crops\20260418170647791_F5-I0_OK_crop_F5_183605.png",
        "prompt": "这是表界面张力仪，提取张力、温度、速度等数值。输出JSON。"
    }
]

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def run_perf_test():
    print(f"{'Image Name':<15} | {'Total Time':<10} | {'Status':<10}")
    print("-" * 45)
    
    for item in test_images:
        if not os.path.exists(item["path"]):
            print(f"{item['name']:<15} | {'MISSING':<10} | Skip")
            continue
            
        img_b64 = image_to_base64(item["path"])
        payload = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": item["prompt"]}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}]}],
            "temperature": 0.0,
            "stream": False
        }
        
        start_time = time.time()
        try:
            response = requests.post(API_URL, json=payload, timeout=90)
            elapsed = time.time() - start_time
            if response.status_code == 200:
                print(f"{item['name']:<15} | {elapsed:>8.2f}s | OK")
            else:
                print(f"{item['name']:<15} | {elapsed:>8.2f}s | ERROR {response.status_code}")
        except Exception as e:
            print(f"{item['name']:<15} | {'FAILED':<10} | {str(e)}")

if __name__ == "__main__":
    run_perf_test()
