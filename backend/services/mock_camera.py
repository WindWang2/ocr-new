"""
模拟相机客户端 - 用于测试，跳过 TCP 连接，读取本地图片并走真实 OCR 流程
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class MockCameraClient:
    """
    模拟相机客户端，接口与 CameraClient 完全相同。

    读取 camera_images/camera_{id}/ 目录下修改时间最新的图片，
    调用 InstrumentReader 做 OCR，返回第一个可解析为 float 的读数。
    """

    def __init__(self, camera_id: int):
        self.camera_id = camera_id
        self.image_dir = PROJECT_ROOT / "camera_images" / f"F{camera_id}"

    def _find_latest_image(self) -> Path | None:
        """返回图片目录中修改时间最新的图片，找不到返回 None"""
        if not self.image_dir.exists():
            return None
        extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        images = [p for p in self.image_dir.iterdir() if p.suffix.lower() in extensions]
        if not images:
            return None
        return max(images, key=lambda p: p.stat().st_mtime)

    def trigger_and_read(self) -> Tuple[bool, dict]:
        """
        模拟拍照：读取本地图片 → OCR → 返回读数

        Returns:
            (success, result_dict)  与 CameraClient.trigger_and_read() 结构相同
        """
        image_path = self._find_latest_image()
        if image_path is None:
            msg = f"[Mock 相机{self.camera_id}] 目录 {self.image_dir} 中未找到图片"
            logger.error(msg)
            return False, {"camera_id": self.camera_id, "error": msg, "success": False}

        logger.info(f"[Mock 相机{self.camera_id}] 使用图片: {image_path}")

        try:
            # 延迟导入避免循环依赖
            import sys
            sys.path.insert(0, str(PROJECT_ROOT))
            from instrument_reader import InstrumentReader
            from backend.services.llm_provider import get_global_provider

            reader = InstrumentReader(provider=get_global_provider())
            result = reader.read_instrument(str(image_path))
        except Exception as e:
            logger.error(f"[Mock 相机{self.camera_id}] OCR 失败: {e}")
            return False, {"camera_id": self.camera_id, "error": str(e), "success": False}

        if not result.get("success"):
            err = result.get("error", "OCR 识别失败")
            return False, {"camera_id": self.camera_id, "error": err, "success": False}

        # 取第一个非 None 的 readings 值
        readings = result.get("readings", {})
        reading_value = None
        for v in readings.values():
            if v is not None:
                try:
                    reading_value = float(v)
                    break
                except (TypeError, ValueError):
                    continue

        if reading_value is None:
            msg = f"[Mock 相机{self.camera_id}] OCR 未返回有效数值，readings={readings}"
            logger.error(msg)
            return False, {"camera_id": self.camera_id, "error": msg, "success": False}

        logger.info(f"[Mock 相机{self.camera_id}] OCR 读数: {reading_value}")
        return True, {
            "camera_id": self.camera_id,
            "raw_response": str(readings),
            "reading": reading_value,
            "image_path": str(image_path),
            "confidence": result.get("confidence"),
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "mock": True,
        }
