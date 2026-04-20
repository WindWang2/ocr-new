'use client'

import { useState, useEffect } from 'react'
import { Reading, InstrumentFieldConfig } from '@/types'
import { captureReading, saveManualReading } from '@/lib/api'
import { Camera, RefreshCw, AlertCircle, Maximize2 } from 'lucide-react'

interface Props {
  experimentId: number
  fieldKey: string
  instrumentId: number
  label: string
  unit: string
  slotIndex: number
  reading: Reading | null
  onComplete: () => Promise<void> | void
}

export default function ManualInstrumentSlot({
  experimentId, fieldKey, instrumentId, label, unit, slotIndex, reading, onComplete
}: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [inputVal, setInputVal] = useState(reading ? String(reading.value) : '')

  useEffect(() => {
    setInputVal(reading ? String(reading.value) : '')
  }, [reading])

  const handleCapture = async () => {
    setLoading(true)
    setError(null)
    try {
      // 执行 拍照 + 识别
      await captureReading(experimentId, fieldKey, instrumentId, slotIndex)
      await onComplete()
    } catch (e: any) {
      setError(e.message || '采集失败')
    } finally {
      setLoading(false)
    }
  }

  const handleBlur = async () => {
    const num = parseFloat(inputVal)
    if (isNaN(num) || (reading && reading.value === num)) return
    try {
      await saveManualReading(experimentId, fieldKey, slotIndex, num, instrumentId)
      await onComplete()
    } catch (e) {
      setError('保存失败')
    }
  }

  return (
    <div className="bg-white border-2 border-gray-100 rounded-2xl overflow-hidden hover:border-brand-200 transition-all flex flex-col h-full shadow-sm">
      {/* 画面区：点此拍照 */}
      <div 
        className="relative aspect-video bg-gray-50 flex items-center justify-center cursor-pointer group"
        onClick={handleCapture}
      >
        {reading?.image_path ? (
          <img src={`/images/${reading.image_path}`} className="w-full h-full object-cover" alt="Capture" />
        ) : (
          <div className="flex flex-col items-center gap-2 text-gray-300">
            <Camera size={32} strokeWidth={1.5} />
            <span className="text-[10px] font-bold uppercase tracking-widest">点击拍照测量</span>
          </div>
        )}

        {/* 遮罩层 */}
        <div className={`absolute inset-0 bg-brand-600/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity ${loading ? 'opacity-100 bg-white/60' : ''}`}>
           {loading ? (
             <div className="flex flex-col items-center gap-2">
                <RefreshCw size={24} className="animate-spin text-brand-600" />
                <span className="text-[10px] font-bold text-brand-600">正在获取画面...</span>
             </div>
           ) : (
             <div className="bg-white/90 p-3 rounded-full shadow-xl transform scale-90 group-hover:scale-100 transition-transform">
                <Camera size={24} className="text-brand-600" />
             </div>
           )}
        </div>
      </div>

      {/* 信息与输入区 */}
      <div className="p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-black text-gray-400 uppercase tracking-tighter">{label}</span>
          <span className="text-[10px] font-bold text-gray-300">#{slotIndex}</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <input
              type="number"
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onBlur={handleBlur}
              placeholder="---"
              className="w-full text-2xl font-black text-gray-900 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500/20 px-3 py-2 tabular-nums"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-gray-300 pointer-events-none">{unit}</span>
          </div>
        </div>

        {error && <p className="text-[10px] text-red-500 font-medium">{error}</p>}
      </div>
    </div>
  )
}