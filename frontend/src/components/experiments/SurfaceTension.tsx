'use client'
/**
 * 表面张力和界面张力实验视图
 * 执行标准：SY/T 5370-2018（表面及界面张力测定方法，铂金环法）
 * 仪器：F5（表界面张力仪）
 */
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import CaptureSlot from '@/components/ExperimentDetail/CaptureSlot'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function SurfaceTension({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.surface_tension
  const p = experiment.manual_params

  const getCameraId = (fieldKey: string) => {
    const config = experiment.camera_configs.find(c => c.field_key === fieldKey)
    const def = schema.cameraFields.find(f => f.fieldKey === fieldKey)
    return config?.camera_id ?? def?.defaultCameraId ?? 5
  }

  const getReading = (fieldKey: string, slotIndex: number) =>
    experiment.readings.find(r => r.field_key === fieldKey && r.run_index === slotIndex) ?? null

  const surfaceField   = schema.cameraFields.find(f => f.fieldKey === 'fluid_surface_tension')!
  const interfaceField = schema.cameraFields.find(f => f.fieldKey === 'fluid_interface_tension')!

  return (
    <div className="space-y-5">

      {/* 实验条件 */}
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">实验条件</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2.5 text-sm">
          <ParamRow label="室内温度" value={p.room_temperature} unit="℃" />
          <ParamRow label="室内湿度" value={p.room_humidity} unit="%" />
          <ParamRow label="25℃ 破胶液密度" value={p.sample_density} unit="g/cm³" />
          <ParamRow label="25℃ 煤油密度" value={p.kerosene_density} unit="g/cm³" />
        </div>
      </div>

      {/* 操作规程（始终展示） */}
      <div className="rounded-xl border border-cyan-100 bg-cyan-50/30 overflow-hidden">
        <div className="px-4 py-2.5 border-b border-cyan-100 bg-cyan-50/60">
          <span className="text-xs font-semibold text-cyan-700">操作规程</span>
          <span className="text-[11px] text-cyan-400 ml-2">SY/T 5370-2018 · 铂金环法</span>
        </div>
        <div className="px-4 py-3 space-y-2.5 text-[12px] text-gray-600 leading-relaxed">
          <p>
            配制浓度为 <strong>0.3%</strong> 的助排剂水溶液 500 mL：
            用移液管吸取 1.5 mL 助排剂置于装有 400 mL 蒸馏水的 500 mL 容量瓶中，
            用蒸馏水稀释至刻度后摇匀，备用。
          </p>
          <ol className="list-decimal list-inside space-y-1 text-gray-600 pl-1">
            <li>取少量样品对玻璃器皿内壁进行预润湿，润湿后倒掉，重新倒入 7~10 mm 高度的样品，将器皿放在托盘上待测。</li>
            <li>酒精灯烧铂金环：与水平面呈 45° 角灼烧至铂金丝红炽状（约 20–30 s），等待约 10 s 冷却后挂在延长钩上。</li>
            <li>上升/下降速度默认 10 mm/min（范围 1~300 mm/min），启动测试前可修改。</li>
            <li>关闭玻璃移门，点击"上升键"，目视铂金环浸入样品约 2 mm 深后停止，点击"去皮键"归零。</li>
            <li>表面张力：上层密度默认 0，下层密度输入样品密度值。界面张力：按实际密度设置上下层。</li>
            <li>点击"启动测试键"，左侧实时显示测量曲线（蓝色线）。</li>
            <li>随托盘缓慢下降，数值逐渐增大，当铂金环与液体即将分离时显示最大值即为最终结果。</li>
            <li>铂金环与液体分离后，托盘自动停止，测试结束。</li>
          </ol>
          <div className="bg-white/70 rounded-lg px-3 py-2 border border-cyan-100 text-[11px] text-gray-500 space-y-0.5">
            <p>25℃ 试样密度：<strong>{p.sample_density ?? '—'}</strong> g/cm³ &nbsp;·&nbsp; 25℃ 煤油密度：<strong>{p.kerosene_density ?? '—'}</strong> g/cm³</p>
          </div>
        </div>
      </div>

      {/* ── 第1节：纯水表面张力 */}
      <Section title="纯水表面张力" subtitle="验证铂金环状态，标准值约 72.8 mN/m (20℃)" color="blue">
        <CaptureSlot
          experimentId={experiment.id}
          fieldKey="water_surface_tension"
          cameraId={getCameraId('water_surface_tension')}
          slotIndex={0}
          label="测试值"
          unit="mN/m"
          reading={getReading('water_surface_tension', 0)}
          onComplete={onRefresh}
          cameraLabel={`F${getCameraId('water_surface_tension')} · 表界面张力仪`}
        />
      </Section>

      {/* ── 第2节：破胶液表面张力（5次） */}
      <Section
        title="破胶液表面张力"
        subtitle={`5次实验取算术平均 · 样品密度 ${p.sample_density ?? '—'} g/cm³`}
        color="cyan"
      >
        <div className="grid grid-cols-1 gap-3">
          {Array.from({ length: surfaceField.maxReadings }, (_, i) => (
            <CaptureSlot
              key={i}
              experimentId={experiment.id}
              fieldKey="fluid_surface_tension"
              cameraId={getCameraId('fluid_surface_tension')}
              slotIndex={i}
              label={`实验 ${i + 1}`}
              unit="mN/m"
              reading={getReading('fluid_surface_tension', i)}
              onComplete={onRefresh}
              cameraLabel={`F${getCameraId('fluid_surface_tension')} · 表界面张力仪`}
            />
          ))}
        </div>
        <AverageRow
          readings={experiment.readings.filter(r => r.field_key === 'fluid_surface_tension')}
          unit="mN/m"
          label="算术平均值"
        />
      </Section>

      {/* ── 第3节：破胶液界面张力（2次） */}
      <Section
        title="破胶液界面张力"
        subtitle={`2次实验取算术平均 · 煤油密度 ${p.kerosene_density ?? '—'} g/cm³`}
        color="teal"
      >
        <div className="grid grid-cols-1 gap-3">
          {Array.from({ length: interfaceField.maxReadings }, (_, i) => (
            <CaptureSlot
              key={i}
              experimentId={experiment.id}
              fieldKey="fluid_interface_tension"
              cameraId={getCameraId('fluid_interface_tension')}
              slotIndex={i}
              label={`实验 ${i + 1}`}
              unit="mN/m"
              reading={getReading('fluid_interface_tension', i)}
              onComplete={onRefresh}
              cameraLabel={`F${getCameraId('fluid_interface_tension')} · 表界面张力仪`}
            />
          ))}
        </div>
        <AverageRow
          readings={experiment.readings.filter(r => r.field_key === 'fluid_interface_tension')}
          unit="mN/m"
          label="算术平均值"
        />
      </Section>

      <ResultSummary
        type="surface_tension"
        readings={experiment.readings}
        manualParams={p}
      />
    </div>
  )
}

function Section({ title, subtitle, color, children }: {
  title: string; subtitle?: string; color: 'blue' | 'cyan' | 'teal'; children: React.ReactNode
}) {
  const styles = {
    blue: 'border-blue-100 from-blue-50/80 to-blue-50/40 text-blue-700',
    cyan: 'border-cyan-100 from-cyan-50/80 to-cyan-50/40 text-cyan-700',
    teal: 'border-teal-100 from-teal-50/80 to-teal-50/40 text-teal-700',
  }
  return (
    <div className="border border-gray-100 rounded-2xl overflow-hidden">
      <div className={`px-5 py-3 border-b bg-gradient-to-r ${styles[color]}`}>
        <div className="font-semibold text-sm">{title}</div>
        {subtitle && <div className="text-[11px] mt-0.5 opacity-70">{subtitle}</div>}
      </div>
      <div className="p-4 space-y-3">{children}</div>
    </div>
  )
}

function AverageRow({ readings, unit, label }: { readings: { value: number }[]; unit: string; label: string }) {
  if (readings.length === 0) return null
  const avg = readings.reduce((s, r) => s + r.value, 0) / readings.length
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-50/80 rounded-xl border border-gray-100 mt-1">
      <span className="text-xs font-medium text-gray-500">{label}</span>
      <span className="font-bold text-gray-800 tabular-nums">
        {avg.toFixed(4)}<span className="text-xs font-normal text-gray-400 ml-1">{unit}</span>
      </span>
    </div>
  )
}

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
