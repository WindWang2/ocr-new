import { Experiment, ExperimentType, ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { exportUrl, runGlobalScan } from '@/lib/api'
import KinematicViscosity from '@/components/experiments/KinematicViscosity'
import ApparentViscosity from '@/components/experiments/ApparentViscosity'
import SurfaceTension from '@/components/experiments/SurfaceTension'
import WaterMineralization from '@/components/experiments/WaterMineralization'
import PhValue from '@/components/experiments/PhValue'
import TestTemplate from '@/components/experiments/TestTemplate'
import OperationStepsFormatter from './OperationStepsFormatter'
import { Download, Play, RefreshCw, Zap } from 'lucide-react'
import React, { useState } from 'react'

const EXPERIMENT_VIEWS: Record<ExperimentType, React.ComponentType<ExperimentViewProps>> = {
  kinematic_viscosity: KinematicViscosity,
  apparent_viscosity: ApparentViscosity,
  surface_tension: SurfaceTension,
  water_mineralization: WaterMineralization,
  ph_value: PhValue,
  test: TestTemplate,
}

interface Props {
  experiment: Experiment
  onRefresh: () => Promise<void>
}

export default function ExperimentDetail({ experiment, onRefresh }: Props) {
  const schema = EXPERIMENT_SCHEMAS[experiment.type]
  const ViewComponent = EXPERIMENT_VIEWS[experiment.type]
  const [isScanning, setIsScanning] = useState(false)

  if (!schema || !ViewComponent) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
        <p className="text-gray-400 text-sm">不支持的实验类型: {experiment.type}</p>
      </div>
    )
  }

  const handleGlobalScan = async () => {
    if (isScanning) return
    setIsScanning(true)
    try {
      await runGlobalScan(experiment)
      await onRefresh()
    } catch (e) {
      console.error('一键读取失败', e)
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-8 py-6 border-b border-gray-100 bg-gradient-to-r from-gray-50/50 to-white">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-black text-gray-900 tracking-tight">{experiment.name}</h2>
            <div className="flex items-center gap-3 mt-1.5">
              <span className="text-sm px-2 py-0.5 bg-white border border-gray-100 rounded-lg shadow-sm">{schema.icon} {schema.label}</span>
              <span className="text-gray-300">·</span>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                Created {new Date(experiment.created_at).toLocaleDateString('en-US')}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={exportUrl(experiment.id)}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-6 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 rounded-2xl transition shadow-sm active:scale-95"
            >
              <Download size={18} />
              导出报表
            </a>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8 bg-gray-50/30">
        {schema.operationSteps && (
          <div className="mb-8 bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-blue-800 mb-3 flex items-center gap-2">
              <span className="w-1.5 h-4 bg-blue-500 rounded-full" />
              实验操作步骤与注意事项
            </h3>
            <OperationStepsFormatter text={schema.operationSteps} svg={schema.flowchartSvg} />
          </div>
        )}
        <ViewComponent
          experiment={experiment}
          onRefresh={onRefresh}
        />
      </div>
    </div>
  )
}
