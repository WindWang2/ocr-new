'use client'
import { useState } from 'react'
import { ExperimentSummary, ExperimentType } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import { Plus, Trash2, FlaskConical } from 'lucide-react'

interface Props {
  experiments: ExperimentSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onDelete: (id: number) => void
}

const TYPE_STYLES: Record<ExperimentType, { bg: string; text: string; dot: string }> = {
  kinematic_viscosity:  { bg: 'bg-brand-50',  text: 'text-brand-600',  dot: 'bg-brand-500' },
  apparent_viscosity:   { bg: 'bg-purple-50', text: 'text-purple-600', dot: 'bg-purple-500' },
  surface_tension:      { bg: 'bg-cyan-50',   text: 'text-cyan-600',   dot: 'bg-cyan-500' },
  water_mineralization: { bg: 'bg-emerald-50',text: 'text-emerald-600',dot: 'bg-emerald-500' },
  ph_value:             { bg: 'bg-rose-50',   text: 'text-rose-600',   dot: 'bg-rose-500' },
  test:                 { bg: 'bg-gray-50',   text: 'text-gray-500',   dot: 'bg-gray-400' },
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <FlaskConical size={16} className="text-blue-300" />
          <h2 className="text-sm font-semibold text-white/90 tracking-wide">实验列表</h2>
          <span className="ml-1 px-1.5 py-0.5 text-[10px] font-medium bg-white/10 text-white/50 rounded-full">
            {experiments.length}
          </span>
        </div>
        <button
          onClick={onNew}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition"
          style={{ background: 'var(--accent)', color: '#fff' }}
        >
          <Plus size={14} />
          新建
        </button>
      </div>

      {/* List */}
      {experiments.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-3">
            <FlaskConical size={22} className="text-white/20" />
          </div>
          <p className="text-white/30 text-sm">暂无实验</p>
          <p className="text-white/15 text-xs mt-1">点击上方按钮创建</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {experiments.map(exp => {
            const schema = EXPERIMENT_SCHEMAS[exp.type]
            const style = TYPE_STYLES[exp.type] ?? { bg: 'bg-gray-500/20', text: 'text-gray-300', dot: 'bg-gray-400' }
            const isSelected = selectedId === exp.id
            return (
              <div
                key={exp.id}
                onClick={() => onSelect(exp.id)}
                className={`group relative px-4 py-3 rounded-xl cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? 'bg-white/15 shadow-lg shadow-black/5'
                    : 'hover:bg-white/[0.06]'
                }`}
              >
                {isSelected && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-full" style={{ background: 'var(--accent)' }} />
                )}
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className={`text-sm font-medium truncate ${isSelected ? 'text-white' : 'text-white/80'}`}>
                      {exp.name}
                    </div>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-medium ${style.bg} ${style.text}`}>
                        <span className={`w-1 h-1 rounded-full ${style.dot}`} />
                        {schema?.label}
                      </span>
                    </div>
                    <div className="text-[11px] text-white/25 mt-1.5">
                      {new Date(exp.created_at).toLocaleDateString('zh-CN')}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, exp.id)}
                    disabled={deletingId === exp.id}
                    className="shrink-0 p-1 rounded-md text-white/0 group-hover:text-white/40 hover:!text-red-400 hover:!bg-red-400/10 transition-all disabled:opacity-30"
                    title="删除实验"
                  >
                    <Trash2 size={13} />
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
