'use client'
/**
 * 表观黏度实验视图
 * 模板：WLD/CNAS-QP7080004 A/3
 *
 * 仪器：F8（6速旋转粘度计）
 * 实验1、实验2各完成 3rpm → 6rpm → 100rpm 三次读数，计算表观粘度。
 * η = α × 5.077 / 1.704  （α 为 100rpm 读数，η 单位：mPa·s）
 */
import { ExperimentViewProps, Reading } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import CaptureSlot from '@/components/ExperimentDetail/CaptureSlot'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

const RPM_FIELDS = ['rpm3', 'rpm6', 'rpm100'] as const
const RPM_LABELS = { rpm3: '3 rpm', rpm6: '6 rpm', rpm100: '100 rpm (α)' }

function ParamRow({ label, value, unit }: { label: string; value: unknown; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium text-gray-700 tabular-nums">
        {value != null && value !== '' ? String(value) : '—'}
        {unit && value != null && value !== '' && <span className="text-gray-300 text-xs ml-1">{unit}</span>}
      </span>
    </div>
  )
}

export default function ApparentViscosity({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.apparent_viscosity

  const getCameraId = (fieldKey: string) => {
    const config = experiment.camera_configs.find(c => c.field_key === fieldKey)
    const def = schema.cameraFields.find(f => f.fieldKey === fieldKey)
    return config?.camera_id ?? def?.defaultCameraId ?? 8
  }

  const getReading = (fieldKey: string, runIndex: number): Reading | null =>
    experiment.readings.find(r => r.field_key === fieldKey && r.run_index === runIndex) ?? null

  const calcEta = (runIndex: number): string => {
    const r = getReading('rpm100', runIndex)
    if (!r) return '—'
    return ((r.value * 5.077) / 1.704).toFixed(4)
  }

  const p = experiment.manual_params

  return (
    <div className="space-y-5">

      {/* 记录头信息 */}
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">检测原始记录</h3>
          <span className="text-[10px] text-gray-300">文件编号：WLD/CNAS-QP7080004　版次：A/3</span>
        </div>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <ParamRow label="检测日期" value={p.test_date} unit="" />
          <ParamRow label="编号 NO." value={p.report_number} unit="" />
          <ParamRow label="被检样品名称" value={p.sample_name} unit="" />
          <ParamRow label="样品编号" value={p.sample_number} unit="" />
          {p.formula_description && (
            <div className="col-span-2 flex justify-between">
              <span className="text-gray-400">配方说明</span>
              <span className="font-medium text-gray-700">{String(p.formula_description)}</span>
            </div>
          )}
        </div>
      </div>

      {/* 操作规程（始终展示） */}
      <div className="rounded-xl border border-amber-100 bg-amber-50/40 overflow-hidden">
        <div className="px-4 py-2.5 border-b border-amber-100 bg-amber-50/60">
          <span className="text-xs font-semibold text-amber-700">操作规程</span>
          <span className="text-[11px] text-amber-400 ml-2">WLD/CNAS-QP7080004 · 检测原始记录</span>
        </div>
        <div className="px-4 py-3 space-y-2.5 text-[12px] text-gray-600 leading-relaxed">
          <p>
            每组实验将粘度计转速依次设置为 <strong>3 rpm → 6 rpm → 100 rpm</strong>，各拍一张读数。
            实验 1 和实验 2 各自独立完成。
          </p>
          <div className="flex items-start gap-4 bg-white/70 rounded-lg px-3 py-2.5 border border-amber-100">
            <div>
              <p className="font-mono text-amber-700 text-sm font-bold">η = α × 5.077 / 1.704</p>
            </div>
            <ul className="space-y-0.5 text-gray-500 text-[11px]">
              <li>η — 试样表观粘度（mPa·s）</li>
              <li>α — 100 r/min 转速下的粘度计读数</li>
              <li>5.077 — α=1 时的剪切应力值（×10⁻¹ Pa）</li>
              <li>1.704 — 1 r/min 的剪切速率值（s⁻¹）</li>
            </ul>
          </div>
          <p className="text-gray-500">最终结果取实验 1、实验 2 表观粘度的平均值。</p>
        </div>
      </div>

      {/* 实验1 和 实验2 */}
      {[0, 1].map(runIndex => (
        <div key={runIndex} className="border border-gray-100 rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-50" style={{ background: 'var(--brand-light)' }}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-brand-700 text-sm">实验 {runIndex + 1}</h3>
              <div className="text-xs text-brand-600 font-mono">
                η{runIndex + 1} = {calcEta(runIndex)} mPa·s
              </div>
            </div>
          </div>

          <div className="p-4 grid grid-cols-3 gap-3">
            {RPM_FIELDS.map(fieldKey => {
              const camId = getCameraId(fieldKey)
              const def = schema.cameraFields.find(f => f.fieldKey === fieldKey)!
              return (
                <div key={fieldKey}>
                  <div className="text-[11px] font-medium text-gray-500 mb-1.5 px-0.5">
                    {RPM_LABELS[fieldKey]}
                  </div>
                  <CaptureSlot
                    experimentId={experiment.id}
                    fieldKey={fieldKey}
                    cameraId={camId}
                    slotIndex={runIndex}
                    readingKey={def.readingKey}
                    label={`实验${runIndex + 1}`}
                    unit={def.unit}
                    reading={getReading(fieldKey, runIndex)}
                    onComplete={onRefresh}
                    cameraLabel={`F${camId}`}
                    compact
                  />
                </div>
              )
            })}
          </div>
        </div>
      ))}

      <ResultSummary
        type="apparent_viscosity"
        readings={experiment.readings}
        manualParams={experiment.manual_params}
      />
    </div>
  )
}
