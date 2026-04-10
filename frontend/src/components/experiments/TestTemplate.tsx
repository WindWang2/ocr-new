'use client'
import { useState, useEffect, useCallback } from 'react'
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { getCameraInstruments, captureImage, runTestCapture } from '@/lib/api'
import { ocrLabel } from '@/lib/ocrLabels'
import { Camera, RefreshCw, ScanSearch } from 'lucide-react'

export default function TestTemplate({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.test
  const [instruments, setInstruments] = useState<Record<string, { name: string; readings: { key: string; label: string; unit: string }[] }>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [warns, setWarns] = useState<Record<string, string>>({})
  const [pendingImages, setPendingImages] = useState<Record<string, string>>({})
  const [phase, setPhase] = useState<Record<string, 'idle' | 'capturing' | 'recognizing'>>({})
  const [precising, setPrecising] = useState<Record<string, boolean>>({})
  const [allOcrMap, setAllOcrMap] = useState<Record<string, Record<string, number | string | null>>>({})
  // F0 专用：手动/自动模式（从绑定配置中读取默认值）
  const f0Config = experiment.camera_configs.find(c => c.field_key === 'F0')
  const [f0Mode, setF0Mode] = useState<'auto' | 'manual'>(
    (f0Config?.camera_mode as 'auto' | 'manual') ?? 'auto'
  )

  useEffect(() => {
    getCameraInstruments().then(setInstruments).catch(() => {})
  }, [])

  const getCameraMode = (fieldKey: string) => fieldKey === 'F0' ? f0Mode : undefined

  const handlePrecise = useCallback(async (fieldKey: string, cameraId: number, readingKey: string, imgPath: string, cameraMode?: string) => {
    setErrors(prev => ({ ...prev, [fieldKey]: '' }))
    setWarns(prev => ({ ...prev, [fieldKey]: '' }))
    setAllOcrMap(prev => ({ ...prev, [fieldKey]: {} }))
    setPrecising(prev => ({ ...prev, [fieldKey]: true }))
    try {
      const result = await runTestCapture(
        experiment.id, fieldKey, cameraId, imgPath, readingKey, undefined, true, cameraMode
      )
      if (result.all_ocr) setAllOcrMap(prev => ({ ...prev, [fieldKey]: result.all_ocr! }))
      if (!result.success) {
        setErrors(prev => ({ ...prev, [fieldKey]: result.detail || '精准识别失败' }))
      } else {
        if (result.detail) setWarns(prev => ({ ...prev, [fieldKey]: result.detail! }))
        await onRefresh()
      }
    } catch (e: unknown) {
      setErrors(prev => ({ ...prev, [fieldKey]: e instanceof Error ? e.message : '精准识别失败' }))
    } finally {
      setPrecising(prev => ({ ...prev, [fieldKey]: false }))
    }
  }, [experiment.id, onRefresh])

  const handleCapture = useCallback(async (fieldKey: string, cameraId: number, readingKey: string, cameraMode?: string) => {
    setErrors(prev => ({ ...prev, [fieldKey]: '' }))
    setWarns(prev => ({ ...prev, [fieldKey]: '' }))
    setAllOcrMap(prev => ({ ...prev, [fieldKey]: {} }))
    try {
      setPhase(prev => ({ ...prev, [fieldKey]: 'capturing' }))
      const captureResult = await captureImage(experiment.id, cameraId)
      if (captureResult.image_path) {
        setPendingImages(prev => ({ ...prev, [fieldKey]: captureResult.image_path! }))
      }

      setPhase(prev => ({ ...prev, [fieldKey]: 'recognizing' }))
      const result = await runTestCapture(
        experiment.id, fieldKey, cameraId, captureResult.image_path, readingKey,
        undefined, false, cameraMode
      )
      if (result.all_ocr) setAllOcrMap(prev => ({ ...prev, [fieldKey]: result.all_ocr! }))
      if (!result.success) {
        setErrors(prev => ({ ...prev, [fieldKey]: result.detail || '识别失败' }))
      } else {
        if (result.detail) setWarns(prev => ({ ...prev, [fieldKey]: result.detail! }))
        await onRefresh()
      }
      setPendingImages(prev => { const n = { ...prev }; delete n[fieldKey]; return n })
    } catch (e: unknown) {
      setErrors(prev => ({ ...prev, [fieldKey]: e instanceof Error ? e.message : '失败' }))
      setPendingImages(prev => { const n = { ...prev }; delete n[fieldKey]; return n })
    } finally {
      setPhase(prev => ({ ...prev, [fieldKey]: 'idle' }))
    }
  }, [experiment.id, onRefresh])

  return (
    <div className="space-y-4">
      {schema.cameraFields.map(field => {
        const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
        if (!config) return null
        const cameraId = config.camera_id
        const instrument = instruments[`F${cameraId}`] || { name: '', readings: [] }
        const currentPhase = phase[field.fieldKey] || 'idle'
        const isBusy = currentPhase !== 'idle'
        const isPrecising = precising[field.fieldKey] || false
        const pendingImage = pendingImages[field.fieldKey]
        const allOcr = allOcrMap[field.fieldKey] || {}
        const isF0 = field.fieldKey === 'F0'
        const cameraMode = isF0 ? f0Mode : undefined

        const fieldReadings = experiment.readings
          .filter(r => r.field_key === field.fieldKey)
          .sort((a, b) => a.run_index - b.run_index)

        const displayImage = pendingImage ?? fieldReadings[fieldReadings.length - 1]?.image_path ?? null
        const ocrEntries = Object.entries(allOcr).filter(([, v]) => v !== null)

        return (
          <div key={field.fieldKey} className="border border-gray-100 rounded-xl p-5 bg-white hover:shadow-sm transition-shadow">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="font-semibold text-gray-800 text-sm">{field.label}</div>
                <div className="text-[11px] text-gray-400 mt-0.5">F{cameraId} · {instrument.name}</div>
              </div>
              <div className="flex items-center gap-2 flex-wrap justify-end">
                {/* F0 专用模式切换 */}
                {isF0 && (
                  <div className="flex rounded-lg overflow-hidden border border-gray-200 text-xs">
                    <button
                      onClick={() => setF0Mode('auto')}
                      className={`px-3 py-1.5 font-medium transition ${
                        f0Mode === 'auto' ? 'bg-brand-500 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'
                      }`}
                      style={f0Mode === 'auto' ? { background: 'var(--brand)' } : undefined}
                    >自动模式</button>
                    <button
                      onClick={() => setF0Mode('manual')}
                      className={`px-3 py-1.5 font-medium transition border-l border-gray-200 ${
                        f0Mode === 'manual' ? 'bg-brand-500 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'
                      }`}
                      style={f0Mode === 'manual' ? { background: 'var(--brand)' } : undefined}
                    >手动模式</button>
                  </div>
                )}
                <button
                  onClick={() => handleCapture(field.fieldKey, cameraId, field.readingKey, cameraMode)}
                  disabled={isBusy || isPrecising}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition ${
                    isBusy || isPrecising ? 'bg-gray-100 text-gray-400 cursor-wait' : 'text-white hover:opacity-90 shadow-sm'
                  }`}
                  style={!(isBusy || isPrecising) ? { background: 'var(--brand)' } : undefined}
                >
                  {isBusy
                    ? <><RefreshCw size={14} className="animate-spin" />{currentPhase === 'capturing' ? '拍摄中' : '识别中'}</>
                    : <><Camera size={14} />拍照识别</>}
                </button>
                <button
                  onClick={() => { const img = pendingImage ?? displayImage; if (img) handlePrecise(field.fieldKey, cameraId, field.readingKey, img, cameraMode) }}
                  disabled={!displayImage || isPrecising || isBusy}
                  title="精准识别：OCR提取文字后二次读数"
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition ${
                    !displayImage || isPrecising || isBusy
                      ? 'border-gray-200 text-gray-300 cursor-not-allowed'
                      : 'border-purple-200 text-purple-600 hover:bg-purple-50'
                  }`}
                >
                  {isPrecising ? <RefreshCw size={13} className="animate-spin" /> : <ScanSearch size={13} />}
                  精准识别
                </button>
              </div>
            </div>

            {warns[field.fieldKey] && (
              <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 mb-3">{warns[field.fieldKey]}</p>
            )}
            {errors[field.fieldKey] && (
              <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2 mb-3">{errors[field.fieldKey]}</p>
            )}

            {displayImage && (
              <div className="flex gap-3 items-start mb-3">
                <div className="relative shrink-0">
                  <img
                    src={`/images/${displayImage}`}
                    alt={field.label}
                    className="w-56 h-40 object-cover rounded-lg border border-gray-200 bg-gray-100"
                  />
                  {(isBusy || isPrecising) && (
                    <div className="absolute inset-0 bg-white/70 flex flex-col items-center justify-center gap-1 rounded-lg">
                      <RefreshCw size={16} className="animate-spin text-brand-500" />
                      <span className="text-[11px] text-brand-500">
                        {isPrecising ? '精准识别中' : currentPhase === 'capturing' ? '拍摄中' : '识别中'}
                      </span>
                    </div>
                  )}
                </div>
                {ocrEntries.length > 0 && (
                  <div className="bg-gray-50 rounded-lg px-3 py-2 border border-gray-100 space-y-1 min-w-[140px]">
                    {ocrEntries.map(([k, v]) => (
                      <div key={k} className={`flex justify-between gap-4 text-[11px] ${k === field.readingKey ? 'text-brand-600 font-semibold' : 'text-gray-500'}`}>
                        <span>{ocrLabel(k)}</span>
                        <span className="tabular-nums">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {fieldReadings.length > 0 && (
              <div className="space-y-1">
                {fieldReadings.map((r, i) => (
                  <div key={r.id} className="flex items-center gap-3 text-sm bg-gray-50/80 rounded-lg px-3 py-1.5">
                    <span className="text-gray-400 text-xs w-6">#{i + 1}</span>
                    <span className="font-semibold text-gray-800 tabular-nums">{r.value}</span>
                    <span className="text-gray-400 text-xs">{field.unit}</span>
                    <span className="text-[11px] text-gray-300 ml-auto">
                      {r.timestamp ? new Date(r.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {!displayImage && fieldReadings.length === 0 && !errors[field.fieldKey] && (
              <p className="text-xs text-gray-300 text-center py-2">暂无读数，点击拍照开始</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
