import { Reading, ManualParams, ExperimentType } from '@/types'
import { calcKinematic, calcApparent, calcSurface } from '@/lib/calculations'

interface Props {
  type: ExperimentType
  readings: Reading[]
  manualParams: ManualParams
}

export default function ResultSummary({ type, readings, manualParams }: Props) {
  if (type === 'kinematic_viscosity') {
    const r = calcKinematic(readings, manualParams)
    return (
      <div className="rounded-xl p-5 border" style={{ background: 'linear-gradient(135deg, #EBF0F8 0%, #F0F4FA 100%)', borderColor: 'rgba(46,94,170,0.12)' }}>
        <h3 className="text-xs font-semibold text-brand-600 uppercase tracking-wider mb-4">计算结果</h3>
        <div className="grid grid-cols-2 gap-4">
          <ResultCard label="平均流经时间 τ" value={r.avgTime} unit="s" />
          <ResultCard label="运动粘度 ν" value={r.viscosity} unit="mm²/s" highlight />
        </div>
      </div>
    )
  }

  if (type === 'apparent_viscosity') {
    const r = calcApparent(readings)
    return (
      <div className="rounded-xl p-5 border border-purple-100" style={{ background: 'linear-gradient(135deg, #F5F0FA 0%, #FAF5FF 100%)' }}>
        <h3 className="text-xs font-semibold text-purple-600 uppercase tracking-wider mb-4">计算结果</h3>
        <div className="grid grid-cols-3 gap-3">
          <ResultCard label="实验1 η₁" value={r.run1} unit="mPa·s" />
          <ResultCard label="实验2 η₂" value={r.run2} unit="mPa·s" />
          <ResultCard label="平均 η" value={r.average} unit="mPa·s" highlight />
        </div>
      </div>
    )
  }

  if (type === 'surface_tension') {
    const r = calcSurface(readings)
    return (
      <div className="rounded-xl p-5 border border-cyan-100" style={{ background: 'linear-gradient(135deg, #EDF8FA 0%, #F0FBFC 100%)' }}>
        <h3 className="text-xs font-semibold text-cyan-600 uppercase tracking-wider mb-4">计算结果</h3>
        <div className="grid grid-cols-2 gap-4">
          <ResultCard label="表面张力" value={r.surfaceAvg} unit="mN/m" highlight />
          <ResultCard label="界面张力" value={r.interfaceAvg} unit="mN/m" highlight />
        </div>
      </div>
    )
  }

  return null
}

function ResultCard({ label, value, unit, highlight = false }: {
  label: string; value: number | null; unit: string; highlight?: boolean
}) {
  return (
    <div className={`rounded-xl p-4 ${highlight ? 'bg-white shadow-sm ring-1 ring-brand-100' : 'bg-white/70'}`}>
      <div className="text-[11px] text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold tabular-nums ${value != null ? 'text-gray-800' : 'text-gray-200'}`}>
        {value != null ? value : '—'}
      </div>
      <div className="text-[11px] text-gray-400 mt-0.5">{unit}</div>
    </div>
  )
}
