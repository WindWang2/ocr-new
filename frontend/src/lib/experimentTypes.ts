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
  test: {
    type: 'test',
    label: '测试模板',
    description: '9个相机位置，选择相机后可选读数，支持多次拍照显示图片',
    icon: '📷',
    manualParams: [],
    cameraFields: [
      { fieldKey: 'F0', label: '位置0', unit: '', maxReadings: 99 },
      { fieldKey: 'F1', label: '位置1', unit: '', maxReadings: 99 },
      { fieldKey: 'F2', label: '位置2', unit: '', maxReadings: 99 },
      { fieldKey: 'F3', label: '位置3', unit: '', maxReadings: 99 },
      { fieldKey: 'F4', label: '位置4', unit: '', maxReadings: 99 },
      { fieldKey: 'F5', label: '位置5', unit: '', maxReadings: 99 },
      { fieldKey: 'F6', label: '位置6', unit: '', maxReadings: 99 },
      { fieldKey: 'F7', label: '位置7', unit: '', maxReadings: 99 },
      { fieldKey: 'F8', label: '位置8', unit: '', maxReadings: 99 },
    ],
  },
}

export const EXPERIMENT_TYPE_LIST = Object.values(EXPERIMENT_SCHEMAS)
