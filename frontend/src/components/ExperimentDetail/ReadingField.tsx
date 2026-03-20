'use client'
import { useState } from 'react'
import { Reading } from '@/types'
import { Camera, RefreshCw } from 'lucide-react'

interface Props {
  fieldKey: string
  label: string
  unit: string
  cameraId: number
  maxReadings: number
  readings: Reading[]
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>
  capturing: string | null   // 任意字段正在拍照时，本组件也应禁用按钮
}

export default function ReadingField({
  fieldKey, label, unit, cameraId, maxReadings, readings, onCapture, capturing
}: Props) {
  const [error, setError] = useState<string | null>(null)
  const isFull = readings.length >= maxReadings
  const isBusy = capturing !== null  // 任何字段拍照中，全部按钮禁用

  const handleCapture = async () => {
    setError(null)
    try {
      await onCapture(fieldKey, cameraId)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '拍照失败')
    }
  }

  return (
    <div className="border rounded-xl p-4 bg-white">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="font-medium text-gray-800">{label}</div>
          <div className="text-xs text-gray-400 mt-0.5">
            相机 {cameraId} · 已读 {readings.length}/{maxReadings} 次{unit ? ` · 单位: ${unit}` : ''}
          </div>
        </div>
        <button
          onClick={handleCapture}
          disabled={isBusy || isFull}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            isFull
              ? 'bg-gray-100 text-gray-400 cursor-default'
              : isBusy
              ? 'bg-gray-200 cursor-wait'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {capturing === fieldKey ? (
            <><RefreshCw size={16} className="animate-spin" />识别中...</>
          ) : isFull ? (
            '已完成'
          ) : (
            <><Camera size={16} />拍照识别</>
          )}
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500 mb-2">{error}</p>
      )}

      {readings.length > 0 && (
        <div className="space-y-1">
          {readings.map((r, i) => (
            <div key={r.id} className="flex justify-between items-center text-sm bg-gray-50 rounded px-3 py-1.5">
              <span className="text-gray-500">第 {i + 1} 次</span>
              <span className="font-semibold text-gray-800">{r.value} {unit}</span>
              {r.confidence != null && (
                <span className="text-xs text-gray-400">置信度 {(r.confidence * 100).toFixed(1)}%</span>
              )}
              <span className="text-xs text-gray-400">
                {new Date(r.timestamp).toLocaleTimeString('zh-CN')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
