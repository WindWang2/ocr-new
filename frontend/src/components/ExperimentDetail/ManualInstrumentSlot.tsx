'use client'

import { useState, useEffect } from 'react'
import { Reading } from '@/types'
import { triggerInstrument, runTestCapture, saveManualReading } from '@/lib/api'
import { Camera, RefreshCw, AlertCircle, ScanSearch, Binary, Hash, Eye, Cpu } from 'lucide-react'

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
  const [viewMode, setViewMode] = useState<'crop' | 'neural' | 'context'>('crop')

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
      
      if (!ocrResult.success) {
        setError(ocrResult.detail || '识别失败')
      } else {
        // Force update local fieldValues from the successful OCR result
        if (ocrResult.all_ocr && Object.keys(ocrResult.all_ocr).length > 0) {
          const newVals: Record<string, string> = {}
          Object.entries(ocrResult.all_ocr).forEach(([k, v]) => {
            newVals[k] = String(v)
          })
          setFieldValues(newVals)
          console.log('[UI_SYNC] ManualSlot updated from all_ocr:', newVals)
        } else if (ocrResult.readings && ocrResult.readings.length > 0 && instrumentFields?.length) {
          setFieldValues({ [instrumentFields[0].key]: String(ocrResult.readings[0].value) })
        }
      }
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
  const fullImage = reading?.ocr_data?._full_image_path as string | undefined || reading?.image_path?.replace('/crops/display/', '/').replace('/crops/recognition/', '/') // Guessing full path if not explicit
  const recognitionImage = reading?.ocr_data?._recognition_image_path as string | undefined
  
  let currentImage = previewImage || displayImage
  if (viewMode === 'neural') currentImage = recognitionImage || previewImage || displayImage
  if (viewMode === 'context') currentImage = fullImage || previewImage || displayImage

  return (
    <div className="module-card flex flex-col h-full group">
      {/* Module Header */}
      <div className="module-header">
        <div className="flex items-center gap-2">
          <Binary size={12} className="text-[var(--text-muted)]" />
          <span className="module-title">Sensor Unit D{instrumentId}</span>
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
        className="relative aspect-video bg-black flex items-center justify-center cursor-pointer overflow-hidden border-b border-[var(--border)] group/image"
      >
        {currentImage ? (
          <>
            <img 
              src={`http://localhost:8001/images/${currentImage}`} 
              className={`w-full h-full transition-all duration-500 ${phase !== 'idle' ? 'opacity-30 blur-sm scale-110' : 'opacity-80 group-hover/image:opacity-100'} ${viewMode === 'neural' ? 'brightness-125 contrast-125 object-contain' : 'object-contain'} ${viewMode === 'context' ? 'object-contain' : 'object-contain'}`} 
              alt="Capture" 
              onClick={handleCapture}
            />
            {viewMode === 'neural' && (
              <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div className="w-full h-[1px] bg-[var(--accent)]/50 absolute top-0 animate-[scan_2s_linear_infinite]" />
                <div className="absolute inset-0 bg-[var(--accent)]/5 opacity-10" />
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 text-zinc-700 group-hover:text-zinc-500 transition-colors" onClick={handleCapture}>
            <Camera size={32} strokeWidth={1.5} />
            <span className="text-[9px] font-bold uppercase tracking-widest">Awaiting Capture</span>
          </div>
        )}

        {/* View Toggle Buttons */}
        {(recognitionImage || previewImage || displayImage) && phase === 'idle' && (
          <div className="absolute top-2 right-2 flex gap-1 z-10">
            <button 
              onClick={(e) => { e.stopPropagation(); setViewMode('crop'); }}
              className={`p-1.5 rounded-lg border backdrop-blur-md transition-all ${viewMode === 'crop' ? 'bg-white border-white text-[var(--accent)] shadow-sm' : 'bg-black/40 border-white/10 text-white/60 hover:text-white'}`}
              title="Crop View"
            >
              <Camera size={12} />
            </button>
            <button 
              onClick={(e) => { e.stopPropagation(); setViewMode('neural'); }}
              className={`p-1.5 rounded-lg border backdrop-blur-md transition-all ${viewMode === 'neural' ? 'bg-[var(--accent)] border-[var(--accent)] text-white shadow-lg' : 'bg-black/40 border-white/10 text-white/60 hover:text-white'}`}
              title="AI Neural View"
            >
              <ScanSearch size={12} />
            </button>
            <button 
              onClick={(e) => { e.stopPropagation(); setViewMode('context'); }}
              className={`p-1.5 rounded-lg border backdrop-blur-md transition-all ${viewMode === 'context' ? 'bg-amber-500 border-amber-500 text-white shadow-lg' : 'bg-black/40 border-white/10 text-white/60 hover:text-white'}`}
              title="Full Context View"
            >
              <Eye size={12} />
            </button>
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

        {/* Info Overlays */}
        <div className="absolute bottom-2 left-2 flex gap-2">
          {reading?.confidence && phase === 'idle' && (
            <div className="bg-black/50 backdrop-blur-md px-2 py-0.5 rounded border border-white/20 flex items-center gap-1.5">
              <span className="text-[9px] font-mono-num text-[var(--accent)]">
                CONF: {(reading.confidence * 100).toFixed(1)}%
              </span>
              {reading?.ocr_data?._performance && (
                <>
                  <div className="w-[1px] h-2 bg-white/20" />
                  <span className="text-[8px] font-mono-num text-white/50 uppercase tracking-tighter">
                    {((reading.ocr_data._performance.total_ms || 0) / 1000).toFixed(1)}s
                  </span>
                </>
              )}
            </div>
          )}
          {viewMode === 'neural' && (
            <div className="bg-[var(--accent)] px-2 py-0.5 rounded shadow-sm">
              <span className="text-[8px] font-bold text-white uppercase tracking-tighter">AI Optimized</span>
            </div>
          )}
          {viewMode === 'context' && (
            <div className="bg-amber-500 px-2 py-0.5 rounded shadow-sm">
              <span className="text-[8px] font-bold text-white uppercase tracking-tighter">Full Scene</span>
            </div>
          )}
        </div>
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

        <div className="space-y-2 flex-1 overflow-auto">
          {Object.keys(fieldValues).length > 0 ? (
            <>
              <div className="bg-white border border-[var(--border)] rounded-lg overflow-hidden shadow-sm">
                <table className="w-full text-[10px] font-mono-num">
                  <tbody className="divide-y divide-zinc-50">
                    {Object.entries(fieldValues).map(([k, v]) => {
                      if (k.startsWith('_')) return null; // Hide internal metadata
                      return (
                        <tr key={k} className="hover:bg-zinc-50/50 transition-colors">
                          <td className="px-3 py-1.5 text-zinc-400 font-medium uppercase tracking-tighter border-r border-zinc-50 w-1/3 bg-zinc-50/30">
                            {k.replace(/_/g, ' ')}
                          </td>
                          <td className="px-3 py-1.5 text-[var(--text-primary)] font-bold flex items-center justify-between">
                            <span className="tabular-nums">{String(v)}</span>
                            <div className="w-1 h-1 bg-[var(--accent)] rounded-full animate-pulse shadow-[0_0_4px_var(--accent)]" />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {viewMode === 'neural' && reading?.ocr_data?._raw_output && (
                <div className="mt-2 p-2 bg-zinc-900 rounded border border-zinc-800">
                  <div className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest mb-1 flex items-center gap-1">
                    <Cpu size={8} /> Raw AI Insight
                  </div>
                  <div className="text-[9px] font-mono text-zinc-300 leading-relaxed whitespace-pre-wrap break-words">
                    {String(reading.ocr_data._raw_output)}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="h-20 flex flex-col items-center justify-center border border-dashed border-[var(--border)] rounded bg-white">
              <Hash size={16} className="text-zinc-200 mb-1" />
              <span className="text-[9px] font-bold text-zinc-300 uppercase">Awaiting Data</span>
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