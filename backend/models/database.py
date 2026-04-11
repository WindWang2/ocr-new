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
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
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
    
    # DB 迁移管理
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT version FROM db_migrations ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    current_version = row["version"] if row else 0

    migrations = [
        # Version 1: Add new columns to experiments
        [
            "ALTER TABLE experiments ADD COLUMN type TEXT",
            "ALTER TABLE experiments ADD COLUMN manual_params TEXT",
            "ALTER TABLE experiments ADD COLUMN camera_configs TEXT"
        ]
    ]

    for i, stmts in enumerate(migrations):
        version = i + 1
        if current_version < version:
            for stmt in stmts:
                try:
                    cursor.execute(stmt)
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise e
            cursor.execute("INSERT INTO db_migrations (version) VALUES (?)", (version,))
            print(f"[DB] Applied migration v{version}")

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

    # 系统配置键值表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instrument_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instrument_type TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        prompt_template TEXT,
        fields_json TEXT NOT NULL,
        keywords_json TEXT NOT NULL,
        example_images_json TEXT,
        default_tier INTEGER DEFAULT 2,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

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


def create_experiment(
    name: str,
    exp_type: str,
    manual_params: dict = None,
    camera_configs: list = None,
    description: str = None,
) -> int:
    """创建实验记录，支持新的 type/manual_params/camera_configs 字段"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO experiments (name, description, type, manual_params, camera_configs, status, started_at)
           VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
        (
            name,
            description,
            exp_type,
            json.dumps(manual_params or {}, ensure_ascii=False),
            json.dumps(camera_configs or [], ensure_ascii=False),
            datetime.now().isoformat(),
        ),
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
    # 旧记录 type 可能为 NULL 或空字符串，回退到通用相机
    if not result.get("type"):
        result["type"] = "test"
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
    return [{**dict(row), "type": dict(row).get("type") or "test"} for row in rows]


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


def upsert_reading(
    experiment_id: int,
    field_key: str,
    camera_id: int,
    value: float,
    run_index: int,
    image_path: str = None,
) -> dict:
    """保存或更新读数（若该字段+槽位已存在则更新值，否则新增）"""
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now().isoformat()
    cursor.execute(
        """SELECT id FROM experiment_readings
           WHERE experiment_id=? AND field_key=? AND run_index=?""",
        (experiment_id, field_key, run_index),
    )
    row = cursor.fetchone()
    if row:
        if image_path:
            cursor.execute(
                "UPDATE experiment_readings SET value=?, camera_id=?, image_path=?, timestamp=? WHERE id=?",
                (value, camera_id, image_path, ts, row["id"]),
            )
        else:
            cursor.execute(
                "UPDATE experiment_readings SET value=?, camera_id=?, timestamp=? WHERE id=?",
                (value, camera_id, ts, row["id"]),
            )
        conn.commit()
        reading_id = row["id"]
        cursor.execute("SELECT * FROM experiment_readings WHERE id=?", (reading_id,))
        updated = dict(cursor.fetchone())
        conn.close()
        return updated
    else:
        conn.close()
        return create_reading(experiment_id, field_key, camera_id, value, run_index, image_path=image_path)


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


def get_config(key: str, default=None):
    """读取系统配置值"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return row["value"]


def set_config(key: str, value) -> None:
    """写入系统配置值"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)",
        (key, json.dumps(value)),
    )
    conn.commit()
    conn.close()


def get_all_templates() -> List[dict]:
    """获取所有仪器模板"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instrument_templates")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_template(instrument_type: str) -> Optional[dict]:
    """根据仪器类型获取指定的仪器模板"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instrument_templates WHERE instrument_type = ?", (instrument_type,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_template(
    instrument_type: str,
    name: str,
    description: str,
    prompt_template: str,
    fields: list,
    keywords: list,
    example_images: Optional[list] = None,
    default_tier: int = 2
) -> None:
    """插入或更新仪器模板记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO instrument_templates (instrument_type, name, description, prompt_template, fields_json, keywords_json, example_images_json, default_tier)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(instrument_type) DO UPDATE SET
        name=excluded.name,
        description=excluded.description,
        prompt_template=excluded.prompt_template,
        fields_json=excluded.fields_json,
        keywords_json=excluded.keywords_json,
        example_images_json=excluded.example_images_json,
        default_tier=excluded.default_tier
    ''', (instrument_type, name, description, prompt_template, json.dumps(fields), json.dumps(keywords), json.dumps(example_images or []), default_tier))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    # 测试添加相机
    add_camera("Camera 0", 0)
    add_camera("Camera 1", 1)
    add_camera("Camera 2", 2)
    print("测试相机:", get_cameras())
