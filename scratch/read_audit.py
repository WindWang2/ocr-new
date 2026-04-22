import os

file_path = r"c:\Users\wangj.KEVIN\projects\ocr-new\scratch\audit_results.txt"

if os.path.exists(file_path):
    # 尝试多种编码读取
    for encoding in ['utf-16', 'utf-16le', 'utf-8', 'gbk']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                if "Result for" in content:
                    print(f"--- Decoded with {encoding} ---")
                    for line in content.splitlines():
                        if "Result for" in line or "[OCR_DEBUG]" in line:
                            print(line)
                    break
        except:
            continue
else:
    print("File not found.")
