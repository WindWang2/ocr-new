import { ExperimentType } from '@/types'

export interface ManualParamDef {
  key: string
  label: string
  unit: string
  type: 'number' | 'text'
  placeholder?: string
}

export interface InstrumentFieldDef {
  fieldKey: string
  label: string           // 字段显示名
  unit: string            // 读数单位
  maxReadings: number     // 最多读数次数（每次读数对应一个拍照槽位）
  targetInstrumentId: number // 目标仪器ID (YOLO类别 0-8)
  readingKey: string      // 仪器读数键：OCR 结果 JSON 中对应此字段的 key
  description?: string    // 字段说明，用于UI提示
}

export interface ExperimentSchema {
  type: ExperimentType
  label: string
  description: string
  icon: string
  standard?: string      // 执行标准
  manualParams: ManualParamDef[]
  instrumentFields: InstrumentFieldDef[]
}

export const EXPERIMENT_SCHEMAS: Record<ExperimentType, ExperimentSchema> = {

  // ─────────────────────────────────────────────────────────────────────────
  // 运动粘度
  // 执行标准：品氏毛细管粘度计法，25℃下恒温10min，测4次流经时间，取平均值
  // 公式：ν = C × τ̄ （ν：运动粘度 mm²/s；C：毛细管系数 mm²/s²；τ̄：平均流经时间 s）
  // ─────────────────────────────────────────────────────────────────────────
  kinematic_viscosity: {
    type: 'kinematic_viscosity',
    label: '运动粘度',
    description: '品氏毛细管粘度计，25℃恒温测量液体流经时间，计算运动粘度 ν = C × τ̄',
    icon: '🧪',
    standard: 'GB/T 265',
    manualParams: [
      { key: 'test_date',        label: '检测日期',         unit: '',       type: 'text',   placeholder: '如 2026-03-30' },
      { key: 'sample_name',      label: '被检样品名称',     unit: '',       type: 'text' },
      { key: 'sample_number',    label: '样品编号',         unit: '',       type: 'text' },
      { key: 'report_number',    label: '报告编号 NO.',     unit: '',       type: 'text' },
      { key: 'formula_description', label: '配方说明',      unit: '',       type: 'text',   placeholder: '如：0.1%减阻剂+200ppm水' },
      { key: 'temperature_set',  label: '温控设置温度',     unit: '℃',     type: 'number', placeholder: '25' },
      { key: 'temperature_max',  label: '最高温度',         unit: '℃',     type: 'number' },
      { key: 'temperature_min',  label: '最低温度',         unit: '℃',     type: 'number' },
      { key: 'capillary_model',  label: '毛细管粘度计型号', unit: '',       type: 'text',   placeholder: '如 0.8mm 品氏' },
      { key: 'capillary_coeff',  label: '毛细管系数 C',     unit: 'mm²/s²', type: 'number' },
    ],
    instrumentFields: [
      {
        fieldKey: 'flow_time',
        label: '流经时间 t',
        unit: 's',
        maxReadings: 4,
        targetInstrumentId: 7, // 对应 F7 水浴锅
        readingKey: 'time',
        description: '每次读数拍摄运动粘度测试仪显示的流经时间，共4次，误差 < 10s',
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 表观黏度
  // 执行标准：WLD/CNAS-QP7080004 A/3
  // 仪器：F8（6速旋转粘度计），每次实验需分别读取 3rpm、6rpm、100rpm 共3次读数
  // 公式：η = α × 5.077 / 1.704（α 为 100rpm 读数；η 单位 mPa·s）
  // 需做2次实验取平均
  // ─────────────────────────────────────────────────────────────────────────
  apparent_viscosity: {
    type: 'apparent_viscosity',
    label: '表观黏度',
    description: '6速旋转粘度计，分别读取3/6/100rpm读数，计算表观黏度 η = α × 5.077/1.704，做2次实验取平均',
    icon: '🔄',
    standard: 'WLD/CNAS-QP7080004',
    manualParams: [
      { key: 'test_date',        label: '检测日期',     unit: '', type: 'text', placeholder: '如 2026-03-30' },
      { key: 'sample_name',      label: '被检样品名称', unit: '', type: 'text' },
      { key: 'sample_number',    label: '样品编号',     unit: '', type: 'text' },
      { key: 'report_number',    label: '编号 NO.',     unit: '', type: 'text' },
      { key: 'formula_description', label: '配方说明',  unit: '', type: 'text', placeholder: '如：配方描述' },
    ],
    instrumentFields: [
      {
        fieldKey: 'rpm3',
        label: '3 rpm 读数',
        unit: '',
        maxReadings: 2,
        targetInstrumentId: 8, // 对应 F8 粘度计
        readingKey: 'actual_reading',
        description: '将粘度计设置为 3rpm，拍摄屏幕读数',
      },
      {
        fieldKey: 'rpm6',
        label: '6 rpm 读数',
        unit: '',
        maxReadings: 2,
        targetInstrumentId: 8,
        readingKey: 'actual_reading',
        description: '将粘度计设置为 6rpm，拍摄屏幕读数',
      },
      {
        fieldKey: 'rpm100',
        label: '100 rpm 读数 (α)',
        unit: '',
        maxReadings: 2,
        targetInstrumentId: 8,
        readingKey: 'actual_reading',
        description: '将粘度计设置为 100rpm，拍摄屏幕读数，此值用于计算表观黏度',
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 表面张力和界面张力
  // 执行标准：SY/T 5370-2018，铂金环法
  // 仪器：F5（表界面张力仪）
  // 测试项目：
  //   1. 纯水表面张力 × 1次（用于验证仪器状态）
  //   2. 破胶液表面张力 × 5次（取算术平均）
  //   3. 破胶液界面张力 × 2次（取算术平均）
  // ─────────────────────────────────────────────────────────────────────────
  surface_tension: {
    type: 'surface_tension',
    label: '表面张力和界面张力',
    description: '铂金环法（SY/T 5370-2018），测量破胶液表面张力（5次均值）和界面张力（2次均值）',
    icon: '💧',
    standard: 'SY/T 5370-2018',
    manualParams: [
      { key: 'test_date',        label: '检测日期',         unit: '',      type: 'text',   placeholder: '如 2026-03-30' },
      { key: 'sample_name',      label: '被检样品名称',     unit: '',      type: 'text' },
      { key: 'sample_number',    label: '样品编号',         unit: '',      type: 'text' },
      { key: 'sample_state',     label: '样品状态',         unit: '',      type: 'text',   placeholder: '如：液态' },
      { key: 'formula_number',   label: '配液编号',         unit: '',      type: 'text' },
      { key: 'report_number',    label: '检测报告编号',     unit: '',      type: 'text' },
      { key: 'formula_description', label: '配方说明',      unit: '',      type: 'text' },
      { key: 'room_temperature', label: '室内温度',         unit: '℃',    type: 'number' },
      { key: 'room_humidity',    label: '室内湿度',         unit: '%',     type: 'number' },
      { key: 'sample_density',   label: '25℃ 破胶液密度',  unit: 'g/cm³', type: 'number', placeholder: '用于表面张力测试' },
      { key: 'kerosene_density', label: '25℃ 煤油密度',    unit: 'g/cm³', type: 'number', placeholder: '用于界面张力测试' },
      { key: 'remarks',          label: '备注',             unit: '',      type: 'text' },
      { key: 'operator_name',    label: '检测人',           unit: '',      type: 'text' },
      { key: 'operator_time',    label: '检测时间',         unit: '',      type: 'text' },
      { key: 'reviewer_name',    label: '审核人',           unit: '',      type: 'text' },
      { key: 'reviewer_date',    label: '审核日期',         unit: '',      type: 'text' },
    ],
    instrumentFields: [
      {
        fieldKey: 'water_surface_tension',
        label: '纯水表面张力',
        unit: 'mN/m',
        maxReadings: 1,
        targetInstrumentId: 5, // 对应 F5 张力仪
        readingKey: 'tension',
        description: '测试前先测纯水表面张力，用于验证铂金环状态',
      },
      {
        fieldKey: 'fluid_surface_tension',
        label: '破胶液表面张力',
        unit: 'mN/m',
        maxReadings: 5,
        targetInstrumentId: 5,
        readingKey: 'tension',
        description: '环法测表面张力，上层密度设为0，下层密度输入破胶液密度，共5次取算术平均',
      },
      {
        fieldKey: 'fluid_interface_tension',
        label: '破胶液界面张力',
        unit: 'mN/m',
        maxReadings: 2,
        targetInstrumentId: 5,
        readingKey: 'tension',
        description: '环法测界面张力，上下层密度按实际值设置（破胶液/煤油），共2次取算术平均',
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 测试模板
  // ─────────────────────────────────────────────────────────────────────────
  test: {
    type: 'test',
    label: '全场景仪表测试',
    description: '自动定位并识别图片中的 9 类仪表（F0~F8），支持多目标自动裁剪',
    icon: '🔬',
    manualParams: [],
    instrumentFields: [
      { fieldKey: 'F0', label: 'F0 · 混调器',       unit: '', maxReadings: 99, targetInstrumentId: 0, readingKey: 'current_speed' },
      { fieldKey: 'F1', label: 'F1 · 电子天平1',    unit: 'g', maxReadings: 99, targetInstrumentId: 1, readingKey: 'weight' },
      { fieldKey: 'F2', label: 'F2 · 电子天平2',    unit: 'g', maxReadings: 99, targetInstrumentId: 2, readingKey: 'weight' },
      { fieldKey: 'F3', label: 'F3 · pH计',         unit: '', maxReadings: 99, targetInstrumentId: 3, readingKey: 'ph_value' },
      { fieldKey: 'F4', label: 'F4 · 水质检测仪',   unit: '', maxReadings: 99, targetInstrumentId: 4, readingKey: 'test_value' },
      { fieldKey: 'F5', label: 'F5 · 表界面张力仪', unit: 'mN/m', maxReadings: 99, targetInstrumentId: 5, readingKey: 'tension' },
      { fieldKey: 'F6', label: 'F6 · 扭矩搅拌器',  unit: '', maxReadings: 99, targetInstrumentId: 6, readingKey: 'rotation_speed' },
      { fieldKey: 'F7', label: 'F7 · 水浴锅',       unit: 's',  maxReadings: 99, targetInstrumentId: 7, readingKey: 'time' },
      { fieldKey: 'F8', label: 'F8 · 6速粘度计',   unit: '', maxReadings: 99, targetInstrumentId: 8, readingKey: 'actual_reading' },
    ],
  },
}

export const EXPERIMENT_TYPE_LIST = Object.values(EXPERIMENT_SCHEMAS)
