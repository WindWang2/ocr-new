import { Experiment, ExperimentSummary, Reading, CameraFieldConfig, ManualParams, ExperimentType, LLMConfig, OllamaModel, LLMStatus } from '@/types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`)
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

export async function getMockConfig(): Promise<boolean> {
  const data = await request<{ mock_enabled: boolean }>('/config/mock')
  return data.mock_enabled
}

export async function setMockConfig(enabled: boolean): Promise<void> {
  await request('/config/mock', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  })
}

export async function getLLMConfig(): Promise<LLMConfig> {
  const data = await request<{ success: boolean; config: LLMConfig }>('/config/llm')
  return data.config
}

export async function setLLMConfig(config: LLMConfig): Promise<void> {
  await request('/config/llm', {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

export async function listOllamaModels(baseUrl?: string): Promise<OllamaModel[]> {
  const query = baseUrl ? `?base_url=${encodeURIComponent(baseUrl)}` : ''
  const data = await request<{ success: boolean; models: OllamaModel[] }>(`/config/llm/models${query}`)
  return data.models
}

export async function checkLLMStatus(): Promise<{ success: boolean; status: LLMStatus; model?: string; provider?: string; detail?: string }> {
  return request('/config/llm/status')
}
