'use client'

import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, ChevronDown } from 'lucide-react'
import type { LLMConfig, LLMStatus, LLMProviderType, OllamaModel } from '@/types'
import { getLLMConfig, setLLMConfig, listOllamaModels, checkLLMStatus } from '@/lib/api'

interface LLMSettingsProps {
  onStatusChange?: (status: LLMStatus) => void
}

export default function LLMSettings({ onStatusChange }: LLMSettingsProps) {
  const [config, setConfig] = useState<LLMConfig | null>(null)
  const [editing, setEditing] = useState<LLMConfig | null>(null)
  const [models, setModels] = useState<OllamaModel[]>([])
  const [loadingModels, setLoadingModels] = useState(false)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showModelDropdown, setShowModelDropdown] = useState(false)

  useEffect(() => {
    getLLMConfig().then(c => {
      setConfig(c)
      setEditing(c)
    })
  }, [])

  const refreshModels = useCallback(async () => {
    if (!editing) return
    setLoadingModels(true)
    setError(null)
    try {
      const list = await listOllamaModels(editing.base_url)
      setModels(list)
      if (list.length === 0) {
        setError('未找到可用模型')
      }
    } catch (e) {
      setError('无法连接 Ollama 服务')
      setModels([])
    } finally {
      setLoadingModels(false)
    }
  }, [editing])

  const apply = async () => {
    if (!editing) return
    setApplying(true)
    setError(null)
    try {
      await setLLMConfig(editing)
      setConfig(editing)
      // 验证连接
      onStatusChange?.('loading')
      const status = await checkLLMStatus()
      onStatusChange?.(status.status)
      if (!status.success) {
        setError(`连接失败: ${status.detail}`)
      }
    } catch (e) {
      setError((e as Error).message)
      onStatusChange?.('error')
    } finally {
      setApplying(false)
    }
  }

  if (!editing) return null

  const providerType: LLMProviderType = editing.provider

  return (
    <div className="space-y-3">
      {/* Provider 类型选择 */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setEditing({ ...editing, provider: 'ollama' })}
          className={`flex-1 text-xs py-1.5 rounded-md transition ${
            providerType === 'ollama'
              ? 'bg-white text-blue-700 font-medium shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Ollama
        </button>
        <button
          onClick={() => setEditing({ ...editing, provider: 'openai_compatible' })}
          className={`flex-1 text-xs py-1.5 rounded-md transition ${
            providerType === 'openai_compatible'
              ? 'bg-white text-blue-700 font-medium shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          OpenAI 兼容
        </button>
      </div>

      {/* 服务地址 */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">服务地址</label>
        <input
          type="text"
          value={editing.base_url}
          onChange={e => setEditing({ ...editing, base_url: e.target.value })}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
          placeholder={providerType === 'ollama' ? 'http://localhost:11434' : 'https://api.openai.com'}
        />
      </div>

      {providerType === 'ollama' ? (
        /* Ollama 模式: 模型列表 */
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-gray-500">模型</label>
            <button
              onClick={refreshModels}
              disabled={loadingModels}
              className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1 disabled:opacity-50"
            >
              <RefreshCw size={12} className={loadingModels ? 'animate-spin' : ''} />
              刷新列表
            </button>
          </div>

          {models.length > 0 ? (
            <div className="relative">
              <button
                onClick={() => setShowModelDropdown(v => !v)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-left flex items-center justify-between hover:border-blue-300 transition"
              >
                <span className="truncate">{editing.model_name}</span>
                <ChevronDown size={14} className="text-gray-400 shrink-0" />
              </button>
              {showModelDropdown && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {models.map(m => (
                    <button
                      key={m.name}
                      onClick={() => {
                        setEditing({ ...editing, model_name: m.name })
                        setShowModelDropdown(false)
                      }}
                      className={`w-full text-sm text-left px-3 py-1.5 hover:bg-blue-50 transition ${
                        editing.model_name === m.name ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                      }`}
                    >
                      <span className="truncate block">{m.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <input
              type="text"
              value={editing.model_name}
              onChange={e => setEditing({ ...editing, model_name: e.target.value })}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
              placeholder="输入模型名称或点击刷新列表"
            />
          )}
        </div>
      ) : (
        /* OpenAI 兼容模式: model + api_key */
        <>
          <div>
            <label className="text-xs text-gray-500 block mb-1">模型名称</label>
            <input
              type="text"
              value={editing.model_name}
              onChange={e => setEditing({ ...editing, model_name: e.target.value })}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
              placeholder="gpt-4o"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">API Key</label>
            <input
              type="password"
              value={editing.api_key || ''}
              onChange={e => setEditing({ ...editing, api_key: e.target.value || null })}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
              placeholder="sk-..."
            />
          </div>
        </>
      )}

      {/* 错误提示 */}
      {error && (
        <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-1.5">{error}</p>
      )}

      {/* 应用按钮 */}
      <button
        onClick={apply}
        disabled={applying}
        className="w-full text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-lg px-3 py-1.5 transition"
      >
        {applying ? '应用中...' : '应用配置'}
      </button>

      {/* 当前状态 */}
      {config && (
        <p className="text-xs text-gray-400 text-center">
          当前: {config.model_name}
        </p>
      )}
    </div>
  )
}
