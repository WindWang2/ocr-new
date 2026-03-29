'use client'
/**
 * CaptureSlot — 单个读数槽位
 *
 * 两步拍照流程：
 *   1. captureImage → 立即显示图片
 *   2. runTestCapture → OCR 识别，完成后调用 onComplete()
 *
 * 读数可手动编辑：点击值区域进入编辑模式，回车/失焦保存。
 */
import { useState, useRef } from 'react'
import { Reading } from '@/types'
import { captureImage, runTestCapture, saveManualReading } from '@/lib/api'
import { Camera, RefreshCw, RotateCcw, Pencil, Check, X } from 'lucide-react'

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
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const [saving, setSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const isBusy = phase !== 'idle'

  const handleCapture = async () => {
    if (isBusy || disabled) return
    setError(null)
    try {
      setPhase('capturing')
      const { image_path } = await captureImage(experimentId, cameraId)
      if (image_path) setPendingImage(image_path)
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

  const startEdit = () => {
    setEditValue(reading ? String(reading.value) : '')
    setEditing(true)
    setTimeout(() => inputRef.current?.select(), 0)
  }

  const cancelEdit = () => {
    setEditing(false)
    setError(null)
  }

  const commitEdit = async () => {
    const num = parseFloat(editValue)
    if (isNaN(num)) {
      setError('请输入有效数字')
      return
    }
    setSaving(true)
    try {
      await saveManualReading(experimentId, fieldKey, slotIndex, num, cameraId)
      setEditing(false)
      onComplete()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') commitEdit()
    if (e.key === 'Escape') cancelEdit()
  }

  const displayImage = reading?.image_path ?? null
  const hasReading = reading !== null

  // ── 编辑态：内联输入框 ────────────────────────────────────────────────────
  const editWidget = editing ? (
    <div className="flex items-center gap-1.5">
      <input
        ref={inputRef}
        type="number"
        value={editValue}
        onChange={e => setEditValue(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-24 px-2 py-1 text-sm border border-brand-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-400 tabular-nums"
        placeholder="输入数值"
        disabled={saving}
        autoFocus
      />
      <span className="text-xs text-gray-400">{unit}</span>
      <button
        onClick={commitEdit}
        disabled={saving}
        className="p-1 rounded text-emerald-500 hover:bg-emerald-50 transition disabled:opacity-40"
        title="确认"
      >
        {saving ? <RefreshCw size={12} className="animate-spin" /> : <Check size={12} />}
      </button>
      <button onClick={cancelEdit} className="p-1 rounded text-gray-400 hover:bg-gray-50 transition" title="取消">
        <X size={12} />
      </button>
    </div>
  ) : null

  if (compact) {
    // ── 紧凑模式：表观黏度 3列网格 ──────────────────────────────────────────
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
        {/* 底部 */}
        <div className="px-2.5 py-2 flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-gray-400">{label}</span>
            {cameraLabel && <span className="text-[10px] text-gray-300">{cameraLabel}</span>}
          </div>
          {editing ? (
            <div className="py-0.5">{editWidget}</div>
          ) : hasReading ? (
            <div className="flex items-center justify-between">
              <button
                onClick={startEdit}
                className="font-bold text-gray-800 text-lg tabular-nums hover:text-brand-600 transition group flex items-center gap-1"
                title="点击编辑"
              >
                {reading.value}
                <span className="text-xs font-normal text-gray-400 ml-1">{unit}</span>
                <Pencil size={10} className="text-gray-300 group-hover:text-brand-400 transition" />
              </button>
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
            <div className="flex flex-col gap-1">
              <button
                onClick={handleCapture}
                disabled={isBusy || disabled}
                className={`w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition ${
                  isBusy || disabled ? 'bg-gray-100 text-gray-400 cursor-wait' : 'text-white hover:opacity-90'
                }`}
                style={!(isBusy || disabled) ? { background: 'var(--brand)' } : undefined}
              >
                {isBusy ? <RefreshCw size={11} className="animate-spin" /> : <Camera size={11} />}
                {phase === 'capturing' ? '拍摄中' : phase === 'recognizing' ? '识别中' : '拍照'}
              </button>
              <button
                onClick={startEdit}
                className="w-full flex items-center justify-center gap-1 py-1 rounded-lg text-[11px] text-gray-400 border border-gray-150 hover:border-gray-300 hover:text-gray-600 transition"
              >
                <Pencil size={10} />手动输入
              </button>
            </div>
          )}
          {error && <p className="text-[10px] text-red-500 truncate" title={error}>{error}</p>}
        </div>
      </div>
    )
  }

  // ── 标准模式：运动粘度、表面张力列表槽位 ─────────────────────────────────
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
            {/* 读数值 / 编辑态 */}
            <div>
              {editing ? (
                editWidget
              ) : hasReading ? (
                <button
                  onClick={startEdit}
                  className="group flex items-baseline gap-1 hover:text-brand-600 transition"
                  title="点击编辑读数"
                >
                  <span className="text-3xl font-bold tabular-nums text-gray-800 group-hover:text-brand-600 transition">
                    {reading.value}
                  </span>
                  <span className="text-sm text-gray-400 ml-1">{unit}</span>
                  <Pencil size={12} className="text-gray-300 group-hover:text-brand-400 transition mb-1" />
                </button>
              ) : (
                <span className="text-sm text-gray-300">暂无读数</span>
              )}
            </div>

            {/* 操作按钮 */}
            {!editing && (
              <div className="flex gap-2">
                {!hasReading && (
                  <button
                    onClick={startEdit}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-500 border border-gray-200 hover:border-gray-300 transition"
                  >
                    <Pencil size={12} />手动
                  </button>
                )}
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
                      isBusy || disabled ? 'bg-gray-100 text-gray-400 cursor-wait' : 'text-white hover:opacity-90 shadow-sm'
                    }`}
                    style={!(isBusy || disabled) ? { background: 'var(--brand)' } : undefined}
                  >
                    {isBusy ? <RefreshCw size={13} className="animate-spin" /> : <Camera size={13} />}
                    {phase === 'capturing' ? '拍摄中...' : phase === 'recognizing' ? '识别中...' : '拍照识别'}
                  </button>
                )}
              </div>
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
