'use client'

import { useState, useEffect } from 'react'
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { getCameraInstrumentsConfig } from '@/lib/api'
import ManualInstrumentSlot from '../ExperimentDetail/ManualInstrumentSlot'
import { Microscope } from 'lucide-react'
import React from 'react'

export default function TestTemplate({ experiment, onRefresh }: ExperimentViewProps) {
  const [instrumentConfigs, setInstrumentConfigs] = useState<any>(null)
  const schema = EXPERIMENT_SCHEMAS.test
  const configs = experiment.instrument_configs || (experiment as any).camera_configs || []

  useEffect(() => {
    getCameraInstrumentsConfig().then(setInstrumentConfigs)
  }, [])

  // 获取最大的 run_index，以确定显示多少个“测量批次”
  const maxRunIndex = experiment.readings.length > 0 
    ? Math.max(...experiment.readings.map(r => r.run_index || 0))
    : 0
  
  // 始终显示到 maxRunIndex，并额外多显示一个空白批次用于“继续测量”
  const runIndices = Array.from({ length: maxRunIndex + 2 }, (_, i) => i)

  return (
    <div className="space-y-16">
      <div className="flex items-center gap-4 border-b-2 border-gray-100 pb-4">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-gray-400">
          <Microscope size={28} />
        </div>
        <div>
          <h2 className="text-2xl font-black text-gray-900 tracking-tight">🔬 全场景仪表调试 工作站</h2>
          <p className="text-xs font-medium text-gray-500 mt-1">系统全量化验证：按批次查看并触发 D0~D8 所有仪表</p>
        </div>
      </div>

      <div className="space-y-20">
        {runIndices.map((runIndex) => (
          <div key={runIndex} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-3">
              <div className="px-4 py-1.5 bg-gray-900 text-white text-xs font-black rounded-full uppercase tracking-widest shadow-lg shadow-gray-200">
                Measurement Set {runIndex + 1}
              </div>
              <div className="h-[2px] flex-grow bg-gray-100 rounded-full" />
              {runIndex > maxRunIndex && (
                <span className="text-[10px] font-black text-brand-500 uppercase tracking-widest bg-brand-50 px-3 py-1 rounded-full border border-brand-100">New Set</span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-8">
              {schema.instrumentFields.map((field) => {
                const config = configs.find((c: any) => c.field_key === field.fieldKey)
                const instrumentId = config ? (config.instrument_id ?? (config as any).camera_id) : field.targetInstrumentId
                const reading = experiment.readings.find(r => r.field_key === field.fieldKey && r.run_index === runIndex) || null

                return (
                  <div key={field.fieldKey} className="group">
                    <div className="flex items-center justify-between px-1 mb-2">
                      <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest group-hover:text-brand-500 transition-colors">
                        D{instrumentId} · {field.label}
                      </span>
                    </div>
                    <ManualInstrumentSlot
                      experimentId={experiment.id}
                      fieldKey={field.fieldKey}
                      instrumentId={instrumentId}
                      label={field.label}
                      unit={field.unit}
                      slotIndex={runIndex}
                      reading={reading}
                      onComplete={onRefresh}
                      instrumentFields={instrumentConfigs?.[`D${instrumentId}`]?.readings}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
