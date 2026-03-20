# 前端重构设计文档

**日期**：2026-03-20
**项目**：OCR 仪表读数系统前端重构
**状态**：已批准

---

## 一、背景与目标

现有前端为单页通用仪器管理界面，不体现实验类型的业务语义，读数字段完全动态，缺乏结构化引导。

重构目标：
- 前端按"实验模板"驱动，支持3种实验类型
- 创建实验时通过两步向导完成配置（手动参数 + 相机绑定）
- 执行实验时按模板结构展示字段，支持拍照追加读数与自动计算

> 注：此次重构同步需要后端适配（新增字段、新增接口），后端改动在第七节 API 接口中详细描述。

---

## 二、实验类型与字段定义

字段的 `maxReadings` 是由 `experimentTypes.ts` 中的 schema 硬编码固定的，不对用户开放修改。Step 2 中显示为只读标签。

### 1. 运动粘度（kinematic_viscosity）

**手动参数（创建时填写）：**
- `temperature_set`：温度设置 (℃)
- `temperature_max`：最高温度 (℃)
- `temperature_min`：最低温度 (℃)
- `capillary_coeff`：毛细管系数 C (mm²/s²)

**相机字段（`experimentTypes.ts` 中定义）：**
| fieldKey | 标签 | maxReadings |
|----------|------|-------------|
| `flow_time` | 流经时间 t(s) | 4 |

**自动计算：**
- 平均流经时间 τ = mean(所有 `flow_time` 读数值)
- 运动粘度 ν = C × τ（单位 mm²/s）

---

### 2. 表观黏度（apparent_viscosity）

**手动参数：** 无（Step 2 手动参数区隐藏，仅显示相机绑定区）

**相机字段（各自独立绑定1台相机）：**
| fieldKey | 标签 | maxReadings |
|----------|------|-------------|
| `rpm3` | 3rpm 读数 | 2 |
| `rpm6` | 6rpm 读数 | 2 |
| `rpm100` | 100rpm 读数（α） | 2 |

**自动计算（按 runIndex 分组）：**
- 第 runIndex=1 次：α₁ 取 `rpm100` 第1条读数，η₁ = (α₁ × 5.077) / 1.704
- 第 runIndex=2 次：α₂ 取 `rpm100` 第2条读数，η₂ = (α₂ × 5.077) / 1.704
- 平均表观黏度 = (η₁ + η₂) / 2

> 公式中 5.077 (10⁻¹Pa / 读数单位) 和 1.704 (s⁻¹) 为仪器标定常数，保持两因子形式以便未来独立调整。

---

### 3. 表面张力和界面张力（surface_tension）

**手动参数（创建时填写）：**
- `room_temperature`：室内温度 (℃)
- `room_humidity`：室内湿度 (%)
- `sample_density`：样品密度 25℃ (g/cm³)
- `kerosene_density`：煤油密度 25℃ (g/cm³)

**相机字段：**
| fieldKey | 标签 | maxReadings |
|----------|------|-------------|
| `water_surface_tension` | 纯水表面张力 (mN/m) | 1 |
| `fluid_surface_tension` | 破胶液表面张力 (mN/m) | 5 |
| `fluid_interface_tension` | 破胶液界面张力 (mN/m) | 2 |

**自动计算：**
- 表面张力算术平均值 = mean(`fluid_surface_tension` 所有读数)
- 界面张力算术平均值 = mean(`fluid_interface_tension` 所有读数)

---

## 三、页面结构

```
┌─────────────────────────────────────────────────────────┐
│  OCR 仪表读数系统                                          │
├──────────────┬──────────────────────────────────────────┤
│  实验列表     │  主内容区                                   │
│              │                                           │
│  [+ 新建]    │  [创建向导 Step1/2]  或  [实验执行页面]      │
│              │                                           │
│  ○ 实验A     │                                           │
│  ● 实验B(当前)│                                           │
│  ○ 实验C     │                                           │
└──────────────┴──────────────────────────────────────────┘
```

---

## 四、UI 流程

### 创建实验——步骤1
- 输入实验名称（文本框）
- 选择实验类型（3张卡片，含图标和说明文字）
- 点击"下一步"

### 创建实验——步骤2
根据类型动态渲染：

**手动参数区**（灰色背景，`apparent_viscosity` 类型时此区域完全隐藏）：
- 各参数字段的标签 + 输入框 + 单位

**相机绑定区**（蓝色背景）：
- 每个相机字段一行：字段名称 + 下拉选择相机号（0-8）+ 只读标签"最多 N 次"
- `maxReadings` 从 `experimentTypes.ts` schema 读取，不可修改

点击"创建实验"→ 调用 `POST /experiments` → 自动跳转实验执行页面。

### 实验执行页面
`ExperimentDetail/index.tsx` 根据 `experiment.type` 映射渲染对应视图组件：

```typescript
const EXPERIMENT_VIEWS: Record<ExperimentType, React.ComponentType<ExperimentViewProps>> = {
  kinematic_viscosity: KinematicViscosity,
  apparent_viscosity: ApparentViscosity,
  surface_tension: SurfaceTension,
}
```

共享 props 接口：
```typescript
interface ExperimentViewProps {
  experiment: Experiment
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>  // 成功返回新Reading，失败抛出异常（前端显示行内错误）
  capturing: string | null   // 当前正在拍照的 fieldKey，null 表示空闲；capturing !== null 时所有拍照按钮均禁用
}
```

各执行视图组件内部结构：

1. **顶部**：实验名、类型标签、手动参数展示（只读）、导出按钮（触发 `/experiments/{id}/export` 下载 xlsx）
2. **中部**：每个相机字段渲染一个 `ReadingField` 卡片，包含：
   - 字段名称 + 绑定相机号
   - 已采集读数列表（时间戳 + 值 + 置信度）
   - "拍照识别"按钮：已达 `maxReadings` 时禁用；拍照失败时显示行内错误，按钮重新可用，失败不计入读数次数
3. **底部**：`ResultSummary` 组件，实时根据当前 readings 计算并展示公式结果

---

## 五、组件结构

```
frontend/src/
├── app/
│   ├── page.tsx                    # 主页面布局骨架
│   └── layout.tsx
├── components/
│   ├── ExperimentList.tsx          # 左侧实验列表
│   ├── CreateExperiment/
│   │   ├── Step1TypeSelector.tsx   # 步骤1：名称+类型选择卡片
│   │   └── Step2Config.tsx         # 步骤2：参数+相机绑定配置
│   ├── ExperimentDetail/
│   │   ├── index.tsx               # 执行主视图（按类型分发，见四节dispatch逻辑）
│   │   ├── ReadingField.tsx        # 单个相机读数字段卡片
│   │   └── ResultSummary.tsx       # 底部自动计算结果汇总
│   └── experiments/
│       ├── KinematicViscosity.tsx  # 运动粘度执行视图
│       ├── ApparentViscosity.tsx   # 表观黏度执行视图
│       └── SurfaceTension.tsx      # 表面张力执行视图
├── lib/
│   ├── api.ts                      # API调用封装
│   ├── experimentTypes.ts          # 实验类型schema：各type的字段列表、maxReadings、手动参数定义
│   └── calculations.ts             # 公式计算函数（kinematicViscosity / apparentViscosity / surfaceTension）
└── types/
    └── index.ts                    # TypeScript类型定义
```

`experimentTypes.ts` 导出每种类型的完整 schema，Step2Config 和各执行视图组件均从此处读取字段列表、`maxReadings`、手动参数标签和单位，避免重复硬编码。

---

## 六、数据模型（前端视角）

```typescript
// 实验类型标识
type ExperimentType = 'kinematic_viscosity' | 'apparent_viscosity' | 'surface_tension'

// 相机字段配置（创建时保存，maxReadings 来自 schema 不可修改）
interface CameraFieldConfig {
  fieldKey: string      // 字段标识，如 "flow_time", "rpm3"
  cameraId: number      // 绑定相机号 0-8
  maxReadings: number   // 最大读数次数（schema 固定值，仅用于展示和前端校验）
}

// 手动参数（创建时保存）
interface ManualParams {
  [key: string]: number | string
}

// 实验记录（id 为 number，与后端 SQLite lastrowid 一致）
interface Experiment {
  id: number
  name: string
  type: ExperimentType
  manualParams: ManualParams
  cameraConfigs: CameraFieldConfig[]
  readings: Reading[]
  createdAt: string
}

// 单次读数
interface Reading {
  id: number
  fieldKey: string
  cameraId: number
  value: number
  runIndex: number      // 同一字段的第几次读数（1-based），用于 apparent_viscosity 分组计算
  confidence?: number
  imagePath?: string
  timestamp: string
}
```

---

## 七、API 接口（与后端对接）

> 标注 **[新增/修改]** 的接口需要后端相应改动。

### GET /experiments
获取实验列表。列表项返回轻量摘要（`id`, `name`, `type`, `created_at`），不包含 `readings` 和 `camera_configs`，避免大载荷。完整数据通过 `GET /experiments/{id}` 获取。

### POST /experiments **[修改]**

请求体：
```json
{
  "name": "2026-03-20运动粘度测试",
  "type": "kinematic_viscosity",
  "manual_params": {
    "temperature_set": 25.0,
    "temperature_max": 26.0,
    "temperature_min": 24.5,
    "capillary_coeff": 0.5
  },
  "camera_configs": [
    { "field_key": "flow_time", "camera_id": 2, "max_readings": 4 }
  ]
}
```

响应体：
```json
{ "success": true, "experiment_id": 42 }
```

后端需在 `experiments` 表新增 `type`、`manual_params`（JSON字符串）、`camera_configs`（JSON字符串）字段。

### GET /experiments/{id} **[修改]**

响应体（新增字段）：
```json
{
  "success": true,
  "experiment": {
    "id": 42,
    "name": "...",
    "type": "kinematic_viscosity",
    "manual_params": { "capillary_coeff": 0.5 },
    "camera_configs": [{ "field_key": "flow_time", "camera_id": 2, "max_readings": 4 }],
    "readings": [
      { "id": 1, "field_key": "flow_time", "camera_id": 2, "value": 45.3, "run_index": 1, "confidence": 0.97, "timestamp": "..." }
    ],
    "created_at": "..."
  }
}
```

### POST /experiments/{id}/run **[修改]**

每次点击"拍照识别"调用一次，明确指定字段和相机。

请求体：
```json
{ "field_key": "flow_time", "camera_id": 2 }
```

响应体（成功）：
```json
{
  "success": true,
  "reading": {
    "id": 7,
    "field_key": "flow_time",
    "camera_id": 2,
    "value": 45.3,
    "run_index": 2,
    "confidence": 0.97,
    "image_path": "/images/...",
    "timestamp": "2026-03-20T10:30:00Z"
  }
}
```

响应体（失败，HTTP 200 + success:false，前端显示行内错误）：
```json
{ "success": false, "detail": "相机连接失败" }
```

### GET /experiments/{id}/export **[新增]**

返回 `.xlsx` 文件下载（Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet）。按实验类型生成对应模板格式的表格。后端需新增此接口并引入 `openpyxl` 库。

---

## 八、导出格式

按各实验模板的表格结构生成 `.xlsx` 文件，各类型对应各自的行列布局，数据填充到对应单元格。后端负责生成，前端仅调用导出接口并触发下载（替换现有的"导出 CSV"按钮，改为"导出 Excel"）。

---

## 九、不包含的功能（本次范围外）

- 相机管理（增删改查相机设备）
- 实验编辑（已创建的实验不可修改配置）
- 用户认证
- 多语言支持
