'use client'

import { useState, useEffect } from 'react'
import { Reading } from '@/types'
import { triggerInstrument, runTestCapture, saveManualReading } from '@/lib/api'
import { Camera, RefreshCw, AlertCircle, ScanSearch, Binary, Hash } from 'lucide-react'

interface Props {
  experimentId: number
  fieldKey: string
  instrumentId: number
  label: string
  unit: string
  slotIndex: number
  reading: Reading | null
  onComplete: () => Promise<void> | void
  instrumentFields?: { key: string, label: string, unit: string }[]
}

export default function ManualInstrumentSlot({
  experimentId, fieldKey, instrumentId, label, unit, slotIndex, reading, onComplete, instrumentFields
}: Props) {
  const [error, setError] = useState<string | null>(null)
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [phase, setPhase] = useState<'idle' | 'capturing' | 'recognizing'>('idle')
  const [previewImage, setPreviewImage] = useState<string | null>(null)

  useEffect(() => {
    if (reading) {
      const initial: Record<string, string> = {}
      if (reading.ocr_data && Object.keys(reading.ocr_data).length > 0) {
        Object.entries(reading.ocr_data).forEach(([k, v]) => {
          initial[k] = String(v)
        })
      } else {
        if (instrumentFields && instrumentFields.length > 0) {
          initial[instrumentFields[0].key] = String(reading.value)
        }
      }
      setFieldValues(initial)
      setPreviewImage(null)
    } else {
      setFieldValues({})
    }
  }, [reading, instrumentFields])

  const handleCapture = async () => {
    if (phase !== 'idle') return
    setPhase('capturing')
    setError(null)
    setPreviewImage(null)
    
    try {
      const triggerRes = await triggerInstrument(experimentId, fieldKey, instrumentId)
      if (triggerRes.cropped_image_path) setPreviewImage(triggerRes.cropped_image_path)
      
      setPhase('recognizing')
      const ocrResult = await runTestCapture(
        experimentId, fieldKey, triggerRes.camera_id || 0,
        triggerRes.cropped_image_path || triggerRes.image_path,
        undefined, slotIndex, false, undefined, instrumentId
      )
      
      if (!ocrResult.success) setError(ocrResult.detail || '识别失败')
      await onComplete()
    } catch (e: any) {
      setError(e.message || '采集失败')
    } finally {
      setPhase('idle')
    }
  }

  const handleFieldChange = (key: string, val: string) => {
    setFieldValues(prev => ({ ...prev, [key]: val }))
  }

  const handleFieldBlur = async () => {
    try {
      const ocrData: Record<string, number | string> = {}
      Object.entries(fieldValues).forEach(([k, v]) => {
        const num = parseFloat(v)
        ocrData[k] = isNaN(num) ? v : num
      })
      const mainValue = parseFloat(Object.values(fieldValues)[0] || '0')
      await saveManualReading(experimentId, fieldKey, slotIndex, isNaN(mainValue) ? 0 : mainValue, instrumentId, ocrData)
      await onComplete()
    } catch (e) {
      setError('保存失败')
    }
  }

  const displayImage = reading?.image_path

  return (
    <div className="module-card flex flex-col h-full group">
      {/* Module Header */}
      <div className="module-header">
        <div className="flex items-center gap-2">
          <Binary size={12} className="text-[var(--text-muted)]" />
          <span className="module-title">Sensor Unit F{instrumentId}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono-num text-[var(--text-muted)] bg-white px-1.5 rounded border border-[var(--border)]">
            IDX: {slotIndex}
          </span>
          <div className={`status-dot ${reading ? 'status-dot-active' : 'bg-gray-200'}`} />
        </div>
      </div>

      {/* Optical Input Section */}
      <div 
        className="relative aspect-video bg-black flex items-center justify-center cursor-pointer overflow-hidden border-b border-[var(--border)]"
        onClick={handleCapture}
      >
        {(displayImage || previewImage) ? (
          <img 
            src={`/images/${previewImage || displayImage}`} 
            className={`w-full h-full object-cover transition-all duration-500 ${phase !== 'idle' ? 'opacity-30 blur-sm scale-110' : 'opacity-80 hover:opacity-100'}`} 
            alt="Capture" 
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-zinc-700 group-hover:text-zinc-500 transition-colors">
            <Camera size={32} strokeWidth={1.5} />
            <span className="text-[9px] font-bold uppercase tracking-widest">Awaiting Capture</span>
          </div>
        )}

        {/* Phase Overlays */}
        {phase !== 'idle' && (
          <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-3">
             <div className="relative">
                <RefreshCw size={24} className="animate-spin text-[var(--accent)]" />
                <ScanSearch size={10} className="absolute inset-0 m-auto text-white" />
              </div>
              <span className="text-[9px] font-bold text-white uppercase tracking-[0.2em] animate-pulse">
                {phase === 'capturing' ? 'Aligning Optics' : 'Neural Inference'}
              </span>
          </div>
        )}

        {/* Confidence Overlay */}
        {reading?.confidence && phase === 'idle' && (
          <div className="absolute bottom-2 left-2 bg-black/50 backdrop-blur-md px-2 py-0.5 rounded border border-white/20">
            <span className="text-[9px] font-mono-num text-[var(--accent)]">
              CONF: {(reading.confidence * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Data Interface Section */}
      <div className="p-3 flex-1 flex flex-col bg-zinc-50/50">
        <div className="mb-3">
          <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-tight truncate">
            {label}
          </h3>
          <p className="text-[10px] text-[var(--text-muted)] font-medium leading-none mt-0.5">
            Manual Override Enabled
          </p>
        </div>

        <div className="space-y-2 flex-1">
          {instrumentFields && instrumentFields.length > 0 ? (
            instrumentFields.map((f) => (
              <div key={f.key} className="flex items-center">
                <div className="flex-1 flex items-center bg-white border border-[var(--border)] rounded px-1.5 py-1 focus-within:border-[var(--text-secondary)] transition-colors">
                  <label className="text-[9px] font-bold text-[var(--text-secondary)] w-[76px] shrink-0 whitespace-nowrap leading-none">
                    {f.label}
                  </label>
                  <input
                    type="text"
                    value={fieldValues[f.key] || ''}
                    onChange={(e) => handleFieldChange(f.key, e.target.value)}
                    onBlur={handleFieldBlur}
                    placeholder="NULL"
                    className="flex-1 bg-transparent border-none text-[11px] font-mono-num font-bold text-[var(--text-primary)] focus:ring-0 p-0 text-right min-w-0"
                  />
                  {f.unit && (
                    <span className="text-[9px] font-bold text-[var(--text-muted)] ml-1 shrink-0">{f.unit}</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="h-20 flex flex-col items-center justify-center border border-dashed border-[var(--border)] rounded bg-white">
              <Hash size={16} className="text-zinc-200 mb-1" />
              <span className="text-[9px] font-bold text-zinc-300 uppercase">Load Templates</span>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 p-2 bg-red-50 border border-red-100 rounded">
            <AlertCircle size={12} className="text-red-500 shrink-0" />
            <p className="text-[9px] text-red-600 font-bold uppercase truncate">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}