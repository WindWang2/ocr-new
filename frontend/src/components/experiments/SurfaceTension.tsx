'use client'

import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import ManualInstrumentSlot from '../ExperimentDetail/ManualInstrumentSlot'
import { Droplets, Calculator } from 'lucide-react'
import React from 'react'

export default function SurfaceTension({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.surface_tension
  
  const getAverage = (fieldKey: string) => {
    const readings = experiment.readings.filter(r => r.field_key === fieldKey)
    if (readings.length === 0) return null
    const sum = readings.reduce((acc, r) => acc + (Number(r.value) || 0), 0)
    return (sum / readings.length).toFixed(3)
  }

  const configs = experiment.instrument_configs || (experiment as any).camera_configs || []

  return (
    <div className="space-y-12">
      {/* 结果汇总 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: '纯水均值', val: getAverage('water_surface_tension'), unit: 'mN/m' },
          { label: '表面张力均值', val: getAverage('fluid_surface_tension'), unit: 'mN/m' },
          { label: '界面张力均值', val: getAverage('fluid_interface_tension'), unit: 'mN/m' }
        ].map(item => (
          <div key={item.label} className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm">
            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">{item.label}</div>
            <div className="text-3xl font-black text-gray-900 tabular-nums">
              {item.val ?? '--'} <span className="text-sm font-medium text-gray-300 ml-1">{item.unit}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 按字段展示测量槽位 */}
      <div className="space-y-16">
        {schema.instrumentFields.map((field) => {
          // 查找配置，如果找不到也要渲染占位槽位
          const config = configs.find((c: any) => c.field_key === field.fieldKey)
          const instrumentId = config ? (config.instrument_id ?? (config as any).camera_id) : field.targetInstrumentId
          const fieldReadings = experiment.readings.filter(r => r.field_key === field.fieldKey)
          
          return (
            <div key={field.fieldKey} className="space-y-6">
              <div className="flex items-center gap-3 border-b-2 border-gray-50 pb-3">
                <div className="w-1.5 h-6 bg-brand-500 rounded-full" />
                <h3 className="text-lg font-black text-gray-800">{field.label}</h3>
                <span className="text-xs text-gray-300 font-bold bg-gray-50 px-3 py-1 rounded-full uppercase tracking-tighter">
                  Instrument: D{instrumentId}
                </span>

              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {Array.from({ length: field.maxReadings }).map((_, idx) => {
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
