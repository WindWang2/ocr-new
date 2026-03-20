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

export type LLMProviderType = 'ollama' | 'openai_compatible'

export interface LLMConfig {
  provider: LLMProviderType
  model_name: string
  base_url: string
  api_key: string | null
  temperature: number
  max_tokens: number
}

export interface OllamaModel {
  name: string
  size: number
  modified_at: string
}

export type LLMStatus = 'connected' | 'error' | 'loading' | 'unknown'
