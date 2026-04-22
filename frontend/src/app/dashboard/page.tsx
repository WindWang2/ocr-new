'use client'

import { useState, useEffect, useCallback } from 'react'
import { Experiment, ExperimentSummary, ExperimentType, InstrumentFieldConfig, ManualParams, LLMStatus } from '@/types'
import { listExperiments, getExperiment, createExperiment, deleteExperiment, getMockConfig, setMockConfig, checkLLMStatus, getImageDir, setImageDir } from '@/lib/api'
import ExperimentList from '@/components/ExperimentList'
import Step1TypeSelector from '@/components/CreateExperiment/Step1TypeSelector'
import Step2Config from '@/components/CreateExperiment/Step2Config'
import ExperimentDetail from '@/components/ExperimentDetail'
import LLMSettings from '@/components/SettingsPanel/LLMSettings'
import InstrumentMatching from '@/components/SettingsPanel/InstrumentMatching'
import { FlaskConical, Settings, X, Home as HomeIcon } from 'lucide-react'
import Link from 'next/link'
import Image from 'next/image'

type View = 'list_empty' | 'create_step1' | 'create_step2' | 'detail'

export default function Dashboard() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null)
  const [view, setView] = useState<View>('list_empty')
  const [creating, setCreating] = useState(false)

  const [draftName, setDraftName] = useState('')
  const [draftType, setDraftType] = useState<ExperimentType | null>(null)


  const [mockEnabled, setMockEnabled] = useState(false)
  const [imageDir, setImageDirState] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [llmStatus, setLlmStatus] = useState<LLMStatus>('unknown')

  useEffect(() => {
    getMockConfig().then(setMockEnabled).catch(() => {})
    getImageDir().then(setImageDirState).catch(() => {})
    checkLLMStatus()
      .then(r => setLlmStatus(r.status))
      .catch(() => setLlmStatus('error'))
  }, [])

  const loadList = useCallback(async () => {
    try {
      const list = await listExperiments()
      setExperiments(list)
    } catch (e) {
      console.error('加载实验列表失败', e)
    }
  }, [])

  useEffect(() => { loadList() }, [loadList])

  const handleSelectExperiment = async (id: number) => {
    try {
      const exp = await getExperiment(id)
      setSelectedExperiment(exp)
      setView('detail')
    } catch (e) {
      console.error('加载实验失败', e)
    }
  }

  const handleStep1 = (name: string, type: ExperimentType) => {
    setDraftName(name)
    setDraftType(type)
    setView('create_step2')
  }

  const handleStep2Submit = async (manualParams: ManualParams, instrumentConfigs: InstrumentFieldConfig[]) => {
    if (!draftType) return
    setCreating(true)
    try {
      const id = await createExperiment({
        name: draftName,
        type: draftType,
        manual_params: manualParams,
        instrument_configs: instrumentConfigs,
      })
      await loadList()
      await handleSelectExperiment(id)
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteExperiment = async (id: number) => {
    try {
      await deleteExperiment(id)
      if (selectedExperiment?.id === id) {
        setSelectedExperiment(null)
        setView('list_empty')
      }
      await loadList()
    } catch (e) {
      console.error('删除实验失败', e)
    } finally {
    }
  }

  // 各实验组件拍照完成后调用，刷新实验数据
  const handleRefresh = async () => {
    if (!selectedExperiment) return
    const updated = await getExperiment(selectedExperiment.id)
    setSelectedExperiment(updated)
  }

  const renderMain = () => {
    if (view === 'create_step1') {
      return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-5 text-gray-800">新建实验</h2>
          <Step1TypeSelector onNext={handleStep1} />
        </div>
      )
    }

    if (view === 'create_step2' && draftType) {
      return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-5 text-gray-800">配置实验</h2>
          <Step2Config
            name={draftName}
            type={draftType}
            onBack={() => setView('create_step1')}
            onSubmit={handleStep2Submit}
            loading={creating}
          />
        </div>
      )
    }

    if (view === 'detail' && selectedExperiment) {
      return (
        <ExperimentDetail
          experiment={selectedExperiment}
          onRefresh={handleRefresh}
        />
      )
    }

    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-5">
          <FlaskConical size={28} className="text-gray-300" />
        </div>
        <p className="text-gray-400 text-sm">从左侧选择实验，或点击"新建"创建实验</p>
      </div>
    )
  }

  return (
    <main className="h-screen flex overflow-hidden">
      {/* Left sidebar - carbon themed */}
      <aside className="w-72 shrink-0 flex flex-col" style={{ background: 'linear-gradient(180deg, #121212 0%, #1a1a1a 100%)' }}>
        {/* Sidebar header */}
        <div className="px-5 py-6 border-b border-white/[0.05]">
          <Link href="/" className="flex items-center gap-2.5">
             <div className="w-8 h-8 bg-[var(--accent)] rounded flex items-center justify-center text-white font-black text-lg">W</div>
             <div className="flex flex-col">
                <span className="text-white text-sm font-black tracking-widest uppercase">WEWODON</span>
                <span className="text-[9px] text-white/30 font-medium tracking-tight uppercase">AI OCR Laboratory</span>
             </div>
          </Link>
        </div>

        {/* Experiment list fills remaining space */}
        <div className="flex-1 overflow-hidden">
          <ExperimentList
            experiments={experiments}
            selectedId={selectedExperiment?.id ?? null}
            onSelect={handleSelectExperiment}
            onNew={() => { setView('create_step1'); setSelectedExperiment(null) }}
            onDelete={handleDeleteExperiment}
          />
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: 'var(--bg)' }}>
        {/* Top bar */}
        <header className="shrink-0 h-14 flex items-center justify-between px-6 bg-white border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-zinc-50 border border-zinc-100 rounded">
              <HomeIcon size={14} className="text-zinc-400" />
            </div>
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              <span>Main</span>
              <span className="text-zinc-200">/</span>
              <span className="text-zinc-800">Dashboard</span>
            </div>
          </div>

          {/* Settings */}
          <div className="relative">
            <button
              onClick={() => setShowSettings(v => !v)}
              className="flex items-center gap-2 px-3 py-1.5 rounded border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:bg-zinc-50 hover:text-zinc-800 transition"
            >
              <div className={`w-2 h-2 rounded-full shrink-0 ${
                llmStatus === 'connected' || llmStatus === 'ready' ? 'status-dot-active' :
                llmStatus === 'error' ? 'bg-red-500' :
                'bg-zinc-300'
              }`} />
              <Settings size={13} className="text-zinc-400" />
              Settings
              {mockEnabled && (
                <span className="px-1.5 py-0.5 bg-amber-50 text-amber-600 border border-amber-100 rounded-[2px]">MOCK</span>
              )}
            </button>

            {showSettings && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowSettings(false)} />
                <div className="absolute right-0 top-10 w-80 bg-white rounded-[var(--radius-md)] shadow-2xl border border-[var(--border)] p-0 z-50 max-h-[85vh] overflow-hidden flex flex-col">
                  <div className="module-header shrink-0">
                    <span className="module-title">System Control Center</span>
                    <button onClick={() => setShowSettings(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition">
                      <X size={14} />
                    </button>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {/* Mock Toggle Module */}
                    <div className="p-3 bg-zinc-50 border border-zinc-100 rounded-[var(--radius-sm)] flex items-center justify-between">
                      <div>
                        <div className="text-[11px] font-bold text-zinc-800 uppercase tracking-tight">Virtual Optics</div>
                        <div className="text-[9px] text-zinc-400 mt-0.5 uppercase">Bypass TCP camera stream</div>
                      </div>
                      <button
                        onClick={async () => {
                          const next = !mockEnabled
                          await setMockConfig(next).catch(() => {})
                          setMockEnabled(next)
                        }}
                        className={`relative inline-flex h-4 w-8 items-center rounded-full transition-colors ${
                          mockEnabled ? 'bg-[var(--accent)]' : 'bg-zinc-200'
                        }`}
                      >
                        <span className={`inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform ${
                          mockEnabled ? 'translate-x-4.5' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>

                    {/* Image Directory Module */}
                    <div className="space-y-2">
                      <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Storage Matrix</div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={imageDir}
                          onChange={e => setImageDirState(e.target.value)}
                          placeholder="Default repository..."
                          className="flex-1 text-[11px] font-mono-num border border-zinc-200 rounded px-2 py-1.5 bg-zinc-50 focus:bg-white transition-colors"
                        />
                        <button
                          onClick={async () => {
                            await setImageDir(imageDir).catch(() => {})
                          }}
                          className="px-3 py-1.5 text-[10px] font-bold text-white bg-zinc-800 rounded hover:bg-black transition-colors"
                        >
                          SAVE
                        </button>
                      </div>
                    </div>

                    <div className="border-t border-zinc-100 pt-3">
                      <InstrumentMatching mockEnabled={mockEnabled} />
                    </div>

                    <div className="border-t border-zinc-100 pt-3">
                      <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Neural Engine</div>
                      <LLMSettings onStatusChange={setLlmStatus} />
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            {renderMain()}
          </div>
        </div>
      </div>
    </main>
  )
}
