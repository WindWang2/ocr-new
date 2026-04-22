import os
import torch
import json
import time
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

# Configuration
MODEL_PATH = r"C:\Users\wangj.KEVIN\projects\GLM-OCR"
TEST_IMAGE = r"C:\Users\wangj.KEVIN\projects\ocr-new\camera_images\F3\000_143804.jpg"
PROMPT_TEXT = "识别图片中的仪表盘数值。请提取出所有的数字并与对应的标签匹配。以 JSON 格式输出，如果无法确定数值，请设为 null。"

def test_glm_ocr():
    print(f"\n{'='*50}")
    print(f"GLM-OCR Standalone Test - Run 5")
    print(f"{'='*50}")
    
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        return

    test_img = TEST_IMAGE
    if not os.path.exists(test_img):
        print(f"Error: Test image not found at {test_img}")
        return

    print(f"1. Loading Model and Processor from: {MODEL_PATH}...")
    start_time = time.time()
    
    try:
        processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
        model = AutoModelForImageTextToText.from_pretrained(
            MODEL_PATH, 
            trust_remote_code=True, 
            torch_dtype=torch.float16,
            device_map="auto"
        )
        print(f"Model loaded in {time.time() - start_time:.2f} seconds.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print(f"\n2. Running Inference on: {test_img}...")
    try:
        image = Image.open(test_img).convert("RGB")
        
        # Use native chat template
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": PROMPT_TEXT}
                ]
            }
        ]
        
        prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        if "<think>" not in prompt:
            prompt += "<think></think>\n"
            
        inputs = processor(images=image, text=prompt, return_tensors="pt").to("cuda")
        
        # Ensure inputs are also float16 if necessary
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor) and v.dtype == torch.float:
                inputs[k] = v.to(torch.float16)

        start_inference = time.time()
        with torch.no_grad():
            output_ids = model.generate(
                **inputs, 
                max_new_tokens=512,
                do_sample=False,
                temperature=0.0
            )
        
        inference_time = time.time() - start_inference
        result = processor.decode(output_ids[0], skip_special_tokens=True)
        
        # Check VRAM first
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        
        print(f"Inference completed in {inference_time:.2f} seconds.")
        print(f"\n{'='*20} Vision OCR Result {'='*20}")
        print(result)
        print(f"{'='*59}")
        
        # Save to file
        output_file = r"c:\Users\wangj.KEVIN\projects\ocr-new\tests\test_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"image": test_img, "result": result, "vram_gb": allocated}, f, ensure_ascii=False, indent=2)
        print(f"Result saved to: {output_file}")
        
        print(f"\nVRAM Usage: Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")
        
    except Exception as e:
        print(f"Inference failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_glm_ocr()
