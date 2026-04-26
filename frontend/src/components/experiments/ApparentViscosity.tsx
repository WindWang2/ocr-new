'use client'

import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ManualInstrumentSlot from '../ExperimentDetail/ManualInstrumentSlot'
import { Calculator } from 'lucide-react'
import React from 'react'

export default function ApparentViscosity({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.apparent_viscosity
  
  const calculateViscosity = () => {
    const readings = experiment.readings.filter(r => r.field_key === 'reading_100rpm')
    if (readings.length === 0) return null
    const sum = readings.reduce((acc, r) => acc + (Number(r.value) || 0), 0)
    const avgAlpha = sum / readings.length
    return (avgAlpha * 5.077 / 1.704).toFixed(2)
  }

  const viscosity = calculateViscosity()
  const configs = experiment.instrument_configs || (experiment as any).camera_configs || []

  return (
    <div className="space-y-12">
      <div className="bg-white border-2 border-purple-100 rounded-3xl p-6 shadow-sm ring-8 ring-purple-50/50 max-w-sm">
        <div className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-1">计算表观黏度 (η)</div>
        <div className="text-4xl font-black text-purple-600 tabular-nums">
          {viscosity ?? '--'} <span className="text-sm font-medium text-purple-200 ml-1">mPa·s</span>
        </div>
      </div>

      <div className="space-y-12">
        {schema.instrumentFields.map((field) => {
          const config = configs.find((c: any) => c.field_key === field.fieldKey)
          const instrumentId = config ? (config.instrument_id ?? (config as any).camera_id) : field.targetInstrumentId
          const fieldReadings = experiment.readings.filter(r => r.field_key === field.fieldKey)
          
          return (
            <div key={field.fieldKey} className="space-y-6">
              <div className="flex items-center gap-3 border-b-2 border-gray-50 pb-3">
                 <div className="w-1.5 h-6 bg-purple-500 rounded-full" />
                 <h3 className="text-lg font-black text-gray-800">{field.label}</h3>
                 <span className="text-xs text-gray-300 font-bold bg-gray-50 px-3 py-1 rounded-full uppercase tracking-tighter">
                   Instrument: D{instrumentId}
                 </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: field.maxReadings }).map((_, idx) => {
                  const reading = fieldReadings.find(r => r.run_index === idx + 1) || null
                  return (
                    <ManualInstrumentSlot
                      key={`${field.fieldKey}-${idx}`}
                      experimentId={experiment.id}
                      fieldKey={field.fieldKey}
                      instrumentId={instrumentId}
                      label={`${field.label} 测量`}
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