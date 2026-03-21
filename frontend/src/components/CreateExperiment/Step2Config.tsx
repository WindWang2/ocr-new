'use client'
import { useState } from 'react'
import { ExperimentType, CameraFieldConfig, ManualParams } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { ArrowLeft, Camera } from 'lucide-react'

const CAMERA_OPTIONS = Array.from({ length: 9 }, (_, i) => i)

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
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-gray-100 transition">
          <ArrowLeft size={18} className="text-gray-400" />
        </button>
        <div>
          <div className="font-semibold text-gray-800">{name}</div>
          <div className="text-xs text-gray-400 mt-0.5">{schema.icon} {schema.label}</div>
        </div>
      </div>

      {/* Manual params */}
      {schema.manualParams.length > 0 && (
        <div className="bg-gray-50/80 rounded-xl p-5 space-y-3 border border-gray-100">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">实验参数</h3>
          {schema.manualParams.map(param => (
            <div key={param.key} className="flex items-center gap-3">
              <label className="text-sm text-gray-600 w-40 shrink-0">{param.label}</label>
              <input
                type={param.type}
                value={manualParams[param.key] ?? ''}
                onChange={e => setManualParams(prev => ({ ...prev, [param.key]: e.target.value }))}
                className="flex-1 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm"
                placeholder={`输入${param.label}`}
              />
              <span className="text-xs text-gray-400 w-16 shrink-0 text-right">{param.unit}</span>
            </div>
          ))}
        </div>
      )}

      {/* Camera binding */}
      <div className="rounded-xl p-5 space-y-3 border" style={{ background: 'var(--brand-light)', borderColor: 'rgba(46,94,170,0.15)' }}>
        <div className="flex items-center gap-2">
          <Camera size={14} className="text-brand-500" />
          <h3 className="text-xs font-semibold text-brand-600 uppercase tracking-wider">相机绑定</h3>
        </div>
        {schema.cameraFields.map((field, idx) => (
          <div key={field.fieldKey} className="flex items-center gap-3 bg-white/60 rounded-lg px-3 py-2.5">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">{field.label}</div>
              {field.unit && <div className="text-[11px] text-gray-400">{field.unit}</div>}
            </div>
            <select
              value={cameraConfigs[idx]?.camera_id ?? 0}
              onChange={e => updateCamera(idx, Number(e.target.value))}
              className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm"
            >
              {CAMERA_OPTIONS.map(c => (
                <option key={c} value={c}>相机 {c}</option>
              ))}
            </select>
            <span className="text-[11px] text-gray-400 w-14 shrink-0 text-right">
              最多 {field.maxReadings} 次
            </span>
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-red-500 bg-red-50 rounded-lg px-4 py-2">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-3 text-white rounded-xl font-medium text-sm transition hover:opacity-90 disabled:opacity-50 shadow-sm"
        style={{ background: 'var(--brand)' }}
      >
        {loading ? '创建中...' : '创建实验'}
      </button>
    </div>
  )
}
