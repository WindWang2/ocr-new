'use client'
import { useState } from 'react'
import { Reading } from '@/types'
import { Camera, RefreshCw, CheckCircle2 } from 'lucide-react'

interface Props {
  fieldKey: string
  label: string
  unit: string
  cameraId: number
  maxReadings: number
  readings: Reading[]
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>
  capturing: string | null
}

export default function ReadingField({
  fieldKey, label, unit, cameraId, maxReadings, readings, onCapture, capturing
}: Props) {
  const [error, setError] = useState<string | null>(null)
  const isFull = readings.length >= maxReadings
  const isBusy = capturing !== null

  const handleCapture = async () => {
    setError(null)
    try {
      await onCapture(fieldKey, cameraId)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '拍照失败')
    }
  }

  return (
    <div className="border border-gray-100 rounded-xl p-5 bg-white hover:shadow-sm transition-shadow duration-200">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="font-semibold text-gray-800 text-sm">{label}</div>
          <div className="text-[11px] text-gray-400 mt-1">
            相机 {cameraId} · 已读 {readings.length}/{maxReadings} 次
            {unit ? ` · ${unit}` : ''}
          </div>
        </div>
        <button
          onClick={handleCapture}
          disabled={isBusy || isFull}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${
            isFull
              ? 'bg-green-50 text-green-600 cursor-default'
              : isBusy
              ? 'bg-gray-100 text-gray-400 cursor-wait'
              : 'text-white hover:opacity-90 shadow-sm'
          }`}
          style={!isFull && !isBusy ? { background: 'var(--brand)' } : undefined}
        >
          {capturing === fieldKey ? (
            <><RefreshCw size={14} className="animate-spin" />识别中...</>
          ) : isFull ? (
            <><CheckCircle2 size={14} />已完成</>
          ) : (
            <><Camera size={14} />拍照识别</>
          )}
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2 mb-3">{error}</p>
      )}

      {readings.length > 0 && (
        <div className="space-y-1.5">
          {readings.map((r, i) => (
            <div
              key={r.id}
              className="flex items-center gap-2.5 text-sm bg-gray-50/80 rounded-lg px-3.5 py-2 border border-gray-50"
            >
              {r.image_path && (
                <img
                  src={`/images/${r.image_path}`}
                  alt={`#${i + 1}`}
                  className="w-16 h-12 object-cover rounded border border-gray-200 shrink-0 bg-gray-100"
                  loading="lazy"
                />
              )}
              <span className="text-gray-400 text-xs font-medium w-8 shrink-0">#{i + 1}</span>
              <span className="font-semibold text-gray-800 flex-1 text-center">{r.value} {unit}</span>
              {r.confidence != null && (
                <span className="text-[11px] text-gray-400 w-16 text-right shrink-0">
                  {(r.confidence * 100).toFixed(1)}%
                </span>
              )}
              <span className="text-[11px] text-gray-300 w-16 text-right shrink-0">
                {new Date(r.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
