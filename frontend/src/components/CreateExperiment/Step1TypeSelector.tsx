'use client'
import { useState } from 'react'
import { ExperimentType } from '@/types'
import { EXPERIMENT_TYPE_LIST } from '@/lib/experimentTypes'
import { ArrowRight } from 'lucide-react'

interface Props {
  onNext: (name: string, type: ExperimentType) => void
}

export default function Step1TypeSelector({ onNext }: Props) {
  const [name, setName] = useState('')
  const [type, setType] = useState<ExperimentType | null>(null)
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
        <label className="block text-sm font-medium text-gray-700 mb-1">实验名称</label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="例如：运动粘度测试-20260320"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">选择实验类型</label>
        <div className="grid grid-cols-1 gap-3">
          {EXPERIMENT_TYPE_LIST.map(schema => (
            <div
              key={schema.type}
              onClick={() => setType(schema.type)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition ${
                type === schema.type
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{schema.icon}</span>
                <div>
                  <div className="font-semibold text-gray-800">{schema.label}</div>
                  <div className="text-sm text-gray-500 mt-0.5">{schema.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={handleNext}
        className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
      >
        下一步
        <ArrowRight size={18} />
      </button>
    </div>
  )
}
