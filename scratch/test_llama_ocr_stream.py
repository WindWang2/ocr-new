import base64
import httpx
import json
import os

IMAGE_PATH = "demo/1.jpg"
URL = "http://127.0.0.1:8080/v1/chat/completions"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_ocr_stream():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image {IMAGE_PATH} not found.")
        return

    base64_image = encode_image(IMAGE_PATH)

    payload = {
        "model": "qwen",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "<image>\n图中是一个什么样的仪表？读数是多少？"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "stream": True
    }

    print("Requesting OCR stream...")
    try:
        with httpx.stream("POST", URL, json=payload, timeout=120.0) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                return

            print("OCR Stream started:")
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        thinking = delta.get("thinking", "")
                        reasoning = delta.get("reasoning_content", "") # DeepSeek-style
                        
                        if content:
                            print(content, end="", flush=True)
                        elif thinking:
                            print(f"<{thinking}>", end="", flush=True)
                        elif reasoning:
                            print(f"[{reasoning}]", end="", flush=True)
                        else:
                            # 如果还是什么都没有，打印原始 delta 看看
                            if delta:
                                print(f"DEBUG_DELTA: {delta}")
                    except Exception:
                        pass
            print("\nOCR Stream finished.")
    except Exception as e:
        print(f"\nOCR Stream failed: {e}")

if __name__ == "__main__":
    test_ocr_stream()
