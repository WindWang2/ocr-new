'use client'

import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ManualInstrumentSlot from '../ExperimentDetail/ManualInstrumentSlot'
import React from 'react'

export default function WaterMineralization({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.water_mineralization
  const configs = experiment.instrument_configs || (experiment as any).camera_configs || []

  return (
    <div className="space-y-12">
      <div className="space-y-12">
        {schema.instrumentFields.map((field) => {
          const config = configs.find((c: any) => c.field_key === field.fieldKey)
          const instrumentId = config ? (config.instrument_id ?? (config as any).camera_id) : field.targetInstrumentId
          const fieldReadings = experiment.readings.filter(r => r.field_key === field.fieldKey)
          
          return (
            <div key={field.fieldKey} className="space-y-4">
              <div className="flex items-center gap-2 px-1">
                <div className="w-1.5 h-4 bg-emerald-400 rounded-full" />
                <h3 className="font-semibold text-gray-900 tracking-wide text-sm">{field.label}</h3>
                {field.description && (
                  <span className="text-[11px] text-gray-400 font-medium ml-2">{field.description}</span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-4">
                {Array.from({ length: field.maxReadings }).map((_, idx) => (
                  <ManualInstrumentSlot
                    key={`${field.fieldKey}-${idx}`}
                    experimentId={experiment.id}
                    fieldKey={field.fieldKey}
                    label={field.label}
                    unit={field.unit}
                    instrumentId={instrumentId}
                    slotIndex={idx}
                    reading={fieldReadings.find(r => r.run_index === idx) ?? null}
                    onComplete={onRefresh}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
