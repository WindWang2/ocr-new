'use client'
import { useState, useEffect } from 'react'
import { ExperimentType, CameraFieldConfig, ManualParams } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { getCameraInstruments } from '@/lib/api'
import { ArrowLeft, Camera, ChevronDown } from 'lucide-react'

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
    schema.cameraFields.map(f => ({
      field_key: f.fieldKey,
      camera_id: f.defaultCameraId,
      max_readings: f.maxReadings,
    }))
  )
  const [error, setError] = useState('')

  // 相机仪器映射数据
  const [instruments, setInstruments] = useState<Record<string, { name: string; readings: { key: string; label: string; unit: string }[] }>>({})
  const [selectedReadings, setSelectedReadings] = useState<Record<number, string[]>>(() =>
    Object.fromEntries(schema.cameraFields.map((f, i) => [i, []]))
  )

  useEffect(() => {
    getCameraInstruments().then(data => {
      setInstruments(data)
      // 默认选中所有读数
      const defaults: Record<number, string[]> = {}
      schema.cameraFields.forEach((f, i) => {
        const cameraId = cameraConfigs[i]?.camera_id ?? f.defaultCameraId
        defaults[i] = (data[`F${cameraId}`]?.readings || []).map(r => r.key)
      })
      setSelectedReadings(defaults)
    }).catch(() => {})
  }, [type])

  const updateCamera = (index: number, cameraId: number) => {
    setCameraConfigs(prev => prev.map((c, i) => i === index ? { ...c, camera_id: cameraId } : c))
    // 切换相机时自动选中该相机所有读数
    const readings = instruments[`F${cameraId}`]?.readings || []
    setSelectedReadings(prev => ({ ...prev, [index]: readings.map(r => r.key) }))
  }

  const toggleReading = (positionIndex: number, readingKey: string) => {
    setSelectedReadings(prev => {
      const current = prev[positionIndex] || []
      const next = current.includes(readingKey)
        ? current.filter(k => k !== readingKey)
        : [...current, readingKey]
      return { ...prev, [positionIndex]: next }
    })
  }

  const handleSubmit = async () => {
    setError('')
    const configs = cameraConfigs.map((c, i) => ({
      ...c,
      selected_readings: selectedReadings[i] || [],
    }))
    await onSubmit(manualParams, configs).catch(e => setError(e.message))
  }

  const getInstrumentName = (cameraId: number) => {
    const key = `F${cameraId}`
    return instruments[key]?.name || ''
  }

  const getReadings = (cameraId: number) => {
    const key = `F${cameraId}`
    return instruments[key]?.readings || []
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
        {schema.cameraFields.map((field, idx) => {
          const cameraId = cameraConfigs[idx]?.camera_id ?? 0
          const instrumentName = getInstrumentName(cameraId)
          const readings = getReadings(cameraId)
          const selected = selectedReadings[idx] || []
          return (
            <div key={field.fieldKey} className="bg-white/60 rounded-lg px-3 py-3 space-y-2.5">
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700">{field.label}</div>
                  {instrumentName && <div className="text-[11px] text-brand-500">{instrumentName}</div>}
                  {field.description && (
                    <div className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">{field.description}</div>
                  )}
                </div>
                <select
                  value={cameraId}
                  onChange={e => updateCamera(idx, Number(e.target.value))}
                  disabled={type === 'test'}
                  className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm disabled:opacity-50 cursor-pointer"
                >
                  {CAMERA_OPTIONS.map(c => (
                    <option key={c} value={c}>
                      F{c} {instruments[`F${c}`]?.name || ''}
                    </option>
                  ))}
                </select>
              </div>
              {/* 读数选择 */}
              {readings.length > 0 && (
                <div className="ml-1">
                  <div className="text-[11px] text-gray-500 mb-1.5">选择需要显示的读数：</div>
                  <div className="flex flex-wrap gap-1.5">
                    {readings.map(r => {
                      const isSelected = selected.includes(r.key)
                      return (
                        <button
                          key={r.key}
                          onClick={() => toggleReading(idx, r.key)}
                          className={`px-2 py-1 rounded text-[11px] transition border ${
                            isSelected
                              ? 'bg-brand-500 text-white border-brand-500'
                              : 'bg-gray-50 text-gray-500 border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {r.label}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
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
