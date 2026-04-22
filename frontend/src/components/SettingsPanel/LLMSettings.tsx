'use client'

import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Cpu, Activity, Database, Settings2 } from 'lucide-react'
import type { LLMConfig, LLMStatus, GPUInfo } from '@/types'
import { getLLMConfig, setLLMConfig, checkLLMStatus } from '@/lib/api'

interface LLMSettingsProps {
  onStatusChange?: (status: LLMStatus) => void
}

export default function LLMSettings({ onStatusChange }: LLMSettingsProps) {
  const [config, setConfig] = useState<LLMConfig | null>(null)
  const [engineStatus, setEngineStatus] = useState<{
    status: LLMStatus
    provider?: string
    model?: string
    gpu?: GPUInfo
    detail?: string
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)

  const refreshStatus = useCallback(async () => {
    setLoading(true)
    try {
      const status = await checkLLMStatus()
      setEngineStatus(status)
      onStatusChange?.(status.status)
    } catch (e) {
      setEngineStatus({ status: 'error', detail: (e as Error).message })
      onStatusChange?.('error')
    } finally {
      setLoading(false)
    }
  }, [onStatusChange])

  useEffect(() => {
    getLLMConfig().then(setConfig)
    refreshStatus()
  }, [refreshStatus])

  const handleApply = async () => {
    if (!config) return
    setApplying(true)
    try {
      await setLLMConfig(config)
      await refreshStatus()
    } catch (e) {
      console.error(e)
    } finally {
      setApplying(false)
    }
  }

  if (!config) return null

  return (
    <div className="space-y-4">
      {/* Module 1: Compute Engine (GPU) */}
      <div className="module-card">
        <div className="module-header">
          <div className="flex items-center gap-2">
            <Cpu size={14} className="text-[var(--text-secondary)]" />
            <span className="module-title">计算引擎 (GPU)</span>
          </div>
          <div className="flex items-center gap-2">
             <span className="text-[10px] text-[var(--text-muted)] font-mono-num uppercase">
               {engineStatus?.gpu ? 'Active' : 'Offline'}
             </span>
             <div className={`status-dot ${engineStatus?.gpu ? 'status-dot-active' : 'bg-gray-300'}`} />
          </div>
        </div>
        <div className="p-3 space-y-2">
          {engineStatus?.gpu ? (
            <>
              <div className="text-xs font-bold text-[var(--text-primary)] truncate">
                {engineStatus.gpu.name}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-[var(--brand-light)] p-2 rounded-[var(--radius-sm)]">
                  <div className="text-[10px] text-[var(--text-muted)] uppercase mb-1">显存占用</div>
                  <div className="text-sm font-mono-num font-bold text-[var(--accent)]">
                    {engineStatus.gpu.memory_allocated}
                  </div>
                </div>
                <div className="bg-[var(--brand-light)] p-2 rounded-[var(--radius-sm)]">
                  <div className="text-[10px] text-[var(--text-muted)] uppercase mb-1">预留显存</div>
                  <div className="text-sm font-mono-num font-bold text-[var(--text-secondary)]">
                    {engineStatus.gpu.memory_reserved}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="py-2 text-center text-xs text-[var(--text-muted)] border border-dashed border-[var(--border)] rounded-[var(--radius-sm)]">
              未检测到可用 GPU 加速
            </div>
          )}
        </div>
      </div>

      {/* Module 2: Model Status */}
      <div className="module-card">
        <div className="module-header">
          <div className="flex items-center gap-2">
            <Database size={14} className="text-[var(--text-secondary)]" />
            <span className="module-title">模型状态</span>
          </div>
          <button 
            onClick={refreshStatus} 
            disabled={loading}
            className="p-1 hover:bg-white/50 rounded-full transition disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        <div className="p-3">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-[10px] text-[var(--text-muted)] uppercase">当前模型</div>
              <div className="text-xs font-bold text-[var(--text-primary)]">{engineStatus?.model || config.model_name}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-[var(--text-muted)] uppercase">核心架构</div>
              <div className="text-xs font-mono-num uppercase text-[var(--text-secondary)]">{engineStatus?.provider || config.provider}</div>
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[var(--text-secondary)]">推理压力</span>
              <span className="font-mono-num text-[var(--accent)]">Normal</span>
            </div>
            <div className="h-1 bg-[var(--brand-light)] rounded-full overflow-hidden">
              <div className="h-full bg-[var(--accent)] w-[15%]" />
            </div>
          </div>
        </div>
      </div>

      {/* Module 3: Inference Settings */}
      <div className="module-card">
        <div className="module-header">
          <div className="flex items-center gap-2">
            <Settings2 size={14} className="text-[var(--text-secondary)]" />
            <span className="module-title">推理参数</span>
          </div>
        </div>
        <div className="p-3 space-y-3">
          <div>
            <div className="flex justify-between mb-1">
              <label className="text-[11px] text-[var(--text-secondary)] font-bold">Temperature</label>
              <span className="text-[11px] font-mono-num text-[var(--brand)]">{config.temperature}</span>
            </div>
            <input
              type="range"
              min={0}
              max={1.5}
              step={0.1}
              value={config.temperature}
              onChange={e => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
              className="w-full h-1 bg-[var(--brand-light)] rounded-full appearance-none cursor-pointer accent-[var(--brand)]"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <label className="text-[11px] text-[var(--text-secondary)] font-bold">Max Tokens</label>
              <span className="text-[11px] font-mono-num text-[var(--brand)]">{config.max_tokens}</span>
            </div>
            <input
              type="range"
              min={128}
              max={4096}
              step={128}
              value={config.max_tokens}
              onChange={e => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
              className="w-full h-1 bg-[var(--brand-light)] rounded-full appearance-none cursor-pointer accent-[var(--brand)]"
            />
          </div>

          <button
            onClick={handleApply}
            disabled={applying}
            className="w-full py-1.5 bg-[var(--brand)] text-white text-[11px] font-bold uppercase tracking-widest rounded-[var(--radius-sm)] hover:opacity-90 transition disabled:opacity-50"
          >
            {applying ? 'Updating Engine...' : 'Sync Configuration'}
          </button>
        </div>
      </div>

      {engineStatus?.detail && (
        <div className="p-2 bg-red-50 border border-red-100 rounded-[var(--radius-sm)]">
          <div className="text-[9px] text-red-400 uppercase font-bold mb-1">Diagnostic Error</div>
          <div className="text-[10px] text-red-600 font-mono-num break-all">{engineStatus.detail}</div>
        </div>
      )}
    </div>
  )
}
