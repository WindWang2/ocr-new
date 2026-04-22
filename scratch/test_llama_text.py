import httpx

URL = "http://127.0.0.1:8080/v1/chat/completions"

def test_text():
    payload = {
        "model": "qwen",
        "messages": [
            {"role": "user", "content": "你好，请自我介绍一下。"}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(URL, json=payload)
            response.raise_for_status()
            result = response.json()
            print("Response JSON:", result)
            print("Content:", result["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"Text test failed: {e}")

if __name__ == "__main__":
    test_text()
