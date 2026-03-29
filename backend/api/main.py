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
import openpyxl
from openpyxl.styles import Font
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
)
from backend.services.camera_control import (
    CameraClient, get_all_enabled_cameras
)
from backend.services.mock_camera import MockCameraClient
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件：挂载图片目录，供前端访问拍照图片
_images_dir = Path("camera_images")
_images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")


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
    save_name = f"{run_index:03d}.jpg"
    save_path = save_dir / save_name
    img.save(str(save_path), "JPEG", quality=85)

    # 返回相对路径
    relative = f"F{camera_id}/{save_name}"
    logger.info(f"图片已保存: {save_path} ({img.size[0]}x{img.size[1]})")
    return relative


# ==================== 请求模型 ====================

class CameraCreate(BaseModel):
    name: str
    camera_id: int
    control_host: Optional[str] = "127.0.0.1"
    control_port: Optional[int] = None


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
            control_port=camera.control_port
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
        client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir) if mock_enabled else CameraClient(camera_id=body.camera_id)
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
            client = CameraClient(camera_id=body.camera_id)
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
            client = MockCameraClient(camera_id=body.camera_id, image_dir=image_dir) if mock_enabled else CameraClient(camera_id=body.camera_id)
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
        from instrument_reader import InstrumentReader
        from backend.services.llm_provider import get_global_provider
        reader = InstrumentReader(provider=get_global_provider())
        ocr_result = reader.read_instrument(full_image_path)
    except Exception as e:
        logger.error(f"OCR 失败: {e}")
        return {"success": False, "detail": f"OCR 识别失败: {e}"}

    if not ocr_result.get("success"):
        return {"success": False, "detail": ocr_result.get("error", "OCR 识别失败")}

    # 存储所有 OCR 读数
    raw_response = ocr_result.get("readings", {})
    try:
        readings_dict = json.loads(str(raw_response)) if raw_response else {}
    except (json.JSONDecodeError, TypeError):
        readings_dict = raw_response if isinstance(raw_response, dict) else {}

    all_readings = []
    for key, value in readings_dict.items():
        try:
            str_val = str(value).strip()
            # time 字段可能是 "MM:SS" 格式，转为秒数（float）
            if key == "time" and ":" in str_val:
                parts = str_val.split(":")
                if len(parts) == 2:
                    float_val = float(parts[0]) * 60 + float(parts[1])
                else:
                    continue
            else:
                float_val = float(str_val)
        except (ValueError, TypeError):
            continue
        existing = [r for r in experiment["readings"] if r["field_key"] == key]
        run_index = len(existing) + 1
        reading = create_reading(
            experiment_id=exp_id,
            field_key=key,
            camera_id=body.camera_id,
            value=float_val,
            run_index=run_index,
            confidence=ocr_result.get("confidence"),
            image_path=saved_image_path,
        )
        all_readings.append(reading)

    return {"success": True, "readings": all_readings}


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
    """导出实验数据为 xlsx，按实验类型生成对应模板格式"""
    # openpyxl, io, StreamingResponse 均已在模块顶部导入

    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    wb = openpyxl.Workbook()
    ws = wb.active
    exp_type = experiment.get("type", "")
    readings = experiment.get("readings", [])
    manual = experiment.get("manual_params", {})

    def cell(row, col, value, bold=False):
        c = ws.cell(row=row, column=col, value=value)
        if bold:
            c.font = Font(bold=True)
        return c

    ws.title = experiment["name"][:31]  # xlsx sheet name limit

    if exp_type == "kinematic_viscosity":
        cell(1, 1, "运动粘度检验记录", bold=True)
        cell(2, 1, f"实验名称: {experiment['name']}")
        cell(3, 1, f"温度设置: {manual.get('temperature_set','')} ℃")
        cell(3, 3, f"最高温度: {manual.get('temperature_max','')} ℃")
        cell(3, 5, f"最低温度: {manual.get('temperature_min','')} ℃")
        cell(4, 1, f"毛细管系数 C: {manual.get('capillary_coeff','')} mm²/s²")
        cell(6, 1, "实验次数", bold=True)
        cell(6, 2, "流经时间 t(s)", bold=True)
        ft_readings = [r for r in readings if r["field_key"] == "flow_time"]
        for i, r in enumerate(ft_readings, start=1):
            cell(6 + i, 1, f"实验{i}")
            cell(6 + i, 2, r["value"])
        if ft_readings:
            avg = sum(r["value"] for r in ft_readings) / len(ft_readings)
            coeff = float(manual.get("capillary_coeff", 0))
            cell(6 + len(ft_readings) + 1, 1, "平均流经时间 τ", bold=True)
            cell(6 + len(ft_readings) + 1, 2, round(avg, 4))
            cell(6 + len(ft_readings) + 2, 1, "运动粘度 ν (mm²/s)", bold=True)
            cell(6 + len(ft_readings) + 2, 2, round(coeff * avg, 4))

    elif exp_type == "apparent_viscosity":
        cell(1, 1, "表观黏度检测记录", bold=True)
        cell(2, 1, f"实验名称: {experiment['name']}")
        cell(4, 1, "实验次数", bold=True)
        cell(4, 2, "3rpm", bold=True)
        cell(4, 3, "6rpm", bold=True)
        cell(4, 4, "100rpm (α)", bold=True)
        cell(4, 5, "表观黏度 η (mPa·s)", bold=True)
        for run_idx in [1, 2]:
            row = 4 + run_idx
            rpm3 = next((r["value"] for r in readings if r["field_key"] == "rpm3" and r["run_index"] == run_idx), "")
            rpm6 = next((r["value"] for r in readings if r["field_key"] == "rpm6" and r["run_index"] == run_idx), "")
            rpm100 = next((r["value"] for r in readings if r["field_key"] == "rpm100" and r["run_index"] == run_idx), "")
            eta = round((rpm100 * 5.077) / 1.704, 4) if rpm100 != "" else ""
            cell(row, 1, f"实验{run_idx}")
            cell(row, 2, rpm3)
            cell(row, 3, rpm6)
            cell(row, 4, rpm100)
            cell(row, 5, eta)
        all_eta = [(r["value"] * 5.077) / 1.704 for r in readings if r["field_key"] == "rpm100"]
        if all_eta:
            cell(7, 1, "平均表观黏度 (mPa·s)", bold=True)
            cell(7, 5, round(sum(all_eta) / len(all_eta), 4))

    elif exp_type == "surface_tension":
        cell(1, 1, "表面张力和界面张力检测记录", bold=True)
        cell(2, 1, f"实验名称: {experiment['name']}")
        cell(3, 1, f"室内温度: {manual.get('room_temperature','')} ℃")
        cell(3, 3, f"室内湿度: {manual.get('room_humidity','')} %")
        cell(4, 1, f"样品密度(25℃): {manual.get('sample_density','')} g/cm³")
        cell(4, 3, f"煤油密度(25℃): {manual.get('kerosene_density','')} g/cm³")
        cell(6, 1, "纯水表面张力 (mN/m)", bold=True)
        wst = next((r["value"] for r in readings if r["field_key"] == "water_surface_tension"), "")
        cell(6, 2, wst)
        cell(8, 1, "破胶液表面张力", bold=True)
        cell(9, 1, "实验次数", bold=True)
        cell(9, 2, "表面张力 (mN/m)", bold=True)
        fst = [r for r in readings if r["field_key"] == "fluid_surface_tension"]
        for i, r in enumerate(fst, start=1):
            cell(9 + i, 1, f"实验{i}")
            cell(9 + i, 2, r["value"])
        if fst:
            cell(9 + len(fst) + 1, 1, "算术平均值", bold=True)
            cell(9 + len(fst) + 1, 2, round(sum(r["value"] for r in fst) / len(fst), 4))
        base = 9 + len(fst) + 3
        cell(base, 1, "破胶液界面张力", bold=True)
        cell(base + 1, 1, "实验次数", bold=True)
        cell(base + 1, 2, "界面张力 (mN/m)", bold=True)
        fit = [r for r in readings if r["field_key"] == "fluid_interface_tension"]
        for i, r in enumerate(fit, start=1):
            cell(base + 1 + i, 1, f"实验{i}")
            cell(base + 1 + i, 2, r["value"])
        if fit:
            cell(base + 1 + len(fit) + 1, 1, "算术平均值", bold=True)
            cell(base + 1 + len(fit) + 1, 2, round(sum(r["value"] for r in fit) / len(fit), 4))

    elif exp_type == "test":
        cell(1, 1, "测试模板拍照记录", bold=True)
        cell(2, 1, f"实验名称: {experiment['name']}")
        row = 4
        cell(row, 1, "相机", bold=True)
        cell(row, 2, "读数项", bold=True)
        cell(row, 3, "序号", bold=True)
        cell(row, 4, "读数值", bold=True)
        cell(row, 5, "时间", bold=True)
        for cam_id in range(9):
            field_key = f"F{cam_id}"
            cam_readings = [r for r in readings if r["camera_id"] == cam_id]
            if cam_readings:
                row += 1
                cell(row, 1, field_key, bold=True)
                for i, r in enumerate(cam_readings, start=1):
                    cell(row + i, 2, r["field_key"])
                    cell(row + i, 3, i)
                    cell(row + i, 4, r["value"])
                    cell(row + i, 5, r["timestamp"][:19])
                row += len(cam_readings)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
