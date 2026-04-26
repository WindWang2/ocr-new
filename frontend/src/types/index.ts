export type ExperimentType =
  | 'kinematic_viscosity'
  | 'apparent_viscosity'
  | 'surface_tension'
  | 'water_mineralization'
  | 'ph_value'
  | 'test'

export interface InstrumentFieldConfig {
  field_key: string
  instrument_id: number // 对应 YOLO 类别 0-8
  max_readings: number
  selected_readings?: string[]
  camera_mode?: string  // F0专用：'auto' | 'manual'
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
  ocr_data?: Record<string, any>
}

export interface Experiment {
  id: number
  name: string
  type: ExperimentType
  manual_params: ManualParams
  instrument_configs: InstrumentFieldConfig[] // 替代 camera_configs
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
  onRefresh: () => Promise<void>  // 拍照完成后刷新实验数据
}

export type LLMProviderType = 'openai_compatible' | 'local_vlm'

export interface LLMConfig {
  provider: LLMProviderType
  model_name: string
  base_url: string
  api_key: string | null
  temperature: number
  max_tokens: number
}

export interface LLMModel {
  name: string
  size: number
  modified_at: string
}

export interface GPUInfo {
  name: string
  memory_allocated: string
  memory_reserved: string
}

export type LLMStatus = 'connected' | 'ready' | 'error' | 'loading' | 'unknown'

export interface TemplateField {
  name: string
  label: string
  unit: string
  type: string
}

export interface InstrumentTemplate {
  id?: number
  instrument_type: string
  name: string
  description: string
  prompt_template: string
  fields: TemplateField[]
  keywords: string[]
  example_images: string[]
  default_tier: number
  created_at?: string
}

export interface Camera {
  id: number
  name: string
  camera_id: number
  control_host: string
  control_port: number
  mode: string
  enabled: number
}
