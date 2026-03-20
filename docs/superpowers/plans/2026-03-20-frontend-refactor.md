# 前端重构实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 OCR 仪表读数系统前端，支持三种实验类型（运动粘度、表观黏度、表面张力和界面张力），通过两步向导创建实验，执行时按模板结构显示相机读数字段。

**Architecture:** 前端用 Next.js + Tailwind，按实验类型驱动字段渲染；后端在现有 FastAPI + SQLite 基础上新增 `type`/`manual_params`/`camera_configs` 字段和独立 `experiment_readings` 表，新增单字段拍照接口和 xlsx 导出接口。

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS, lucide-react, FastAPI, SQLite, openpyxl

**Spec:** `docs/superpowers/specs/2026-03-20-frontend-refactor-design.md`

---

## 文件映射

### 后端（修改）
| 文件 | 变更 |
|------|------|
| `backend/models/database.py` | 新增 `experiment_readings` 表；`experiments` 表加 `type`/`manual_params`/`camera_configs` 列；新增 `create_reading`/`get_readings_by_experiment` 函数；修改 `get_experiment`/`list_experiments` |
| `backend/api/main.py` | 更新 `ExperimentCreate` 模型；修改 POST/GET experiments；改造 POST `/run`（单字段拍照）；新增 GET `/export` |
| `requirements.txt` | 新增 `openpyxl>=3.1.0` |

### 前端（全新）
| 文件 | 职责 |
|------|------|
| `frontend/src/types/index.ts` | 所有 TypeScript 类型定义 |
| `frontend/src/lib/experimentTypes.ts` | 三种实验类型的字段 schema（fieldKey、maxReadings、手动参数定义） |
| `frontend/src/lib/calculations.ts` | 三种类型的公式计算函数 |
| `frontend/src/lib/api.ts` | 所有 API 调用封装 |
| `frontend/src/components/ExperimentList.tsx` | 左侧实验列表 |
| `frontend/src/components/CreateExperiment/Step1TypeSelector.tsx` | 创建向导步骤1：名称+类型选择 |
| `frontend/src/components/CreateExperiment/Step2Config.tsx` | 创建向导步骤2：手动参数+相机绑定 |
| `frontend/src/components/ExperimentDetail/ReadingField.tsx` | 单个相机读数字段卡片 |
| `frontend/src/components/ExperimentDetail/ResultSummary.tsx` | 底部自动计算结果汇总 |
| `frontend/src/components/ExperimentDetail/index.tsx` | 执行主视图（按类型分发） |
| `frontend/src/components/experiments/KinematicViscosity.tsx` | 运动粘度执行视图 |
| `frontend/src/components/experiments/ApparentViscosity.tsx` | 表观黏度执行视图 |
| `frontend/src/components/experiments/SurfaceTension.tsx` | 表面张力执行视图 |
| `frontend/src/app/page.tsx` | 主页面骨架（重写） |

---

## Chunk 1: 后端数据库与 API

### Task 1: 数据库迁移与新增读数表

**Files:**
- Modify: `backend/models/database.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 在 `requirements.txt` 中添加 openpyxl**

```
openpyxl>=3.1.0
```

- [ ] **Step 2: 修改 `init_db()` — 为 experiments 表新增列，创建 experiment_readings 表**

在 `database.py` 的 `init_db()` 函数中，在现有 `experiments` 表 CREATE 语句**之后**追加以下代码（`conn.commit()` 之前）：

```python
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
```

- [ ] **Step 3: 新增 `create_reading()` 函数**

在 `database.py` 末尾添加：

```python
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
        """SELECT * FROM experiment_readings
           WHERE experiment_id = ?
           ORDER BY field_key, run_index""",
        (experiment_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

- [ ] **Step 4: 修改 `create_experiment()` — 接收 type/manual_params/camera_configs**

将现有 `create_experiment` 函数签名改为：

```python
def create_experiment(
    name: str,
    exp_type: str,
    manual_params: dict = None,
    camera_configs: list = None,
    description: str = None,
) -> int:
    import json
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
```

- [ ] **Step 5: 修改 `get_experiment()` — 包含 readings + 解析新字段**

将现有 `get_experiment` 函数替换为：

```python
def get_experiment(exp_id: int) -> Optional[dict]:
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["manual_params"] = json.loads(result.get("manual_params") or "{}")
    result["camera_configs"] = json.loads(result.get("camera_configs") or "[]")
    result["readings"] = get_readings_by_experiment(exp_id)
    return result
```

- [ ] **Step 6: 修改 `list_experiments()` — 返回摘要（不含 readings）**

将现有 `list_experiments` 函数替换为：

```python
def list_experiments(limit: int = 50, offset: int = 0) -> List[dict]:
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, type, created_at FROM experiments ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

- [ ] **Step 7: 手动验证数据库迁移**

```bash
cd /home/kevin/github/ocr-new
python3 -c "from backend.models.database import init_db; init_db(); print('OK')"
```

期望输出：`[DB] 初始化完成: ...experiments.db` 且无报错

> ⚠️ **原子提交注意**：Task 1 Step 4（`create_experiment` 签名变更）必须与 Task 2 Step 3（API handler 更新）一起提交，否则中间状态会导致运行时 `TypeError`。完成 Task 2 Step 3 后，用 Task 2 Step 9 一次性提交两个文件。**本步骤（Step 8）只提交其余内容：**

- [ ] **Step 8: Commit（不含 create_experiment 签名变更）**

```bash
git add backend/models/database.py requirements.txt
git commit -m "feat(db): 新增 experiment_readings 表，新增 create_reading/get_readings_by_experiment 函数，experiments 加 type/manual_params/camera_configs 列"
```

---

### Task 2: 更新后端 API 接口

**Files:**
- Modify: `backend/api/main.py`

- [ ] **Step 1: 更新顶部 import，添加新数据库函数和导出依赖**

在 `main.py` 的顶部 import 区域作如下修改：

```python
# 原有 fastapi 导入行，追加 StreamingResponse
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# 新增标准库导入
import io
import openpyxl
from openpyxl.styles import Font

# 数据库函数（追加 create_reading, get_readings_by_experiment；移除 update_experiment_readings，Step 6 替换后不再使用）
from backend.models.database import (
    init_db, add_camera, get_cameras, get_camera_by_id,
    create_experiment,
    get_experiment, list_experiments, delete_experiment,
    create_reading, get_readings_by_experiment,
)
```

- [ ] **Step 2: 替换 `ExperimentCreate` 请求模型**

将现有 `ExperimentCreate` 类替换为：

```python
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
```

- [ ] **Step 3: 更新 `POST /experiments` 接口**

将现有 `create_experiment_api` 函数替换为：

```python
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
```

- [ ] **Step 4: 更新 `GET /experiments/{id}` 接口**

```python
@app.get("/experiments/{exp_id}")
def get_experiment_api(exp_id: int):
    """获取实验详情（含所有读数）"""
    experiment = get_experiment(exp_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    return {"success": True, "experiment": experiment}
```

- [ ] **Step 5: 更新 `GET /experiments` 接口**

```python
@app.get("/experiments")
def list_experiments_api(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """获取实验列表（摘要，不含读数）"""
    experiments = list_experiments(limit=limit, offset=offset)
    return {"success": True, "count": len(experiments), "experiments": experiments}
```

- [ ] **Step 6: 改造 `POST /experiments/{id}/run` — 单字段拍照**

将现有 `run_experiment_api` 替换为：

```python
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
```

- [ ] **Step 7: 新增 `GET /experiments/{id}/export` 接口**

```python
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
```

- [ ] **Step 8: 手动测试后端**

启动后端：
```bash
cd /home/kevin/github/ocr-new
uvicorn backend.api.main:app --port 8001 --reload
```

在另一个终端测试：
```bash
# 创建实验
curl -s -X POST http://localhost:8001/experiments \
  -H "Content-Type: application/json" \
  -d '{"name":"测试-运动粘度","type":"kinematic_viscosity","manual_params":{"temperature_set":25,"capillary_coeff":0.5},"camera_configs":[{"field_key":"flow_time","camera_id":0,"max_readings":4}]}' | python3 -m json.tool

# 获取列表
curl -s http://localhost:8001/experiments | python3 -m json.tool

# 获取详情（替换 1 为实际 id）
curl -s http://localhost:8001/experiments/1 | python3 -m json.tool
```

期望：创建返回 `{"success": true, "experiment_id": N}`；列表返回摘要；详情包含 `type`、`manual_params`、`camera_configs`、`readings`。

- [ ] **Step 9: Atomic Commit（同时提交 database.py 的 create_experiment 签名变更 + main.py 的全部改动）**

```bash
git add backend/api/main.py backend/models/database.py
git commit -m "feat(api+db): 更新实验接口和 create_experiment 签名，改造单字段拍照接口，新增 xlsx 导出"
```

---

## Chunk 2: 前端基础层（类型 + 工具库 + API）

### Task 3: TypeScript 类型定义

**Files:**
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建类型文件**

```bash
mkdir -p /home/kevin/github/ocr-new/frontend/src/types
```

创建 `frontend/src/types/index.ts`：

```typescript
export type ExperimentType =
  | 'kinematic_viscosity'
  | 'apparent_viscosity'
  | 'surface_tension'

export interface CameraFieldConfig {
  field_key: string
  camera_id: number
  max_readings: number
}

export interface ManualParams {
  [key: string]: number | string
}

export interface Reading {
  id: number
  field_key: string
  camera_id: number
  value: number
  run_index: number
  confidence?: number
  image_path?: string
  timestamp: string
}

export interface Experiment {
  id: number
  name: string
  type: ExperimentType
  manual_params: ManualParams
  camera_configs: CameraFieldConfig[]
  readings: Reading[]
  created_at: string
}

export interface ExperimentSummary {
  id: number
  name: string
  type: ExperimentType
  created_at: string
}

export interface ExperimentViewProps {
  experiment: Experiment
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>
  capturing: string | null
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(frontend): 添加 TypeScript 类型定义"
```

---

### Task 4: 实验类型 Schema

**Files:**
- Create: `frontend/src/lib/experimentTypes.ts`

- [ ] **Step 1: 创建 experimentTypes.ts**

```bash
mkdir -p /home/kevin/github/ocr-new/frontend/src/lib
```

创建 `frontend/src/lib/experimentTypes.ts`：

```typescript
import { ExperimentType } from '@/types'

export interface ManualParamDef {
  key: string
  label: string
  unit: string
  type: 'number' | 'text'
}

export interface CameraFieldDef {
  fieldKey: string
  label: string
  unit: string
  maxReadings: number
}

export interface ExperimentSchema {
  type: ExperimentType
  label: string
  description: string
  icon: string          // lucide-react 图标名或 emoji 占位
  manualParams: ManualParamDef[]
  cameraFields: CameraFieldDef[]
}

export const EXPERIMENT_SCHEMAS: Record<ExperimentType, ExperimentSchema> = {
  kinematic_viscosity: {
    type: 'kinematic_viscosity',
    label: '运动粘度',
    description: '品氏毛细管粘度计，测量液体流经时间，计算运动粘度 ν',
    icon: '🧪',
    manualParams: [
      { key: 'temperature_set', label: '温度设置', unit: '℃', type: 'number' },
      { key: 'temperature_max', label: '最高温度', unit: '℃', type: 'number' },
      { key: 'temperature_min', label: '最低温度', unit: '℃', type: 'number' },
      { key: 'capillary_coeff', label: '毛细管系数 C', unit: 'mm²/s²', type: 'number' },
    ],
    cameraFields: [
      { fieldKey: 'flow_time', label: '流经时间 t', unit: 's', maxReadings: 4 },
    ],
  },
  apparent_viscosity: {
    type: 'apparent_viscosity',
    label: '表观黏度',
    description: '旋转粘度计，三种转速读数，计算表观黏度 η',
    icon: '🔄',
    manualParams: [],
    cameraFields: [
      { fieldKey: 'rpm3', label: '3rpm 读数', unit: '', maxReadings: 2 },
      { fieldKey: 'rpm6', label: '6rpm 读数', unit: '', maxReadings: 2 },
      { fieldKey: 'rpm100', label: '100rpm 读数 (α)', unit: '', maxReadings: 2 },
    ],
  },
  surface_tension: {
    type: 'surface_tension',
    label: '表面张力和界面张力',
    description: '铂金环法，测量表面张力和界面张力',
    icon: '💧',
    manualParams: [
      { key: 'room_temperature', label: '室内温度', unit: '℃', type: 'number' },
      { key: 'room_humidity', label: '室内湿度', unit: '%', type: 'number' },
      { key: 'sample_density', label: '样品密度 (25℃)', unit: 'g/cm³', type: 'number' },
      { key: 'kerosene_density', label: '煤油密度 (25℃)', unit: 'g/cm³', type: 'number' },
    ],
    cameraFields: [
      { fieldKey: 'water_surface_tension', label: '纯水表面张力', unit: 'mN/m', maxReadings: 1 },
      { fieldKey: 'fluid_surface_tension', label: '破胶液表面张力', unit: 'mN/m', maxReadings: 5 },
      { fieldKey: 'fluid_interface_tension', label: '破胶液界面张力', unit: 'mN/m', maxReadings: 2 },
    ],
  },
}

export const EXPERIMENT_TYPE_LIST = Object.values(EXPERIMENT_SCHEMAS)
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/experimentTypes.ts
git commit -m "feat(frontend): 添加实验类型 schema 定义"
```

---

### Task 5: 计算函数与 API 封装

**Files:**
- Create: `frontend/src/lib/calculations.ts`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 1: 创建 `calculations.ts`**

```typescript
// frontend/src/lib/calculations.ts
import { Reading, ManualParams } from '@/types'

export interface KinematicResult {
  avgTime: number | null      // τ
  viscosity: number | null    // ν = C × τ
}

export interface ApparentResult {
  run1: number | null         // η₁
  run2: number | null         // η₂
  average: number | null
}

export interface SurfaceResult {
  surfaceAvg: number | null   // 表面张力均值
  interfaceAvg: number | null // 界面张力均值
}

export function calcKinematic(readings: Reading[], params: ManualParams): KinematicResult {
  const times = readings.filter(r => r.field_key === 'flow_time').map(r => r.value)
  if (times.length === 0) return { avgTime: null, viscosity: null }
  const avgTime = times.reduce((a, b) => a + b, 0) / times.length
  const C = Number(params.capillary_coeff) || 0
  return {
    avgTime: round4(avgTime),
    viscosity: C > 0 ? round4(C * avgTime) : null,
  }
}

export function calcApparent(readings: Reading[]): ApparentResult {
  const eta = (runIndex: number): number | null => {
    const r = readings.find(r => r.field_key === 'rpm100' && r.run_index === runIndex)
    if (!r) return null
    return round4((r.value * 5.077) / 1.704)
  }
  const r1 = eta(1)
  const r2 = eta(2)
  const average = r1 !== null && r2 !== null ? round4((r1 + r2) / 2) : null
  return { run1: r1, run2: r2, average }
}

export function calcSurface(readings: Reading[]): SurfaceResult {
  const fst = readings.filter(r => r.field_key === 'fluid_surface_tension').map(r => r.value)
  const fit = readings.filter(r => r.field_key === 'fluid_interface_tension').map(r => r.value)
  return {
    surfaceAvg: fst.length > 0 ? round4(fst.reduce((a, b) => a + b, 0) / fst.length) : null,
    interfaceAvg: fit.length > 0 ? round4(fit.reduce((a, b) => a + b, 0) / fit.length) : null,
  }
}

function round4(n: number): number {
  return Math.round(n * 10000) / 10000
}
```

- [ ] **Step 2: 创建 `api.ts`**

```typescript
// frontend/src/lib/api.ts
import { Experiment, ExperimentSummary, Reading, CameraFieldConfig, ManualParams, ExperimentType } from '@/types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function listExperiments(): Promise<ExperimentSummary[]> {
  const data = await request<{ experiments: ExperimentSummary[] }>('/experiments')
  return data.experiments
}

export async function getExperiment(id: number): Promise<Experiment> {
  const data = await request<{ experiment: Experiment }>(`/experiments/${id}`)
  return data.experiment
}

export async function createExperiment(payload: {
  name: string
  type: ExperimentType
  manual_params: ManualParams
  camera_configs: CameraFieldConfig[]
}): Promise<number> {
  const data = await request<{ experiment_id: number }>('/experiments', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  return data.experiment_id
}

export async function captureReading(
  experimentId: number,
  fieldKey: string,
  cameraId: number,
): Promise<Reading> {
  const data = await request<{ success: boolean; reading?: Reading; detail?: string }>(
    `/experiments/${experimentId}/run`,
    {
      method: 'POST',
      body: JSON.stringify({ field_key: fieldKey, camera_id: cameraId }),
    },
  )
  if (!data.success) throw new Error(data.detail || 'OCR 识别失败')
  return data.reading!
}

export function exportUrl(experimentId: number): string {
  return `${BASE}/experiments/${experimentId}/export`
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/calculations.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): 添加计算函数和 API 封装"
```

---

## Chunk 3: 前端组件

### Task 6: ExperimentList 组件

**Files:**
- Create: `frontend/src/components/ExperimentList.tsx`

- [ ] **Step 1: 创建 ExperimentList 组件**

```bash
mkdir -p /home/kevin/github/ocr-new/frontend/src/components
```

创建 `frontend/src/components/ExperimentList.tsx`：

```tsx
'use client'
import { ExperimentSummary, ExperimentType } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { FlaskConical, Plus } from 'lucide-react'

interface Props {
  experiments: ExperimentSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
  onNew: () => void
}

const TYPE_COLORS: Record<ExperimentType, string> = {
  kinematic_viscosity: 'bg-blue-100 text-blue-700',
  apparent_viscosity: 'bg-purple-100 text-purple-700',
  surface_tension: 'bg-cyan-100 text-cyan-700',
}

export default function ExperimentList({ experiments, selectedId, onSelect, onNew }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-4 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-base font-semibold flex items-center gap-2 text-gray-700">
          <FlaskConical size={18} />
          实验列表
        </h2>
        <button
          onClick={onNew}
          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
        >
          <Plus size={15} />
          新建
        </button>
      </div>

      {experiments.length === 0 ? (
        <p className="text-gray-400 text-sm text-center mt-8">暂无实验，点击新建开始</p>
      ) : (
        <div className="space-y-2 overflow-y-auto flex-1">
          {experiments.map(exp => {
            const schema = EXPERIMENT_SCHEMAS[exp.type]
            return (
              <div
                key={exp.id}
                onClick={() => onSelect(exp.id)}
                className={`p-3 rounded-lg cursor-pointer transition ${
                  selectedId === exp.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="font-medium text-sm text-gray-800 truncate">{exp.name}</div>
                <div className="mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[exp.type]}`}>
                    {schema?.icon} {schema?.label}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(exp.created_at).toLocaleDateString('zh-CN')}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ExperimentList.tsx
git commit -m "feat(frontend): 添加 ExperimentList 组件"
```

---

### Task 7: 创建向导组件（Step1 + Step2）

**Files:**
- Create: `frontend/src/components/CreateExperiment/Step1TypeSelector.tsx`
- Create: `frontend/src/components/CreateExperiment/Step2Config.tsx`

- [ ] **Step 1: 创建 Step1TypeSelector.tsx**

```bash
mkdir -p /home/kevin/github/ocr-new/frontend/src/components/CreateExperiment
```

创建 `frontend/src/components/CreateExperiment/Step1TypeSelector.tsx`：

```tsx
'use client'
import { useState } from 'react'
import { ExperimentType } from '@/types'
import { EXPERIMENT_TYPE_LIST } from '@/lib/experimentTypes'
import { ArrowRight } from 'lucide-react'

interface Props {
  onNext: (name: string, type: ExperimentType) => void
}

export default function Step1TypeSelector({ onNext }: Props) {
  const [name, setName] = useState('')
  const [type, setType] = useState<ExperimentType | null>(null)
  const [error, setError] = useState('')

  const handleNext = () => {
    if (!name.trim()) { setError('请输入实验名称'); return }
    if (!type) { setError('请选择实验类型'); return }
    setError('')
    onNext(name.trim(), type)
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">实验名称</label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="例如：运动粘度测试-20260320"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">选择实验类型</label>
        <div className="grid grid-cols-1 gap-3">
          {EXPERIMENT_TYPE_LIST.map(schema => (
            <div
              key={schema.type}
              onClick={() => setType(schema.type)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition ${
                type === schema.type
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{schema.icon}</span>
                <div>
                  <div className="font-semibold text-gray-800">{schema.label}</div>
                  <div className="text-sm text-gray-500 mt-0.5">{schema.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={handleNext}
        className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
      >
        下一步
        <ArrowRight size={18} />
      </button>
    </div>
  )
}
```

- [ ] **Step 2: 创建 Step2Config.tsx**

创建 `frontend/src/components/CreateExperiment/Step2Config.tsx`：

```tsx
'use client'
import { useState } from 'react'
import { ExperimentType, CameraFieldConfig, ManualParams } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { ArrowLeft, Plus } from 'lucide-react'

const CAMERA_OPTIONS = Array.from({ length: 9 }, (_, i) => i)  // 0-8

interface Props {
  name: string
  type: ExperimentType
  onBack: () => void
  onSubmit: (manualParams: ManualParams, cameraConfigs: CameraFieldConfig[]) => Promise<void>
  loading: boolean
}

export default function Step2Config({ name, type, onBack, onSubmit, loading }: Props) {
  const schema = EXPERIMENT_SCHEMAS[type]
  const [manualParams, setManualParams] = useState<ManualParams>(() =>
    Object.fromEntries(schema.manualParams.map(p => [p.key, '']))
  )
  const [cameraConfigs, setCameraConfigs] = useState<CameraFieldConfig[]>(() =>
    schema.cameraFields.map(f => ({ field_key: f.fieldKey, camera_id: 0, max_readings: f.maxReadings }))
  )
  const [error, setError] = useState('')

  const updateCamera = (index: number, cameraId: number) => {
    setCameraConfigs(prev => prev.map((c, i) => i === index ? { ...c, camera_id: cameraId } : c))
  }

  const handleSubmit = async () => {
    setError('')
    await onSubmit(manualParams, cameraConfigs).catch(e => setError(e.message))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <button onClick={onBack} className="p-1.5 rounded hover:bg-gray-100">
          <ArrowLeft size={18} className="text-gray-600" />
        </button>
        <div>
          <div className="font-semibold text-gray-800">{name}</div>
          <div className="text-sm text-gray-500">{schema.icon} {schema.label}</div>
        </div>
      </div>

      {/* 手动参数区（apparent_viscosity 无参数时隐藏） */}
      {schema.manualParams.length > 0 && (
        <div className="bg-gray-50 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">实验参数</h3>
          {schema.manualParams.map(param => (
            <div key={param.key} className="flex items-center gap-3">
              <label className="text-sm text-gray-600 w-36 shrink-0">{param.label}</label>
              <input
                type={param.type}
                value={manualParams[param.key] ?? ''}
                onChange={e => setManualParams(prev => ({ ...prev, [param.key]: e.target.value }))}
                className="flex-1 px-3 py-1.5 border rounded-lg text-sm focus:ring-2 focus:ring-blue-400"
                placeholder={`输入${param.label}`}
              />
              <span className="text-sm text-gray-400 w-16 shrink-0">{param.unit}</span>
            </div>
          ))}
        </div>
      )}

      {/* 相机绑定区 */}
      <div className="bg-blue-50 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">相机绑定</h3>
        {schema.cameraFields.map((field, idx) => (
          <div key={field.fieldKey} className="flex items-center gap-3">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">{field.label}</div>
              {field.unit && <div className="text-xs text-gray-400">{field.unit}</div>}
            </div>
            <select
              value={cameraConfigs[idx]?.camera_id ?? 0}
              onChange={e => updateCamera(idx, Number(e.target.value))}
              className="px-3 py-1.5 border rounded-lg text-sm bg-white"
            >
              {CAMERA_OPTIONS.map(c => (
                <option key={c} value={c}>相机 {c}</option>
              ))}
            </select>
            <span className="text-xs text-gray-400 w-16 shrink-0 text-right">
              最多 {field.maxReadings} 次
            </span>
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 font-medium"
      >
        {loading ? '创建中...' : '创建实验'}
      </button>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/CreateExperiment/
git commit -m "feat(frontend): 添加创建向导 Step1/Step2 组件"
```

---

### Task 8: ReadingField 和 ResultSummary 组件

**Files:**
- Create: `frontend/src/components/ExperimentDetail/ReadingField.tsx`
- Create: `frontend/src/components/ExperimentDetail/ResultSummary.tsx`

- [ ] **Step 1: 创建 ReadingField.tsx**

```bash
mkdir -p /home/kevin/github/ocr-new/frontend/src/components/ExperimentDetail
```

创建 `frontend/src/components/ExperimentDetail/ReadingField.tsx`：

```tsx
'use client'
import { useState } from 'react'
import { Reading } from '@/types'
import { Camera, RefreshCw } from 'lucide-react'

interface Props {
  fieldKey: string
  label: string
  unit: string
  cameraId: number
  maxReadings: number
  readings: Reading[]
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>
  capturing: string | null   // 任意字段正在拍照时，本组件也应禁用按钮
}

export default function ReadingField({
  fieldKey, label, unit, cameraId, maxReadings, readings, onCapture, capturing
}: Props) {
  const [error, setError] = useState<string | null>(null)
  const isFull = readings.length >= maxReadings
  const isBusy = capturing !== null  // 任何字段拍照中，全部按钮禁用

  const handleCapture = async () => {
    setError(null)
    try {
      await onCapture(fieldKey, cameraId)
    } catch (e: any) {
      setError(e.message || '拍照失败')
    }
  }

  return (
    <div className="border rounded-xl p-4 bg-white">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="font-medium text-gray-800">{label}</div>
          <div className="text-xs text-gray-400 mt-0.5">
            相机 {cameraId} · 已读 {readings.length}/{maxReadings} 次{unit ? ` · 单位: ${unit}` : ''}
          </div>
        </div>
        <button
          onClick={handleCapture}
          disabled={isBusy || isFull}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            isFull
              ? 'bg-gray-100 text-gray-400 cursor-default'
              : isBusy
              ? 'bg-gray-200 cursor-wait'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {capturing === fieldKey ? (
            <><RefreshCw size={16} className="animate-spin" />识别中...</>
          ) : isFull ? (
            '已完成'
          ) : (
            <><Camera size={16} />拍照识别</>
          )}
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500 mb-2">{error}</p>
      )}

      {readings.length > 0 && (
        <div className="space-y-1">
          {readings.map((r, i) => (
            <div key={r.id} className="flex justify-between items-center text-sm bg-gray-50 rounded px-3 py-1.5">
              <span className="text-gray-500">第 {i + 1} 次</span>
              <span className="font-semibold text-gray-800">{r.value} {unit}</span>
              {r.confidence != null && (
                <span className="text-xs text-gray-400">置信度 {(r.confidence * 100).toFixed(1)}%</span>
              )}
              <span className="text-xs text-gray-400">
                {new Date(r.timestamp).toLocaleTimeString('zh-CN')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: 创建 ResultSummary.tsx**

创建 `frontend/src/components/ExperimentDetail/ResultSummary.tsx`：

```tsx
import { Reading, ManualParams, ExperimentType } from '@/types'
import { calcKinematic, calcApparent, calcSurface } from '@/lib/calculations'

interface Props {
  type: ExperimentType
  readings: Reading[]
  manualParams: ManualParams
}

export default function ResultSummary({ type, readings, manualParams }: Props) {
  if (type === 'kinematic_viscosity') {
    const r = calcKinematic(readings, manualParams)
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">计算结果</h3>
        <div className="grid grid-cols-2 gap-4">
          <ResultCard label="平均流经时间 τ" value={r.avgTime} unit="s" />
          <ResultCard label="运动粘度 ν" value={r.viscosity} unit="mm²/s" />
        </div>
      </div>
    )
  }

  if (type === 'apparent_viscosity') {
    const r = calcApparent(readings)
    return (
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">计算结果</h3>
        <div className="grid grid-cols-3 gap-4">
          <ResultCard label="实验1 表观黏度 η₁" value={r.run1} unit="mPa·s" />
          <ResultCard label="实验2 表观黏度 η₂" value={r.run2} unit="mPa·s" />
          <ResultCard label="平均表观黏度" value={r.average} unit="mPa·s" highlight />
        </div>
      </div>
    )
  }

  if (type === 'surface_tension') {
    const r = calcSurface(readings)
    return (
      <div className="bg-gradient-to-r from-cyan-50 to-teal-50 rounded-xl p-4 border border-cyan-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">计算结果</h3>
        <div className="grid grid-cols-2 gap-4">
          <ResultCard label="表面张力算术平均值" value={r.surfaceAvg} unit="mN/m" highlight />
          <ResultCard label="界面张力算术平均值" value={r.interfaceAvg} unit="mN/m" highlight />
        </div>
      </div>
    )
  }

  return null
}

function ResultCard({ label, value, unit, highlight = false }: {
  label: string; value: number | null; unit: string; highlight?: boolean
}) {
  return (
    <div className={`bg-white rounded-lg p-3 shadow-sm ${highlight ? 'ring-2 ring-blue-300' : ''}`}>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-xl font-bold ${value != null ? 'text-gray-800' : 'text-gray-300'}`}>
        {value != null ? value : '—'}
      </div>
      <div className="text-xs text-gray-400">{unit}</div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ExperimentDetail/
git commit -m "feat(frontend): 添加 ReadingField 和 ResultSummary 组件"
```

---

### Task 9: 三种实验执行视图组件

**Files:**
- Create: `frontend/src/components/experiments/KinematicViscosity.tsx`
- Create: `frontend/src/components/experiments/ApparentViscosity.tsx`
- Create: `frontend/src/components/experiments/SurfaceTension.tsx`

- [ ] **Step 1: 创建目录**

```bash
mkdir -p /home/kevin/github/ocr-new/frontend/src/components/experiments
```

- [ ] **Step 2: 创建 KinematicViscosity.tsx**

```tsx
// frontend/src/components/experiments/KinematicViscosity.tsx
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ReadingField from '@/components/ExperimentDetail/ReadingField'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function KinematicViscosity({ experiment, onCapture, capturing }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.kinematic_viscosity
  const p = experiment.manual_params

  return (
    <div className="space-y-6">
      {/* 手动参数只读展示 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">实验参数</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <ParamRow label="温度设置" value={p.temperature_set} unit="℃" />
          <ParamRow label="最高温度" value={p.temperature_max} unit="℃" />
          <ParamRow label="最低温度" value={p.temperature_min} unit="℃" />
          <ParamRow label="毛细管系数 C" value={p.capillary_coeff} unit="mm²/s²" />
        </div>
      </div>

      {/* 相机读数字段 */}
      {schema.cameraFields.map(field => {
        const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
        const readings = experiment.readings.filter(r => r.field_key === field.fieldKey)
        return (
          <ReadingField
            key={field.fieldKey}
            fieldKey={field.fieldKey}
            label={field.label}
            unit={field.unit}
            cameraId={config?.camera_id ?? 0}
            maxReadings={field.maxReadings}
            readings={readings}
            onCapture={onCapture}
            capturing={capturing}
          />
        )
      })}

      <ResultSummary type="kinematic_viscosity" readings={experiment.readings} manualParams={p} />
    </div>
  )
}

function ParamRow({ label, value, unit }: { label: string; value: any; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value ?? '—'} <span className="text-gray-400 text-xs">{unit}</span></span>
    </div>
  )
}
```

- [ ] **Step 3: 创建 ApparentViscosity.tsx**

```tsx
// frontend/src/components/experiments/ApparentViscosity.tsx
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ReadingField from '@/components/ExperimentDetail/ReadingField'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function ApparentViscosity({ experiment, onCapture, capturing }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.apparent_viscosity

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        每个转速字段需拍照 2 次（对应实验1、实验2），系统自动按读取顺序分配 run_index。
      </p>

      {schema.cameraFields.map(field => {
        const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
        const readings = experiment.readings.filter(r => r.field_key === field.fieldKey)
        return (
          <ReadingField
            key={field.fieldKey}
            fieldKey={field.fieldKey}
            label={field.label}
            unit={field.unit}
            cameraId={config?.camera_id ?? 0}
            maxReadings={field.maxReadings}
            readings={readings}
            onCapture={onCapture}
            capturing={capturing}
          />
        )
      })}

      <ResultSummary type="apparent_viscosity" readings={experiment.readings} manualParams={experiment.manual_params} />
    </div>
  )
}
```

- [ ] **Step 4: 创建 SurfaceTension.tsx**

```tsx
// frontend/src/components/experiments/SurfaceTension.tsx
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ReadingField from '@/components/ExperimentDetail/ReadingField'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function SurfaceTension({ experiment, onCapture, capturing }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.surface_tension
  const p = experiment.manual_params

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">实验参数</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <ParamRow label="室内温度" value={p.room_temperature} unit="℃" />
          <ParamRow label="室内湿度" value={p.room_humidity} unit="%" />
          <ParamRow label="样品密度 (25℃)" value={p.sample_density} unit="g/cm³" />
          <ParamRow label="煤油密度 (25℃)" value={p.kerosene_density} unit="g/cm³" />
        </div>
      </div>

      {schema.cameraFields.map(field => {
        const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
        const readings = experiment.readings.filter(r => r.field_key === field.fieldKey)
        return (
          <ReadingField
            key={field.fieldKey}
            fieldKey={field.fieldKey}
            label={field.label}
            unit={field.unit}
            cameraId={config?.camera_id ?? 0}
            maxReadings={field.maxReadings}
            readings={readings}
            onCapture={onCapture}
            capturing={capturing}
          />
        )
      })}

      <ResultSummary type="surface_tension" readings={experiment.readings} manualParams={p} />
    </div>
  )
}

function ParamRow({ label, value, unit }: { label: string; value: any; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value ?? '—'} <span className="text-gray-400 text-xs">{unit}</span></span>
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/experiments/
git commit -m "feat(frontend): 添加三种实验执行视图组件"
```

---

### Task 10: ExperimentDetail 主视图

**Files:**
- Create: `frontend/src/components/ExperimentDetail/index.tsx`

- [ ] **Step 1: 创建 ExperimentDetail/index.tsx**

```tsx
'use client'
import { Experiment, ExperimentType, Reading } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { exportUrl } from '@/lib/api'
import KinematicViscosity from '@/components/experiments/KinematicViscosity'
import ApparentViscosity from '@/components/experiments/ApparentViscosity'
import SurfaceTension from '@/components/experiments/SurfaceTension'
import { Download, FlaskConical } from 'lucide-react'
import { ExperimentViewProps } from '@/types'
import React from 'react'

const EXPERIMENT_VIEWS: Record<ExperimentType, React.ComponentType<ExperimentViewProps>> = {
  kinematic_viscosity: KinematicViscosity,
  apparent_viscosity: ApparentViscosity,
  surface_tension: SurfaceTension,
}

interface Props {
  experiment: Experiment
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>
  capturing: string | null
}

export default function ExperimentDetail({ experiment, onCapture, capturing }: Props) {
  const schema = EXPERIMENT_SCHEMAS[experiment.type]
  const ViewComponent = EXPERIMENT_VIEWS[experiment.type]

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      {/* 顶部 */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{experiment.name}</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-lg">{schema.icon}</span>
            <span className="text-sm text-gray-500">{schema.label}</span>
            <span className="text-xs text-gray-400">
              · 创建于 {new Date(experiment.created_at).toLocaleDateString('zh-CN')}
            </span>
          </div>
        </div>
        <a
          href={exportUrl(experiment.id)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
        >
          <Download size={16} />
          导出 Excel
        </a>
      </div>

      {/* 实验内容（按类型分发） */}
      <ViewComponent
        experiment={experiment}
        onCapture={onCapture}
        capturing={capturing}
      />
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ExperimentDetail/index.tsx
git commit -m "feat(frontend): 添加 ExperimentDetail 主视图（按类型分发）"
```

---

### Task 11: 重写主页面 page.tsx

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: 完全替换 page.tsx**

```tsx
'use client'

import { useState, useEffect, useCallback } from 'react'
import { Experiment, ExperimentSummary, ExperimentType, Reading, CameraFieldConfig, ManualParams } from '@/types'
import { listExperiments, getExperiment, createExperiment, captureReading } from '@/lib/api'
import ExperimentList from '@/components/ExperimentList'
import Step1TypeSelector from '@/components/CreateExperiment/Step1TypeSelector'
import Step2Config from '@/components/CreateExperiment/Step2Config'
import ExperimentDetail from '@/components/ExperimentDetail'
import { FlaskConical } from 'lucide-react'

type View = 'list_empty' | 'create_step1' | 'create_step2' | 'detail'

export default function Home() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null)
  const [view, setView] = useState<View>('list_empty')
  const [creating, setCreating] = useState(false)

  // 创建向导状态
  const [draftName, setDraftName] = useState('')
  const [draftType, setDraftType] = useState<ExperimentType | null>(null)

  // 拍照状态
  const [capturing, setCapturing] = useState<string | null>(null)

  const loadList = useCallback(async () => {
    try {
      const list = await listExperiments()
      setExperiments(list)
    } catch (e) {
      console.error('加载实验列表失败', e)
    }
  }, [])

  useEffect(() => { loadList() }, [loadList])

  const handleSelectExperiment = async (id: number) => {
    try {
      const exp = await getExperiment(id)
      setSelectedExperiment(exp)
      setView('detail')
    } catch (e) {
      console.error('加载实验失败', e)
    }
  }

  const handleStep1 = (name: string, type: ExperimentType) => {
    setDraftName(name)
    setDraftType(type)
    setView('create_step2')
  }

  const handleStep2Submit = async (manualParams: ManualParams, cameraConfigs: CameraFieldConfig[]) => {
    if (!draftType) return
    setCreating(true)
    try {
      const id = await createExperiment({
        name: draftName,
        type: draftType,
        manual_params: manualParams,
        camera_configs: cameraConfigs,
      })
      await loadList()
      await handleSelectExperiment(id)
    } finally {
      setCreating(false)
    }
  }

  const handleCapture = async (fieldKey: string, cameraId: number): Promise<Reading> => {
    if (!selectedExperiment) throw new Error('无当前实验')
    setCapturing(fieldKey)
    try {
      const reading = await captureReading(selectedExperiment.id, fieldKey, cameraId)
      // 刷新实验数据（追加新读数到本地状态）
      setSelectedExperiment(prev =>
        prev ? { ...prev, readings: [...prev.readings, reading] } : prev
      )
      return reading
    } finally {
      setCapturing(null)
    }
  }

  const renderMain = () => {
    if (view === 'create_step1') {
      return (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-800">新建实验</h2>
          <Step1TypeSelector onNext={handleStep1} />
        </div>
      )
    }

    if (view === 'create_step2' && draftType) {
      return (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-800">配置实验</h2>
          <Step2Config
            name={draftName}
            type={draftType}
            onBack={() => setView('create_step1')}
            onSubmit={handleStep2Submit}
            loading={creating}
          />
        </div>
      )
    }

    if (view === 'detail' && selectedExperiment) {
      return (
        <ExperimentDetail
          experiment={selectedExperiment}
          onCapture={handleCapture}
          capturing={capturing}
        />
      )
    }

    return (
      <div className="bg-white rounded-xl shadow-sm p-12 text-center">
        <FlaskConical size={48} className="mx-auto text-gray-300 mb-4" />
        <p className="text-gray-400">从左侧选择实验，或点击"新建"创建实验</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen p-4 md:p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
            <FlaskConical className="text-blue-600" />
            OCR 仪表读数系统
          </h1>
          <p className="text-gray-500 text-sm mt-1">实验室仪器自动拍照识别与数据管理</p>
        </header>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <ExperimentList
              experiments={experiments}
              selectedId={selectedExperiment?.id ?? null}
              onSelect={handleSelectExperiment}
              onNew={() => { setView('create_step1'); setSelectedExperiment(null) }}
            />
          </div>
          <div className="md:col-span-2">
            {renderMain()}
          </div>
        </div>
      </div>
    </main>
  )
}
```

- [ ] **Step 2: 确认 tsconfig.json 中 `@` 别名已配置**

检查 `frontend/tsconfig.json` 是否包含：

```json
"paths": {
  "@/*": ["./src/*"]
}
```

若无，添加到 `compilerOptions` 中。

- [ ] **Step 3: 构建验证**

```bash
cd /home/kevin/github/ocr-new/frontend
npm run build 2>&1 | tail -30
```

期望：无 TypeScript 报错，build 成功。若有报错，逐一修复后重新 build。

- [ ] **Step 4: 启动开发服务器验证**

```bash
npm run dev
```

浏览器访问 `http://localhost:3000`，验证：
1. 页面正常加载，左侧显示"暂无实验"
2. 点击"新建"→ 显示 Step1 类型选择页
3. 选择类型 → 下一步 → 显示 Step2 配置页
4. 创建成功后自动跳转实验详情页

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/page.tsx frontend/tsconfig.json
git commit -m "feat(frontend): 重写主页面，完成两步创建向导与实验执行视图集成"
```

---

## 最终验证清单

- [ ] 后端启动无报错：`uvicorn backend.api.main:app --port 8001`
- [ ] 前端启动无报错：`npm run dev`（在 `frontend/` 目录下）
- [ ] 创建运动粘度实验：填写手动参数 + 绑定相机 → 创建成功 → 进入执行页
- [ ] 创建表观黏度实验：无手动参数区 → 直接绑定相机 → 创建成功
- [ ] 创建表面张力实验：填写4个手动参数 + 绑定3个字段相机 → 创建成功
- [ ] 执行页点击"拍照识别"：按钮变为 loading → 读数追加到列表 → 计算结果更新
- [ ] 读数达到 maxReadings 后按钮自动禁用显示"已完成"
- [ ] 点击"导出 Excel"：下载 xlsx 文件，内容与实验数据一致
- [ ] 左侧列表显示实验类型标签和创建日期
- [ ] 拍照失败时（模拟相机断开）：ReadingField 显示行内红色错误，按钮恢复可用，readings.length 不变
