'use client'

import { useState, useEffect } from 'react'
import { Plus, Trash2, Save, X, Info } from 'lucide-react'
import { InstrumentTemplate, TemplateField } from '@/types'
import { saveTemplate } from '@/lib/api'

interface TemplateEditorProps {
  template: InstrumentTemplate | null
  onSave: () => void
  onCancel: () => void
}

export default function TemplateEditor({ template, onSave, onCancel }: TemplateEditorProps) {
  const [formData, setFormData] = useState<InstrumentTemplate>({
    instrument_type: '',
    name: '',
    description: '',
    prompt_template: '',
    fields: [],
    keywords: [],
    example_images: [],
    default_tier: 2,
  })

  const [newKeyword, setNewKeyword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (template) {
      setFormData(template)
    }
  }, [template])

  const handleAddField = () => {
    const newField: TemplateField = {
      name: '',
      label: '',
      unit: '',
      type: 'float',
    }
    setFormData({ ...formData, fields: [...formData.fields, newField] })
  }

  const handleRemoveField = (index: number) => {
    const newFields = [...formData.fields]
    newFields.splice(index, 1)
    setFormData({ ...formData, fields: newFields })
  }

  const handleFieldChange = (index: number, key: keyof TemplateField, value: string) => {
    const newFields = [...formData.fields]
    newFields[index] = { ...newFields[index], [key]: value }
    setFormData({ ...formData, fields: newFields })
  }

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !formData.keywords.includes(newKeyword.trim())) {
      setFormData({ ...formData, keywords: [...formData.keywords, newKeyword.trim()] })
      setNewKeyword('')
    }
  }

  const handleRemoveKeyword = (kw: string) => {
    setFormData({ ...formData, keywords: formData.keywords.filter((k) => k !== kw) })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await saveTemplate(formData)
      onSave()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-50 flex items-center justify-between bg-gray-50/50">
        <h3 className="font-bold text-gray-900">
          {template ? '编辑模板' : '创建新模板'}
        </h3>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-gray-200/50 rounded-full transition text-gray-400 hover:text-gray-600"
        >
          <X size={20} />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-8">
        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm border border-red-100 flex items-start gap-3">
            <Info size={18} className="shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        <div className="grid sm:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              仪器标识 (instrument_type)
              <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              disabled={!!template}
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition disabled:opacity-60"
              placeholder="例如: ph_meter"
              value={formData.instrument_type}
              onChange={(e) => setFormData({ ...formData, instrument_type: e.target.value })}
            />
            <p className="text-xs text-gray-400">唯一标识符，创建后不可修改</p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              显示名称
              <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition"
              placeholder="例如: PH仪"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">描述</label>
          <textarea
            className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition min-h-[80px]"
            placeholder="简要描述该仪器的功能和用途"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-gray-700">识别关键词</label>
            <div className="flex gap-2">
              <input
                type="text"
                className="px-3 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition"
                placeholder="添加关键词"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
              />
              <button
                type="button"
                onClick={handleAddKeyword}
                className="p-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 min-h-[42px] p-3 bg-gray-50 rounded-xl border border-gray-100">
            {formData.keywords.length === 0 && (
              <span className="text-sm text-gray-400">点击右侧按钮添加 OCR 识别关键词，用于自动判断仪器类型</span>
            )}
            {formData.keywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-200 rounded-lg text-sm text-gray-600"
              >
                {kw}
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(kw)}
                  className="text-gray-400 hover:text-red-500 transition"
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-gray-700">读数字段配置</label>
            <button
              type="button"
              onClick={handleAddField}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 transition"
            >
              <Plus size={16} />
              添加字段
            </button>
          </div>
          
          <div className="space-y-3">
            {formData.fields.length === 0 && (
              <div className="text-center py-8 bg-gray-50 rounded-2xl border border-dashed border-gray-200 text-gray-400 text-sm">
                暂无字段配置，点击右上角“添加字段”开始
              </div>
            )}
            {formData.fields.map((field, idx) => (
              <div key={idx} className="grid sm:grid-cols-4 gap-3 p-4 bg-gray-50 rounded-xl relative group">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Key</span>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm outline-none focus:border-blue-500 transition"
                    placeholder="字段Key (如 ph_value)"
                    value={field.name}
                    onChange={(e) => handleFieldChange(idx, 'name', e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Label</span>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm outline-none focus:border-blue-500 transition"
                    placeholder="显示名称 (如 pH值)"
                    value={field.label}
                    onChange={(handleFieldChange(idx, 'label', e.target.value) as any)}
                  />
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Unit</span>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm outline-none focus:border-blue-500 transition"
                    placeholder="单位 (如 °C)"
                    value={field.unit}
                    onChange={(e) => handleFieldChange(idx, 'unit', e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Type</span>
                  <select
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm outline-none focus:border-blue-500 transition appearance-none"
                    value={field.type}
                    onChange={(e) => handleFieldChange(idx, 'type', e.target.value)}
                  >
                    <option value="float">数值 (Float)</option>
                    <option value="int">整数 (Int)</option>
                    <option value="string">文本 (String)</option>
                  </select>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveField(idx)}
                  className="absolute -right-2 -top-2 p-1.5 bg-white border border-gray-200 text-gray-400 hover:text-red-500 rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">识别提示词 (Prompt Template)</label>
          <textarea
            required
            className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition min-h-[160px] font-mono text-sm leading-relaxed"
            placeholder="输入大模型识别提示词，告知模型如何从图片中提取上述字段。建议包含输出 JSON 格式的要求。"
            value={formData.prompt_template}
            onChange={(e) => setFormData({ ...formData, prompt_template: e.target.value })}
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-50">
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2.5 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 px-8 py-2.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition shadow-lg shadow-blue-500/20 disabled:opacity-70"
          >
            <Save size={18} />
            {loading ? '保存中...' : '保存模板'}
          </button>
        </div>
      </form>
    </div>
  )
}
