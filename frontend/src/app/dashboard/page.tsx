'use client'

import { useState, useEffect, useCallback } from 'react'
import { Experiment, ExperimentSummary, ExperimentType, Reading, CameraFieldConfig, ManualParams, LLMStatus } from '@/types'
import { listExperiments, getExperiment, createExperiment, deleteExperiment, captureReading, getMockConfig, setMockConfig, checkLLMStatus, getImageDir, setImageDir } from '@/lib/api'
import ExperimentList from '@/components/ExperimentList'
import Step1TypeSelector from '@/components/CreateExperiment/Step1TypeSelector'
import Step2Config from '@/components/CreateExperiment/Step2Config'
import ExperimentDetail from '@/components/ExperimentDetail'
import LLMSettings from '@/components/SettingsPanel/LLMSettings'
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

  const [capturing, setCapturing] = useState<string | null>(null)

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

  const handleStep2Submit = async (manualParams: ManualParams, cameraConfigs: CameraFieldConfig[]) => {
    if (!draftType) return
    setCreating(true)
    try {
      const id = await createExperiment({
        name: draftName,
        type: draftType,
        manual_params: manualParams,
        camera_configs: cameraConfigs,
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

  const handleCapture = async (fieldKey: string, cameraId: number): Promise<Reading> => {
    if (!selectedExperiment) throw new Error('无当前实验')
    setCapturing(fieldKey)
    try {
      const reading = await captureReading(selectedExperiment.id, fieldKey, cameraId)
      setSelectedExperiment(prev =>
        prev ? { ...prev, readings: [...prev.readings, reading] } : prev
      )
      return reading
    } finally {
      setCapturing(null)
    }
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
          onCapture={handleCapture}
          capturing={capturing}
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
      {/* Left sidebar - dark themed */}
      <aside className="w-72 shrink-0 flex flex-col" style={{ background: 'linear-gradient(180deg, #0F1B2D 0%, #162744 100%)' }}>
        {/* Sidebar header */}
        <div className="px-5 py-4 border-b border-white/[0.06]">
          <Link href="/" className="flex items-center gap-2.5">
            <Image src="/logo.png" alt="WEWODON" width={120} height={80} className="h-7 w-auto brightness-0 invert opacity-80" />
          </Link>
          <div className="mt-2 text-[11px] text-white/30 font-medium tracking-wide">
            智能实验方舱 · 控制台
          </div>
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
        <header className="shrink-0 h-14 flex items-center justify-between px-6 bg-white border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Link href="/" className="text-gray-300 hover:text-brand-500 transition">
              <HomeIcon size={15} />
            </Link>
            <span className="text-gray-200 text-xs">/</span>
            <span className="text-xs text-gray-400 font-medium">控制台</span>
          </div>

          {/* Settings */}
          <div className="relative">
            <button
              onClick={() => setShowSettings(v => !v)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition"
            >
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                llmStatus === 'connected' ? 'bg-emerald-400' :
                llmStatus === 'error' ? 'bg-red-400' :
                'bg-amber-400'
              }`} />
              <Settings size={14} />
              设置
              {mockEnabled && (
                <span className="px-1.5 py-0.5 bg-amber-50 text-amber-600 text-[10px] font-medium rounded">Mock</span>
              )}
            </button>

            {showSettings && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowSettings(false)} />
                <div className="absolute right-0 top-9 w-72 bg-white rounded-xl shadow-xl border border-gray-100 p-4 z-50 max-h-[480px] overflow-y-auto">
                  <div className="flex justify-between items-center mb-4">
                    <span className="font-semibold text-gray-800 text-sm">系统设置</span>
                    <button onClick={() => setShowSettings(false)} className="text-gray-300 hover:text-gray-500 transition">
                      <X size={15} />
                    </button>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <div>
                      <div className="text-sm font-medium text-gray-700">Mock 相机模式</div>
                      <div className="text-[11px] text-gray-400 mt-0.5">
                        跳过 TCP，读取本地图片做 OCR 测试
                      </div>
                    </div>
                    <button
                      onClick={async () => {
                        const next = !mockEnabled
                        await setMockConfig(next).catch(() => {})
                        setMockEnabled(next)
                      }}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        mockEnabled ? 'bg-amber-500' : 'bg-gray-200'
                      }`}
                    >
                      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform ${
                        mockEnabled ? 'translate-x-4' : 'translate-x-0.5'
                      }`} />
                    </button>
                  </div>

                  {mockEnabled && (
                    <p className="text-[11px] text-amber-600 bg-amber-50 rounded-lg px-3 py-2 mt-1">
                      已开启：拍照将读取 image_dir/F&#123;id&#125;/ 目录最新图片
                    </p>
                  )}

                  {/* 图片存储目录 */}
                  <div className="mt-3 pt-3 border-t border-gray-50">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">图片存储目录</div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={imageDir}
                          onChange={e => setImageDirState(e.target.value)}
                          placeholder="留空使用默认 camera_images/"
                          className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-1.5 bg-gray-50"
                        />
                        <button
                          onClick={async () => {
                            await setImageDir(imageDir).catch(() => {})
                          }}
                          className="px-3 py-1.5 text-xs font-medium text-white rounded-lg shrink-0"
                          style={{ background: 'var(--brand)' }}
                        >
                          保存
                        </button>
                      </div>
                      <p className="text-[10px] text-gray-400 mt-1.5">
                        {mockEnabled ? 'Mock 模式' : '拍照模式'}将读取该目录下 F0 ~ F8 子文件夹的最新图片
                      </p>
                    </div>

                  <div className="border-t border-gray-50 mt-3 pt-3">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">LLM 模型</div>
                    <LLMSettings onStatusChange={setLlmStatus} />
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
