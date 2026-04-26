'use client'
import { useState, useEffect } from 'react'
import { ExperimentType, InstrumentFieldConfig, ManualParams } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { getCameraInstruments } from '@/lib/api'
import { ArrowLeft, Cpu, ChevronDown } from 'lucide-react'

const CAMERA_OPTIONS = Array.from({ length: 9 }, (_, i) => i)

interface Props {
  name: string
  type: ExperimentType
  onBack: () => void
  onSubmit: (manualParams: ManualParams, instrumentConfigs: InstrumentFieldConfig[]) => Promise<void>
  loading: boolean
}

export default function Step2Config({ name, type, onBack, onSubmit, loading }: Props) {
  const schema = EXPERIMENT_SCHEMAS[type]
  const [manualParams, setManualParams] = useState<ManualParams>(() =>
    Object.fromEntries(schema.manualParams.map(p => [p.key, '']))
  )
  const [instrumentConfigs, setInstrumentConfigs] = useState<InstrumentFieldConfig[]>(() =>
    schema.instrumentFields.map(f => ({
      field_key: f.fieldKey,
      instrument_id: f.targetInstrumentId,
      max_readings: f.maxReadings,
    }))
  )
  const [error, setError] = useState('')

  // 仪器显示数据
  const [instruments, setInstruments] = useState<Record<string, { name: string; readings: { key: string; label: string; unit: string }[] }>>({})
  const [selectedReadings, setSelectedReadings] = useState<Record<number, string[]>>(() =>
    Object.fromEntries(schema.instrumentFields.map((f, i) => [i, []]))
  )
  // D0 混调器专用：手动/自动模式
  const [d0Mode, setD0Mode] = useState<'auto' | 'manual'>('auto')

  useEffect(() => {
    getCameraInstruments().then(data => {
      setInstruments(data)
      const defaults: Record<number, string[]> = {}
      schema.instrumentFields.forEach((f, i) => {
        if (type === 'test') {
          // 测试模板默认选中所有读数
          defaults[i] = (data[`D${f.targetInstrumentId}`]?.readings || []).map(r => r.key)
        } else {
          // 模板实验默认只选 schema 中指定的一种读数
          defaults[i] = [f.readingKey]
        }
      })
      setSelectedReadings(defaults)
    }).catch(() => {})
  }, [type])

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
    const configs = instrumentConfigs.map((c, i) => {
      const fieldKey = schema.instrumentFields[i]?.fieldKey
      const cfg: typeof c & { selected_readings: string[]; camera_mode?: string } = {
        ...c,
        selected_readings: selectedReadings[i] || [],
      }
      if (fieldKey === 'D0') cfg.camera_mode = d0Mode
      return cfg
    })
    await onSubmit(manualParams, configs).catch(e => setError(e.message))
  }

  const getInstrumentName = (instrumentId: number) => {
    const key = `D${instrumentId}`
    return instruments[key]?.name || ''
  }

  const getReadings = (instrumentId: number) => {
    const key = `D${instrumentId}`
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

      {/* Instrument Selection (Auto-bound) */}
      <div className="rounded-xl p-5 space-y-3 border" style={{ background: 'var(--brand-light)', borderColor: 'rgba(46,94,170,0.15)' }}>
        <div className="flex items-center gap-2">
          <Cpu size={14} className="text-brand-500" />
          <h3 className="text-xs font-semibold text-brand-600 uppercase tracking-wider">仪器配置</h3>
        </div>
        <p className="text-[11px] text-gray-400 mb-2">系统将自动定位以下仪器并读取数据</p>
        
        {schema.instrumentFields.map((field, idx) => {
          const instrumentId = field.targetInstrumentId
          const instrumentName = getInstrumentName(instrumentId)
          const readings = getReadings(instrumentId)
          const selected = selectedReadings[idx] || []
          const isD0 = field.fieldKey === 'D0'
          return (
            <div key={field.fieldKey} className="bg-white/60 rounded-lg px-3 py-3 space-y-2.5 border border-gray-100/50">
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700">{field.label}</div>
                  <div className="text-[11px] font-mono text-brand-500 uppercase tracking-tighter">
                    {instrumentName || `仪器类别 #${instrumentId}`}
                  </div>
                </div>
                {/* D0 专用：自动/手动模式选择 */}
                {isD0 && (
                  <div className="flex rounded-lg overflow-hidden border border-gray-200 text-xs shrink-0">
                    <button
                      type="button"
                      onClick={() => setD0Mode('auto')}
                      className={`px-3 py-1.5 font-medium transition ${
                        d0Mode === 'auto' ? 'text-white' : 'bg-white text-gray-500 hover:bg-gray-50'
                      }`}
                      style={d0Mode === 'auto' ? { background: 'var(--brand)' } : undefined}
                    >自动模式</button>
                    <button
                      type="button"
                      onClick={() => setD0Mode('manual')}
                      className={`px-3 py-1.5 font-medium transition border-l border-gray-200 ${
                        d0Mode === 'manual' ? 'text-white' : 'bg-white text-gray-500 hover:bg-gray-50'
                      }`}
                      style={d0Mode === 'manual' ? { background: 'var(--brand)' } : undefined}
                    >手动模式</button>
                  </div>
                )}
              </div>
              {/* 读数选择 */}
              {readings.length > 0 && (
                <div className="ml-1">
                  <div className="text-[11px] text-gray-500 mb-1.5 font-medium">展示字段：</div>
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
