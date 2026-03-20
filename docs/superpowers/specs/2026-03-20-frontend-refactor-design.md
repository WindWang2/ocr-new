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

---

## 二、实验类型与字段定义

### 1. 运动粘度（kinematic_viscosity）

**手动参数（创建时填写）：**
- 温度设置 (℃)
- 最高温度 (℃)
- 最低温度 (℃)
- 毛细管系数 C (mm²/s²)

**相机字段：**
- 流经时间 t(s)：绑定1台相机，最多拍照4次（追加）

**自动计算：**
- 平均流经时间 τ = mean(t₁, t₂, t₃, t₄)
- 运动粘度 ν = C × τ（单位 mm²/s）

---

### 2. 表观黏度（apparent_viscosity）

**手动参数：** 无

**相机字段（各自独立绑定1台相机，最多2次追加）：**
- 3rpm 读数
- 6rpm 读数
- 100rpm 读数（α）

**自动计算（每次实验）：**
- 表观黏度 η = (α × 5.077) / 1.704（单位 mPa·s）

**最终结果：**
- 实验1 η、实验2 η 的平均值

---

### 3. 表面张力和界面张力（surface_tension）

**手动参数（创建时填写）：**
- 室内温度 (℃)
- 室内湿度 (%)
- 样品密度 25℃ (g/cm³)
- 煤油密度 25℃ (g/cm³)

**相机字段：**
- 纯水表面张力 (mN/m)：绑定1台相机，拍照1次
- 破胶液表面张力 (mN/m)：绑定1台相机，最多5次追加
- 破胶液界面张力 (mN/m)：绑定1台相机，最多2次追加

**自动计算：**
- 表面张力算术平均值 = mean(5次值)
- 界面张力算术平均值 = mean(2次值)

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
根据类型动态渲染两类区域：

**手动参数区**（灰色背景）：
- 各参数字段的标签 + 输入框 + 单位

**相机绑定区**（蓝色背景）：
- 每个相机字段一行：字段名称 + 下拉选择相机号（0-8）
- 最多可读次数提示

点击"创建实验"→ 调用后端 API → 自动跳转实验执行页面。

### 实验执行页面
按实验类型渲染对应的执行视图组件，各组件结构：

1. **顶部**：实验名、类型标签、手动参数展示（只读）、导出按钮
2. **中部**：每个相机字段卡片，包含：
   - 字段名称 + 绑定相机号
   - 已采集读数列表（时间戳 + 值 + 置信度）
   - "拍照识别"按钮（达到最大次数后禁用）
3. **底部**：自动计算结果汇总区（实时更新）

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
│   │   ├── index.tsx               # 执行主视图（按类型分发）
│   │   ├── ReadingField.tsx        # 单个相机读数字段卡片
│   │   └── ResultSummary.tsx       # 底部自动计算结果汇总
│   └── experiments/
│       ├── KinematicViscosity.tsx  # 运动粘度执行视图
│       ├── ApparentViscosity.tsx   # 表观黏度执行视图
│       └── SurfaceTension.tsx      # 表面张力执行视图
├── lib/
│   ├── api.ts                      # API调用封装
│   ├── experimentTypes.ts          # 实验类型schema定义
│   └── calculations.ts             # 公式计算函数
└── types/
    └── index.ts                    # TypeScript类型定义
```

---

## 六、数据模型（前端视角）

```typescript
// 实验类型标识
type ExperimentType = 'kinematic_viscosity' | 'apparent_viscosity' | 'surface_tension'

// 相机字段配置（创建时保存）
interface CameraFieldConfig {
  fieldKey: string      // 字段标识，如 "flow_time", "rpm3"
  cameraId: number      // 绑定相机号 0-8
  maxReadings: number   // 最大读数次数
}

// 手动参数（创建时保存）
interface ManualParams {
  [key: string]: number | string
}

// 实验记录
interface Experiment {
  id: string
  name: string
  type: ExperimentType
  manualParams: ManualParams
  cameraConfigs: CameraFieldConfig[]
  readings: Reading[]
  createdAt: string
}

// 单次读数
interface Reading {
  id: string
  fieldKey: string
  cameraId: number
  value: number
  confidence?: number
  imagePath?: string
  timestamp: string
}
```

---

## 七、API 接口（与后端对接）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /experiments | 获取实验列表 |
| POST | /experiments | 创建实验（含type、manualParams、cameraConfigs） |
| GET | /experiments/{id} | 获取实验详情（含所有readings） |
| POST | /experiments/{id}/run | 触发指定相机拍照→OCR→返回读数 |
| GET | /experiments/{id}/export | 导出Excel（按模板格式） |

> 注：后端 `POST /experiments/{id}/run` 需接受 `field_key` 和 `camera_id` 参数，以便前端明确指定本次拍照对应哪个字段。

---

## 八、导出格式

按各实验模板的表格结构生成 `.xlsx` 文件，各类型对应各自的行列布局，数据填充到对应单元格。后端负责生成，前端仅调用导出接口并触发下载。

---

## 九、不包含的功能（本次范围外）

- 相机管理（增删改查相机设备）
- 实验编辑（已创建的实验不可修改配置）
- 用户认证
- 多语言支持
