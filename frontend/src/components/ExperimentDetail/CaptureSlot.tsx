'use client'
/**
 * CaptureSlot — 单个读数槽位
 *
 * 每个槽位始终显示可编辑输入框，支持：
 *   A. 拍照识别：captureImage → 显示图片 → runTestCapture(readingKey) → 自动填入主读数
 *      图片下方展示该仪器所有 OCR 读数（all_ocr）
 *   B. 手动填写：直接在输入框输入数值，失焦或回车保存
 *
 * run_index 与 slotIndex 严格对应（0-based），避免索引错位。
 * pendingImage 由 useEffect 监听 reading.image_path 更新后清除，不会有空窗期。
 */
import { useState, useEffect } from 'react'
import { Reading } from '@/types'
import { captureImage, runTestCapture, saveManualReading } from '@/lib/api'
import { Camera, RefreshCw, RotateCcw } from 'lucide-react'

interface Props {
  experimentId: number
  fieldKey: string
  cameraId: number
  slotIndex: number     // 0-based，对应 run_index
  readingKey: string    // 仪器 OCR 结果中对应此槽位的键，如 "actual_reading"、"tension"
  label: string
  unit: string
  reading: Reading | null
  onComplete: () => Promise<void> | void
  disabled?: boolean
  cameraLabel?: string
  compact?: boolean
}

export default function CaptureSlot({
  experimentId, fieldKey, cameraId, slotIndex, readingKey,
  label, unit, reading, onComplete, disabled = false,
  cameraLabel, compact = false,
}: Props) {
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const [phase, setPhase] = useState<'idle' | 'capturing' | 'recognizing'>('idle')
  const [error, setError] = useState<string | null>(null)
  const [inputVal, setInputVal] = useState(reading ? String(reading.value) : '')
  const [saving, setSaving] = useState(false)
  // 所有 OCR 读数（仪器原始键值对），展示在图片下方
  const [allOcr, setAllOcr] = useState<Record<string, number | string | null> | null>(null)

  useEffect(() => {
    if (reading != null) setInputVal(String(reading.value))
  }, [reading])

  // reading.image_path 到位后清除 pendingImage，避免图片空窗期
  useEffect(() => {
    if (reading?.image_path && pendingImage) {
      setPendingImage(null)
    }
  }, [reading])

  const isBusy = phase !== 'idle'

  const handleCapture = async () => {
    if (isBusy || disabled) return
    setError(null)
    setAllOcr(null)
    try {
      setPhase('capturing')
      const { image_path } = await captureImage(experimentId, cameraId)
      if (image_path) setPendingImage(image_path)

      setPhase('recognizing')
      const result = await runTestCapture(
        experimentId, fieldKey, cameraId, image_path, readingKey, slotIndex
      )
      if (result.all_ocr) setAllOcr(result.all_ocr)
      await onComplete()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '拍照失败')
      setPendingImage(null)
    } finally {
      setPhase('idle')
    }
  }

  const handleInputBlur = async () => {
    const num = parseFloat(inputVal)
    if (isNaN(num)) return
    if (reading && reading.value === num) return
    setSaving(true)
    setError(null)
    try {
      await saveManualReading(experimentId, fieldKey, slotIndex, num, cameraId)
      await onComplete()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleInputKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') e.currentTarget.blur()
  }

  const displayImage = pendingImage ?? reading?.image_path ?? null

  // 所有 OCR 读数展示（只显示数值型字段，跳过 mode/date 等字符串）
  const ocrEntries = allOcr
    ? Object.entries(allOcr).filter(([, v]) => v !== null && typeof v === 'number')
    : []

  const inputBox = (
    <div className="flex items-center gap-1.5">
      <input
        type="number"
        value={inputVal}
        onChange={e => setInputVal(e.target.value)}
        onBlur={handleInputBlur}
        onKeyDown={handleInputKey}
        disabled={saving}
        placeholder="填写读数"
        className="w-28 px-2.5 py-1.5 text-sm font-semibold tabular-nums border-2 border-dashed border-gray-300 rounded-lg bg-white focus:outline-none focus:border-brand-400 focus:border-solid focus:ring-1 focus:ring-brand-200 hover:border-gray-400 transition placeholder:text-gray-300 placeholder:font-normal disabled:opacity-50"
      />
      <span className="text-xs text-gray-400 shrink-0">{unit}</span>
      {saving && <RefreshCw size={11} className="animate-spin text-gray-400" />}
    </div>
  )

  if (compact) {
    return (
      <div className="flex flex-col border border-gray-100 rounded-xl overflow-hidden bg-white">
        {/* 图片区 */}
        <div className="relative bg-gray-50 h-28">
          {displayImage ? (
            <img src={`/images/${displayImage}`} alt={label} className="w-full h-full object-cover" />
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

        {/* OCR 所有读数（图片下方） */}
        {ocrEntries.length > 0 && (
          <div className="px-2.5 pt-1.5 flex flex-wrap gap-x-2 gap-y-0.5">
            {ocrEntries.map(([k, v]) => (
              <span key={k} className={`text-[10px] ${k === readingKey ? 'text-brand-600 font-semibold' : 'text-gray-400'}`}>
                {k}: {String(v)}
              </span>
            ))}
          </div>
        )}

        {/* 底部 */}
        <div className="px-2.5 py-2 flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-gray-400">{label}</span>
            {cameraLabel && <span className="text-[10px] text-gray-300">{cameraLabel}</span>}
          </div>
          {inputBox}
          <button
            onClick={handleCapture}
            disabled={isBusy || disabled}
            className={`w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition ${
              isBusy || disabled ? 'bg-gray-100 text-gray-400 cursor-wait' : 'text-white hover:opacity-90'
            }`}
            style={!(isBusy || disabled) ? { background: 'var(--brand)' } : undefined}
          >
            {isBusy ? <RefreshCw size={11} className="animate-spin" /> : <Camera size={11} />}
            {phase === 'capturing' ? '拍摄中' : phase === 'recognizing' ? '识别中' : '拍照识别'}
          </button>
          {error && <p className="text-[10px] text-red-500 truncate" title={error}>{error}</p>}
        </div>
      </div>
    )
  }

  // ── 标准模式 ────────────────────────────────────────────────────────────────
  return (
    <div className="border border-gray-100 rounded-xl bg-white overflow-hidden hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-4 p-4">
        {/* 左侧：图片 */}
        <div className="flex flex-col gap-2 shrink-0">
          <div className="relative w-48 h-36 rounded-lg overflow-hidden bg-gray-50 border border-gray-100">
            {displayImage ? (
              <img src={`/images/${displayImage}`} alt={label} className="w-full h-full object-cover" />
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
          {/* 图片下方：所有 OCR 读数 */}
          {ocrEntries.length > 0 && (
            <div className="w-48 bg-gray-50/80 rounded-lg px-2.5 py-2 border border-gray-100 space-y-0.5">
              {ocrEntries.map(([k, v]) => (
                <div key={k} className={`flex justify-between text-[11px] ${k === readingKey ? 'text-brand-600 font-semibold' : 'text-gray-500'}`}>
                  <span>{k}</span>
                  <span className="tabular-nums">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 右侧 */}
        <div className="flex-1 min-w-0 flex flex-col justify-between h-36">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-700 text-sm">{label}</span>
              {cameraLabel && <span className="text-[11px] text-gray-400">{cameraLabel}</span>}
            </div>
            {reading?.timestamp && (
              <div className="text-[11px] text-gray-300">
                {new Date(reading.timestamp).toLocaleString('zh-CN', {
                  month: '2-digit', day: '2-digit',
                  hour: '2-digit', minute: '2-digit', second: '2-digit',
                })}
              </div>
            )}
            <div className="pt-1">{inputBox}</div>
          </div>

          <div className="flex items-center gap-2 justify-end">
            {reading && (
              <button
                onClick={handleCapture}
                disabled={isBusy || disabled}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-500 border border-gray-200 hover:border-gray-300 transition disabled:opacity-40"
              >
                <RotateCcw size={12} />重拍
              </button>
            )}
            {!reading && (
              <button
                onClick={handleCapture}
                disabled={isBusy || disabled}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition ${
                  isBusy || disabled ? 'bg-gray-100 text-gray-400 cursor-wait' : 'text-white hover:opacity-90 shadow-sm'
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

      {error && (
        <div className="px-4 pb-3">
          <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">{error}</p>
        </div>
      )}
    </div>
  )
}
