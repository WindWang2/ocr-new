'use client'

import { useState, useEffect, useCallback } from 'react'
import { Experiment, ExperimentSummary, ExperimentType, Reading, CameraFieldConfig, ManualParams } from '@/types'
import { listExperiments, getExperiment, createExperiment, captureReading, getMockConfig, setMockConfig } from '@/lib/api'
import ExperimentList from '@/components/ExperimentList'
import Step1TypeSelector from '@/components/CreateExperiment/Step1TypeSelector'
import Step2Config from '@/components/CreateExperiment/Step2Config'
import ExperimentDetail from '@/components/ExperimentDetail'
import { FlaskConical, Settings, X } from 'lucide-react'

type View = 'list_empty' | 'create_step1' | 'create_step2' | 'detail'

export default function Home() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null)
  const [view, setView] = useState<View>('list_empty')
  const [creating, setCreating] = useState(false)

  // 创建向导状态
  const [draftName, setDraftName] = useState('')
  const [draftType, setDraftType] = useState<ExperimentType | null>(null)

  // 拍照状态
  const [capturing, setCapturing] = useState<string | null>(null)

  // Mock 相机设置
  const [mockEnabled, setMockEnabled] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  useEffect(() => {
    getMockConfig().then(setMockEnabled).catch(() => {})
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
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-800">新建实验</h2>
          <Step1TypeSelector onNext={handleStep1} />
        </div>
      )
    }

    if (view === 'create_step2' && draftType) {
      return (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-800">配置实验</h2>
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
      <div className="bg-white rounded-xl shadow-sm p-12 text-center">
        <FlaskConical size={48} className="mx-auto text-gray-300 mb-4" />
        <p className="text-gray-400">从左侧选择实验，或点击"新建"创建实验</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen p-4 md:p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
              <FlaskConical className="text-blue-600" />
              OCR 仪表读数系统
            </h1>
            <p className="text-gray-500 text-sm mt-1">实验室仪器自动拍照识别与数据管理</p>
          </div>

          {/* 设置按钮 */}
          <div className="relative">
            <button
              onClick={() => setShowSettings(v => !v)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-white hover:shadow-sm transition"
            >
              <Settings size={17} />
              系统设置
              {mockEnabled && (
                <span className="ml-1 px-1.5 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">Mock</span>
              )}
            </button>

            {showSettings && (
              <div className="absolute right-0 top-10 w-72 bg-white rounded-xl shadow-lg border border-gray-200 p-4 z-50">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold text-gray-800 text-sm">系统设置</span>
                  <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-gray-600">
                    <X size={16} />
                  </button>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div>
                    <div className="text-sm font-medium text-gray-700">Mock 相机模式</div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      跳过 TCP，读取本地图片做 OCR 测试
                    </div>
                  </div>
                  <button
                    onClick={async () => {
                      const next = !mockEnabled
                      await setMockConfig(next).catch(() => {})
                      setMockEnabled(next)
                    }}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      mockEnabled ? 'bg-amber-500' : 'bg-gray-300'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      mockEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                {mockEnabled && (
                  <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 mt-1">
                    已开启：拍照将读取 camera_images/camera_&#123;id&#125;/ 目录最新图片
                  </p>
                )}
              </div>
            )}
          </div>
        </header>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <ExperimentList
              experiments={experiments}
              selectedId={selectedExperiment?.id ?? null}
              onSelect={handleSelectExperiment}
              onNew={() => { setView('create_step1'); setSelectedExperiment(null) }}
            />
          </div>
          <div className="md:col-span-2">
            {renderMain()}
          </div>
        </div>
      </div>
    </main>
  )
}
