"""
OCR 实验 API 服务

功能：
1. 相机管理（增删改查）
2. 实验执行（触发单字段相机拍照并保存读数）
3. 实验记录查询

启动: uvicorn main:app --reload --port 8001
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import json
import io
import os
import openpyxl
import asyncio
import time
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.database import (
    init_db, add_camera, get_cameras, get_camera_by_id,
    create_experiment,
    get_experiment, list_experiments, delete_experiment,
    create_reading, upsert_reading, get_readings_by_experiment, get_connection,
    get_config, set_config,
    get_all_templates, get_template, upsert_template,
)
from backend.services.camera_control import (
    CameraClient, get_all_enabled_cameras
)
from backend.services.mock_camera import MockCameraClient
from backend.services.task_manager import task_manager, TaskState
from config import Config

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()

# FastAPI 应用
app = FastAPI(
    title="OCR 实验服务 API",
    description="多相机仪表读数识别实验管理",
    version="1.0.0"
)

# CORS 中间件
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8001,http://127.0.0.1:8001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件：挂载图片目录，供前端访问拍照图片
_images_dir = Path("camera_images")
_images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")

async def image_cleanup_task():
    """定期清理过期的图片文件，防止磁盘占满"""
    retention_days = float(os.getenv("IMAGE_RETENTION_DAYS", "7"))
    while True:
        try:
            now = time.time()
            for root, dirs, files in os.walk(str(_images_dir)):
                for file in files:
                    file_path = os.path.join(root, file)
                    if now - os.path.getmtime(file_path) > retention_days * 86400:
                        os.remove(file_path)
                        logger.info(f"Cleaned up old image: {file_path}")
        except Exception as e:
            logger.error(f"图片清理任务出错: {e}")
        await asyncio.sleep(86400)  # 每天运行一次

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(image_cleanup_task())
    asyncio.create_task(_task_cleanup_loop())


async def _task_cleanup_loop():
    """定期清理过期的异步任务记录"""
    while True:
        try:
            task_manager.cleanup()
        except Exception as e:
            logger.error(f"任务清理出错: {e}")
        await asyncio.sleep(300)  # 每5分钟清理一次


# ==================== 异步任务查询 API ====================

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """查询异步任务状态和结果"""
    info = task_manager.get_status(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="任务不存在")
    resp = {
        "task_id": info.task_id,
        "status": info.status.value,
        "progress": info.progress,
        "message": info.message,
        "created_at": info.created_at,
    }
    if info.started_at:
        resp["started_at"] = info.started_at
    if info.completed_at:
        resp["completed_at"] = info.completed_at
    if info.status == TaskState.COMPLETED and info.result is not None:
        resp["result"] = info.result
    if info.status == TaskState.FAILED and info.error:
        resp["error"] = info.error
    return resp


def _convert_and_save_image(raw_path: str, camera_id: int, run_index: int) -> Optional[str]:
    """
    将相机拍摄的图片（可能是BMP）转换为JPG格式，缩放最长边到500px，保存到 camera_images/ 目录。
    返回相对于 camera_images/ 的路径（如 F0/001.jpg），供前端通过 /images/ 访问。
    """
    from PIL import Image

    src = Path(raw_path)
    if not src.exists():
        return None

    try:
        img = Image.open(src).convert("RGB")
    except Exception as e:
        logger.warning(f"无法打开图片 {raw_path}: {e}")
        return None

    # 缩放：最长边 500px
    max_size = 500
    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # 保存到 camera_images/F{camera_id}/ 目录
    save_dir = _images_dir / f"F{camera_id}"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_name = f"{run_index:03d}_{datetime.now().strftime('%H%M%S')}.jpg"
    save_path = save_dir / save_name
    img.save(str(save_path), "JPEG", quality=85)

    # 返回相对路径
    relative = f"F{camera_id}/{save_name}"
    logger.info(f"图片已保存: {save_path} ({img.size[0]}x{img.size[1]})")
    return relative


# ==================== 请求模型 ====================

class TemplateField(BaseModel):
    name: str
    label: str
    unit: Optional[str] = ""
    type: str = "float"

class InstrumentTemplateCreate(BaseModel):
    instrument_type: str
    name: str
    description: Optional[str] = ""
    prompt_template: str
    fields: List[TemplateField]
    keywords: List[str]
    example_images: Optional[List[str]] = []
    default_tier: int = 2

class CameraCreate(BaseModel):
    name: str
    camera_id: int
    control_host: Optional[str] = "127.0.0.1"
    control_port: Optional[int] = None
    mode: Optional[str] = 'single'


class CameraConfigItem(BaseModel):
    field_key: str
    camera_id: int
    max_readings: int
    selected_readings: Optional[List[str]] = None


class ExperimentCreate(BaseModel):
    name: str
    type: str  # kinematic_viscosity | apparent_viscosity | surface_tension
    manual_params: Optional[dict] = {}
    camera_configs: Optional[List[CameraConfigItem]] = []
    description: Optional[str] = None


class ExperimentRunField(BaseModel):
    field_key: str
    camera_id: int


class ExperimentCaptureBody(BaseModel):
    camera_id: int


# ==================== 相机管理 API ====================

@app.get("/cameras")
def list_cameras(enabled_only: bool = True):
    """获取相机列表"""
    cameras = get_cameras(enabled_only=enabled_only)
    return {"success": True, "count": len(cameras), "cameras": cameras}


@app.get("/cameras/{camera_id}")
def get_camera(camera_id: int):
    """获取单个相机信息"""
    camera = get_camera_by_id(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="相机不存在")
    return {"success": True, "camera": camera}


@app.post("/cameras")
def create_camera(camera: CameraCreate):
    """添加新相机"""
    try:
        camera_id_db = add_camera(
            name=camera.name,
            camera_id=camera.camera_id,
            control_host=camera.control_host,
            control_port=camera.control_port,
            mode=camera.mode or 'single',
        )
        return {"success": True, "camera_id": camera_id_db, "message": "相机添加成功"}
    except Exception as e:
        logger.error(f"添加相机失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cameras/{camera_id}")
def remove_camera(camera_id: int):
    """删除相机（软删除设置为 disabled）"""
    # 这里使用软删除，实际禁用
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cameras SET enabled = 0 WHERE camera_id = ?", (camera_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="相机不存在")
    return {"success": True, "message": "相机已禁用"}


# ==================== 实验管理 API ====================

@app.get("/experiments")
def list_experiments_api(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """获取实验列表（摘要，不含读数）"""
    experiments = list_experiments(limit=limit, offset=offset)
    return {"success": True, "count": len(experiments), "experiments": experiments}


@app.get("/experiments/{exp_id}")
def get_experiment_api(exp_id: int):
    """获取实验详情（含所有读数）"""
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    return {"success": True, "experiment": experiment}


@app.post("/experiments")
def create_experiment_api(exp: ExperimentCreate):
    """创建实验记录"""
    VALID_TYPES = {"kinematic_viscosity", "apparent_viscosity", "surface_tension", "test"}
    if exp.type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"无效实验类型: {exp.type}")
    try:
        exp_id = create_experiment(
            name=exp.name,
            exp_type=exp.type,
            manual_params=exp.manual_params,
            camera_configs=[c.dict() for c in exp.camera_configs],
            description=exp.description,
        )
        return {"success": True, "experiment_id": exp_id}
    except Exception as e:
        logger.error(f"创建实验失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/experiments/{exp_id}/run")
def run_experiment_field(exp_id: int, body: ExperimentRunField):
    """
    触发单个字段的相机拍照→OCR→保存读数

    每次点击"拍照识别"按钮调用一次，明确指定 field_key 和 camera_id。
    """
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    # 计算本次读数的 run_index（当前该字段已有几条读数 + 1）
    existing = [r for r in experiment["readings"] if r["field_key"] == body.field_key]
    run_index = len(existing) + 1

    # 调用相机拍照并 OCR（根据 mock 开关选择真实或模拟客户端）
    mock_enabled = get_config("mock_camera_enabled", default=False)
    try:
        image_dir = get_config("image_dir", default=None) or None
        if mock_enabled:
            client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir)
            success, result = client.trigger_and_read()
        else:
            camera_config = Config.get_camera_config()
            if image_dir:
                camera_config["image_dir"] = image_dir
            client = CameraClient(camera_id=body.camera_id, config=camera_config)
            success, result = client.trigger_and_read()
    except Exception as e:
        logger.error(f"相机 {body.camera_id} 拍照失败: {e}")
        return {"success": False, "detail": f"相机连接失败: {e}"}

    if not success:
        return {"success": False, "detail": result.get("error", "OCR 识别失败")}

    # 将 OCR 字符串解析为 float（取数字部分）
    raw_reading = result.get("reading", "")
    try:
        value = float(str(raw_reading).strip())
    except (ValueError, TypeError):
        logger.error(f"相机 {body.camera_id} OCR 结果无法解析为数字: {raw_reading!r}")
        return {"success": False, "detail": f"OCR 结果无法解析: {raw_reading}"}

    # 处理图片：BMP转JPG + 缩放
    saved_image_path = None
    raw_image_path = result.get("image_path")
    if raw_image_path:
        saved_image_path = _convert_and_save_image(raw_image_path, body.camera_id, run_index)

    reading = create_reading(
        experiment_id=exp_id,
        field_key=body.field_key,
        camera_id=body.camera_id,
        value=value,
        run_index=run_index,
        confidence=result.get("confidence"),
        image_path=saved_image_path,
    )
    return {"success": True, "reading": reading}


@app.post("/experiments/{exp_id}/capture")
def capture_image_endpoint(exp_id: int, body: ExperimentCaptureBody):
    """
    仅拍照并保存图片（不做OCR），立即返回图片路径供前端显示。
    前端收到图片后可立即展示，再调用 /run-test 进行 OCR。
    """
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    mock_enabled = get_config("mock_camera_enabled", default=False)
    image_dir_config = get_config("image_dir", default=None) or None

    try:
        if mock_enabled:
            client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir_config)
            success, result = client.capture_image()
        else:
            camera_config = Config.get_camera_config()
            if image_dir_config:
                camera_config["image_dir"] = image_dir_config
            client = CameraClient(camera_id=body.camera_id, config=camera_config)
            success, result = client.trigger_and_read()
    except Exception as e:
        logger.error(f"相机 {body.camera_id} 拍照失败: {e}")
        return {"success": False, "detail": f"相机连接失败: {e}"}

    if not success:
        return {"success": False, "detail": result.get("error", "拍照失败")}

    raw_image_path = result.get("image_path")
    if not raw_image_path:
        return {"success": False, "detail": "未获取到图片"}

    # 计算该相机的下一个 run_index
    existing_images = set(
        r.get("image_path") for r in experiment["readings"]
        if r.get("image_path") and r["camera_id"] == body.camera_id
    )
    run_index = len(existing_images) + 1

    saved_image_path = _convert_and_save_image(raw_image_path, body.camera_id, run_index)
    return {"success": True, "image_path": saved_image_path, "camera_id": body.camera_id}


class ExperimentRunTestBody(BaseModel):
    field_key: str
    camera_id: int
    image_path: Optional[str] = None
    reading_key: Optional[str] = None   # 仪器读数键，如 "actual_reading"、"tension"
    run_index: Optional[int] = None     # 槽位序号（0-based），不传则追加
    precise: bool = False               # 精准识别：先 OCR 提取文字识别仪器类型，再二次读数
    camera_mode: Optional[str] = None  # F0 专用："auto"（自动模式）或 "manual"（手动模式）


@app.post("/experiments/{exp_id}/run-test")
def run_test_capture(exp_id: int, body: ExperimentRunTestBody):
    """
    测试模板 OCR 识别。
    如果提供 image_path 则跳过拍照，直接对指定图片做 OCR。
    """
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    saved_image_path = body.image_path

    if not saved_image_path:
        # 未提供 image_path，执行完整拍照+OCR
        mock_enabled = get_config("mock_camera_enabled", default=False)
        try:
            image_dir = get_config("image_dir", default=None) or None
            if mock_enabled:
                client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir)
                success, result = client.capture_image()
            else:
                camera_config = Config.get_camera_config()
                if image_dir:
                    camera_config["image_dir"] = image_dir
                client = CameraClient(camera_id=body.camera_id, config=camera_config)
                success, result = client.trigger_and_read()
        except Exception as e:
            logger.error(f"相机 {body.camera_id} 拍照失败: {e}")
            return {"success": False, "detail": f"相机连接失败: {e}"}

        if not success:
            return {"success": False, "detail": result.get("error", "OCR 识别失败")}

        raw_image_path = result.get("image_path")
        if raw_image_path:
            saved_image_path = _convert_and_save_image(raw_image_path, body.camera_id, 0)

    if not saved_image_path:
        return {"success": False, "detail": "无可用图片"}

    # 对保存的图片做 OCR
    full_image_path = str(_images_dir / saved_image_path)
    try:
        from instrument_reader import InstrumentReader, DynamicInstrumentLibrary
        from backend.services.llm_provider import get_global_provider
        reader = InstrumentReader(provider=get_global_provider())
        if body.camera_mode and body.camera_id == 0:
            # F0 指定模式：直接使用 auto/manual 专用 prompt，跳过自动判断
            instrument_type = f"wuying_mixer_{body.camera_mode}"
            prompt = DynamicInstrumentLibrary.get_instrument_prompt(instrument_type)
            parsed = reader.mm_reader.analyze_image(full_image_path, prompt, call_type="read")
            if "error" in parsed:
                ocr_result = {"success": False, "error": parsed["error"]}
            else:
                ocr_result = {"success": True, "readings": parsed, "instrument_type": instrument_type}
        elif body.precise:
            # 精准模式：OCR提取文字 → 识别仪器类型 → 二次读数
            ocr_result = reader._read_by_identification(full_image_path)
        else:
            # 快速模式：相机专用prompt直接读数
            ocr_result = reader.read_instrument(full_image_path)
    except Exception as e:
        logger.error(f"OCR 失败: {e}")
        return {"success": False, "detail": f"OCR 识别失败: {e}"}

    if not ocr_result.get("success"):
        return {"success": False, "detail": ocr_result.get("error", "OCR 识别失败")}

    # 解析 OCR 返回的所有读数（仪器原始键值对）
    raw_response = ocr_result.get("readings", {})
    if isinstance(raw_response, dict):
        readings_dict = raw_response
    elif isinstance(raw_response, str):
        try:
            readings_dict = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            readings_dict = {}
    else:
        readings_dict = {}

    # 过滤掉非数值（如 mode、date 字符串字段），同时保留 "MM:SS" 时间格式
    numeric_ocr: dict = {}
    for k, v in readings_dict.items():
        if v is None:
            continue
        str_val = str(v).strip()
        if k == "time" and ":" in str_val:
            parts = str_val.split(":")
            if len(parts) == 2:
                try:
                    numeric_ocr[k] = float(parts[0]) * 60 + float(parts[1])
                except ValueError:
                    pass
        else:
            try:
                numeric_ocr[k] = float(str_val)
            except (ValueError, TypeError):
                # "##.##" 类占位符视为 0；纯字符串（mode、date 等）跳过
                if all(c in '#.-+ ' for c in str_val) and '#' in str_val:
                    numeric_ocr[k] = 0.0
                # 否则跳过

    if not numeric_ocr:
        # 无数值字段（如仅有字符串字段），仍返回 all_ocr 供前端展示，不保存读数
        return {"success": True, "detail": "OCR 未识别到可保存的数值", "all_ocr": readings_dict, "readings": []}

    # 确定主读数键：优先使用请求中传入的 reading_key，
    # 其次查相机配置的 selected_readings[0]，最后取第一个数值字段
    primary_key = body.reading_key
    if not primary_key:
        config = next(
            (c for c in experiment["camera_configs"] if c["field_key"] == body.field_key),
            None
        )
        selected = (config.get("selected_readings") or []) if config else []
        primary_key = next((k for k in selected if k in numeric_ocr), None)
    if not primary_key:
        primary_key = next(iter(numeric_ocr), None)

    primary_value = numeric_ocr.get(primary_key) if primary_key else None
    if primary_value is None:
        # 读数键不在 OCR 结果中，用 0 保存并附带提示
        logger.warning(f"未找到读数键 '{primary_key}'，以 0 保存。OCR结果: {readings_dict}")
        primary_value = 0.0

    # 确定 run_index：使用前端传入值（0-based），否则追加
    if body.run_index is not None:
        run_index = body.run_index
    else:
        existing = [r for r in experiment["readings"] if r["field_key"] == body.field_key]
        run_index = len(existing)   # 0-based

    # 保存主读数，field_key 使用实验字段名（不是仪器键名）
    reading = upsert_reading(
        experiment_id=exp_id,
        field_key=body.field_key,
        camera_id=body.camera_id,
        value=primary_value,
        run_index=run_index,
        image_path=saved_image_path,
    )

    # 若 primary_value 为 0 且原始 OCR 中无该键，附加提示
    detail = None
    if primary_key and primary_key not in readings_dict:
        detail = f"未找到读数键 '{primary_key}'，已以 0 保存"

    return {
        "success": True,
        "readings": [reading],
        "all_ocr": readings_dict,   # 完整 OCR 结果，前端用于在图片下方展示所有读数
        **({"detail": detail} if detail else {}),
    }


# ==================== 异步任务版本 API ====================
# 以下端点将耗时操作（拍照 + OCR + LLM）放入后台线程执行，
# 立即返回 task_id，前端通过 GET /tasks/{task_id} 轮询结果。

def _do_run_experiment_field(exp_id: int, field_key: str, camera_id: int):
    """后台线程：执行 run_experiment_field 的实际逻辑"""
    experiment = get_experiment(exp_id)
    if not experiment:
        return {"success": False, "detail": "实验不存在"}

    existing = [r for r in experiment["readings"] if r["field_key"] == field_key]
    run_index = len(existing) + 1

    mock_enabled = get_config("mock_camera_enabled", default=False)
    try:
        image_dir = get_config("image_dir", default=None) or None
        if mock_enabled:
            client = MockCameraClient(camera_id=camera_id, image_dir=image_dir)
            success, result = client.trigger_and_read()
        else:
            camera_config = Config.get_camera_config()
            if image_dir:
                camera_config["image_dir"] = image_dir
            client = CameraClient(camera_id=camera_id, config=camera_config)
            success, result = client.trigger_and_read()
    except Exception as e:
        logger.error(f"相机 {camera_id} 拍照失败: {e}")
        return {"success": False, "detail": f"相机连接失败: {e}"}

    if not success:
        return {"success": False, "detail": result.get("error", "OCR 识别失败")}

    raw_reading = result.get("reading", "")
    try:
        value = float(str(raw_reading).strip())
    except (ValueError, TypeError):
        logger.error(f"相机 {camera_id} OCR 结果无法解析为数字: {raw_reading!r}")
        return {"success": False, "detail": f"OCR 结果无法解析: {raw_reading}"}

    saved_image_path = None
    raw_image_path = result.get("image_path")
    if raw_image_path:
        saved_image_path = _convert_and_save_image(raw_image_path, camera_id, run_index)

    reading = create_reading(
        experiment_id=exp_id,
        field_key=field_key,
        camera_id=camera_id,
        value=value,
        run_index=run_index,
        confidence=result.get("confidence"),
        image_path=saved_image_path,
    )
    return {"success": True, "reading": reading}


@app.post("/experiments/{exp_id}/run-async")
def run_experiment_field_async(exp_id: int, body: ExperimentRunField):
    """
    [异步版] 触发单个字段的相机拍照→OCR→保存读数。

    立即返回 task_id，前端轮询 GET /tasks/{task_id} 获取结果。
    """
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    task_id = task_manager.submit(
        _do_run_experiment_field, exp_id, body.field_key, body.camera_id,
    )
    return {"task_id": task_id, "status": "pending", "message": "任务已提交，请轮询 /tasks/{task_id} 获取结果"}


def _do_run_test_capture(exp_id: int, body_dict: dict):
    """后台线程：执行 run_test_capture 的实际逻辑"""
    # Reconstruct body-like access from dict
    field_key = body_dict["field_key"]
    camera_id = body_dict["camera_id"]
    image_path = body_dict.get("image_path")
    reading_key = body_dict.get("reading_key")
    run_index_body = body_dict.get("run_index")
    precise = body_dict.get("precise", False)
    camera_mode = body_dict.get("camera_mode")

    experiment = get_experiment(exp_id)
    if not experiment:
        return {"success": False, "detail": "实验不存在"}

    saved_image_path = image_path

    if not saved_image_path:
        mock_enabled = get_config("mock_camera_enabled", default=False)
        try:
            image_dir = get_config("image_dir", default=None) or None
            if mock_enabled:
                client = MockCameraClient(camera_id=camera_id, image_dir=image_dir)
                success, result = client.capture_image()
            else:
                camera_config = Config.get_camera_config()
                if image_dir:
                    camera_config["image_dir"] = image_dir
                client = CameraClient(camera_id=camera_id, config=camera_config)
                success, result = client.trigger_and_read()
        except Exception as e:
            logger.error(f"相机 {camera_id} 拍照失败: {e}")
            return {"success": False, "detail": f"相机连接失败: {e}"}

        if not success:
            return {"success": False, "detail": result.get("error", "OCR 识别失败")}

        raw_image_path = result.get("image_path")
        if raw_image_path:
            saved_image_path = _convert_and_save_image(raw_image_path, camera_id, 0)

    if not saved_image_path:
        return {"success": False, "detail": "无可用图片"}

    # OCR
    full_image_path = str(_images_dir / saved_image_path)
    try:
        from instrument_reader import InstrumentReader, DynamicInstrumentLibrary
        from backend.services.llm_provider import get_global_provider
        reader = InstrumentReader(provider=get_global_provider())
        if camera_mode and camera_id == 0:
            instrument_type = f"wuying_mixer_{camera_mode}"
            prompt = DynamicInstrumentLibrary.get_instrument_prompt(instrument_type)
            parsed = reader.mm_reader.analyze_image(full_image_path, prompt, call_type="read")
            if "error" in parsed:
                ocr_result = {"success": False, "error": parsed["error"]}
            else:
                ocr_result = {"success": True, "readings": parsed, "instrument_type": instrument_type}
        elif precise:
            ocr_result = reader._read_by_identification(full_image_path)
        else:
            ocr_result = reader.read_instrument(full_image_path)
    except Exception as e:
        logger.error(f"OCR 失败: {e}")
        return {"success": False, "detail": f"OCR 识别失败: {e}"}

    if not ocr_result.get("success"):
        return {"success": False, "detail": ocr_result.get("error", "OCR 识别失败")}

    raw_response = ocr_result.get("readings", {})
    if isinstance(raw_response, dict):
        readings_dict = raw_response
    elif isinstance(raw_response, str):
        try:
            readings_dict = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            readings_dict = {}
    else:
        readings_dict = {}

    numeric_ocr: dict = {}
    for k, v in readings_dict.items():
        if v is None:
            continue
        str_val = str(v).strip()
        if k == "time" and ":" in str_val:
            parts = str_val.split(":")
            if len(parts) == 2:
                try:
                    numeric_ocr[k] = float(parts[0]) * 60 + float(parts[1])
                except ValueError:
                    pass
        else:
            try:
                numeric_ocr[k] = float(str_val)
            except (ValueError, TypeError):
                if all(c in '#.-+ ' for c in str_val) and '#' in str_val:
                    numeric_ocr[k] = 0.0

    if not numeric_ocr:
        return {"success": True, "detail": "OCR 未识别到可保存的数值", "all_ocr": readings_dict, "readings": []}

    primary_key = reading_key
    if not primary_key:
        config = next(
            (c for c in experiment["camera_configs"] if c["field_key"] == field_key),
            None
        )
        selected = (config.get("selected_readings") or []) if config else []
        primary_key = next((k for k in selected if k in numeric_ocr), None)
    if not primary_key:
        primary_key = next(iter(numeric_ocr), None)

    primary_value = numeric_ocr.get(primary_key) if primary_key else None
    if primary_value is None:
        logger.warning(f"未找到读数键 '{primary_key}'，以 0 保存。OCR结果: {readings_dict}")
        primary_value = 0.0

    if run_index_body is not None:
        run_index = run_index_body
    else:
        existing = [r for r in experiment["readings"] if r["field_key"] == field_key]
        run_index = len(existing)

    reading = upsert_reading(
        experiment_id=exp_id,
        field_key=field_key,
        camera_id=camera_id,
        value=primary_value,
        run_index=run_index,
        image_path=saved_image_path,
    )

    detail = None
    if primary_key and primary_key not in readings_dict:
        detail = f"未找到读数键 '{primary_key}'，已以 0 保存"

    return {
        "success": True,
        "readings": [reading],
        "all_ocr": readings_dict,
        **({"detail": detail} if detail else {}),
    }


@app.post("/experiments/{exp_id}/run-test-async")
def run_test_capture_async(exp_id: int, body: ExperimentRunTestBody):
    """
    [异步版] 测试模板 OCR 识别。

    立即返回 task_id，前端轮询 GET /tasks/{task_id} 获取结果。
    """
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    task_id = task_manager.submit(
        _do_run_test_capture, exp_id, body.model_dump(),
    )
    return {"task_id": task_id, "status": "pending", "message": "任务已提交，请轮询 /tasks/{task_id} 获取结果"}


def _do_read_multi_instruments(body_dict: dict):
    """后台线程：执行 read_multi_instruments 的实际逻辑"""
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    from PIL import Image

    full_image_path = body_dict.get("image_path")

    if not full_image_path and body_dict.get("camera_id") is not None:
        camera_id = body_dict["camera_id"]
        mock_enabled = get_config("mock_camera_enabled", default=False)
        image_dir = get_config("image_dir", default=None) or None
        try:
            if mock_enabled:
                from backend.services.mock_camera import MockCameraClient
                client = MockCameraClient(camera_id=camera_id, image_dir=image_dir)
                success, result = client.capture_image()
            else:
                from backend.services.camera_control import CameraClient
                camera_config = Config.get_camera_config()
                if image_dir:
                    camera_config["image_dir"] = image_dir
                client = CameraClient(camera_id=camera_id, config=camera_config)
                success, result = client.capture_image()
        except Exception as e:
            logger.error(f"Camera {camera_id} capture failed: {e}")
            return {"success": False, "detections": [], "detail": f"Capture failed: {str(e)}"}

        if not success:
            return {"success": False, "detections": [], "detail": result.get("error", "Capture failed")}
        full_image_path = result.get("image_path")
        if not full_image_path:
            return {"success": False, "detections": [], "detail": "No image captured"}

    try:
        assert full_image_path is not None
        image = Image.open(full_image_path).convert("RGB")
    except Exception as e:
        return {"success": False, "detections": [], "detail": f"Cannot open image: {str(e)}"}

    try:
        pipeline = MultiInstrumentPipeline()
        detections = pipeline.process_image(image)
        return {"success": True, "detections": detections}
    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        return {"success": False, "detections": [], "detail": f"Processing failed: {str(e)}"}


@app.post("/api/read-multi-async")
def read_multi_instruments_async(body: ReadMultiRequest):
    """
    [异步版] Multi-instrument reading endpoint.

    立即返回 task_id，前端轮询 GET /tasks/{task_id} 获取结果。
    """
    task_id = task_manager.submit(
        _do_read_multi_instruments, body.model_dump(),
    )
    return {"task_id": task_id, "status": "pending", "message": "任务已提交，请轮询 /tasks/{task_id} 获取结果"}


@app.get("/config/camera-instruments")
def get_camera_instruments():
    """返回相机编号到仪器的映射"""
    CAMERA_INSTRUMENTS = {
        "F0": {
            "name": "超级吴英混调器",
            "readings": [
                {"key": "seg1_speed", "label": "段一转速", "unit": "转"},
                {"key": "seg1_time", "label": "段一时间", "unit": "S"},
                {"key": "seg2_speed", "label": "段二转速", "unit": "转"},
                {"key": "seg2_time", "label": "段二时间", "unit": "S"},
                {"key": "seg3_speed", "label": "段三转速", "unit": "转"},
                {"key": "seg3_time", "label": "段三时间", "unit": "S"},
                {"key": "total_time", "label": "总时长", "unit": "S"},
                {"key": "remaining_time", "label": "剩余时长", "unit": "S"},
                {"key": "current_segment", "label": "当前段数", "unit": ""},
                {"key": "current_speed", "label": "当前转速", "unit": "转"},
                {"key": "high_speed", "label": "高速转速", "unit": "转"},
                {"key": "high_time", "label": "高速时间", "unit": "S"},
                {"key": "low_speed", "label": "低速转速", "unit": "转"},
                {"key": "low_time", "label": "低速时间", "unit": "S"},
            ],
        },
        "F1": {
            "name": "电子天枰1号",
            "readings": [{"key": "weight", "label": "重量", "unit": "g"}],
        },
        "F2": {
            "name": "电子天枰2号",
            "readings": [{"key": "weight", "label": "重量", "unit": "g"}],
        },
        "F3": {
            "name": "PH仪",
            "readings": [
                {"key": "ph_value", "label": "pH值", "unit": ""},
                {"key": "temperature", "label": "温度", "unit": "°C"},
                {"key": "pts", "label": "PTS值", "unit": "%PTS"},
            ],
        },
        "F4": {
            "name": "水质检测仪",
            "readings": [
                {"key": "date", "label": "检测日期", "unit": ""},
                {"key": "blank_value", "label": "空白值", "unit": ""},
                {"key": "test_value", "label": "检测值", "unit": ""},
                {"key": "absorbance", "label": "吸光度", "unit": ""},
                {"key": "content_mg_l", "label": "含量", "unit": "mg/L"},
                {"key": "transmittance", "label": "透光度", "unit": "%"},
                {"key": "mode", "label": "量程模式", "unit": ""},
            ],
        },
        "F5": {
            "name": "表界面张力仪",
            "readings": [
                {"key": "tension", "label": "张力", "unit": "mN/m"},
                {"key": "temperature", "label": "温度", "unit": "°C"},
                {"key": "upper_density", "label": "上层密度", "unit": "g/cm³"},
                {"key": "lower_density", "label": "下层密度", "unit": "g/cm³"},
                {"key": "rise_speed", "label": "上升速度", "unit": "mm/min"},
                {"key": "fall_speed", "label": "下降速度", "unit": "mm/min"},
            ],
        },
        "F6": {
            "name": "电动搅拌器",
            "readings": [
                {"key": "rotation_speed", "label": "转速", "unit": "rpm"},
                {"key": "torque", "label": "扭矩", "unit": "N/cm"},
                {"key": "time", "label": "时间", "unit": ""},
            ],
        },
        "F7": {
            "name": "水浴锅",
            "readings": [
                {"key": "temperature", "label": "温度", "unit": "°C"},
                {"key": "time", "label": "时间", "unit": "min"},
            ],
        },
        "F8": {
            "name": "6速旋转粘度计",
            "readings": [
                {"key": "actual_reading", "label": "实施读数", "unit": ""},
                {"key": "max_reading", "label": "最大读数", "unit": ""},
                {"key": "min_reading", "label": "最小读数", "unit": ""},
                {"key": "rotation_speed", "label": "转速", "unit": "RPM"},
                {"key": "shear_rate", "label": "剪切速率", "unit": "S-1"},
                {"key": "shear_stress", "label": "剪切应力", "unit": "Pa"},
                {"key": "apparent_viscosity", "label": "表观粘度", "unit": "mPa·s"},
                {"key": "avg_5s", "label": "5秒平均值", "unit": "mPa·s"},
            ],
        },
    }
    return {"success": True, "cameras": CAMERA_INSTRUMENTS}


class ManualReadingBody(BaseModel):
    field_key: str
    run_index: int
    value: float
    camera_id: int = 0


@app.put("/experiments/{exp_id}/readings")
def save_manual_reading(exp_id: int, body: ManualReadingBody):
    """手动保存/更新单次读数（用于 OCR 失败时人工填写）"""
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    reading = upsert_reading(
        experiment_id=exp_id,
        field_key=body.field_key,
        camera_id=body.camera_id,
        value=body.value,
        run_index=body.run_index,
    )
    return {"success": True, "reading": reading}


@app.delete("/experiments/{exp_id}")
def delete_experiment_api(exp_id: int):
    """删除实验记录"""
    deleted = delete_experiment(exp_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="实验不存在")
    return {"success": True, "message": "实验已删除"}


@app.get("/experiments/{exp_id}/export")
def export_experiment(exp_id: int):
    """导出实验数据为 xlsx，按实验类型生成对应模板格式，包含图片路径"""

    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    wb = openpyxl.Workbook()
    ws = wb.active
    exp_type = experiment.get("type", "")
    readings = experiment.get("readings", [])
    manual = experiment.get("manual_params", {})

    # 样式辅助
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    subheader_fill = PatternFill("solid", fgColor="EEF2FA")
    thin = Side(style="thin", color="BBBBBB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def cell(row, col, value, bold=False, fill=None, align="left"):
        c = ws.cell(row=row, column=col, value=value)
        if bold:
            c.font = Font(bold=True)
        if fill:
            c.fill = fill
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
        c.border = border
        return c

    def header_row(row, cols_values: list, fill=None):
        """写一行标题，cols_values = [(col, value), ...]"""
        for col, val in cols_values:
            cell(row, col, val, bold=True, fill=fill or header_fill, align="center")

    ws.title = experiment["name"][:31]

    if exp_type == "kinematic_viscosity":
        # ── 标题行
        ws.merge_cells("A1:F1")
        cell(1, 1, "运动粘度检验原始记录", bold=True, align="center")
        ws.cell(1, 1).font = Font(bold=True, size=13)

        # ── 文件信息
        cell(2, 1, "文件编号 File：WLD-QP5100113-02　版次 Edition：A/1", align="left")
        ws.merge_cells("A2:F2")

        # ── 头信息
        header_row(3, [(1, "检测日期"), (3, "报告编号 NO.")], fill=subheader_fill)
        cell(3, 2, manual.get("test_date", ""))
        ws.merge_cells("B3:C3") if False else None  # skip merge for simplicity
        cell(3, 4, manual.get("report_number", ""))
        ws.merge_cells("D3:F3") if False else None

        header_row(4, [(1, "被检样品名称"), (3, "样品编号")], fill=subheader_fill)
        cell(4, 2, manual.get("sample_name", ""))
        cell(4, 4, manual.get("sample_number", ""))

        cell(5, 1, "配方说明", bold=True, fill=subheader_fill)
        cell(5, 2, manual.get("formula_description", ""))
        ws.merge_cells("B5:F5")

        # ── 实验参数
        header_row(6, [(1, "温控设置温度 (℃)"), (2, "最高温度 (℃)"), (3, "最低温度 (℃)"),
                       (4, "毛细管粘度计型号"), (5, "毛细管系数 C (mm²/s²)")], fill=subheader_fill)
        cell(7, 1, manual.get("temperature_set", ""), align="center")
        cell(7, 2, manual.get("temperature_max", ""), align="center")
        cell(7, 3, manual.get("temperature_min", ""), align="center")
        cell(7, 4, manual.get("capillary_model", ""), align="center")
        cell(7, 5, manual.get("capillary_coeff", ""), align="center")

        # ── 流经时间读数
        header_row(9, [(1, "实验次数"), (2, "流经时间 t (s)"), (3, "时间戳"), (4, "图片路径")],
                   fill=header_fill)
        ft_readings = [r for r in readings if r["field_key"] == "flow_time"]
        for i, r in enumerate(ft_readings):
            row_n = 10 + i
            cell(row_n, 1, f"实验 {i + 1}", align="center")
            cell(row_n, 2, r["value"], align="center")
            cell(row_n, 3, (r.get("timestamp") or "")[:19])
            cell(row_n, 4, r.get("image_path") or "")

        # ── 计算结果
        res_row = 10 + len(ft_readings) + 1
        if ft_readings:
            avg = sum(r["value"] for r in ft_readings) / len(ft_readings)
            coeff = float(manual.get("capillary_coeff") or 0)
            cell(res_row, 1, "平均流经时间 t̄ (s)", bold=True, fill=subheader_fill)
            cell(res_row, 2, round(avg, 4), align="center")
            cell(res_row + 1, 1, "运动粘度 ν = C × t̄  (mm²/s)", bold=True, fill=subheader_fill)
            cell(res_row + 1, 2, round(coeff * avg, 4), align="center")

        # 列宽
        for col, width in [(1, 22), (2, 16), (3, 20), (4, 36), (5, 22)]:
            ws.column_dimensions[get_column_letter(col)].width = width
        ws.row_dimensions[1].height = 24

    elif exp_type == "apparent_viscosity":
        ws.merge_cells("A1:F1")
        cell(1, 1, "表观黏度检测原始记录", bold=True, align="center")
        ws.cell(1, 1).font = Font(bold=True, size=13)

        cell(2, 1, "文件编号 File：WLD/CNAS-QP7080004　版次 Edition：A/3")
        ws.merge_cells("A2:F2")

        header_row(3, [(1, "检测日期"), (3, "编号 NO.")], fill=subheader_fill)
        cell(3, 2, manual.get("test_date", ""))
        cell(3, 4, manual.get("report_number", ""))
        header_row(4, [(1, "被检样品名称"), (3, "样品编号")], fill=subheader_fill)
        cell(4, 2, manual.get("sample_name", ""))
        cell(4, 4, manual.get("sample_number", ""))
        cell(5, 1, "配方说明", bold=True, fill=subheader_fill)
        cell(5, 2, manual.get("formula_description", ""))
        ws.merge_cells("B5:F5")

        # ── 表头
        header_row(7, [(1, "实验次数"), (2, "3 rpm"), (3, "6 rpm"), (4, "100 rpm (α)"),
                       (5, "表观黏度 η (mPa·s)"), (6, "图片路径（100rpm）")], fill=header_fill)

        for run_idx in [0, 1]:
            row_n = 8 + run_idx
            rpm3 = next((r["value"] for r in readings if r["field_key"] == "rpm3" and r["run_index"] == run_idx), "")
            rpm6 = next((r["value"] for r in readings if r["field_key"] == "rpm6" and r["run_index"] == run_idx), "")
            rpm100_r = next((r for r in readings if r["field_key"] == "rpm100" and r["run_index"] == run_idx), None)
            rpm100 = rpm100_r["value"] if rpm100_r else ""
            eta = round((rpm100 * 5.077) / 1.704, 4) if rpm100 != "" else ""
            img = rpm100_r.get("image_path") or "" if rpm100_r else ""
            cell(row_n, 1, f"实验 {run_idx + 1}", align="center")
            cell(row_n, 2, rpm3, align="center")
            cell(row_n, 3, rpm6, align="center")
            cell(row_n, 4, rpm100, align="center")
            cell(row_n, 5, eta, align="center")
            cell(row_n, 6, img)

        all_eta = [(r["value"] * 5.077) / 1.704 for r in readings if r["field_key"] == "rpm100"]
        if all_eta:
            cell(11, 1, "平均表观黏度 (mPa·s)", bold=True, fill=subheader_fill)
            cell(11, 5, round(sum(all_eta) / len(all_eta), 4), align="center")

        # ── 每个字段的完整读数+图片
        row_n = 13
        cell(row_n, 1, "各读数详情（含图片路径）", bold=True, fill=subheader_fill)
        ws.merge_cells(f"A{row_n}:F{row_n}")
        row_n += 1
        header_row(row_n, [(1, "字段"), (2, "实验次数"), (3, "读数值"), (4, "时间戳"), (5, "图片路径")],
                   fill=header_fill)
        row_n += 1
        for r in readings:
            cell(row_n, 1, r["field_key"])
            cell(row_n, 2, f"实验 {r['run_index'] + 1}", align="center")
            cell(row_n, 3, r["value"], align="center")
            cell(row_n, 4, (r.get("timestamp") or "")[:19])
            cell(row_n, 5, r.get("image_path") or "")
            row_n += 1

        for col, width in [(1, 18), (2, 10), (3, 12), (4, 12), (5, 20), (6, 36)]:
            ws.column_dimensions[get_column_letter(col)].width = width
        ws.row_dimensions[1].height = 24

    elif exp_type == "surface_tension":
        ws.merge_cells("A1:F1")
        cell(1, 1, "表面张力和界面张力检测原始记录", bold=True, align="center")
        ws.cell(1, 1).font = Font(bold=True, size=13)

        cell(2, 1, "文件编号 File：WLD/CNAS-QP7080004　版次 Edition：A/3　执行标准：SY/T 5370-2018")
        ws.merge_cells("A2:F2")

        # ── 头信息
        for r_idx, (lbl1, key1, lbl2, key2) in enumerate([
            ("检测日期", "test_date", "检测报告编号", "report_number"),
            ("被检样品名称", "sample_name", "样品编号", "sample_number"),
            ("样品状态", "sample_state", "配液编号", "formula_number"),
        ], start=3):
            cell(r_idx, 1, lbl1, bold=True, fill=subheader_fill)
            cell(r_idx, 2, manual.get(key1, ""))
            cell(r_idx, 3, lbl2, bold=True, fill=subheader_fill)
            cell(r_idx, 4, manual.get(key2, ""))

        cell(6, 1, "配方说明", bold=True, fill=subheader_fill)
        cell(6, 2, manual.get("formula_description", ""))
        ws.merge_cells("B6:F6")

        # ── 环境条件
        header_row(7, [(1, "室内温度 (℃)"), (2, "室内湿度 (%)"),
                       (3, "25℃ 破胶液密度 (g/cm³)"), (4, "25℃ 煤油密度 (g/cm³)")],
                   fill=subheader_fill)
        cell(8, 1, manual.get("room_temperature", ""), align="center")
        cell(8, 2, manual.get("room_humidity", ""), align="center")
        cell(8, 3, manual.get("sample_density", ""), align="center")
        cell(8, 4, manual.get("kerosene_density", ""), align="center")

        # ── 纯水表面张力
        cell(10, 1, "纯水表面张力验证", bold=True, fill=subheader_fill)
        ws.merge_cells("A10:F10")
        header_row(11, [(1, "项目"), (2, "测试值 (mN/m)"), (3, "时间戳"), (4, "图片路径")],
                   fill=header_fill)
        wst_r = next((r for r in readings if r["field_key"] == "water_surface_tension"), None)
        cell(12, 1, "纯水表面张力")
        cell(12, 2, wst_r["value"] if wst_r else "", align="center")
        cell(12, 3, (wst_r.get("timestamp") or "")[:19] if wst_r else "")
        cell(12, 4, wst_r.get("image_path") or "" if wst_r else "")

        # ── 破胶液表面张力
        cell(14, 1, f"破胶液表面张力（样品密度 {manual.get('sample_density','')} g/cm³）",
             bold=True, fill=subheader_fill)
        ws.merge_cells("A14:F14")
        header_row(15, [(1, "实验次数"), (2, "表面张力 (mN/m)"), (3, "时间戳"), (4, "图片路径")],
                   fill=header_fill)
        fst = [r for r in readings if r["field_key"] == "fluid_surface_tension"]
        for i, r in enumerate(fst):
            rn = 16 + i
            cell(rn, 1, f"实验 {i + 1}", align="center")
            cell(rn, 2, r["value"], align="center")
            cell(rn, 3, (r.get("timestamp") or "")[:19])
            cell(rn, 4, r.get("image_path") or "")
        avg_row = 16 + len(fst)
        if fst:
            cell(avg_row, 1, "算术平均值", bold=True, fill=subheader_fill)
            cell(avg_row, 2, round(sum(r["value"] for r in fst) / len(fst), 4), align="center")

        # ── 破胶液界面张力
        base = avg_row + 2
        cell(base, 1, f"破胶液界面张力（煤油密度 {manual.get('kerosene_density','')} g/cm³）",
             bold=True, fill=subheader_fill)
        ws.merge_cells(f"A{base}:F{base}")
        header_row(base + 1, [(1, "实验次数"), (2, "界面张力 (mN/m)"), (3, "时间戳"), (4, "图片路径")],
                   fill=header_fill)
        fit = [r for r in readings if r["field_key"] == "fluid_interface_tension"]
        for i, r in enumerate(fit):
            rn = base + 2 + i
            cell(rn, 1, f"实验 {i + 1}", align="center")
            cell(rn, 2, r["value"], align="center")
            cell(rn, 3, (r.get("timestamp") or "")[:19])
            cell(rn, 4, r.get("image_path") or "")
        if fit:
            avg_r = base + 2 + len(fit)
            cell(avg_r, 1, "算术平均值", bold=True, fill=subheader_fill)
            cell(avg_r, 2, round(sum(r["value"] for r in fit) / len(fit), 4), align="center")
            sign_row = avg_r + 2
        else:
            sign_row = base + 4

        # ── 签署区
        cell(sign_row, 1, "备注", bold=True, fill=subheader_fill)
        cell(sign_row, 2, manual.get("remarks", ""))
        ws.merge_cells(f"B{sign_row}:F{sign_row}")
        cell(sign_row + 1, 1, "检测人", bold=True, fill=subheader_fill)
        cell(sign_row + 1, 2, manual.get("operator_name", ""))
        cell(sign_row + 1, 3, "检测时间", bold=True, fill=subheader_fill)
        cell(sign_row + 1, 4, manual.get("operator_time", ""))
        cell(sign_row + 2, 1, "审核人", bold=True, fill=subheader_fill)
        cell(sign_row + 2, 2, manual.get("reviewer_name", ""))
        cell(sign_row + 2, 3, "审核日期", bold=True, fill=subheader_fill)
        cell(sign_row + 2, 4, manual.get("reviewer_date", ""))

        for col, width in [(1, 22), (2, 16), (3, 20), (4, 36)]:
            ws.column_dimensions[get_column_letter(col)].width = width
        ws.row_dimensions[1].height = 24

    elif exp_type == "test":
        ws.merge_cells("A1:F1")
        cell(1, 1, "全相机测试拍照记录", bold=True, align="center")
        ws.cell(1, 1).font = Font(bold=True, size=13)
        cell(2, 1, f"实验名称: {experiment['name']}")
        ws.merge_cells("A2:F2")

        header_row(4, [(1, "相机位"), (2, "字段"), (3, "序号"), (4, "读数值"),
                       (5, "时间戳"), (6, "图片路径")], fill=header_fill)
        row_n = 5
        for cam_id in range(9):
            cam_readings = [r for r in readings if r["camera_id"] == cam_id]
            for i, r in enumerate(cam_readings):
                cell(row_n, 1, f"F{cam_id}", align="center")
                cell(row_n, 2, r["field_key"])
                cell(row_n, 3, i + 1, align="center")
                cell(row_n, 4, r["value"], align="center")
                cell(row_n, 5, (r.get("timestamp") or "")[:19])
                cell(row_n, 6, r.get("image_path") or "")
                row_n += 1

        for col, width in [(1, 10), (2, 16), (3, 8), (4, 12), (5, 20), (6, 36)]:
            ws.column_dimensions[get_column_letter(col)].width = width
        ws.row_dimensions[1].height = 24

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"experiment_{exp_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==================== 系统配置 API ====================

@app.get("/config/mock")
def get_mock_config():
    """获取 Mock 相机模式开关状态"""
    enabled = get_config("mock_camera_enabled", default=False)
    return {"mock_enabled": bool(enabled)}


class MockConfigUpdate(BaseModel):
    enabled: bool


@app.post("/config/mock")
def set_mock_config(body: MockConfigUpdate):
    """设置 Mock 相机模式开关"""
    set_config("mock_camera_enabled", body.enabled)
    logger.info(f"Mock 相机模式已{'开启' if body.enabled else '关闭'}")
    return {"mock_enabled": body.enabled, "message": f"Mock 模式已{'开启' if body.enabled else '关闭'}"}


@app.get("/config/image-dir")
def get_image_dir():
    """获取图片存储目录配置"""
    image_dir = get_config("image_dir", default="")
    return {"image_dir": image_dir}


class ImageDirUpdate(BaseModel):
    image_dir: str


@app.post("/config/image-dir")
def set_image_dir_config(body: ImageDirUpdate):
    """设置图片存储目录"""
    set_config("image_dir", body.image_dir)
    logger.info(f"图片存储目录已设置为: {body.image_dir}")
    return {"image_dir": body.image_dir, "message": "图片存储目录已更新"}


# ==================== 工具 API ====================

@app.get("/templates")
def list_templates():
    """获取所有仪器模板"""
    templates = get_all_templates()
    for t in templates:
        t['fields'] = json.loads(t['fields_json'])
        t['keywords'] = json.loads(t['keywords_json'])
        t['example_images'] = json.loads(t['example_images_json'] or '[]')
    return {"success": True, "templates": templates}

@app.post("/templates")
def create_or_update_template(body: InstrumentTemplateCreate):
    """创建或更新仪器模板"""
    upsert_template(
        instrument_type=body.instrument_type,
        name=body.name,
        description=body.description,
        prompt_template=body.prompt_template,
        fields=[f.model_dump() for f in body.fields],
        keywords=body.keywords,
        example_images=body.example_images,
        default_tier=body.default_tier
    )
    return {"success": True, "message": "Template saved"}

# ==================== LLM 模型配置 API ====================

def _mask_api_key(key: Optional[str]) -> Optional[str]:
    """脱敏 API Key，仅显示前4位和后4位"""
    if not key or len(key) <= 8:
        return key
    return key[:4] + "****" + key[-4:]


@app.get("/config/llm")
def get_llm_config():
    """获取当前 LLM 模型配置（API Key 脱敏）"""
    saved = get_config("llm_config", default=None)
    if saved:
        saved = {**saved, "api_key": _mask_api_key(saved.get("api_key"))}
        return {"success": True, "config": saved}
    return {
        "success": True,
        "config": {
            "provider": "openai_compatible",
            "model_name": Config.LMSTUDIO_MODEL,
            "base_url": Config.LMSTUDIO_BASE_URL,
            "api_key": None,
            "temperature": Config.MODEL_TEMPERATURE,
            "max_tokens": Config.MODEL_MAX_TOKENS,
        }
    }


class LLMConfigUpdate(BaseModel):
    provider: str
    model_name: str
    base_url: str
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@app.post("/config/llm")
def set_llm_config(body: LLMConfigUpdate):
    """设置 LLM 模型配置并重建 provider"""
    from backend.services.llm_provider import create_provider, LLMConfig, set_global_provider

    if body.provider not in ("openai_compatible",):
        raise HTTPException(status_code=400, detail=f"不支持的 provider 类型: {body.provider}")

    # 如果前端传回脱敏后的 key（包含 ****），保留数据库中的原始 key
    api_key = body.api_key
    if api_key and "****" in api_key:
        saved = get_config("llm_config", default=None)
        api_key = saved.get("api_key") if isinstance(saved, dict) else None

    config = LLMConfig(
        provider=body.provider,
        model_name=body.model_name,
        base_url=body.base_url,
        api_key=api_key,
        temperature=body.temperature if body.temperature is not None else Config.MODEL_TEMPERATURE,
        max_tokens=body.max_tokens if body.max_tokens is not None else Config.MODEL_MAX_TOKENS,
    )

    try:
        provider = create_provider(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法创建 LLM 客户端: {str(e)}")

    config_dict = {
        "provider": config.provider,
        "model_name": config.model_name,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    set_config("llm_config", config_dict)
    set_global_provider(provider)

    # 返回脱敏后的配置
    response_config = {**config_dict, "api_key": _mask_api_key(config.api_key)}
    logger.info(f"LLM 模型已切换: {config.provider}/{config.model_name} @ {config.base_url}")
    return {"success": True, "config": response_config, "message": "模型配置已更新"}


@app.get("/config/llm/models")
def list_llm_models(base_url: Optional[str] = None):
    """列出 LMStudio 服务上的可用模型"""
    if base_url:
        url = base_url
    else:
        saved = get_config("llm_config", default=None)
        if isinstance(saved, dict):
            url = saved.get("base_url", Config.LMSTUDIO_BASE_URL)
        else:
            url = Config.LMSTUDIO_BASE_URL
    try:
        import httpx
        resp = httpx.get(f"{url}/api/tags", timeout=5.0)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return {
            "success": True,
            "models": [
                {"name": m["name"], "size": m.get("size", 0), "modified_at": m.get("modified_at", "")}
                for m in models
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"无法连接 LMStudio 服务: {str(e)}")


@app.get("/config/llm/status")
def check_llm_status():
    """检查 LLM 模型连接状态（使用轻量级 API，不消耗 GPU）"""
    try:
        from backend.services.llm_provider import get_global_provider
        provider = get_global_provider()
        import httpx
        if provider.provider_type == "openai_compatible":
            # LMStudio / OpenAI 兼容: 使用 /v1/models 轻量级检查
            headers = {}
            if provider._api_key:
                headers["Authorization"] = f"Bearer {provider._api_key}"
            resp = httpx.get(f"{provider._base_url}/v1/models", headers=headers, timeout=5.0)
            resp.raise_for_status()
        return {
            "success": True,
            "status": "connected",
            "provider": provider.provider_type,
            "model": provider.model_name,
        }
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "detail": str(e),
        }

@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "message": "OCR 实验服务运行中"
    }


@app.get("/config")
def get_system_config():
    """获取系统配置"""
    return {
        "success": True,
        "config": {
            "camera_count": Config.CAMERA_COUNT,
            "camera_control_host": Config.CAMERA_CONTROL_HOST,
            "camera_control_port": Config.CAMERA_CONTROL_PORT,
            "lmstudio_base_url": Config.LMSTUDIO_BASE_URL,
            "lmstudio_model": Config.LMSTUDIO_MODEL
        }
    }


# ==================== Multi-Instrument Pipeline API ====================

class ReadMultiRequest(BaseModel):
    image_path: Optional[str] = None
    camera_id: Optional[int] = None


@app.post("/api/read-multi")
def read_multi_instruments(body: ReadMultiRequest):
    """Multi-instrument reading endpoint.
    Detects, classifies, and reads all instruments in the image.
    """
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    from PIL import Image

    full_image_path = body.image_path

    if not full_image_path and body.camera_id is not None:
        mock_enabled = get_config("mock_camera_enabled", default=False)
        image_dir = get_config("image_dir", default=None) or None
        try:
            if mock_enabled:
                from backend.services.mock_camera import MockCameraClient
                client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir)
                success, result = client.capture_image()
            else:
                from backend.services.camera_control import CameraClient
                camera_config = Config.get_camera_config()
                if image_dir:
                    camera_config["image_dir"] = image_dir
                client = CameraClient(camera_id=body.camera_id, config=camera_config)
                success, result = client.capture_image()
        except Exception as e:
            logger.error(f"Camera {body.camera_id} capture failed: {e}")
            return {"success": False, "detections": [], "detail": f"Capture failed: {str(e)}"}

        if not success:
            return {"success": False, "detections": [], "detail": result.get("error", "Capture failed")}
        full_image_path = result.get("image_path")
        if not full_image_path:
            return {"success": False, "detections": [], "detail": "No image captured"}

    try:
        assert full_image_path is not None
        image = Image.open(full_image_path).convert("RGB")
    except Exception as e:
        return {"success": False, "detections": [], "detail": f"Cannot open image: {str(e)}"}

    try:
        pipeline = MultiInstrumentPipeline()
        detections = pipeline.process_image(image)
        return {"success": True, "detections": detections}
    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        return {"success": False, "detections": [], "detail": f"Processing failed: {str(e)}"}


@app.post("/api/rebuild-clip-cache")
def rebuild_clip_cache():
    """Rebuild CLIP embedding cache after template/reference image changes"""
    from backend.services.multi_instrument_pipeline import MultiInstrumentPipeline
    try:
        pipeline = MultiInstrumentPipeline()
        pipeline.rebuild_clip_cache()
        return {"success": True, "message": "CLIP cache rebuilt successfully"}
    except Exception as e:
        logger.error(f"Failed to rebuild CLIP cache: {e}")
        return {"success": False, "detail": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
