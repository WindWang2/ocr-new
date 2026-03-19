"""
OCR 仪表读数系统 - HTTP API 服务

基于 FastAPI，封装 TCP camera_service 为 REST API
"""

import os
import sys
import json
import base64
import socket
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import Config
from instrument_reader import InstrumentReader

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR 仪表读数系统",
    description="实验室仪器自动拍照识别 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 OCR 读取器
reader = InstrumentReader()

# ============ 数据模型 ============

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    instruments: List[Dict[str, Any]]  # [{camera_id: 0, type: "ph_meter", name: "pH计1"}, ...]

class ReadingResult(BaseModel):
    camera_id: int
    instrument_type: str
    values: Dict[str, Any]
    image_path: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: str

class CaptureRequest(BaseModel):
    camera_id: int

# ============ 存储 (后续可换数据库) ============

EXPERIMENTS_FILE = Path("data/experiments.json")
EXPERIMENTS_FILE.parent.mkdir(exist_ok=True)

def load_experiments() -> Dict:
    if EXPERIMENTS_FILE.exists():
        return json.loads(EXPERIMENTS_FILE.read_text())
    return {"experiments": {}, "readings": {}}

def save_experiments(data: Dict):
    EXPERIMENTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

# ============ API 端点 ============

@app.get("/")
async def root():
    return {"message": "OCR 仪表读数系统 API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ---- 相机控制 ----

@app.post("/api/camera/capture")
async def capture_photo(req: CaptureRequest):
    """触发指定相机拍照并返回读数"""
    try:
        # 调用 TCP 服务
        host = Config.CAMERA_CONFIG["control_host"]
        port = Config.CAMERA_CONFIG["control_port_base"] + req.camera_id
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        sock.sendall(f"{Config.CAMERA_CONFIG['trigger_prefix']},{req.camera_id}".encode())
        response = sock.recv(1024).decode().strip()
        sock.close()
        
        if "OK" not in response.upper():
            raise HTTPException(500, f"相机响应错误: {response}")
        
        # 等待图片生成并读取
        await asyncio.sleep(1)
        image_dir = Path(Config.CAMERA_CONFIG["image_dir"]) / f"camera_{req.camera_id}"
        images = sorted(image_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not images:
            raise HTTPException(404, "未找到拍摄的图片")
        
        latest_image = images[0]
        
        # OCR 识别
        result = reader.read_instrument(str(latest_image))
        
        return {
            "success": True,
            "camera_id": req.camera_id,
            "image_path": str(latest_image),
            "reading": result
        }
    except socket.timeout:
        raise HTTPException(504, "相机连接超时")
    except ConnectionRefusedError:
        raise HTTPException(503, "相机服务未启动")
    except Exception as e:
        logger.exception("拍照失败")
        raise HTTPException(500, str(e))

@app.post("/api/camera/upload")
async def upload_and_read(file: UploadFile = File(...)):
    """上传图片并 OCR 识别"""
    try:
        # 保存上传的图片
        content = await file.read()
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(exist_ok=True, parents=True)
        
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = upload_dir / filename
        filepath.write_bytes(content)
        
        # OCR 识别
        result = reader.read_instrument(str(filepath))
        
        return {
            "success": True,
            "image_path": str(filepath),
            "reading": result
        }
    except Exception as e:
        logger.exception("上传识别失败")
        raise HTTPException(500, str(e))

# ---- 仪器类型 ----

@app.get("/api/instruments/types")
async def get_instrument_types():
    """获取支持的仪器类型列表"""
    return {
        "types": [
            {"id": "electronic_balance", "name": "电子天平", "attributes": ["weight"]},
            {"id": "ph_meter", "name": "pH计", "attributes": ["ph_value", "temperature"]},
            {"id": "temperature_controller", "name": "恒温设备", "attributes": ["temperature"]},
            {"id": "peristaltic_pump", "name": "蠕动泵", "attributes": ["flow_rate", "rotation_speed"]},
            {"id": "water_quality_meter", "name": "水质检测仪", "attributes": ["test_value"]},
            {"id": "centrifuge", "name": "离心机", "attributes": ["rotation_speed", "time"]},
            {"id": "surface_tension_meter", "name": "表面张力仪", "attributes": ["surface_tension"]},
            {"id": "viscometer", "name": "粘度计", "attributes": ["viscosity"]},
        ]
    }

# ---- 实验管理 ----

@app.get("/api/experiments")
async def list_experiments():
    """列出所有实验"""
    data = load_experiments()
    return data["experiments"]

@app.post("/api/experiments")
async def create_experiment(exp: ExperimentCreate):
    """创建新实验"""
    data = load_experiments()
    exp_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    data["experiments"][exp_id] = {
        "id": exp_id,
        "name": exp.name,
        "description": exp.description,
        "instruments": exp.instruments,
        "created_at": datetime.now().isoformat(),
        "readings": []
    }
    
    save_experiments(data)
    return {"success": True, "id": exp_id, "experiment": data["experiments"][exp_id]}

@app.get("/api/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    """获取实验详情"""
    data = load_experiments()
    if exp_id not in data["experiments"]:
        raise HTTPException(404, "实验不存在")
    return data["experiments"][exp_id]

@app.post("/api/experiments/{exp_id}/reading")
async def add_reading(exp_id: str, reading: ReadingResult):
    """添加读数记录"""
    data = load_experiments()
    if exp_id not in data["experiments"]:
        raise HTTPException(404, "实验不存在")
    
    reading_dict = reading.dict()
    reading_dict["id"] = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    data["experiments"][exp_id]["readings"].append(reading_dict)
    save_experiments(data)
    
    return {"success": True, "reading": reading_dict}

@app.get("/api/experiments/{exp_id}/export")
async def export_experiment(exp_id: str):
    """导出实验数据为 CSV"""
    import csv
    from io import StringIO
    
    data = load_experiments()
    if exp_id not in data["experiments"]:
        raise HTTPException(404, "实验不存在")
    
    exp = data["experiments"][exp_id]
    
    # 生成 CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # 表头
    writer.writerow(["时间", "相机ID", "仪器类型", "数值"])
    
    for r in exp.get("readings", []):
        writer.writerow([
            r.get("timestamp", ""),
            r.get("camera_id", ""),
            r.get("instrument_type", ""),
            json.dumps(r.get("values", {}), ensure_ascii=False)
        ])
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={exp['name']}.csv"}
    )

# ---- 启动 ----

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
