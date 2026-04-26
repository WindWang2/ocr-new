import os
import sys

# 修复 Windows 下 llama-cpp-python 找不到 DLL 的问题
llama_cpp_lib_path = os.path.join(sys.prefix, "Lib", "site-packages", "llama_cpp", "lib")
if os.path.exists(llama_cpp_lib_path):
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(llama_cpp_lib_path)
    os.environ["PATH"] = llama_cpp_lib_path + os.pathsep + os.environ["PATH"]

import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import LlavaChatHandler

# 模型路径
model_path = r"C:\Users\wangj.KEVIN\projects\Qianfan-OCR-GGUF\Qianfan-OCR-q4_k_m.gguf"
mmproj_path = r"C:\Users\wangj.KEVIN\projects\Qianfan-OCR-GGUF\Qianfan-OCR-mmproj-f16.gguf"

# 使用 D0 自动模式的裁剪图进行测试
image_path = r"C:\Users\wangj.KEVIN\Downloads\更换镜头后-测试20260415\更换镜头后-测试20260415\F0\20260418\crops\20260418170647791_F0-I0_OK_crop_F0_184851.png"

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_ocr():
    if not os.path.exists(model_path) or not os.path.exists(mmproj_path):
        print(f"Error: Model ({os.path.exists(model_path)}) or mmproj ({os.path.exists(mmproj_path)}) file not found.")
        return

    print(f"Loading Qianfan-OCR model: {os.path.basename(model_path)}...")
    chat_handler = LlavaChatHandler(clip_model_path=mmproj_path)
    
    llm = Llama(
        model_path=model_path,
        chat_handler=chat_handler,
        n_gpu_layers=-1, 
        n_ctx=4096,
        verbose=False
    )

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print(f"Analyzing D0 Mixer (Auto Mode): {os.path.basename(image_path)}...")
    
    # 构造针对 D0 自动模式的 Prompt
    prompt = """这是实验室混料机屏幕。
1. 判断运行模式（左侧菜单）。
2. 提取段一、段二、段三的转速和时间。
3. 提取总共时长、剩余时长、当前段数、当前转速。

严格按以下JSON格式输出，使用中文键名：
{"模式": "自动", "段一转速": "10000", "段一时间": "20", "段二转速": "16000", "段二时间": "20", "段三转速": "22000", "段三时间": "20", "总共时长": "60", "剩余时长": "1", "当前段数": "1", "当前转速": "0"}
"""
    
    img_b64 = image_to_base64(image_path)
    
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "You are a professional industrial instrument reading assistant. Output JSON only."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ],
        temperature=0.0
    )

    print("\n--- OCR Result ---")
    print(response["choices"][0]["message"]["content"])
    print("------------------\n")

if __name__ == "__main__":
    test_ocr()
