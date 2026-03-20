"""
数据库模型 - 实验表和相机关联
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


DB_PATH = Path(__file__).parent.parent / "experiments.db"


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 相机表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            camera_id INTEGER NOT NULL UNIQUE,
            control_host TEXT,
            control_port INTEGER,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 实验表 - 支持多相机关联
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            -- 单相机兼容: 关联相机ID (旧字段)
            camera_id INTEGER,
            -- 多相机: 关联的相机ID列表 (逗号分隔)
            camera_ids TEXT,
            -- 汇总的完整读数 (JSON格式)
            readings_json TEXT,
            -- 原始各相机读数 (JSON格式)
            raw_readings_json TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 迁移：为旧 experiments 表添加新列（幂等）
    for col_def in [
        "ALTER TABLE experiments ADD COLUMN type TEXT",
        "ALTER TABLE experiments ADD COLUMN manual_params TEXT",
        "ALTER TABLE experiments ADD COLUMN camera_configs TEXT",
    ]:
        try:
            cursor.execute(col_def)
        except Exception:
            pass  # 列已存在则忽略

    # 新增：每次读数独立记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            field_key TEXT NOT NULL,
            camera_id INTEGER NOT NULL,
            value REAL NOT NULL,
            run_index INTEGER NOT NULL DEFAULT 1,
            confidence REAL,
            image_path TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] 初始化完成: {DB_PATH}")


def add_camera(name: str, camera_id: int, control_host: str = "127.0.0.1", 
               control_port: int = None) -> int:
    """添加相机"""
    if control_port is None:
        control_port = 9000 + camera_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cameras (name, camera_id, control_host, control_port) VALUES (?, ?, ?, ?)",
        (name, camera_id, control_host, control_port)
    )
    conn.commit()
    camera_id_db = cursor.lastrowid
    conn.close()
    return camera_id_db


def get_cameras(enabled_only: bool = True) -> List[dict]:
    """获取相机列表"""
    conn = get_connection()
    cursor = conn.cursor()
    if enabled_only:
        cursor.execute("SELECT * FROM cameras WHERE enabled = 1 ORDER BY camera_id")
    else:
        cursor.execute("SELECT * FROM cameras ORDER BY camera_id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_camera_by_id(camera_id: int) -> Optional[dict]:
    """根据相机ID获取相机"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cameras WHERE camera_id = ?", (camera_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_experiment(name: str, description: str = None, 
                     camera_ids: List[int] = None, camera_id: int = None) -> int:
    """
    创建实验记录
    
    Args:
        name: 实验名称
        description: 实验描述
        camera_ids: 多相机模式 - 相机ID列表
        camera_id: 单相机模式 - 相机ID (兼容旧逻辑)
    
    Returns:
        实验ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 兼容旧逻辑：单相机模式
    camera_ids_str = None
    single_camera_id = None
    
    if camera_ids and len(camera_ids) > 1:
        # 多相机模式
        camera_ids_str = ",".join(map(str, camera_ids))
    elif camera_ids and len(camera_ids) == 1:
        # 单相机
        single_camera_id = camera_ids[0]
    elif camera_id:
        # 旧字段
        single_camera_id = camera_id
    
    cursor.execute(
        """INSERT INTO experiments (name, description, camera_id, camera_ids, status, started_at)
           VALUES (?, ?, ?, ?, 'running', ?)""",
        (name, description, single_camera_id, camera_ids_str, datetime.now().isoformat())
    )
    conn.commit()
    exp_id = cursor.lastrowid
    conn.close()
    return exp_id


def update_experiment_readings(exp_id: int, readings: dict, raw_readings: dict = None):
    """更新实验读数"""
    conn = get_connection()
    cursor = conn.cursor()
    
    readings_json = json.dumps(readings, ensure_ascii=False)
    raw_json = json.dumps(raw_readings, ensure_ascii=False) if raw_readings else None
    
    cursor.execute(
        """UPDATE experiments 
           SET readings_json = ?, raw_readings_json = ?, status = 'completed', completed_at = ?
           WHERE id = ?""",
        (readings_json, raw_json, datetime.now().isoformat(), exp_id)
    )
    conn.commit()
    conn.close()


def get_experiment(exp_id: int) -> Optional[dict]:
    """获取实验详情（含解析后的 manual_params/camera_configs 和所有 readings）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    try:
        result["manual_params"] = json.loads(result.get("manual_params") or "{}")
    except json.JSONDecodeError:
        logger.warning(f"实验 {exp_id} manual_params JSON 解析失败，使用空值")
        result["manual_params"] = {}
    try:
        result["camera_configs"] = json.loads(result.get("camera_configs") or "[]")
    except json.JSONDecodeError:
        logger.warning(f"实验 {exp_id} camera_configs JSON 解析失败，使用空值")
        result["camera_configs"] = []
    result["readings"] = get_readings_by_experiment(exp_id)
    return result


def list_experiments(limit: int = 50, offset: int = 0) -> List[dict]:
    """获取实验列表（摘要：id/name/type/created_at，不含 readings）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, type, created_at FROM experiments ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_experiment(exp_id: int) -> bool:
    """删除实验"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def create_reading(
    experiment_id: int,
    field_key: str,
    camera_id: int,
    value: float,
    run_index: int,
    confidence: float = None,
    image_path: str = None,
) -> dict:
    """保存单次读数，返回完整读数记录"""
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now().isoformat()
    cursor.execute(
        """INSERT INTO experiment_readings
           (experiment_id, field_key, camera_id, value, run_index, confidence, image_path, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (experiment_id, field_key, camera_id, value, run_index, confidence, image_path, ts),
    )
    conn.commit()
    reading_id = cursor.lastrowid
    conn.close()
    return {
        "id": reading_id,
        "field_key": field_key,
        "camera_id": camera_id,
        "value": value,
        "run_index": run_index,
        "confidence": confidence,
        "image_path": image_path,
        "timestamp": ts,
    }


def get_readings_by_experiment(experiment_id: int) -> List[dict]:
    """获取实验的所有读数，按 field_key + run_index 排序"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, experiment_id, field_key, camera_id, value, run_index, confidence, image_path, timestamp
           FROM experiment_readings
           WHERE experiment_id = ?
           ORDER BY field_key, run_index""",
        (experiment_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    # 测试添加相机
    add_camera("Camera 0", 0)
    add_camera("Camera 1", 1)
    add_camera("Camera 2", 2)
    print("测试相机:", get_cameras())
