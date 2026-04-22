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
            mode TEXT DEFAULT 'single',
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
        ],
        # Version 2: Add mode column to cameras for single/multi mode
        [
            "ALTER TABLE cameras ADD COLUMN mode TEXT DEFAULT 'single'"
        ],
        # Version 3: Add ocr_data column to experiment_readings
        [
            "ALTER TABLE experiment_readings ADD COLUMN ocr_data TEXT"
        ],
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
            ocr_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """)
    
    # 必须建立联合唯一索引，以支持 ON CONFLICT 语法
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_experiment_reading_unique 
        ON experiment_readings (experiment_id, field_key, run_index)
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

    seed_initial_data(conn)
    conn.commit()
    conn.close()
    print(f"[DB] 初始化完成: {DB_PATH}")


def seed_initial_data(conn):
    """预填充初始数据（如果表为空）"""
    cursor = conn.cursor()
    
    # 检查相机表
    cursor.execute("SELECT COUNT(*) FROM cameras")
    if cursor.fetchone()[0] == 0:
        logger.info("[DB] 正在预填充默认相机 (Camera 0-8)...")
        for i in range(0, 9):
            cursor.execute(
                "INSERT INTO cameras (name, camera_id, mode, enabled) VALUES (?, ?, ?, ?)",
                (f"Camera {i}", i, "single", 1)
            )
    
    # 检查模板表
    cursor.execute("SELECT COUNT(*) FROM instrument_templates")
    if cursor.fetchone()[0] == 0:
        logger.info("[DB] 正在预填充默认仪器模板...")
        templates = [
            {
                "type": "0", "name": "超级吴英混调度器", 
                "fields_json": json.dumps([
                    {"name": "mode", "label": "模式", "unit": ""},
                    {"name": "current_speed", "label": "当前转速", "unit": "转"},
                    {"name": "total_time", "label": "总时长", "unit": "S"},
                    {"name": "remaining_time", "label": "剩余时长", "unit": "S"},
                    {"name": "seg1_speed", "label": "段一转速", "unit": "转"},
                    {"name": "seg2_speed", "label": "段二转速", "unit": "转"},
                    {"name": "seg3_speed", "label": "段三转速", "unit": "转"}
                ]),
                "keywords_json": json.dumps(["mixer", "control", "吴英混"]),
                "prompt_template": """这是超级吴英混调器（SN: 258795）控制屏幕。请先判断当前是自动模式还是手动模式（看左侧菜单哪个选项高亮），然后读取对应数值。

自动模式字段：seg1_speed(段一转速,转)、seg1_time(段一时间,S)、seg2_speed(段二转速,转)、seg2_time(段二时间,S)、seg3_speed(段三转速,转)、seg3_time(段三时间,S)、total_time(总时长,S)、remaining_time(剩余时长,S)、current_segment(当前段数)、current_speed(当前转速,转)

手动模式：屏幕中间有一个表格，列标题为"转速(转)"和"时间(S)"，两行分别为"高速"和"低速"。从表格中读取：
- high_speed = "高速"行、"转速(转)"列的数字
- high_time = "高速"行、"时间(S)"列的数字
- low_speed = "低速"行、"转速(转)"列的数字
- low_time = "低速"行、"时间(S)"列的数字
表格下方还有：remaining_time(剩余时间,S)、current_speed(当前转速,转)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
自动模式：{"mode": "auto", "seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0}
手动模式：{"mode": "manual", "high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0}

只输出一行JSON，数值为纯数字不含单位，无法读取的值设为null。"""
            },
            {
                "type": "1", "name": "天平 1", 
                "fields_json": json.dumps([{"name": "weight", "label": "重量", "unit": "g"}]),
                "keywords_json": json.dumps(["balance", "weight", "scale"]),
                "prompt_template": """这是电子天枰1号（SN: 53662），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g，只输出纯数字不含单位。"""
            },
            {
                "type": "2", "name": "天平 2", 
                "fields_json": json.dumps([{"name": "weight", "label": "重量", "unit": "g"}]),
                "keywords_json": json.dumps(["balance", "weight", "scale"]),
                "prompt_template": """这是电子天枰2号（SN: 230199），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g，只输出纯数字不含单位。"""
            },
            {
                "type": "3", "name": "PH 仪", 
                "fields_json": json.dumps([
                    {"name": "ph_value", "label": "PH值", "unit": ""},
                    {"name": "temperature", "label": "温度", "unit": "°C"},
                    {"name": "pts", "label": "PTS", "unit": "%"}
                ]),
                "keywords_json": json.dumps(["ph", "meter", "acidity"]),
                "prompt_template": """这是PH仪（SN: 176585），读取屏幕上的三个数值：pH值(ph_value)、温度(temperature,°C,MTC)、PTS值(pts,%PTS)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"ph_value": 0.00, "temperature": 0.0, "pts": 0.0}

注意：pH值通常带2位小数，温度带1位小数，PTS通常为100.0。只输出一行JSON，数值不含单位，无法读取设为null。"""
            },
            {
                "type": "4", "name": "水质检测仪", 
                "fields_json": json.dumps([
                    {"name": "content_mg_l", "label": "含量", "unit": "mg/L"},
                    {"name": "transmittance", "label": "透光度", "unit": "%"},
                    {"name": "absorbance", "label": "吸光度", "unit": ""},
                    {"name": "test_value", "label": "检测值", "unit": ""},
                    {"name": "blank_value", "label": "空白值", "unit": ""}
                ]),
                "keywords_json": json.dumps(["water", "quality", "analyzer"]),
                "prompt_template": """这是水质检测仪（SN: 43373），检测总硬度。请先判断当前是高量程还是低量程模式，然后读取屏幕显示的所有数值。

读数字段：当前量程模式(mode)、检测日期(date)、空白值(blank_value)、检测值(test_value)、吸光度(absorbance)、含量mg/L(content_mg_l)、透光度%(transmittance)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"mode": "high", "date": "", "blank_value": 0, "test_value": 0, "absorbance": 0.000, "content_mg_l": 0.00, "transmittance": 0.0}

注意：mode字段为"high"（高量程）或"low"（低量程），date字段为字符串（格式xxxx-xx-xx xx:xx:xx），其他字段为数值，无法读取设为null。只输出一行JSON。"""
            },
            {
                "type": "5", "name": "表界面张力仪", 
                "fields_json": json.dumps([
                    {"name": "tension", "label": "张力值", "unit": "mN/m"},
                    {"name": "temperature", "label": "温度", "unit": "°C"},
                    {"name": "upper_density", "label": "上层密度", "unit": "g/cm3"},
                    {"name": "lower_density", "label": "下层密度", "unit": "g/cm3"},
                    {"name": "rise_speed", "label": "上升速度", "unit": "mm/min"},
                    {"name": "fall_speed", "label": "下降速度", "unit": "mm/min"}
                ]),
                "keywords_json": json.dumps(["tension", "meter", "surface"]),
                "prompt_template": """这是表界面张力仪（SN: 101663），读取屏幕上的六个数值：表/界面张力(tension,nN/m)、温度(temperature,°C)、上层密度(upper_density,g/cm3)、下层密度(lower_density,g/cm3)、上升速度(rise_speed,mm/min)、下降速度(fall_speed,mm/min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"tension": 0.000, "temperature": 0.0, "upper_density": 0.000, "lower_density": 0.000, "rise_speed": 0, "fall_speed": 0}

注意：张力通常带3位小数，可能为负数；温度若显示N/A则设为null；F值旁的-/+是按钮不是正负号。只输出一行JSON，数值不含单位。"""
            },
            {
                "type": "6", "name": "电动搅拌器", 
                "fields_json": json.dumps([
                    {"name": "rotation_speed", "label": "转速", "unit": "rpm"},
                    {"name": "torque", "label": "扭矩", "unit": "N/cm"},
                    {"name": "time", "label": "运行时间", "unit": ""}
                ]),
                "keywords_json": json.dumps(["stirrer", "electric", "mixer"]),
                "prompt_template": """这是电动搅拌器（SN: 208721），屏幕显示三行数值：第一行转速(rotation_speed,rpm)、第二行张力(torque,N/cm)、第三行时间(time,XX:XX)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"rotation_speed": 0, "torque": 0, "time": "00:00"}

注意：time字段保留MM:SS字符串格式；torque可能显示为00表示0N/cm。只输出一行JSON，数值不含单位。"""
            },
            {
                "type": "7", "name": "水浴锅", 
                "fields_json": json.dumps([
                    {"name": "temperature", "label": "温度", "unit": "°C"},
                    {"name": "time", "label": "时间", "unit": "min"}
                ]),
                "keywords_json": json.dumps(["water", "bath", "temp"]),
                "prompt_template": """这是水浴锅（SN: 37844），读取屏幕显示的温度(temperature,°C)和定时时间(time,min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"temperature": 0.0, "time": 0}

注意：TEMP标签下方为温度（通常带1位小数，LED数码管小数点很小，如"17.3"），TIME标签下方为时间（整数分钟）。只输出一行JSON，数值不含单位。"""
            },
            {
                "type": "8", "name": "6速旋转粘度计", 
                "fields_json": json.dumps([
                    {"name": "actual_reading", "label": "实时读数", "unit": ""},
                    {"name": "max_reading", "label": "最大读数", "unit": ""},
                    {"name": "min_reading", "label": "最小读数", "unit": ""},
                    {"name": "rotation_speed", "label": "转速", "unit": "RPM"},
                    {"name": "apparent_viscosity", "label": "粘度", "unit": "mPa·s"}
                ]),
                "keywords_json": json.dumps(["viscosity", "viscometer"]),
                "prompt_template": """这是6速旋转粘度计（SN: 106833），读取屏幕上的八个数值：实施读数(actual_reading)、最大读数(max_reading)、最小读数(min_reading)、转速(rotation_speed,RPM)、剪切速率(shear_rate,S-1)、剪切应力(shear_stress,Pa)、表观粘度(apparent_viscosity,mpa.s)、5秒平均值(avg_5s,mpa.s)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 0.000, "apparent_viscosity": 0.0, "avg_5s": 0.0}

只输出一行JSON，数值不含单位，无法读取设为null。"""
            }
        ]
        for t in templates:
            cursor.execute(
                "INSERT INTO instrument_templates (instrument_type, name, fields_json, keywords_json, prompt_template) VALUES (?, ?, ?, ?, ?)",
                (t["type"], t["name"], t["fields_json"], t["keywords_json"], t["prompt_template"])
            )


def add_camera(name: str, camera_id: int, control_host: str = "127.0.0.1",
               control_port: int = None, mode: str = 'single') -> int:
    """添加相机"""
    if control_port is None:
        control_port = 9000 + camera_id

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cameras (name, camera_id, control_host, control_port, mode) VALUES (?, ?, ?, ?, ?)",
        (name, camera_id, control_host, control_port, mode)
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
    ocr_data: dict = None,
) -> dict:
    """保存单次读数，返回完整读数记录"""
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now().isoformat()
    ocr_json = json.dumps(ocr_data, ensure_ascii=False) if ocr_data else None
    cursor.execute(
        """INSERT INTO experiment_readings
           (experiment_id, field_key, camera_id, value, run_index, confidence, image_path, timestamp, ocr_data)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(experiment_id, field_key, run_index) DO UPDATE SET
             value=excluded.value,
             camera_id=excluded.camera_id,
             confidence=excluded.confidence,
             image_path=excluded.image_path,
             timestamp=excluded.timestamp,
             ocr_data=excluded.ocr_data
        """,
        (experiment_id, field_key, camera_id, value, run_index, confidence, image_path, ts, ocr_json),
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
        "ocr_data": ocr_data,
    }


def upsert_reading(
    experiment_id: int,
    field_key: str,
    camera_id: int,
    value: float,
    run_index: int,
    image_path: str = None,
    ocr_data: dict = None,
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
        ocr_json = json.dumps(ocr_data, ensure_ascii=False) if ocr_data else None
        if image_path:
            cursor.execute(
                "UPDATE experiment_readings SET value=?, camera_id=?, image_path=?, timestamp=?, ocr_data=? WHERE id=?",
                (value, camera_id, image_path, ts, ocr_json, row["id"]),
            )
        else:
            cursor.execute(
                "UPDATE experiment_readings SET value=?, camera_id=?, timestamp=?, ocr_data=? WHERE id=?",
                (value, camera_id, ts, ocr_json, row["id"]),
            )
        conn.commit()
        reading_id = row["id"]
        cursor.execute("SELECT * FROM experiment_readings WHERE id=?", (reading_id,))
        updated = dict(cursor.fetchone())
        conn.close()
        return updated
    else:
        conn.close()
        return create_reading(experiment_id, field_key, camera_id, value, run_index, image_path=image_path, ocr_data=ocr_data)


def get_readings_by_experiment(experiment_id: int) -> List[dict]:
    """获取实验的所有读数，按 field_key + run_index 排序"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, experiment_id, field_key, camera_id, value, run_index, confidence, image_path, timestamp, ocr_data
           FROM experiment_readings
           WHERE experiment_id = ?
           ORDER BY field_key, run_index""",
        (experiment_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    
    readings = []
    for row in rows:
        r = dict(row)
        if r.get("ocr_data"):
            try:
                r["ocr_data"] = json.loads(r["ocr_data"])
            except:
                r["ocr_data"] = {}
        else:
            r["ocr_data"] = {}
        readings.append(r)
    return readings


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
