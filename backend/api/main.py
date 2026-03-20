"""
OCR 实验 API 服务

功能：
1. 相机管理（增删改查）
2. 实验执行（触发单字段相机拍照并保存读数）
3. 实验记录查询

启动: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
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
    create_reading, get_readings_by_experiment,
)
from backend.services.camera_control import (
    CameraClient, get_all_enabled_cameras
)
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


class ExperimentCreate(BaseModel):
    name: str
    type: str  # kinematic_viscosity | apparent_viscosity | surface_tension
    manual_params: Optional[dict] = {}
    camera_configs: Optional[List[CameraConfigItem]] = []
    description: Optional[str] = None


class ExperimentRunField(BaseModel):
    field_key: str
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
    from backend.models.database import get_connection
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
    VALID_TYPES = {"kinematic_viscosity", "apparent_viscosity", "surface_tension"}
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

    # 调用相机拍照并 OCR
    # CameraClient.trigger_and_read() 返回 (success: bool, result: dict)
    # result 结构: {"camera_id", "raw_response", "reading"(OCR字符串), "timestamp", "success"}
    try:
        client = CameraClient(camera_id=body.camera_id)
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

    reading = create_reading(
        experiment_id=exp_id,
        field_key=body.field_key,
        camera_id=body.camera_id,
        value=value,
        run_index=run_index,
        confidence=None,   # trigger_and_read() 不返回置信度
        image_path=None,   # trigger_and_read() 不返回图片路径
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

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"experiment_{exp_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==================== 工具 API ====================

@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "message": "OCR 实验服务运行中"
    }


@app.get("/config")
def get_config():
    """获取系统配置"""
    return {
        "success": True,
        "config": {
            "camera_count": Config.CAMERA_COUNT,
            "camera_control_host": Config.CAMERA_CONTROL_HOST,
            "camera_control_port_base": Config.CAMERA_CONTROL_PORT_BASE,
            "ollama_base_url": Config.OLLAMA_BASE_URL,
            "ollama_model": Config.OLLAMA_QWEN_MODEL
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
