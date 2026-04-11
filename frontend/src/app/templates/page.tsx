'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import {
  Settings,
  Plus,
  Edit2,
  Trash2,
  ChevronLeft,
  Layout,
  Tag,
  FileText,
  AlertCircle,
  Loader2,
  Search,
} from 'lucide-react'
import { InstrumentTemplate } from '@/types'
import { listTemplates } from '@/lib/api'
import TemplateEditor from '@/components/TemplateManagement/TemplateEditor'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<InstrumentTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<InstrumentTemplate | null>(null)

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const data = await listTemplates()
      setTemplates(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取模板失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTemplates()
  }, [])

  const handleEdit = (template: InstrumentTemplate) => {
    setEditingTemplate(template)
    setIsEditing(true)
  }

  const handleCreate = () => {
    setEditingTemplate(null)
    setIsEditing(true)
  }

  const handleSave = () => {
    setIsEditing(false)
    fetchTemplates()
  }

  const filteredTemplates = templates.filter(
    (t) =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.instrument_type.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="min-h-screen bg-gray-50/50">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-3">
              <Image src="/logo.png" alt="WEWODON" width={100} height={67} className="h-8 w-auto" />
            </Link>
            <div className="h-6 w-px bg-gray-200" />
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-900 transition"
            >
              <ChevronLeft size={16} />
              返回控制台
            </Link>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="px-3 py-1 bg-blue-50 text-blue-600 rounded-lg text-xs font-bold uppercase tracking-wider">
              Templates
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
              <Layout className="text-blue-500" />
              仪器识别模板管理
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              定义不同型号仪器的识别逻辑、关键词及读数字段
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition shadow-lg shadow-blue-500/20"
          >
            <Plus size={20} />
            新增仪器模板
          </button>
        </div>

        {isEditing ? (
          <div className="max-w-3xl mx-auto">
            <TemplateEditor
              template={editingTemplate}
              onSave={handleSave}
              onCancel={() => setIsEditing(false)}
            />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Toolbar */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-col sm:flex-row gap-4 items-center">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="搜索模板名称或标识..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition text-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="text-sm text-gray-400 font-medium px-2">
                共 {filteredTemplates.length} 个模板
              </div>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-gray-100 shadow-sm">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">加载模板列表中...</p>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-gray-100 shadow-sm text-center px-4">
                <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-4">
                  <AlertCircle size={32} />
                </div>
                <h3 className="text-lg font-bold text-gray-900">加载失败</h3>
                <p className="mt-2 text-gray-500 max-w-md">{error}</p>
                <button
                  onClick={fetchTemplates}
                  className="mt-6 px-6 py-2 bg-gray-100 text-gray-600 font-semibold rounded-xl hover:bg-gray-200 transition"
                >
                  重试
                </button>
              </div>
            ) : filteredTemplates.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 bg-white rounded-3xl border border-gray-100 shadow-sm text-center px-4">
                <div className="w-20 h-20 bg-gray-50 text-gray-300 rounded-full flex items-center justify-center mb-6">
                  <Layout size={40} />
                </div>
                <h3 className="text-xl font-bold text-gray-900">暂无仪器模板</h3>
                <p className="mt-2 text-gray-500 max-w-md">
                  {searchQuery ? '未找到匹配搜索条件的模板' : '您可以点击右上角的“新增仪器模板”按钮来添加一个新的仪器识别规则'}
                </p>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="mt-6 text-blue-600 font-semibold hover:underline"
                  >
                    清除搜索条件
                  </button>
                )}
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredTemplates.map((template) => (
                  <div
                    key={template.instrument_type}
                    className="group bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-100 transition flex flex-col"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300">
                        <Settings size={24} />
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => handleEdit(template)}
                          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                          title="编辑模板"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                          title="删除模板 (暂不支持)"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-blue-600 transition">
                      {template.name}
                    </h3>
                    <code className="text-xs font-mono text-gray-400 mb-3 block">
                      {template.instrument_type}
                    </code>
                    
                    <p className="text-sm text-gray-500 mb-6 line-clamp-2 flex-1">
                      {template.description || '暂无描述'}
                    </p>

                    <div className="space-y-3 pt-4 border-t border-gray-50 mt-auto">
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Tag size={14} className="shrink-0" />
                        <span className="font-semibold text-gray-600">关键词:</span>
                        <span className="truncate">
                          {template.keywords.length > 0 ? template.keywords.join(', ') : '未设置'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <FileText size={14} className="shrink-0" />
                        <span className="font-semibold text-gray-600">字段:</span>
                        <span className="truncate">
                          {template.fields.length > 0 
                            ? template.fields.map(f => f.label).join(', ') 
                            : '未配置读数字段'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
