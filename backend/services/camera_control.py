"""
相机控制服务 - 触发拍照并读取仪器读数
"""

import socket
import json
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from backend.models.database import get_camera_by_id, get_cameras

logger = logging.getLogger(__name__)

# 导入配置（从项目根目录）
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Config


class CameraClient:
    """相机客户端 - 触发相机拍照并读取结果"""
    
    def __init__(self, camera_id: int, config: dict = None):
        self.camera_id = camera_id
        self.config = config or self._default_config()
        self.control_host = self.config["control_host"]
        self.control_port = self.config["control_port_base"] + camera_id
        self.capture_timeout = self.config.get("capture_timeout", 10.0)
        self.trigger_prefix = self.config.get("trigger_prefix", "XXXX")
        
        # 图片目录
        self.image_dir = Path(self.config.get("image_dir", "camera_images")) / f"camera_{camera_id}"
    
    def _default_config(self):
        """默认配置"""
        return Config.get_camera_config()
    
    def trigger_and_read(self) -> Tuple[bool, dict]:
        """
        触发相机拍照并读取仪器读数
        
        Returns:
            (success, result_dict)
        """
        try:
            # 1. 连接相机控制端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.capture_timeout)
            
            logger.info(f"[相机{self.camera_id}] 连接 {self.control_host}:{self.control_port}")
            sock.connect((self.control_host, self.control_port))
            
            # 2. 发送拍照指令
            command = f"{self.trigger_prefix},{self.camera_id}"
            sock.sendall(command.encode('utf-8'))
            logger.info(f"[相机{self.camera_id}] 发送指令: {command}")
            
            # 3. 等待响应
            response = sock.recv(4096).decode('utf-8').strip()
            sock.close()
            
            logger.info(f"[相机{self.camera_id}] 响应: {response}")
            
            # 4. 解析响应（JSON或纯文本）
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {"raw": response, "reading": response}
            
            # 5. 返回成功结果
            return True, {
                "camera_id": self.camera_id,
                "raw_response": response,
                "reading": result.get("reading") or result.get("value") or result.get("raw"),
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except socket.timeout:
            logger.error(f"[相机{self.camera_id}] 连接超时")
            return False, {"camera_id": self.camera_id, "error": "timeout", "success": False}
        except ConnectionRefusedError:
            logger.error(f"[相机{self.camera_id}] 连接被拒绝")
            return False, {"camera_id": self.camera_id, "error": "connection_refused", "success": False}
        except Exception as e:
            logger.error(f"[相机{self.camera_id}] 异常: {str(e)}")
            return False, {"camera_id": self.camera_id, "error": str(e), "success": False}
    
    def get_reading_only(self) -> Tuple[bool, dict]:
        """仅读取当前读数（不触发拍照）"""
        return self.trigger_and_read()


class MultiCameraController:
    """多相机控制器 - 依次控制多台相机"""
    
    def __init__(self, camera_ids: List[int], config: dict = None):
        """
        Args:
            camera_ids: 要控制的相机ID列表
            config: 相机配置
        """
        self.camera_ids = camera_ids
        self.config = config or Config.get_camera_config()
        self.clients = {cid: CameraClient(cid, self.config) for cid in camera_ids}
    
    def run_experiment(self) -> dict:
        """
        执行多相机实验 - 依次触发所有相机拍照并汇总读数
        
        Returns:
            汇总结果字典
        """
        results = []
        raw_readings = {}
        
        logger.info(f"开始多相机实验，相机: {self.camera_ids}")
        
        for camera_id in self.camera_ids:
            logger.info(f"处理相机 {camera_id}...")
            client = self.clients[camera_id]
            success, result = client.trigger_and_read()
            
            raw_readings[camera_id] = result
            
            if success:
                results.append({
                    "camera_id": camera_id,
                    "reading": result.get("reading"),
                    "timestamp": result.get("timestamp"),
                    "success": True
                })
            else:
                results.append({
                    "camera_id": camera_id,
                    "error": result.get("error"),
                    "success": False
                })
        
        # 汇总读数
        success_readings = [r for r in results if r.get("success")]
        
        if not success_readings:
            summary = {"error": "所有相机拍照失败", "total": len(self.camera_ids)}
        elif len(success_readings) == 1:
            # 单相机兼容
            summary = success_readings[0]["reading"]
        else:
            # 多相机：汇总所有读数
            summary = {
                "total_cameras": len(self.camera_ids),
                "successful": len(success_readings),
                "failed": len(self.camera_ids) - len(success_readings),
                "readings": {r["camera_id"]: r["reading"] for r in success_readings},
                "all_readings": [r["reading"] for r in success_readings]
            }
        
        return {
            "experiment_id": None,  # 后续绑定
            "camera_ids": self.camera_ids,
            "results": results,
            "raw_readings": raw_readings,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def read_all_cameras(self) -> List[dict]:
        """读取所有相机当前读数（不触发拍照）"""
        results = []
        for camera_id in self.camera_ids:
            client = self.clients[camera_id]
            success, result = client.get_reading_only()
            results.append(result)
        return results


def get_all_enabled_cameras() -> List[int]:
    """获取所有已启用的相机ID列表"""
    cameras = get_cameras(enabled_only=True)
    return [c["camera_id"] for c in cameras]


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试单相机
    client = CameraClient(0)
    success, result = client.trigger_and_read()
    print("单相机测试:", result)
    
    # 测试多相机
    controller = MultiCameraController([0, 1, 2])
    exp_result = controller.run_experiment()
    print("多相机实验结果:", json.dumps(exp_result, ensure_ascii=False, indent=2))
