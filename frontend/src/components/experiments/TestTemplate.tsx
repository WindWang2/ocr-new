'use client'

import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ManualInstrumentSlot from '../ExperimentDetail/ManualInstrumentSlot'
import { Microscope } from 'lucide-react'
import React from 'react'

export default function TestTemplate({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.test
  const configs = experiment.instrument_configs || (experiment as any).camera_configs || []

  return (
    <div className="space-y-12">
      <div className="flex items-center gap-4 border-b-2 border-gray-100 pb-4">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-gray-400">
          <Microscope size={28} />
        </div>
        <div>
          <h2 className="text-2xl font-black text-gray-900 tracking-tight">🔬 全场景仪表调试 工作站</h2>
          <p className="text-xs font-medium text-gray-500 mt-1">手动触发任意仪表采集，用于系统校准与验证</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-12">
        {schema.instrumentFields.map((field) => {
          const config = configs.find((c: any) => c.field_key === field.fieldKey)
          const instrumentId = config ? (config.instrument_id ?? (config as any).camera_id) : field.targetInstrumentId
          const fieldReadings = experiment.readings.filter(r => r.field_key === field.fieldKey)

          return (
            <div key={field.fieldKey} className="space-y-4">
              <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest px-1">
                F{instrumentId} · {field.label}
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {/* 测试模板默认显示 2 个槽位 */}
                {Array.from({ length: Math.max(2, fieldReadings.length) }).map((_, idx) => {
                  const reading = fieldReadings.find(r => r.run_index === idx + 1) || null
                  return (
                    <ManualInstrumentSlot
                      key={`${field.fieldKey}-${idx}`}
                      experimentId={experiment.id}
                      fieldKey={field.fieldKey}
                      instrumentId={instrumentId}
                      label={field.label}
                      unit={field.unit}
                      slotIndex={idx + 1}
                      reading={reading}
                      onComplete={onRefresh}
                    />
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}