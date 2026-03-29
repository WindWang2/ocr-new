'use client'
/**
 * 运动粘度实验视图
 *
 * 模板来源：WLD-QP5100113-02 A/1
 * 流程：
 *   - 仪器：品氏毛细管粘度计（F7 温控设备控温）
 *   - 在设定温度（25℃）下恒温 10min 后，测量 4 次液体流经时间
 *   - 误差要求：各次读数误差 < 10s
 *   - 计算：ν = C × τ̄  （ν: mm²/s，C: 毛细管系数 mm²/s²，τ̄: 平均流经时间 s）
 */
import { useState } from 'react'
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import CaptureSlot from '@/components/ExperimentDetail/CaptureSlot'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'
import { ChevronDown } from 'lucide-react'

export default function KinematicViscosity({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.kinematic_viscosity
  const p = experiment.manual_params
  const field = schema.cameraFields[0]  // flow_time
  const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
  const cameraId = config?.camera_id ?? field.defaultCameraId
  const [showGuide, setShowGuide] = useState(false)

  const getReading = (slotIndex: number) =>
    experiment.readings.find(r => r.field_key === field.fieldKey && r.run_index === slotIndex) ?? null

  return (
    <div className="space-y-5">

      {/* 实验参数 */}
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">实验参数</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2.5 text-sm">
          <ParamRow label="温控设置温度" value={p.temperature_set} unit="℃" />
          <ParamRow label="毛细管粘度计型号" value={p.capillary_model} unit="" />
          <ParamRow label="最高温度" value={p.temperature_max} unit="℃" />
          <ParamRow label="最低温度" value={p.temperature_min} unit="℃" />
          <ParamRow label="毛细管系数 C" value={p.capillary_coeff} unit="mm²/s²" />
        </div>
      </div>

      {/* 操作指南（可折叠） */}
      <div className="rounded-xl border border-gray-100 overflow-hidden">
        <button
          onClick={() => setShowGuide(v => !v)}
          className="w-full flex items-center justify-between px-4 py-3 bg-blue-50/60 hover:bg-blue-50 transition text-left"
        >
          <div>
            <span className="text-xs font-semibold text-blue-700">操作规程</span>
            <span className="text-[11px] text-blue-500 ml-2">WLD-QP5100113-02 · 检验原始记录</span>
          </div>
          <ChevronDown size={14} className={`text-blue-400 transition-transform ${showGuide ? 'rotate-180' : ''}`} />
        </button>
        {showGuide && (
          <div className="px-4 py-3 bg-white space-y-2 text-[12px] text-gray-600 leading-relaxed">
            <p>
              使用 <strong>0.8mm 品氏毛细管粘度计</strong>，在 25℃ 下使用运动粘度测试仪恒温 10 min 后，
              测试 3 次液体在品氏粘度计的流经时间，读数要求误差 &lt; 10s，
              取 3 次测试流经时间平均值 <em>t̄</em>。
            </p>
            <div className="bg-blue-50/60 rounded-lg px-3 py-2 font-mono text-blue-700">
              ν = C × t̄
            </div>
            <ul className="space-y-0.5 text-gray-500">
              <li>ν — 运动粘度（mm²/s）</li>
              <li>C — 毛细管粘度计系数（mm²/s²）</li>
              <li>t̄ — 试样平均流动时间（s）</li>
            </ul>
          </div>
        )}
      </div>

      {/* 流经时间读数槽位（实验1~4） */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">流经时间 t（s）</h3>
          <span className="text-[11px] text-gray-400">
            F{cameraId} · {field.unit ? `单位 ${field.unit}` : ''}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: field.maxReadings }, (_, i) => (
            <CaptureSlot
              key={i}
              experimentId={experiment.id}
              fieldKey={field.fieldKey}
              cameraId={cameraId}
              slotIndex={i}
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
