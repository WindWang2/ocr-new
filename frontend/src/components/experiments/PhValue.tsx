'use client'

import { ExperimentViewProps, Reading } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ManualInstrumentSlot from '../ExperimentDetail/ManualInstrumentSlot'
import React from 'react'

export default function PhValue({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.ph_value
  const configs = experiment.instrument_configs || (experiment as any).camera_configs || []

  const getAverage = (key: string) => {
    // 我们的 field_key 现在是 ph_measurement，但是 ocr_data 里面存了 ph_value 和 temperature
    const readings = experiment.readings.filter(r => r.field_key === 'ph_measurement')
    if (readings.length === 0) return null
    
    let sum = 0
    let count = 0
    readings.forEach(r => {
      // 优先从 ocr_data 获取具体指标，如果 key 是 ph_value 也可以直接取 value
      let val: any = null
      if (key === 'ph_value') {
         val = r.value
      } else if (r.ocr_data && r.ocr_data[key] !== undefined) {
         val = r.ocr_data[key]
      }
      
      if (val !== null && val !== undefined && !isNaN(Number(val))) {
        sum += Number(val)
        count++
      }
    })
    
    if (count === 0) return null
    return (sum / count).toFixed(2)
  }

  return (
    <div className="space-y-12">
      {/* 均值汇总看板 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[
          { label: '平均 pH 值', val: getAverage('ph_value'), unit: '' },
          { label: '平均温度', val: getAverage('temperature'), unit: '℃' }
        ].map(item => (
          <div key={item.label} className="bg-white border-2 border-rose-100 rounded-3xl p-6 shadow-sm ring-8 ring-rose-50/50">
            <div className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-1">{item.label}</div>
            <div className="text-4xl font-black text-rose-600 tabular-nums">
              {item.val ?? '--'} <span className="text-sm font-medium text-rose-200 ml-1">{item.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-12">
        {schema.instrumentFields.map((field) => {
          const config = configs.find((c: any) => c.field_key === field.fieldKey)
          const instrumentId = config ? (config.instrument_id ?? (config as any).camera_id) : field.targetInstrumentId
          const fieldReadings = experiment.readings.filter(r => r.field_key === field.fieldKey)
          
          return (
            <div key={field.fieldKey} className="space-y-6">
              <div className="flex items-center gap-3 border-b-2 border-gray-50 pb-3">
                 <div className="w-1.5 h-6 bg-rose-500 rounded-full" />
                 <h3 className="text-lg font-black text-gray-800">{field.label}</h3>
                 <span className="text-xs text-gray-300 font-bold bg-gray-50 px-3 py-1 rounded-full uppercase tracking-tighter">
                   Instrument: D{instrumentId}
                 </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: field.maxReadings }).map((_, idx) => (
                  <ManualInstrumentSlot
                    key={`${field.fieldKey}-${idx}`}
                    experimentId={experiment.id}
                    fieldKey={field.fieldKey}
                    label={`${field.label} - 第 ${idx + 1} 次`}
                    unit={field.unit}
                    instrumentId={instrumentId}
                    slotIndex={idx + 1}
                    reading={fieldReadings.find(r => r.run_index === idx + 1) ?? null}
                    onComplete={onRefresh}
                    instrumentFields={[
                      { key: 'ph_value', label: 'pH值', unit: '' },
                      { key: 'temperature', label: '温度', unit: '℃' }
                    ]}
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