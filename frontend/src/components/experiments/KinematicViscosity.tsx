import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ReadingField from '@/components/ExperimentDetail/ReadingField'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function KinematicViscosity({ experiment, onCapture, capturing }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.kinematic_viscosity
  const p = experiment.manual_params

  return (
    <div className="space-y-6">
      {/* 手动参数只读展示 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">实验参数</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <ParamRow label="温度设置" value={p.temperature_set} unit="℃" />
          <ParamRow label="最高温度" value={p.temperature_max} unit="℃" />
          <ParamRow label="最低温度" value={p.temperature_min} unit="℃" />
          <ParamRow label="毛细管系数 C" value={p.capillary_coeff} unit="mm²/s²" />
        </div>
      </div>

      {/* 相机读数字段 */}
      {schema.cameraFields.map(field => {
        const config = experiment.camera_configs.find(c => c.field_key === field.fieldKey)
        const readings = experiment.readings.filter(r => r.field_key === field.fieldKey)
        return (
          <ReadingField
            key={field.fieldKey}
            fieldKey={field.fieldKey}
            label={field.label}
            unit={field.unit}
            cameraId={config?.camera_id ?? 0}
            maxReadings={field.maxReadings}
            readings={readings}
            onCapture={onCapture}
            capturing={capturing}
          />
        )
      })}

      <ResultSummary type="kinematic_viscosity" readings={experiment.readings} manualParams={p} />
    </div>
  )
}

function ParamRow({ label, value, unit }: { label: string; value: unknown; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value != null ? String(value) : '—'} <span className="text-gray-400 text-xs">{unit}</span></span>
    </div>
  )
}
