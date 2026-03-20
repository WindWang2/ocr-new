'use client'
import { useState } from 'react'
import { ExperimentType, CameraFieldConfig, ManualParams } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { ArrowLeft } from 'lucide-react'

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
