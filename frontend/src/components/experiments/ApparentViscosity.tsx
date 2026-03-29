'use client'
/**
 * 表观黏度实验视图
 *
 * 模板来源：WLD/CNAS-QP7080004 A/3
 * 仪器：F8（6速旋转粘度计）
 *
 * 流程：
 *   实验1、实验2各独立完成以下3次读数：
 *     - 3rpm：将粘度计转速设为 3rpm，拍摄读数
 *     - 6rpm：将粘度计转速设为 6rpm，拍摄读数
 *     - 100rpm（α）：将粘度计转速设为 100rpm，拍摄读数
 *
 * 计算公式：
 *   η = α × 5.077 / 1.704   （η 单位：mPa·s；α 为 100rpm 读数）
 *   最终结果取实验1、实验2的平均值
 */
import { ExperimentViewProps, Reading } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import CaptureSlot from '@/components/ExperimentDetail/CaptureSlot'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

const RPM_FIELDS = ['rpm3', 'rpm6', 'rpm100'] as const
const RPM_LABELS = { rpm3: '3 rpm', rpm6: '6 rpm', rpm100: '100 rpm (α)' }

export default function ApparentViscosity({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.apparent_viscosity

  const getCameraId = (fieldKey: string) => {
    const config = experiment.camera_configs.find(c => c.field_key === fieldKey)
    const def = schema.cameraFields.find(f => f.fieldKey === fieldKey)
    return config?.camera_id ?? def?.defaultCameraId ?? 8
  }

  // 查找特定字段、特定实验轮次的读数
  const getReading = (fieldKey: string, runIndex: number): Reading | null =>
    experiment.readings.find(r => r.field_key === fieldKey && r.run_index === runIndex) ?? null

  // 计算单次实验的 η 值
  const calcEta = (runIndex: number): string => {
    const r = getReading('rpm100', runIndex)
    if (!r) return '—'
    const eta = (r.value * 5.077) / 1.704
    return eta.toFixed(4)
  }

  return (
    <div className="space-y-6">

      {/* 说明 */}
      <div className="bg-amber-50/60 rounded-xl px-4 py-3 border border-amber-100">
        <p className="text-xs text-amber-700 leading-relaxed">
          <span className="font-semibold">操作顺序：</span>
          每组实验先将粘度计转速依次设置为 3rpm → 6rpm → 100rpm，各拍一张。
          计算公式：<span className="font-mono">η = α × 5.077 / 1.704</span>，α 为 100rpm 读数。
        </p>
      </div>

      {/* 实验1 和 实验2 */}
      {[0, 1].map(runIndex => (
        <div key={runIndex} className="border border-gray-100 rounded-2xl overflow-hidden">
          {/* 实验标题行 */}
          <div className="px-5 py-3 border-b border-gray-50" style={{ background: 'var(--brand-light)' }}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-brand-700 text-sm">实验 {runIndex + 1}</h3>
              <div className="text-xs text-brand-600 font-mono">
                η{runIndex + 1} = {calcEta(runIndex)} mPa·s
              </div>
            </div>
          </div>

          {/* 三列读数槽：3rpm / 6rpm / 100rpm */}
          <div className="p-4 grid grid-cols-3 gap-3">
            {RPM_FIELDS.map(fieldKey => {
              const cameraId = getCameraId(fieldKey)
              const def = schema.cameraFields.find(f => f.fieldKey === fieldKey)!
              return (
                <div key={fieldKey}>
                  <div className="text-[11px] font-medium text-gray-500 mb-1.5 px-0.5">
                    {RPM_LABELS[fieldKey]}
                  </div>
                  <CaptureSlot
                    experimentId={experiment.id}
                    fieldKey={fieldKey}
                    cameraId={cameraId}
                    slotIndex={runIndex}
                    label={`实验${runIndex + 1}`}
                    unit={def.unit}
                    reading={getReading(fieldKey, runIndex)}
                    onComplete={onRefresh}
                    cameraLabel={`F${cameraId}`}
                    compact
                  />
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {/* 计算汇总 */}
      <ResultSummary
        type="apparent_viscosity"
        readings={experiment.readings}
        manualParams={experiment.manual_params}
      />
    </div>
  )
}
