import base64
import requests
import json
import os

# 配置
API_URL = "http://localhost:8080/v1/chat/completions"
# 使用 D0 自动模式的裁剪图进行测试
IMAGE_PATH = r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F0\20260418\crops\20260418170647791_F0-I0_OK_crop_F0_184851.png"

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_llama_server_ocr():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        return

    print(f"Testing Qianfan-OCR via llama-server...")
    print(f"Image: {os.path.basename(IMAGE_PATH)}")
    
    img_b64 = image_to_base64(IMAGE_PATH)
    
    prompt = """这是实验室混料机屏幕。
1. 判断运行模式（左侧菜单）。
2. 提取段一、段二、段三的转速和时间。
3. 提取总共时长、剩余时长、当前段数、当前转速。

严格按以下JSON格式输出，使用中文键名：
{"模式": "自动", "段一转速": "10000", "段一时间": "20", "段二转速": "16000", "段二时间": "20", "段三转速": "22000", "段三时间": "20", "总共时长": "60", "剩余时长": "1", "当前段数": "1", "当前转速": "0"}
"""

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.0,
        "stream": False
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        print("\n--- OCR Result from llama-server ---")
        print(content)
        print("------------------------------------\n")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_llama_server_ocr()
