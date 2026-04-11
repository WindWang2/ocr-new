import { Experiment, ExperimentSummary, Reading, CameraFieldConfig, ManualParams, ExperimentType, LLMConfig, LLMModel, LLMStatus, InstrumentTemplate } from '@/types'

const BASE = process.env.NEXT_PUBLIC_API_URL || '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new Error('无法连接到后端服务，请确认后端已启动（端口 8001）')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || `服务器错误 (${res.status})`)
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

export async function deleteExperiment(id: number): Promise<void> {
  await request(`/experiments/${id}`, { method: 'DELETE' })
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
  if (!data.success || !data.reading) throw new Error(data.detail || 'OCR 识别失败')
  return data.reading
}

export function exportUrl(experimentId: number): string {
  return `/api/experiments/${experimentId}/export`
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

export async function listLLMModels(baseUrl?: string): Promise<LLMModel[]> {
  const query = baseUrl ? `?base_url=${encodeURIComponent(baseUrl)}` : ''
  const data = await request<{ success: boolean; models: LLMModel[] }>(`/config/llm/models${query}`)
  return data.models
}

export async function checkLLMStatus(): Promise<{ success: boolean; status: LLMStatus; model?: string; provider?: string; detail?: string }> {
  return request('/config/llm/status')
}

export async function getCameraInstruments(): Promise<Record<string, { name: string; readings: { key: string; label: string; unit: string }[] }>> {
  const data = await request<{ success: boolean; cameras: Record<string, { name: string; readings: { key: string; label: string; unit: string }[] }> }>('/config/camera-instruments')
  return data.cameras
}

export async function captureImage(
  experimentId: number,
  cameraId: number,
): Promise<{ success: boolean; image_path?: string; camera_id?: number; detail?: string }> {
  const data = await request<{ success: boolean; image_path?: string; camera_id?: number; detail?: string }>(
    `/experiments/${experimentId}/capture`,
    {
      method: 'POST',
      body: JSON.stringify({ camera_id: cameraId }),
    },
  )
  if (!data.success) throw new Error(data.detail || '拍照失败')
  return data
}

interface RunTestBody {
  field_key: string
  camera_id: number
  image_path?: string
  reading_key?: string
  run_index?: number
  precise?: boolean
  camera_mode?: string
}

export async function runTestCapture(
  experimentId: number,
  fieldKey: string,
  cameraId: number,
  imagePath?: string,
  readingKey?: string,
  runIndex?: number,
  precise?: boolean,
  cameraMode?: string,
): Promise<{ success: boolean; readings?: Reading[]; all_ocr?: Record<string, number | string | null>; detail?: string }> {
  const body: RunTestBody = { field_key: fieldKey, camera_id: cameraId }
  if (imagePath) body.image_path = imagePath
  if (readingKey) body.reading_key = readingKey
  if (runIndex !== undefined) body.run_index = runIndex
  if (precise) body.precise = true
  if (cameraMode) body.camera_mode = cameraMode
  const data = await request<{ success: boolean; readings?: Reading[]; all_ocr?: Record<string, number | string | null>; detail?: string }>(
    `/experiments/${experimentId}/run-test`,
    { method: 'POST', body: JSON.stringify(body) },
  )
  // 即使识别失败，如果有 all_ocr 数据也返回给前端展示（不抛出）
  if (!data.success && !data.all_ocr) throw new Error(data.detail || '识别失败')
  return data
}

export async function saveManualReading(
  experimentId: number,
  fieldKey: string,
  runIndex: number,
  value: number,
  cameraId: number = 0,
): Promise<Reading> {
  const data = await request<{ success: boolean; reading: Reading }>(
    `/experiments/${experimentId}/readings`,
    {
      method: 'PUT',
      body: JSON.stringify({ field_key: fieldKey, run_index: runIndex, value, camera_id: cameraId }),
    },
  )
  return data.reading
}

export async function getImageDir(): Promise<string> {
  const data = await request<{ image_dir: string }>('/config/image-dir')
  return data.image_dir
}

export async function setImageDir(imageDir: string): Promise<void> {
  await request('/config/image-dir', {
    method: 'POST',
    body: JSON.stringify({ image_dir: imageDir }),
  })
}

export async function listTemplates(): Promise<InstrumentTemplate[]> {
  const data = await request<{ success: boolean; templates: InstrumentTemplate[] }>('/templates')
  return data.templates
}

export async function saveTemplate(template: InstrumentTemplate): Promise<void> {
  await request('/templates', {
    method: 'POST',
    body: JSON.stringify(template),
  })
}
