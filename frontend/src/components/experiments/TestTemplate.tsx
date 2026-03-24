'use client'
import { useState, useEffect, useCallback } from 'react'
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { getCameraInstruments, captureImage, runTestCapture, getExperiment } from '@/lib/api'
import { Camera, RefreshCw } from 'lucide-react'

export default function TestTemplate({ experiment, onCapture }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.test
  const [instruments, setInstruments] = useState<Record<string, { name: string; readings: { key: string; label: string; unit: string }[] }>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  // 拍照后立即显示的图片（OCR 完成前）
  const [pendingImages, setPendingImages] = useState<Record<string, { image_path: string; timestamp: string }>>({})
  // 每个位置的 OCR 状态
  const [ocrBusy, setOcrBusy] = useState<Record<string, boolean>>({})

  useEffect(() => {
    getCameraInstruments().then(setInstruments).catch(() => {})
  }, [])

  const getInstrument = (cameraId: number) => {
    return instruments[`F${cameraId}`] || { name: '', readings: [] }
  }

  const getSelectedKeys = (cameraId: number): string[] => {
    const config = experiment.camera_configs.find(c => c.camera_id === cameraId)
    return config?.selected_readings || []
  }

  const handleCapture = useCallback(async (fieldKey: string, cameraId: number) => {
    setErrors(prev => ({ ...prev, [fieldKey]: '' }))
    try {
      // 第一步：拍照并保存图片（快速）
      const captureResult = await captureImage(experiment.id, cameraId)
      if (captureResult.image_path) {
        setPendingImages(prev => ({
          ...prev,
          [fieldKey]: { image_path: captureResult.image_path!, timestamp: new Date().toISOString() },
        }))
      }

      // 第二步：OCR 识别（较慢），传入 image_path 跳过重复拍照
      setOcrBusy(prev => ({ ...prev, [fieldKey]: true }))
      const ocrResult = await runTestCapture(experiment.id, fieldKey, cameraId, captureResult.image_path)

      // OCR 完成，通知父组件刷新实验数据（获取真实 readings）
      await onCapture(fieldKey, cameraId)

      // 清除 pending 状态
      setPendingImages(prev => {
        const next = { ...prev }
        delete next[fieldKey]
        return next
      })
      setOcrBusy(prev => ({ ...prev, [fieldKey]: false }))
    } catch (e: unknown) {
      setErrors(prev => ({ ...prev, [fieldKey]: e instanceof Error ? e.message : '失败' }))
      setPendingImages(prev => {
        const next = { ...prev }
        delete next[fieldKey]
        return next
      })
      setOcrBusy(prev => ({ ...prev, [fieldKey]: false }))
    }
  }, [experiment.id, onCapture])

  // 将 readings 按 camera_id → 图片分组
  const readingsByCamera = new Map<number, Map<string, typeof experiment.readings>>()
  for (const r of experiment.readings) {
    if (!readingsByCamera.has(r.camera_id)) {
      readingsByCamera.set(r.camera_id, new Map())
    }
    const camMap = readingsByCamera.get(r.camera_id)!
    const groupKey = r.image_path || r.timestamp
    if (!camMap.has(groupKey)) {
      camMap.set(groupKey, [])
    }
    camMap.get(groupKey)!.push(r)
  }

  return (
    <div className="space-y-4">
      {schema.cameraFields.map(field => {
        const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
        if (!config) return null
        const cameraId = config.camera_id
        const instrument = getInstrument(cameraId)
        const selectedKeys = getSelectedKeys(cameraId)
        const captureGroups = readingsByCamera.get(cameraId)
        const pending = pendingImages[field.fieldKey]
        const isOcrBusy = ocrBusy[field.fieldKey] || false
        const isBusy = Object.values(ocrBusy).some(Boolean)

        // 按 selected_readings 过滤
        let filteredGroups: Map<string, typeof experiment.readings> | null = null
        if (captureGroups) {
          filteredGroups = new Map()
          for (const [key, readings] of captureGroups) {
            const filtered = selectedKeys.length > 0
              ? readings.filter(r => selectedKeys.includes(r.field_key))
              : readings
            if (filtered.length > 0) {
              filteredGroups.set(key, filtered)
            }
          }
        }

        const totalReadings = filteredGroups
          ? Array.from(filteredGroups.values()).reduce((sum, g) => sum + g.length, 0)
          : 0

        return (
          <div key={field.fieldKey} className="border border-gray-100 rounded-xl p-5 bg-white hover:shadow-sm transition-shadow duration-200">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="font-semibold text-gray-800 text-sm">{field.label}</div>
                <div className="text-[11px] text-gray-400 mt-1">
                  F{cameraId} · {instrument.name}
                </div>
                {selectedKeys.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {selectedKeys.map(k => {
                      const rd = instrument.readings.find(r => r.key === k)
                      return rd ? (
                        <span key={k} className="px-1.5 py-0.5 bg-brand-50 text-brand-600 rounded text-[10px]">
                          {rd.label}
                        </span>
                      ) : null
                    })}
                  </div>
                )}
              </div>
              <button
                onClick={() => handleCapture(field.fieldKey, cameraId)}
                disabled={isBusy}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                  isBusy
                    ? 'bg-gray-100 text-gray-400 cursor-wait'
                    : 'text-white hover:opacity-90 shadow-sm'
                }`}
                style={!isBusy ? { background: 'var(--brand)' } : undefined}
              >
                {isOcrBusy ? (
                  <><RefreshCw size={14} className="animate-spin" />识别中...</>
                ) : (
                  <><Camera size={14} />拍照识别</>
                )}
              </button>
            </div>

            {errors[field.fieldKey] && (
              <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2 mb-3">{errors[field.fieldKey]}</p>
            )}

            {/* Pending image: 拍照成功但 OCR 还没完成 */}
            {pending && (
              <div className="bg-blue-50/50 rounded-lg px-3.5 py-2.5 border border-blue-100">
                <div className="flex items-start gap-2.5">
                  {pending.image_path && (
                    <img
                      src={`/images/${pending.image_path}`}
                      alt="识别中"
                      className="w-56 h-40 object-cover rounded border border-blue-200 shrink-0 bg-gray-100"
                    />
                  )}
                  <div className="flex items-center gap-2 flex-1">
                    <RefreshCw size={14} className="animate-spin text-brand-500" />
                    <span className="text-xs text-brand-500">正在识别读数...</span>
                  </div>
                </div>
              </div>
            )}

            {/* 已完成的读数组 */}
            {filteredGroups && filteredGroups.size > 0 && (
              <div className="space-y-2">
                {Array.from(filteredGroups.entries()).map(([groupKey, groupReadings], groupIdx) => {
                  const imagePath = groupReadings[0]?.image_path
                  const timestamp = groupReadings[0]?.timestamp
                  return (
                    <div key={groupKey} className="bg-gray-50/80 rounded-lg px-3.5 py-2.5 border border-gray-50">
                      <div className="flex items-start gap-2.5">
                        {imagePath && (
                          <img
                            src={`/images/${imagePath}`}
                            alt={`#${groupIdx + 1}`}
                            className="w-56 h-40 object-cover rounded border border-gray-200 shrink-0 bg-gray-100"
                            loading="lazy"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-gray-400 text-xs font-medium">#{groupIdx + 1}</span>
                            <span className="text-[11px] text-gray-300">
                              {timestamp ? new Date(timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-x-4 gap-y-0.5">
                            {groupReadings.map(r => {
                              const rd = instrument.readings.find(ir => ir.key === r.field_key)
                              return (
                                <div key={r.id} className="text-sm">
                                  <span className="text-gray-400 text-xs">{rd?.label || r.field_key}: </span>
                                  <span className="font-semibold text-gray-800">{r.value}</span>
                                  <span className="text-gray-400 text-xs"> {rd?.unit || ''}</span>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {totalReadings === 0 && !pending && !errors[field.fieldKey] && (
              <p className="text-xs text-gray-300 text-center py-2">暂无读数，点击拍照开始</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
