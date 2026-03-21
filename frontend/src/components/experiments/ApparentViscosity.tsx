import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ReadingField from '@/components/ExperimentDetail/ReadingField'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function ApparentViscosity({ experiment, onCapture, capturing }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.apparent_viscosity

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-400 leading-relaxed bg-gray-50/80 rounded-lg px-4 py-3 border border-gray-100">
        每个转速字段需拍照 2 次（对应实验1、实验2），系统自动按读取顺序分配 run_index。
      </p>

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

      <ResultSummary type="apparent_viscosity" readings={experiment.readings} manualParams={experiment.manual_params} />
    </div>
  )
}
