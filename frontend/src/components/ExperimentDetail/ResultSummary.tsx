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
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">计算结果</h3>
        <div className="grid grid-cols-2 gap-4">
          <ResultCard label="平均流经时间 τ" value={r.avgTime} unit="s" />
          <ResultCard label="运动粘度 ν" value={r.viscosity} unit="mm²/s" />
        </div>
      </div>
    )
  }

  if (type === 'apparent_viscosity') {
    const r = calcApparent(readings)
    return (
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">计算结果</h3>
        <div className="grid grid-cols-3 gap-4">
          <ResultCard label="实验1 表观黏度 η₁" value={r.run1} unit="mPa·s" />
          <ResultCard label="实验2 表观黏度 η₂" value={r.run2} unit="mPa·s" />
          <ResultCard label="平均表观黏度" value={r.average} unit="mPa·s" highlight />
        </div>
      </div>
    )
  }

  if (type === 'surface_tension') {
    const r = calcSurface(readings)
    return (
      <div className="bg-gradient-to-r from-cyan-50 to-teal-50 rounded-xl p-4 border border-cyan-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">计算结果</h3>
        <div className="grid grid-cols-2 gap-4">
          <ResultCard label="表面张力算术平均值" value={r.surfaceAvg} unit="mN/m" highlight />
          <ResultCard label="界面张力算术平均值" value={r.interfaceAvg} unit="mN/m" highlight />
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
    <div className={`bg-white rounded-lg p-3 shadow-sm ${highlight ? 'ring-2 ring-blue-300' : ''}`}>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-xl font-bold ${value != null ? 'text-gray-800' : 'text-gray-300'}`}>
        {value != null ? value : '—'}
      </div>
      <div className="text-xs text-gray-400">{unit}</div>
    </div>
  )
}
