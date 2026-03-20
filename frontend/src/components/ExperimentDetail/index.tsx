'use client'
import { Experiment, ExperimentType, Reading, ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { exportUrl } from '@/lib/api'
import KinematicViscosity from '@/components/experiments/KinematicViscosity'
import ApparentViscosity from '@/components/experiments/ApparentViscosity'
import SurfaceTension from '@/components/experiments/SurfaceTension'
import { Download } from 'lucide-react'
import React from 'react'

const EXPERIMENT_VIEWS: Record<ExperimentType, React.ComponentType<ExperimentViewProps>> = {
  kinematic_viscosity: KinematicViscosity,
  apparent_viscosity: ApparentViscosity,
  surface_tension: SurfaceTension,
}

interface Props {
  experiment: Experiment
  onCapture: (fieldKey: string, cameraId: number) => Promise<Reading>
  capturing: string | null
}

export default function ExperimentDetail({ experiment, onCapture, capturing }: Props) {
  const schema = EXPERIMENT_SCHEMAS[experiment.type]
  const ViewComponent = EXPERIMENT_VIEWS[experiment.type]

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      {/* 顶部 */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{experiment.name}</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-lg">{schema.icon}</span>
            <span className="text-sm text-gray-500">{schema.label}</span>
            <span className="text-xs text-gray-400">
              · 创建于 {new Date(experiment.created_at).toLocaleDateString('zh-CN')}
            </span>
          </div>
        </div>
        <a
          href={exportUrl(experiment.id)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
        >
          <Download size={16} />
          导出 Excel
        </a>
      </div>

      {/* 实验内容（按类型分发） */}
      <ViewComponent
        experiment={experiment}
        onCapture={onCapture}
        capturing={capturing}
      />
    </div>
  )
}
