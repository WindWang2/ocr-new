'use client'
/**
 * CaptureSlot — 单个读数槽位
 *
 * 每个槽位对应一次拍照读数（run_index = slotIndex）。
 * 两步流程：
 *   1. captureImage(experimentId, cameraId) → 立即显示拍摄图片
 *   2. runTestCapture(experimentId, fieldKey, cameraId, imagePath) → OCR 识别，完成后调用 onComplete()
 *
 * Props:
 *   experimentId  - 实验 ID
 *   fieldKey      - 字段键，如 'rpm3'、'flow_time'
 *   cameraId      - 绑定相机编号（0~8）
 *   slotIndex     - 槽位序号（0-based），对应 run_index
 *   label         - 槽位标签，如 "实验1"、"实验3"
 *   unit          - 读数单位，如 "mN/m"
 *   reading       - 已完成的读数（null = 尚未拍摄）
 *   onComplete    - 读数完成后的回调（父组件应刷新实验数据）
 *   disabled      - 禁用按钮（其他槽位正在拍摄时）
 *   cameraLabel   - 相机说明，如 "F8 · 6速旋转粘度计"
 *   compact       - 紧凑模式（横排布局，用于表观黏度的网格）
 */
import { useState } from 'react'
import { Reading } from '@/types'
import { captureImage, runTestCapture } from '@/lib/api'
import { Camera, RefreshCw, RotateCcw } from 'lucide-react'

interface Props {
  experimentId: number
  fieldKey: string
  cameraId: number
  slotIndex: number
  label: string
  unit: string
  reading: Reading | null
  onComplete: () => void
  disabled?: boolean
  cameraLabel?: string
  compact?: boolean
}

export default function CaptureSlot({
  experimentId, fieldKey, cameraId, slotIndex,
  label, unit, reading, onComplete, disabled = false,
  cameraLabel, compact = false,
}: Props) {
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const [phase, setPhase] = useState<'idle' | 'capturing' | 'recognizing'>('idle')
  const [error, setError] = useState<string | null>(null)

  const isBusy = phase !== 'idle'

  const handleCapture = async () => {
    if (isBusy || disabled) return
    setError(null)
    try {
      // 第一步：触发相机，立即显示图片
      setPhase('capturing')
      const { image_path } = await captureImage(experimentId, cameraId)
      if (image_path) setPendingImage(image_path)

      // 第二步：OCR 识别
      setPhase('recognizing')
      await runTestCapture(experimentId, fieldKey, cameraId, image_path)
      setPendingImage(null)
      onComplete()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '拍照失败')
      setPendingImage(null)
    } finally {
      setPhase('idle')
    }
  }

  // 已完成的读数显示图片
  const displayImage = reading?.image_path ?? null
  const hasReading = reading !== null

  if (compact) {
    // ── 紧凑模式：用于表观黏度 3列网格 ──────────────────────────────────
    return (
      <div className="flex flex-col border border-gray-100 rounded-xl overflow-hidden bg-white">
        {/* 图片区 */}
        <div className="relative bg-gray-50 h-28">
          {(pendingImage || displayImage) ? (
            <img
              src={`/images/${pendingImage || displayImage}`}
              alt={label}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Camera size={20} className="text-gray-200" />
            </div>
          )}
          {isBusy && (
            <div className="absolute inset-0 bg-white/70 flex flex-col items-center justify-center gap-1">
              <RefreshCw size={16} className="animate-spin text-brand-500" />
              <span className="text-[10px] text-brand-500">
                {phase === 'capturing' ? '拍摄中' : '识别中'}
              </span>
            </div>
          )}
        </div>
        {/* 底部：标签 + 值 + 按钮 */}
        <div className="px-2.5 py-2 flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-gray-400">{label}</span>
            {cameraLabel && <span className="text-[10px] text-gray-300">{cameraLabel}</span>}
          </div>
          {hasReading ? (
            <div className="flex items-center justify-between">
              <span className="font-bold text-gray-800 text-lg tabular-nums">
                {reading.value}<span className="text-xs font-normal text-gray-400 ml-1">{unit}</span>
              </span>
              <button
                onClick={handleCapture}
                disabled={isBusy || disabled}
                title="重新拍摄"
                className="p-1 rounded text-gray-300 hover:text-gray-500 transition disabled:opacity-30"
              >
                <RotateCcw size={12} />
              </button>
            </div>
          ) : (
            <button
              onClick={handleCapture}
              disabled={isBusy || disabled}
              className={`w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition ${
                isBusy || disabled
                  ? 'bg-gray-100 text-gray-400 cursor-wait'
                  : 'text-white hover:opacity-90'
              }`}
              style={!(isBusy || disabled) ? { background: 'var(--brand)' } : undefined}
            >
              {isBusy
                ? <RefreshCw size={11} className="animate-spin" />
                : <Camera size={11} />
              }
              {phase === 'capturing' ? '拍摄中' : phase === 'recognizing' ? '识别中' : '拍照'}
            </button>
          )}
          {error && <p className="text-[10px] text-red-500 truncate" title={error}>{error}</p>}
        </div>
      </div>
    )
  }

  // ── 标准模式：用于运动粘度、表面张力的列表槽位 ────────────────────────
  return (
    <div className="border border-gray-100 rounded-xl bg-white overflow-hidden hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-4 p-4">
        {/* 左侧：图片 */}
        <div className="relative shrink-0 w-48 h-36 rounded-lg overflow-hidden bg-gray-50 border border-gray-100">
          {(pendingImage || displayImage) ? (
            <img
              src={`/images/${pendingImage || displayImage}`}
              alt={label}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Camera size={24} className="text-gray-200" />
            </div>
          )}
          {isBusy && (
            <div className="absolute inset-0 bg-white/75 flex flex-col items-center justify-center gap-1.5">
              <RefreshCw size={18} className="animate-spin text-brand-500" />
              <span className="text-xs text-brand-500">
                {phase === 'capturing' ? '正在拍摄...' : '正在识别...'}
              </span>
            </div>
          )}
        </div>

        {/* 右侧：信息 + 按钮 */}
        <div className="flex-1 min-w-0 flex flex-col justify-between h-36">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-gray-700 text-sm">{label}</span>
              <span className="text-[11px] text-gray-300">/</span>
              <span className="text-[11px] text-gray-400">槽位 {slotIndex + 1}</span>
            </div>
            {cameraLabel && (
              <div className="text-[11px] text-gray-400 mb-2">{cameraLabel}</div>
            )}
            {reading?.timestamp && (
              <div className="text-[11px] text-gray-300">
                {new Date(reading.timestamp).toLocaleString('zh-CN', {
                  month: '2-digit', day: '2-digit',
                  hour: '2-digit', minute: '2-digit', second: '2-digit',
                })}
              </div>
            )}
          </div>

          <div className="flex items-end justify-between">
            {/* 读数值 */}
            <div>
              {hasReading ? (
                <div>
                  <span className="text-3xl font-bold tabular-nums text-gray-800">{reading.value}</span>
                  <span className="text-sm text-gray-400 ml-1.5">{unit}</span>
                </div>
              ) : (
                <span className="text-sm text-gray-300">暂无读数</span>
              )}
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-2">
              {hasReading && (
                <button
                  onClick={handleCapture}
                  disabled={isBusy || disabled}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-500 border border-gray-200 hover:border-gray-300 transition disabled:opacity-40"
                >
                  <RotateCcw size={12} />重拍
                </button>
              )}
              {!hasReading && (
                <button
                  onClick={handleCapture}
                  disabled={isBusy || disabled}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition ${
                    isBusy || disabled
                      ? 'bg-gray-100 text-gray-400 cursor-wait'
                      : 'text-white hover:opacity-90 shadow-sm'
                  }`}
                  style={!(isBusy || disabled) ? { background: 'var(--brand)' } : undefined}
                >
                  {isBusy ? <RefreshCw size={13} className="animate-spin" /> : <Camera size={13} />}
                  {phase === 'capturing' ? '拍摄中...' : phase === 'recognizing' ? '识别中...' : '拍照识别'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="px-4 pb-3">
          <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">{error}</p>
        </div>
      )}
    </div>
  )
}
