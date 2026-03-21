import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ReadingField from '@/components/ExperimentDetail/ReadingField'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function SurfaceTension({ experiment, onCapture, capturing }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.surface_tension
  const p = experiment.manual_params

  return (
    <div className="space-y-5">
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">实验参数</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2.5 text-sm">
          <ParamRow label="室内温度" value={p.room_temperature} unit="℃" />
          <ParamRow label="室内湿度" value={p.room_humidity} unit="%" />
          <ParamRow label="样品密度 (25℃)" value={p.sample_density} unit="g/cm³" />
          <ParamRow label="煤油密度 (25℃)" value={p.kerosene_density} unit="g/cm³" />
        </div>
      </div>

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

      <ResultSummary type="surface_tension" readings={experiment.readings} manualParams={p} />
    </div>
  )
}

function ParamRow({ label, value, unit }: { label: string; value: unknown; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium text-gray-700 tabular-nums">
        {value != null ? String(value) : '—'}
        <span className="text-gray-300 text-xs ml-1">{unit}</span>
      </span>
    </div>
  )
}
