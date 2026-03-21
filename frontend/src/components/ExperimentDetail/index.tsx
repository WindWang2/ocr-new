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
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-gray-50/80 to-white">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{experiment.name}</h2>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-sm">{schema.icon}</span>
              <span className="text-xs text-gray-400">{schema.label}</span>
              <span className="text-gray-200">·</span>
              <span className="text-xs text-gray-400">
                {new Date(experiment.created_at).toLocaleDateString('zh-CN')}
              </span>
            </div>
          </div>
          <a
            href={exportUrl(experiment.id)}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-lg transition hover:opacity-90"
            style={{ background: 'var(--accent)', color: '#fff' }}
          >
            <Download size={14} />
            导出 Excel
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <ViewComponent
          experiment={experiment}
          onCapture={onCapture}
          capturing={capturing}
        />
      </div>
    </div>
  )
}
