"""
相机TCP控制服务

功能：
1. 监听TCP端口，接收触发指令
2. 收到 "XXXX,N" 格式消息后，触发第N+1个相机拍照
3. 等待拍摄完成
4. 读取新拍摄的图片
5. 返回仪器读数结果

使用方式：
  python camera_service.py                    # 启动服务
  python camera_service.py --test             # 测试模式（不连接真实相机）
"""

import os
import sys
import json
import time
import socket
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import cv2
import numpy as np

from config import Config
from instrument_reader import InstrumentReader
from backend.models.database import get_config

logger = logging.getLogger(__name__)


class CameraController:
    """相机控制器 - 负责与相机通信并触发拍照"""

    def __init__(self, camera_id: int, config: dict):
        """
        Args:
            camera_id: 相机ID (0-8)
            config: 相机配置
        """
        self.camera_id = camera_id
        self.config = config
        self.control_host = config["control_host"]
        self.control_port = config["control_port"]
        self.image_dir = Path(config["image_dir"]) / f"F{camera_id}"
        self.capture_command = config["capture_command"]
        self.capture_timeout = config["capture_timeout"]
        self.file_wait_timeout = config["file_wait_timeout"]
        self.file_check_interval = config["file_check_interval"]

        # 确保图片目录存在
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def trigger_capture(self) -> Tuple[bool, str]:
        """
        触发相机拍照

        Returns:
            (success, message)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.capture_timeout)

            logger.info(f"[相机{self.camera_id}] 连接 {self.control_host}:{self.control_port}")
            sock.connect((self.control_host, self.control_port))

            # 发送拍照指令 VTFP,X\r\n
            command = f"{self.config['trigger_prefix']},{self.camera_id}\r\n"
            sock.sendall(command.encode('utf-8'))
            logger.info(f"[相机{self.camera_id}] 发送指令: {command.strip()}")

            # 等待响应
            response = sock.recv(1024).decode('utf-8').strip()
            sock.close()

            logger.info(f"[相机{self.camera_id}] 收到响应: {response}")

            # 成功响应为 VTFP,0
            if response == "VTFP,0":
                return True, response
            else:
                return False, f"相机返回错误: {response}"

        except socket.timeout:
            return False, f"连接相机超时 ({self.capture_timeout}秒)"
        except ConnectionRefusedError:
            return False, f"无法连接相机 (连接被拒绝)"
        except Exception as e:
            return False, f"相机通信异常: {str(e)}"

    def get_latest_image(self, before_time: float = None) -> Optional[Path]:
        """
        获取最新拍摄的图片

        目录结构: F{camera_id}/YYYYMMDD/YYYYMMDDHHMMSSMM_F{id}-I0_OK.bmp
        在今天的日期子目录中查找最新的 BMP 图片。

        Args:
            before_time: 拍照前的时间戳，用于筛选新文件

        Returns:
            图片路径或None
        """
        if not self.image_dir.exists():
            logger.warning(f"[相机{self.camera_id}] 图片目录不存在: {self.image_dir}")
            return None

        # 优先在今天的日期目录中查找
        today_dir = self.image_dir / datetime.now().strftime("%Y%m%d")
        search_dirs = []
        if today_dir.exists():
            search_dirs.append(today_dir)

        # 如果今天目录没有，则查找所有日期子目录
        if not search_dirs:
            date_dirs = sorted(
                [d for d in self.image_dir.iterdir() if d.is_dir()],
                key=lambda d: d.name, reverse=True
            )
            search_dirs = date_dirs[:1]  # 取最新的日期目录

        if not search_dirs:
            # 兜底：直接在 image_dir 下查找
            search_dirs = [self.image_dir]

        # 在目标目录中查找图片
        image_files = []
        for search_dir in search_dirs:
            for ext in Config.IMAGE_EXTENSIONS:
                image_files.extend(search_dir.glob(f"*{ext}"))
                image_files.extend(search_dir.glob(f"*{ext.upper()}"))

        if not image_files:
            return None

        # 按文件名排序（文件名包含时间戳），取最新的
        if before_time:
            new_files = [f for f in image_files if f.stat().st_mtime > before_time]
            if new_files:
                new_files.sort(key=lambda x: x.name, reverse=True)
                return new_files[0]

        image_files.sort(key=lambda x: x.name, reverse=True)
        return image_files[0]

    def wait_for_new_image(self, timeout: float = None, interval: float = None) -> Optional[Path]:
        """
        等待新图片出现

        Args:
            timeout: 超时时间
            interval: 检查间隔

        Returns:
            新图片路径或None
        """
        timeout = timeout or self.file_wait_timeout
        interval = interval or self.file_check_interval

        start_time = time.time()

        # 今天的日期目录
        today_dir = self.image_dir / datetime.now().strftime("%Y%m%d")

        def _scan_files():
            files = set()
            for search_dir in [today_dir, self.image_dir]:
                if search_dir.exists():
                    for ext in Config.IMAGE_EXTENSIONS:
                        files.update(search_dir.glob(f"*{ext}"))
                        files.update(search_dir.glob(f"*{ext.upper()}"))
            return files

        initial_files = _scan_files()

        while time.time() - start_time < timeout:
            current_files = _scan_files()
            new_files = current_files - initial_files
            if new_files:
                new_file = max(new_files, key=lambda x: x.name)
                logger.info(f"[相机{self.camera_id}] 检测到新图片: {new_file.name}")
                return new_file

            time.sleep(interval)

        logger.warning(f"[相机{self.camera_id}] 等待新图片超时 ({timeout}秒)")
        return None


def resize_image(image_path: str, max_size: int = 500) -> str:
    """
    缩放图像，保持长宽比，最长边不超过max_size像素

    Args:
        image_path: 图像路径
        max_size: 最长边最大像素数

    Returns:
        缩放后的图像路径（原地修改，返回原路径）
    """
    img = cv2.imread(image_path)
    if img is None:
        logger.warning(f"无法读取图像: {image_path}")
        return image_path

    h, w = img.shape[:2]
    max_dim = max(h, w)

    if max_dim <= max_size:
        logger.debug(f"图像尺寸 {w}x{h} 已满足要求，无需缩放")
        return image_path

    # 计算缩放比例
    scale = max_size / max_dim
    new_w = int(w * scale)
    new_h = int(h * scale)

    # 缩放图像
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 原地保存
    cv2.imwrite(image_path, resized)
    logger.info(f"图像已缩放: {w}x{h} -> {new_w}x{new_h}")

    return image_path


class CameraService:
    """相机TCP服务"""

    def __init__(self, test_mode: bool = False):
        """
        Args:
            test_mode: 测试模式，不连接真实相机
        """
        # 同步数据库配置到全局 Config
        db_image_dir = get_config("image_dir")
        if db_image_dir:
            Config.update_image_dir(db_image_dir)
            logger.info(f"已同步数据库图片目录到 Config: {db_image_dir}")

        self.config = Config.get_camera_config()
        self.test_mode = test_mode

        # 初始化相机控制器
        self.camera_controllers = {}
        for i in range(self.config["camera_count"]):
            self.camera_controllers[i] = CameraController(i, self.config)

        # 初始化仪器读取器
        self.reader = InstrumentReader()

        # 服务状态
        self.running = False
        self.server_socket = None

        logger.info(f"相机服务初始化完成，共 {self.config['camera_count']} 个相机")
        logger.info(f"监听端口: {self.config['service_port']}")
        if test_mode:
            logger.info("⚠️  测试模式: 不会连接真实相机")

    def parse_command(self, data: str) -> Optional[int]:
        """
        解析命令

        Args:
            data: 接收到的数据，格式为 "XXXX,N"

        Returns:
            相机ID (0-8) 或 None
        """
        data = data.strip()
        prefix = self.config["trigger_prefix"]

        if not data.startswith(prefix):
            return None

        try:
            # 解析相机编号
            parts = data.split(",")
            if len(parts) != 2:
                return None

            camera_num = int(parts[1].strip())

            # 验证范围
            if 0 <= camera_num < self.config["camera_count"]:
                return camera_num
            else:
                logger.warning(f"相机编号超出范围: {camera_num}")
                return None

        except (ValueError, IndexError):
            return None

    def process_camera(self, camera_id: int) -> Dict[str, Any]:
        """
        处理单个相机的拍照和读取流程

        Args:
            camera_id: 相机ID (0-8)

        Returns:
            处理结果
        """
        result = {
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }

        controller = self.camera_controllers[camera_id]

        try:
            # 记录开始时间
            start_time = time.time()

            if self.test_mode:
                # 测试模式：直接读取最新图片
                logger.info(f"[相机{camera_id}] 测试模式: 跳过拍照，直接读取图片")
                time.sleep(0.5)  # 模拟拍照延迟
            else:
                # 触发拍照
                capture_start = time.time()
                success, message = controller.trigger_capture()

                if not success:
                    result["error"] = f"拍照失败: {message}"
                    return result

                logger.info(f"[相机{camera_id}] 拍照完成: {message}")

                # 等待新图片
                if self.config["wait_for_file"]:
                    new_image = controller.wait_for_new_image()
                    if new_image is None:
                        result["error"] = "等待新图片超时"
                        return result
                else:
                    # 固定等待
                    time.sleep(1.0)

            # 获取最新图片
            image_path = controller.get_latest_image(start_time)

            if image_path is None:
                result["error"] = f"未找到图片文件: {controller.image_dir}"
                return result

            result["image_path"] = str(image_path)
            logger.info(f"[相机{camera_id}] 读取图片: {image_path.name}")

            # 缩放图像 (注意：此处已禁用，改为在裁剪特写时缩放，以保留原图清晰度)
            # if Config.IMAGE_RESIZE_ENABLED:
            #     resize_image(str(image_path), Config.IMAGE_MAX_SIZE)

            # 读取仪器
            reading_result = self.reader.read_instrument(str(image_path))

            if reading_result.get("success"):
                result["success"] = True
                result["instrument_type"] = reading_result.get("instrument_type")
                result["instrument_name"] = reading_result.get("instrument_name")
                result["readings"] = reading_result.get("readings", {})
                result["confidence"] = reading_result.get("confidence", 0)
                result["method"] = reading_result.get("method")

                # 计算耗时
                result["elapsed_time"] = round(time.time() - start_time, 2)

                logger.info(f"[相机{camera_id}] 识别成功: {result['instrument_name']}")
                for attr, value in result["readings"].items():
                    if value is not None:
                        logger.info(f"  {attr}: {value}")
            else:
                result["error"] = reading_result.get("error", "识别失败")

        except Exception as e:
            result["error"] = f"处理异常: {str(e)}"
            logger.exception(f"[相机{camera_id}] 处理异常")

        return result

    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """处理客户端连接"""
        logger.info(f"客户端连接: {client_address}")

        try:
            # 接收数据
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return

            logger.info(f"收到命令: {data.strip()}")

            # 解析命令
            camera_id = self.parse_command(data)

            if camera_id is None:
                response = json.dumps({
                    "success": False,
                    "error": f"无效命令格式，期望: {self.config['trigger_prefix']},N"
                }, ensure_ascii=False)
            else:
                # 处理相机
                result = self.process_camera(camera_id)
                response = json.dumps(result, ensure_ascii=False)

            # 发送响应
            client_socket.sendall(response.encode('utf-8'))
            logger.info(f"已发送响应给 {client_address}")

        except Exception as e:
            logger.exception(f"处理客户端异常")
            try:
                error_response = json.dumps({
                    "success": False,
                    "error": str(e)
                }, ensure_ascii=False)
                client_socket.sendall(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()

    def start(self):
        """启动服务"""
        self.running = True

        # 创建服务器socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.config["service_host"], self.config["service_port"]))
            self.server_socket.listen(5)

            logger.info(f"✅ 相机服务已启动")
            logger.info(f"   监听: {self.config['service_host']}:{self.config['service_port']}")
            logger.info(f"   相机数量: {self.config['camera_count']}")
            logger.info(f"   触发格式: {self.config['trigger_prefix']},N (N=0~{self.config['camera_count']-1})")
            print()

            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()

                    # 在新线程中处理客户端
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    thread.daemon = True
                    thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.exception("接受连接异常")

        except Exception as e:
            logger.exception("服务启动失败")
        finally:
            self.stop()

    def stop(self):
        """停止服务"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("相机服务已停止")


def main():
    """主函数"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(description="相机TCP控制服务")
    parser.add_argument("--test", action="store_true", help="测试模式（不连接真实相机）")
    parser.add_argument("--port", type=int, help="服务端口（覆盖配置）")
    args = parser.parse_args()

    # 覆盖端口
    if args.port:
        Config.CAMERA_SERVICE_PORT = args.port

    # 创建并启动服务
    service = CameraService(test_mode=args.test)

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止服务...")
        service.stop()


if __name__ == "__main__":
    main()
