export type ExperimentType =
  | 'kinematic_viscosity'
  | 'apparent_viscosity'
  | 'surface_tension'
  | 'test'

export interface CameraFieldConfig {
  field_key: string
  camera_id: number
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
  onRefresh: () => Promise<void>  // 拍照完成后刷新实验数据
}

export type LLMProviderType = 'openai_compatible'

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

export type LLMStatus = 'connected' | 'error' | 'loading' | 'unknown'
