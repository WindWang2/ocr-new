import base64
import httpx
import json
import os

IMAGE_PATH = "demo/1.jpg"
URL = "http://127.0.0.1:8080/v1/chat/completions"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_ocr():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image {IMAGE_PATH} not found.")
        return

    print(f"Encoding image {IMAGE_PATH}...")
    base64_image = encode_image(IMAGE_PATH)

    payload = {
        "model": "qwen",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "图中是一个什么样的仪表？读数是多少？"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }

    print("Sending request to local llama-server...")
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(URL, json=payload)
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            content = message.get("content") or ""
            reasoning = message.get("reasoning_content") or ""
            
            print("\n--- OCR Test Result ---")
            if reasoning:
                print(f"Reasoning:\n{reasoning}\n")
            print(f"Final Content:\n{content}")
            print("------------------------")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_ocr()
