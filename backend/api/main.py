"""
OCR 实验 API 服务

功能：
1. 相机管理（增删改查）
2. 实验执行（触发多相机拍照并汇总读数）
3. 实验记录查询

启动: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import json
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.database import (
    init_db, add_camera, get_cameras, get_camera_by_id,
    create_experiment, update_experiment_readings, 
    get_experiment, list_experiments, delete_experiment
)
from backend.services.camera_control import (
    CameraClient, MultiCameraController, get_all_enabled_cameras
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


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    camera_ids: Optional[List[int]] = None  # 多相机模式
    camera_id: Optional[int] = None  # 单相机模式（兼容）


class ExperimentRun(BaseModel):
    experiment_id: int


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
    offset: int = Query(0, ge=0)
):
    """获取实验列表"""
    experiments = list_experiments(limit=limit, offset=offset)
    return {"success": True, "count": len(experiments), "experiments": experiments}


@app.get("/experiments/{exp_id}")
def get_experiment_api(exp_id: int):
    """获取实验详情"""
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    return {"success": True, "experiment": experiment}


@app.post("/experiments")
def create_experiment_api(exp: ExperimentCreate):
    """创建实验记录"""
    try:
        exp_id = create_experiment(
            name=exp.name,
            description=exp.description,
            camera_ids=exp.camera_ids,
            camera_id=exp.camera_id
        )
        return {"success": True, "experiment_id": exp_id, "message": "实验创建成功"}
    except Exception as e:
        logger.error(f"创建实验失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/experiments/{exp_id}/run")
def run_experiment_api(exp_id: int):
    """
    执行实验 - 触发关联相机拍照并汇总读数
    
    多相机：依次向所有关联相机发送拍照指令，获取读数，汇总
    单相机：兼容原有逻辑
    """
    # 1. 获取实验记录
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    # 2. 确定要使用的相机
    camera_ids = experiment.get("camera_id_list")
    single_camera_id = experiment.get("camera_id")
    
    if not camera_ids and single_camera_id:
        # 单相机兼容模式
        camera_ids = [single_camera_id]
    
    if not camera_ids:
        # 如果没有指定相机，使用所有已启用的相机
        camera_ids = get_all_enabled_cameras()
        if not camera_ids:
            raise HTTPException(status_code=400, detail="没有可用的相机")
    
    logger.info(f"实验 {exp_id} 执行，使用相机: {camera_ids}")
    
    # 3. 执行多相机实验
    controller = MultiCameraController(camera_ids)
    result = controller.run_experiment()
    
    # 4. 更新实验记录
    update_experiment_readings(
        exp_id=exp_id,
        readings=result["summary"],
        raw_readings=result["raw_readings"]
    )
    
    # 5. 返回完整结果
    return {
        "success": True,
        "experiment_id": exp_id,
        "camera_ids": camera_ids,
        "results": result["results"],
        "summary": result["summary"]
    }


@app.delete("/experiments/{exp_id}")
def delete_experiment_api(exp_id: int):
    """删除实验记录"""
    deleted = delete_experiment(exp_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="实验不存在")
    return {"success": True, "message": "实验已删除"}


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
