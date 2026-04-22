import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch

print(f"Python: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA NOT AVAILABLE")

yolo_model = r"C:\Users\wangj.KEVIN\projects\last.pt"
print(f"YOLO model exists: {os.path.exists(yolo_model)}")

glm_model = r"C:\Users\wangj.KEVIN\projects\GLM-OCR"
print(f"GLM model exists: {os.path.exists(glm_model)}")
