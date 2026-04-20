"""
配置文件
支持通过环境变量覆盖默认值

后端架构: LMStudio 服务部署（OpenAI 兼容 API）
  多模态读取: 4b (http://127.0.0.1:1234)
"""

import os


def _env(key: str, default, cast=None):
    """从环境变量读取值，支持类型转换"""
    value = os.environ.get(key)
    if value is None:
        return default
    if cast is not None:
        return cast(value)
    return value


class Config:
    """系统配置（支持环境变量覆盖）"""

    # LMStudio 配置（OpenAI 兼容 API）
    LMSTUDIO_BASE_URL = _env("LMSTUDIO_BASE_URL", "http://192.168.31.127:1234")
    LMSTUDIO_MODEL = _env("LMSTUDIO_MODEL", "2b-new")
    LMSTUDIO_OCR_MODEL = _env("LMSTUDIO_OCR_MODEL", "ocr")
    DEFAULT_LLM_PROVIDER = _env("DEFAULT_LLM_PROVIDER", "openai_compatible")

    # 模型推理参数
    MODEL_TEMPERATURE = _env("MODEL_TEMPERATURE", 0.1, float)
    MODEL_MAX_TOKENS = _env("MODEL_MAX_TOKENS", 4000, int)

    # 图片格式
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.JPG', '.JPEG', '.PNG', '.BMP']

    # ==================== 相机服务配置 ====================

    # TCP服务配置
    CAMERA_SERVICE_HOST = _env("CAMERA_SERVICE_HOST", "0.0.0.0")
    CAMERA_SERVICE_PORT = _env("CAMERA_SERVICE_PORT", 8888, int)

    # 相机控制配置
    CAMERA_COUNT = _env("CAMERA_COUNT", 9, int)  # 相机数量
    CAMERA_IMAGE_DIR = _env("CAMERA_IMAGE_DIR", "camera_images")  # 相机图片根目录

    # 相机TCP控制（向相机发送拍照指令）
    CAMERA_CONTROL_HOST = _env("CAMERA_CONTROL_HOST", "127.0.0.1")
    CAMERA_CONTROL_PORT = _env("CAMERA_CONTROL_PORT", 10401, int)  # 所有相机共用同一端口
    CAMERA_CAPTURE_COMMAND = _env("CAMERA_CAPTURE_COMMAND", "VTFP")  # 拍照指令
    CAMERA_CAPTURE_TIMEOUT = _env("CAMERA_CAPTURE_TIMEOUT", 10.0, float)  # 拍照超时

    # 拍照完成等待配置
    CAMERA_WAIT_FOR_FILE = _env("CAMERA_WAIT_FOR_FILE", True, lambda x: x.lower() == 'true')
    CAMERA_FILE_WAIT_TIMEOUT = _env("CAMERA_FILE_WAIT_TIMEOUT", 15.0, float)
    CAMERA_FILE_CHECK_INTERVAL = _env("CAMERA_FILE_CHECK_INTERVAL", 0.5, float)

    # 图像缩放配置
    IMAGE_RESIZE_ENABLED = _env("IMAGE_RESIZE_ENABLED", True, lambda x: x.lower() == 'true')
    IMAGE_MAX_SIZE = _env("IMAGE_MAX_SIZE", 500, int)  # 最长边像素数

    # 触发指令格式
    TRIGGER_COMMAND_PREFIX = _env("TRIGGER_COMMAND_PREFIX", "VTFP")

    @classmethod
    def get_camera_config(cls):
        """获取相机服务配置"""
        return {
            "service_host": cls.CAMERA_SERVICE_HOST,
            "service_port": cls.CAMERA_SERVICE_PORT,
            "camera_count": cls.CAMERA_COUNT,
            "image_dir": cls.CAMERA_IMAGE_DIR,
            "control_host": cls.CAMERA_CONTROL_HOST,
            "control_port": cls.CAMERA_CONTROL_PORT,
            "capture_command": cls.CAMERA_CAPTURE_COMMAND,
            "capture_timeout": cls.CAMERA_CAPTURE_TIMEOUT,
            "wait_for_file": cls.CAMERA_WAIT_FOR_FILE,
            "file_wait_timeout": cls.CAMERA_FILE_WAIT_TIMEOUT,
            "file_check_interval": cls.CAMERA_FILE_CHECK_INTERVAL,
            "trigger_prefix": cls.TRIGGER_COMMAND_PREFIX,
            "image_resize_enabled": cls.IMAGE_RESIZE_ENABLED,
            "image_max_size": cls.IMAGE_MAX_SIZE,
        }
