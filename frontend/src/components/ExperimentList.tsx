'use client'
import { useState } from 'react'
import { ExperimentSummary, ExperimentType } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { FlaskConical, Plus, Trash2 } from 'lucide-react'

interface Props {
  experiments: ExperimentSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onDelete: (id: number) => void
}

const TYPE_COLORS: Record<ExperimentType, string> = {
  kinematic_viscosity: 'bg-blue-100 text-blue-700',
  apparent_viscosity: 'bg-purple-100 text-purple-700',
  surface_tension: 'bg-cyan-100 text-cyan-700',
}

export default function ExperimentList({ experiments, selectedId, onSelect, onNew, onDelete }: Props) {
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    if (confirm('确定要删除该实验吗？删除后不可恢复。')) {
      setDeletingId(id)
      onDelete(id)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-base font-semibold flex items-center gap-2 text-gray-700">
          <FlaskConical size={18} />
          实验列表
        </h2>
        <button
          onClick={onNew}
          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
        >
          <Plus size={15} />
          新建
        </button>
      </div>

      {experiments.length === 0 ? (
        <p className="text-gray-400 text-sm text-center mt-8">暂无实验，点击新建开始</p>
      ) : (
        <div className="space-y-2 overflow-y-auto flex-1">
          {experiments.map(exp => {
            const schema = EXPERIMENT_SCHEMAS[exp.type]
            return (
              <div
                key={exp.id}
                onClick={() => onSelect(exp.id)}
                className={`group p-3 rounded-lg cursor-pointer transition ${
                  selectedId === exp.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-sm text-gray-800 truncate">{exp.name}</div>
                    <div className="mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[exp.type]}`}>
                        {schema?.icon} {schema?.label}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {new Date(exp.created_at).toLocaleDateString('zh-CN')}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, exp.id)}
                    disabled={deletingId === exp.id}
                    className="shrink-0 p-1 rounded text-gray-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition disabled:opacity-50"
                    title="删除实验"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
