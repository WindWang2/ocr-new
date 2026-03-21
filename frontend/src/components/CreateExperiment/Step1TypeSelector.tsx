'use client'
import { useState } from 'react'
import { ExperimentType } from '@/types'
import { EXPERIMENT_TYPE_LIST } from '@/lib/experimentTypes'
import { ArrowRight, Check } from 'lucide-react'

interface Props {
  onNext: (name: string, type: ExperimentType) => void
}

function generateDefaultName(type: ExperimentType | null): string {
  if (!type) return ''
  const now = new Date()
  const date = now.toISOString().slice(0, 10).replace(/-/g, '')
  const hour = String(now.getHours()).padStart(2, '0')
  const label = EXPERIMENT_TYPE_LIST.find(s => s.type === type)?.label ?? ''
  return `${label}-${date}${hour}`
}

export default function Step1TypeSelector({ onNext }: Props) {
  const [type, setType] = useState<ExperimentType | null>(null)
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const handleNext = () => {
    if (!name.trim()) { setError('请输入实验名称'); return }
    if (!type) { setError('请选择实验类型'); return }
    setError('')
    onNext(name.trim(), type)
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">实验名称</label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm transition hover:border-gray-300"
          placeholder="例如：运动粘度测试-20260320"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">选择实验类型</label>
        <div className="grid grid-cols-1 gap-3">
          {EXPERIMENT_TYPE_LIST.map(schema => (
            <div
              key={schema.type}
              onClick={() => {
                setType(schema.type)
                if (!name.trim()) setName(generateDefaultName(schema.type))
              }}
              className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${
                type === schema.type
                  ? 'border-brand-500 bg-brand-50/50 shadow-sm'
                  : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50/50'
              }`}
            >
              {type === schema.type && (
                <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-brand-500 flex items-center justify-center">
                  <Check size={12} className="text-white" />
                </div>
              )}
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-lg shrink-0">
                  {schema.icon}
                </div>
                <div>
                  <div className="font-semibold text-gray-800 text-sm">{schema.label}</div>
                  <div className="text-xs text-gray-400 mt-0.5 leading-relaxed">{schema.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500 bg-red-50 rounded-lg px-4 py-2">{error}</p>
      )}

      <button
        onClick={handleNext}
        className="w-full flex items-center justify-center gap-2 py-3 text-white text-sm font-medium rounded-xl transition hover:opacity-90 shadow-sm"
        style={{ background: 'var(--brand)' }}
      >
        下一步
        <ArrowRight size={16} />
      </button>
    </div>
  )
}
