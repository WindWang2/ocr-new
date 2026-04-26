import os
import subprocess

def check_cuda():
    print("--- Environment Check ---")
    print(f"PATH: {os.environ.get('PATH', '')[:200]}...")
    
    # 检查 nvcc
    try:
        res = subprocess.check_output(["nvcc", "--version"], stderr=subprocess.STDOUT)
        print(f"NVCC: {res.decode().splitlines()[-1]}")
    except:
        print("NVCC: Not found in PATH")

    # 检查常见的 CUDA DLL
    dlls = ["cudart64_12.dll", "cublas64_12.dll", "cublasLt64_12.dll"]
    print("\n--- DLL Check ---")
    for dll in dlls:
        found = False
        # 尝试使用 where 命令
        try:
            subprocess.check_output(["where", dll], stderr=subprocess.STDOUT)
            print(f"{dll}: Found (via WHERE)")
            found = True
        except:
            pass
            
        if not found:
            print(f"{dll}: NOT FOUND")

if __name__ == "__main__":
    check_cuda()
