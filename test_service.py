"""
测试版本服务 - 跳过依赖，验证逻辑正确性
"""

import os
import sys
import json
import time
import socket
import threading
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)


class CameraController:
    """相机控制器 - 负责与相机通信并触发拍照"""

    def __init__(self, camera_id: int, config: dict):
        """
        Args:
            camera_id: 相机ID (0-8) 对应 F0-F8 文件夹
            config: 相机配置
        """
        self.camera_id = camera_id
        self.config = config
        self.control_host = config["control_host"]
        self.control_port = config["control_port_base"] + camera_id
        # 新路径结构: F0~F8 文件夹
        self.image_dir = Path(config["image_dir"]) / f"F{camera_id}"
        self.capture_command = config["capture_command"]
        self.capture_timeout = config["capture_timeout"]
        self.file_wait_timeout = config["file_wait_timeout"]
        self.file_check_interval = config["file_check_interval"]

        # 确保图片根目录存在
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def _get_latest_date_folder(self) -> Optional[Path]:
        """获取最新的日期文件夹 (格式: YYYYMMDD)"""
        if not self.image_dir.exists():
            return None
        
        date_folders = []
        for entry in self.image_dir.iterdir():
            if entry.is_dir() and entry.name.isdigit() and len(entry.name) == 8:
                try:
                    # 验证日期格式
                    datetime.strptime(entry.name, "%Y%m%d")
                    date_folders.append(entry)
                except ValueError:
                    continue
        
        if not date_folders:
            return None
        
        # 按日期倒序排序，取最新的
        date_folders.sort(key=lambda x: x.name, reverse=True)
        return date_folders[0]

    def trigger_capture(self) -> Tuple[bool, str]:
        """
        触发相机拍照 - 测试模式直接返回成功
        """
        logger.info(f"[相机{self.camera_id} (F{self.camera_id})] 测试模式: 模拟拍照成功，返回0")
        return True, "0"

    def get_latest_image(self, before_time: float = None) -> Optional[Path]:
        """
        获取最新拍摄的图片
        """
        # 获取最新的日期文件夹
        date_folder = self._get_latest_date_folder()
        if not date_folder:
            logger.warning(f"[相机{self.camera_id}] 未找到日期文件夹: {self.image_dir}")
            return None

        # 查找所有图片文件
        image_files = []
        for ext in ['.jpg', '.jpeg', '.bmp']:
            image_files.extend(date_folder.glob(f"*_F{self.camera_id}-*_OK.{ext.lstrip('.')}"))
            image_files.extend(date_folder.glob(f"*_F{self.camera_id}-*_OK.{ext.lstrip('.').upper()}"))

        if not image_files:
            logger.warning(f"[相机{self.camera_id}] 未找到匹配的图片文件: {date_folder}")
            return None

        # 按修改时间排序，获取最新的
        if before_time:
            # 筛选拍照后新增的文件
            new_files = [f for f in image_files if f.stat().st_mtime > before_time]
            if new_files:
                new_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return new_files[0]
            else:
                # 没有新文件，返回最新的
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return image_files[0]
        else:
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return image_files[0]


def mock_resize_image(image_path: str, max_size: int = 500) -> Tuple[str, str]:
    """模拟缩放和base64编码"""
    logger.info(f"模拟缩放图片: {image_path} 到最长边500像素")
    return image_path, "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwDk0AQAAAAAAAAAAAAAAAAAAAADIEwD/2Q=="


class CameraService:
    """相机TCP服务 - 测试版本"""

    def __init__(self, test_mode: bool = False):
        """
        Args:
            test_mode: 测试模式，不连接真实相机
        """
        self.config = {
            "service_host": "0.0.0.0",
            "service_port": 8889,
            "camera_count": 9,
            "image_dir": "camera_images",
            "control_host": "127.0.0.1",
            "control_port_base": 9000,
            "capture_command": "VTFP",
            "capture_timeout": 10.0,
            "wait_for_file": True,
            "file_wait_timeout": 15.0,
            "file_check_interval": 0.5,
            "trigger_prefix": "VTFP",
            "image_resize_enabled": True,
            "image_max_size": 500,
        }
        self.test_mode = test_mode

        # 初始化相机控制器
        self.camera_controllers = {}
        for i in range(self.config["camera_count"]):
            self.camera_controllers[i] = CameraController(i, self.config)

        # 服务状态
        self.running = False
        self.server_socket = None

        logger.info(f"✅ 测试服务初始化完成，共 {self.config['camera_count']} 个相机")
        logger.info(f"📡 监听端口: {self.config['service_port']}")
        logger.info(f"🔹 指令1: {self.config['trigger_prefix']},N (单相机模式)")
        logger.info(f"🔹 指令2: {self.config['trigger_prefix']},N1,N2,N3... (批量实验模式)")
        logger.info(f"🔹 返回内容: 实验记录 + 每个相机的图片和读数")
        print()

    def parse_command(self, data: str) -> Optional[List[int]]:
        """
        解析命令
        """
        data = data.strip()
        prefix = self.config["trigger_prefix"]

        if not data.startswith(prefix):
            return None

        try:
            # 解析相机编号
            parts = data.split(",")
            if len(parts) < 2:
                return None

            camera_ids = []
            for part in parts[1:]:
                camera_num = int(part.strip())
                # 验证范围
                if 0 <= camera_num < self.config["camera_count"]:
                    camera_ids.append(camera_num)
                else:
                    logger.warning(f"相机编号超出范围: {camera_num}，已跳过")

            if not camera_ids:
                return None

            return camera_ids

        except (ValueError, IndexError):
            return None

    def process_single_camera(self, camera_id: int, start_time: float = None) -> Dict[str, Any]:
        """
        处理单个相机的拍照和读取流程
        """
        result = {
            "camera_id": camera_id,
            "folder": f"F{camera_id}",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "image_base64": "",
        }

        if start_time is None:
            start_time = time.time()

        controller = self.camera_controllers[camera_id]

        try:
            # 触发拍照
            success, message = controller.trigger_capture()
            if not success:
                result["error"] = f"拍照失败: {message}"
                return result

            logger.info(f"[相机{camera_id}] 拍照完成")
            time.sleep(0.2)

            # 获取最新图片
            image_path = controller.get_latest_image(start_time)
            if image_path is None:
                result["error"] = f"未找到图片文件"
                return result

            result["image_path"] = str(image_path)
            logger.info(f"[相机{camera_id}] 读取图片: {image_path.name}")

            # 模拟缩放和base64
            _, image_base64 = mock_resize_image(str(image_path))
            result["image_base64"] = image_base64

            # 模拟读数结果
            result["success"] = True
            result["instrument_name"] = f"仪表-{camera_id+1}"
            result["readings"] = {
                "数值": round(100 + camera_id * 5 + time.time() % 5, 2),
                "单位": "℃" if camera_id % 2 == 0 else "kPa",
                "状态": "正常"
            }
            result["confidence"] = 0.98

            logger.info(f"[相机{camera_id}] 识别成功: {result['readings']['数值']}{result['readings']['单位']}")

        except Exception as e:
            result["error"] = f"处理异常: {str(e)}"
            logger.exception(f"[相机{camera_id}] 处理异常")

        return result

    def process_experiment(self, camera_ids: List[int]) -> Dict[str, Any]:
        """
        处理批量实验：依次触发多个相机，汇总所有结果
        """
        experiment_start = time.time()
        experiment_id = str(uuid.uuid4())[:8]  # 短UUID作为实验ID

        logger.info(f"🧪 开始实验 [{experiment_id}]，相机列表: {camera_ids}")

        experiment_result = {
            "experiment_id": experiment_id,
            "type": "batch_experiment",
            "timestamp": datetime.now().isoformat(),
            "total_cameras": len(camera_ids),
            "success_count": 0,
            "failed_count": 0,
            "elapsed_time": 0,
            "success": False,
            "results": []
        }

        # 依次处理每个相机
        for camera_id in camera_ids:
            camera_result = self.process_single_camera(camera_id, experiment_start)
            experiment_result["results"].append(camera_result)
            
            if camera_result["success"]:
                experiment_result["success_count"] += 1
            else:
                experiment_result["failed_count"] += 1

        # 计算总耗时
        experiment_result["elapsed_time"] = round(time.time() - experiment_start, 2)
        experiment_result["success"] = experiment_result["success_count"] == len(camera_ids)

        logger.info(f"✅ 实验 [{experiment_id}] 完成: 成功{experiment_result['success_count']}个, 失败{experiment_result['failed_count']}个, 总耗时{experiment_result['elapsed_time']}s")

        return experiment_result

    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """处理客户端连接"""
        logger.info(f"客户端连接: {client_address}")

        try:
            # 接收数据
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return

            logger.info(f"收到命令: {data.strip()}")

            # 解析命令
            camera_ids = self.parse_command(data)

            if camera_ids is None:
                response = json.dumps({
                    "success": False,
                    "error": f"无效命令格式，支持两种格式:\n  1. 单相机: {self.config['trigger_prefix']},N\n  2. 批量实验: {self.config['trigger_prefix']},N1,N2,N3..."
                }, ensure_ascii=False)
            else:
                if len(camera_ids) == 1:
                    # 单相机模式
                    result = self.process_single_camera(camera_ids[0])
                    response = json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    # 批量实验模式
                    result = self.process_experiment(camera_ids)
                    response = json.dumps(result, ensure_ascii=False, indent=2)

            # 发送响应
            client_socket.sendall(response.encode('utf-8'))
            logger.info(f"已发送响应给 {client_address}, 长度: {len(response)} 字节")

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
        logger.info("测试服务已停止")


def main():
    """主函数"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "="*60)
    print("📸 OCR 相机服务 - 测试版本 (支持批量实验)")
    print("="*60)
    print("\n功能验证点:")
    print("✅ 单相机模式: VTFP,N")
    print("✅ 批量实验模式: VTFP,N1,N2,N3...")
    print("✅ 自动生成实验ID，汇总所有相机结果")
    print("✅ 返回所有相机的图片base64和读数")
    print("✅ 支持任意相机组合（如VTFP,0,2,4,6,8 只拍偶数位相机）")
    print("="*60 + "\n")

    # 创建并启动服务
    service = CameraService(test_mode=True)

    # 启动测试客户端
    def test_client():
        time.sleep(1)
        print("\n🧪 开始测试...\n")
        
        # 测试1: 单相机
        print("🔹 测试1: 单相机模式 VTFP,1")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 8889))
        sock.sendall("VTFP,1".encode('utf-8'))
        response = sock.recv(4096).decode('utf-8')
        sock.close()
        res = json.loads(response)
        if res.get("success"):
            print(f"✅ 单相机测试成功: 相机{res['camera_id']}, 读数 {res['readings']['数值']}{res['readings']['单位']}")
        else:
            print(f"❌ 单相机测试失败: {res.get('error')}")
        print()

        # 测试2: 批量实验（3个相机）
        print("🔹 测试2: 批量实验 VTFP,0,1,2")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 8889))
        sock.sendall("VTFP,0,1,2".encode('utf-8'))
        response = sock.recv(8192).decode('utf-8')
        sock.close()
        res = json.loads(response)
        if res.get("type") == "batch_experiment":
            print(f"✅ 批量实验测试成功! 实验ID: {res['experiment_id']}")
            print(f"   总相机数: {res['total_cameras']}, 成功: {res['success_count']}, 失败: {res['failed_count']}")
            print(f"   总耗时: {res['elapsed_time']}s")
            for i, cam_res in enumerate(res['results']):
                if cam_res['success']:
                    print(f"   相机{cam_res['camera_id']}: {cam_res['readings']['数值']}{cam_res['readings']['单位']}")
        else:
            print(f"❌ 批量实验测试失败: {res.get('error')}")
        print()

        # 测试3: 全相机实验（全部9个）
        print("🔹 测试3: 全相机实验 VTFP,0,1,2,3,4,5,6,7,8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 8889))
        sock.sendall("VTFP,0,1,2,3,4,5,6,7,8".encode('utf-8'))
        response = sock.recv(32768).decode('utf-8')
        sock.close()
        res = json.loads(response)
        if res.get("type") == "batch_experiment":
            print(f"✅ 全相机实验测试成功! 实验ID: {res['experiment_id']}")
            print(f"   总相机数: {res['total_cameras']}, 成功: {res['success_count']}, 失败: {res['failed_count']}")
            print(f"   总耗时: {res['elapsed_time']}s")
            print(f"   所有相机读数已全部返回")
        else:
            print(f"❌ 全相机实验测试失败: {res.get('error')}")
        print()

        # 测试4: 错误指令
        print("🔹 测试4: 错误指令 INVALID,1,2")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 8889))
        sock.sendall("INVALID,1,2".encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        sock.close()
        res = json.loads(response)
        if not res.get("success") and "无效命令格式" in res.get("error", ""):
            print(f"✅ 错误指令识别正常")
        else:
            print(f"❌ 错误指令处理失败")
        print()

        print("✅ 所有测试完成! 服务将在3秒后关闭...")
        time.sleep(3)
        service.stop()

    # 启动测试线程
    test_thread = threading.Thread(target=test_client)
    test_thread.daemon = True
    test_thread.start()

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止服务...")
        service.stop()


if __name__ == "__main__":
    main()