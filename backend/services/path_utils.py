import os
import platform
import re
from pathlib import Path

def normalize_path(path_str: str) -> Path:
    """
    智能路径转换：
    1. 在 Linux/WSL 环境下，将 C:\\... 转换为 /mnt/c/...
    2. 处理正反斜杠
    """
    if not path_str:
        return Path()

    # 统一处理反斜杠
    normalized = path_str.replace('\\', '/')
    
    # 如果在 Linux 下识别到 Windows 盘符开头 (如 C:/)
    if platform.system() == 'Linux':
        match = re.match(r'^([a-zA-Z]):/', normalized)
        if match:
            drive = match.group(1).lower()
            normalized = re.sub(r'^[a-zA-Z]:/', f'/mnt/{drive}/', normalized)
            
    return Path(normalized)
