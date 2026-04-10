'use client'
/**
 * 运动粘度实验视图
 * 模板：WLD-QP5100113-02 A/1
 *
 * 使用 0.8mm 品氏毛细管粘度计，在设定温度下恒温 10 min 后测量 4 次流经时间。
 * 计算：ν = C × t̄  （ν: mm²/s，C: 毛细管系数 mm²/s²，t̄: 平均流经时间 s）
 */
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import CaptureSlot from '@/components/ExperimentDetail/CaptureSlot'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function KinematicViscosity({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.kinematic_viscosity
  const p = experiment.manual_params
  const field = schema.cameraFields[0]
  const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
  const cameraId = config?.camera_id ?? field.defaultCameraId

  const getReading = (slotIndex: number) =>
    experiment.readings.find(r => r.field_key === field.fieldKey && r.run_index === slotIndex) ?? null

  return (
    <div className="space-y-5">

      {/* 记录头信息 */}
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">检验原始记录</h3>
          <span className="text-[10px] text-gray-300">文件编号：WLD-QP5100113-02　版次：A/1</span>
        </div>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm mb-3">
          <ParamRow label="检测日期" value={p.test_date} unit="" />
          <ParamRow label="报告编号 NO." value={p.report_number} unit="" />
          <ParamRow label="被检样品名称" value={p.sample_name} unit="" />
          <ParamRow label="样品编号" value={p.sample_number} unit="" />
          {p.formula_description && (
            <div className="col-span-2 flex justify-between">
              <span className="text-gray-400">配方说明</span>
              <span className="font-medium text-gray-700">{String(p.formula_description)}</span>
            </div>
          )}
        </div>
        <div className="border-t border-gray-100 pt-3">
          <h4 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">实验参数</h4>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <ParamRow label="温控设置温度" value={p.temperature_set} unit="℃" />
            <ParamRow label="毛细管粘度计型号" value={p.capillary_model} unit="" />
            <ParamRow label="最高温度" value={p.temperature_max} unit="℃" />
            <ParamRow label="最低温度" value={p.temperature_min} unit="℃" />
            <ParamRow label="毛细管系数 C" value={p.capillary_coeff} unit="mm²/s²" />
          </div>
        </div>
      </div>

      {/* 操作规程（始终展示） */}
      <div className="rounded-xl border border-blue-100 bg-blue-50/40 overflow-hidden">
        <div className="px-4 py-2.5 border-b border-blue-100 bg-blue-50/60">
          <span className="text-xs font-semibold text-blue-700">操作规程</span>
          <span className="text-[11px] text-blue-400 ml-2">WLD-QP5100113-02 · 检验原始记录</span>
        </div>
        <div className="px-4 py-3 space-y-2.5 text-[12px] text-gray-600 leading-relaxed">
          <p>
            使用 <strong>0.8 mm 品氏毛细管粘度计</strong>，在 25℃ 下使用运动粘度测试仪恒温 10 min 后，
            测试 3 次液体在品氏粘度计的流经时间，读数要求误差 &lt; 10 s，
            取 3 次测试流经时间平均值 <em>t̄</em>。
          </p>
          <div className="flex items-start gap-4 bg-white/70 rounded-lg px-3 py-2.5 border border-blue-100">
            <div>
              <p className="font-mono text-blue-700 text-sm font-bold">ν = C × t̄</p>
            </div>
            <ul className="space-y-0.5 text-gray-500 text-[11px]">
              <li>ν — 运动粘度（mm²/s）</li>
              <li>C — 毛细管粘度计系数（mm²/s²）</li>
              <li>t̄ — 试样平均流动时间（s）</li>
            </ul>
          </div>
          <p className="text-gray-500">
            运动粘度测试仪设置温度：<strong>{p.temperature_set ?? '—'}</strong> ℃；
            最高温度：<strong>{p.temperature_max ?? '—'}</strong> ℃；
            最低温度：<strong>{p.temperature_min ?? '—'}</strong> ℃。
            平氏毛细管粘度计型号：<strong>{p.capillary_model ?? '—'}</strong>；
            毛细管粘度计系数：C = <strong>{p.capillary_coeff ?? '—'}</strong> mm²/s²。
          </p>
        </div>
      </div>

      {/* 流经时间读数槽位（实验1~4） */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">流经时间 t（s）</h3>
          <span className="text-[11px] text-gray-400">F{cameraId} · 温控仪</span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: field.maxReadings }, (_, i) => (
            <CaptureSlot
              key={i}
              experimentId={experiment.id}
              fieldKey={field.fieldKey}
              cameraId={cameraId}
              slotIndex={i}
              readingKey={field.readingKey}
              label={`实验 ${i + 1}`}
              unit={field.unit}
              reading={getReading(i)}
              onComplete={onRefresh}
              cameraLabel={`F${cameraId} · 温控仪`}
            />
          ))}
        </div>
      </div>

      {/* 计算结果 */}
      <ResultSummary
        type="kinematic_viscosity"
        readings={experiment.readings}
        manualParams={p}
      />
    </div>
  )
}

function ParamRow({ label, value, unit }: { label: string; value: unknown; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium text-gray-700 tabular-nums">
        {value != null && value !== '' ? String(value) : '—'}
        {unit && value != null && value !== '' && (
          <span className="text-gray-300 text-xs ml-1">{unit}</span>
        )}
      </span>
    </div>
  )
}
