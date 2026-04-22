import httpx
import json

URL = "http://127.0.0.1:8080/v1/chat/completions"

def test_stream():
    payload = {
        "model": "qwen",
        "messages": [
            {"role": "user", "content": "1+1等于几？"}
        ],
        "temperature": 0.1,
        "max_tokens": 100,
        "stream": True
    }

    print("Requesting stream...")
    try:
        with httpx.stream("POST", URL, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.read())
                return

            print("Stream started:")
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
                        if content:
                            print(content, end="", flush=True)
                        if thinking:
                            print(f"[Thinking: {thinking}]", end="", flush=True)
                    except Exception as e:
                        print(f"\nParse error: {e} | Line: {line}")
            print("\nStream finished.")
    except Exception as e:
        print(f"\nStream failed: {e}")

if __name__ == "__main__":
    test_stream()
