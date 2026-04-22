import subprocess
import os
import time
import socket
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class LlamaLauncher:
    """管理 llama-server 进程的启动与监控"""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        host: str = "127.0.0.1",
        port: int = 8080,
    ):
        self.root = base_dir or Path(__file__).parent.parent.parent
        self.host = host
        self.port = port
        self.process: Optional[subprocess.Popen] = None

        # 默认路径探测
        self.bin_path = self.root.parent / "llama-cpp" / "llama-server.exe"
        self.model_path = self.root.parent / "2B-new" / "Qwen3.5-2B.Q4_K_M.gguf"
        self.mmproj_path = self.root.parent / "2B-new" / "mmproj-BF16.gguf"

    def is_running(self) -> bool:
        """检查端口是否已被占用（ server 是否在线）"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((self.host, self.port)) == 0

    def start(self, wait_for_ready: bool = True) -> bool:
        """启动 llama-server 进程"""
        if self.is_running():
            logger.info("Llama server 已经在运行中")
            return True

        if not self.bin_path.exists():
            logger.error(f"未找到 llama-server 可执行文件: {self.bin_path}")
            return False

        if not self.model_path.exists():
            logger.error(f"未找到模型文件: {self.model_path}")
            return False

        cmd = [
            str(self.bin_path),
            "-m", str(self.model_path),
            "--mmproj", str(self.mmproj_path),
            "-ngl", "-1",
            "--host", self.host,
            "--port", str(self.port),
            "-c", "8192"
        ]

        logger.info(f"正在启动 Llama Server: {' '.join(cmd)}")
        
        # 使用 CREATE_NEW_CONSOLE 在 Windows 上开启新窗口，或者直接静默运行
        # 这里选择静默运行并重定向输出到日志，或者通过 subprocess.DEVNULL
        try:
            log_out = open(self.root / "llama_stdout.log", "a")
            log_err = open(self.root / "llama_error.log", "a")
            self.process = subprocess.Popen(
                cmd,
                stdout=log_out,
                stderr=log_err,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except Exception as e:
            logger.error(f"启动 Llama Server 进程失败: {e}")
            return False

        if wait_for_ready:
            logger.info("等待 Llama Server 就绪...")
            for _ in range(30): # 最多等待 30 秒
                if self.is_running():
                    logger.info("Llama Server 已成功启动并就绪")
                    return True
                time.sleep(1)
            logger.warning("Llama Server 启动超时，请检查 GPU 内存或驱动")
            return False

        return True

    def stop(self):
        """停止进程"""
        if self.process:
            self.process.terminate()
            self.process = None
            logger.info("Llama Server 进程已发送终止信号")

# 单例实例
llama_launcher = LlamaLauncher()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    launcher = LlamaLauncher()
    if launcher.start():
        print("启动成功")
        # Keep alive for testing if run manually
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop()
    else:
        print("启动失败")
