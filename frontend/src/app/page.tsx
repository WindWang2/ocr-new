'use client'

import { useState, useEffect } from 'react'
import { Camera, Plus, Trash2, Download, RefreshCw, FileText, Beaker } from 'lucide-react'

// API 基础地址
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8765'

// 类型定义
interface InstrumentType {
  id: string
  name: string
  attributes: string[]
}

interface Instrument {
  camera_id: number
  type: string
  name: string
}

interface Reading {
  id: string
  camera_id: number
  instrument_type: string
  values: Record<string, any>
  image_path?: string
  timestamp: string
}

interface Experiment {
  id: string
  name: string
  description: string
  instruments: Instrument[]
  created_at: string
  readings: Reading[]
}

export default function Home() {
  // 状态
  const [instrumentTypes, setInstrumentTypes] = useState<InstrumentType[]>([])
  const [experiments, setExperiments] = useState<Record<string, Experiment>>({})
  const [currentExperiment, setCurrentExperiment] = useState<Experiment | null>(null)
  const [loading, setLoading] = useState(false)
  const [capturingCamera, setCapturingCamera] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 新实验表单
  const [newExpName, setNewExpName] = useState('')
  const [newExpDesc, setNewExpDesc] = useState('')
  const [newInstruments, setNewInstruments] = useState<Instrument[]>([])

  // 加载初始数据
  useEffect(() => {
    loadInstrumentTypes()
    loadExperiments()
  }, [])

  // API 调用
  const loadInstrumentTypes = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/instruments/types`)
      const data = await res.json()
      setInstrumentTypes(data.types || [])
    } catch (e) {
      console.error('加载仪器类型失败', e)
    }
  }

  const loadExperiments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/experiments`)
      const data = await res.json()
      setExperiments(data || {})
    } catch (e) {
      console.error('加载实验列表失败', e)
    }
  }

  const createExperiment = async () => {
    if (!newExpName.trim()) {
      setError('请输入实验名称')
      return
    }
    if (newInstruments.length === 0) {
      setError('请至少添加一个仪器')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/experiments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newExpName,
          description: newExpDesc,
          instruments: newInstruments
        })
      })
      const data = await res.json()
      if (data.success) {
        setCurrentExperiment(data.experiment)
        setExperiments(prev => ({ ...prev, [data.id]: data.experiment }))
        setNewExpName('')
        setNewExpDesc('')
        setNewInstruments([])
      } else {
        setError('创建实验失败')
      }
    } catch (e) {
      setError('网络错误')
    }
    setLoading(false)
  }

  const captureAndRead = async (cameraId: number, instrumentType: string) => {
    setCapturingCamera(cameraId)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/camera/capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_id: cameraId })
      })
      const data = await res.json()
      
      if (data.success && currentExperiment) {
        // 保存读数
        await fetch(`${API_BASE}/api/experiments/${currentExperiment.id}/reading`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            camera_id: cameraId,
            instrument_type: instrumentType,
            values: data.reading?.values || {},
            image_path: data.image_path,
            timestamp: new Date().toISOString()
          })
        })
        // 刷新实验数据
        loadExperiment(currentExperiment.id)
      } else {
        setError(data.detail || '拍照识别失败')
      }
    } catch (e) {
      setError('网络错误')
    }
    setCapturingCamera(null)
  }

  const loadExperiment = async (expId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/experiments/${expId}`)
      const data = await res.json()
      setCurrentExperiment(data)
      setExperiments(prev => ({ ...prev, [expId]: data }))
    } catch (e) {
      console.error('加载实验失败', e)
    }
  }

  const exportExperiment = async (expId: string) => {
    window.open(`${API_BASE}/api/experiments/${expId}/export`, '_blank')
  }

  // 仪器管理
  const addInstrument = () => {
    setNewInstruments(prev => [...prev, {
      camera_id: prev.length,
      type: 'electronic_balance',
      name: `仪器 ${prev.length + 1}`
    }])
  }

  const removeInstrument = (index: number) => {
    setNewInstruments(prev => prev.filter((_, i) => i !== index))
  }

  const updateInstrument = (index: number, field: keyof Instrument, value: any) => {
    setNewInstruments(prev => prev.map((inst, i) => 
      i === index ? { ...inst, [field]: value } : inst
    ))
  }

  const getInstrumentTypeName = (typeId: string) => {
    return instrumentTypes.find(t => t.id === typeId)?.name || typeId
  }

  return (
    <main className="min-h-screen p-4 md:p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        {/* 标题 */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Beaker className="text-blue-600" />
            OCR 仪表读数系统
          </h1>
          <p className="text-gray-600 mt-2">实验室仪器自动拍照识别与数据管理</p>
        </header>

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
            <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">关闭</button>
          </div>
        )}

        <div className="grid md:grid-cols-3 gap-6">
          {/* 左侧：实验列表 */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FileText className="text-gray-600" />
                实验列表
              </h2>
              
              {Object.keys(experiments).length === 0 ? (
                <p className="text-gray-500 text-sm">暂无实验</p>
              ) : (
                <div className="space-y-2">
                  {Object.values(experiments).map(exp => (
                    <div 
                      key={exp.id}
                      onClick={() => loadExperiment(exp.id)}
                      className={`p-3 rounded-lg cursor-pointer transition ${
                        currentExperiment?.id === exp.id 
                          ? 'bg-blue-50 border-blue-200 border' 
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium">{exp.name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {exp.instruments?.length || 0} 个仪器 · {exp.readings?.length || 0} 条读数
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 右侧：实验详情/创建 */}
          <div className="md:col-span-2">
            {currentExperiment ? (
              /* 实验详情 */
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-xl font-semibold">{currentExperiment.name}</h2>
                    <p className="text-gray-500 text-sm mt-1">{currentExperiment.description}</p>
                  </div>
                  <button 
                    onClick={() => exportExperiment(currentExperiment.id)}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <Download size={18} />
                    导出 CSV
                  </button>
                </div>

                {/* 仪器列表 */}
                <div className="space-y-4 mb-6">
                  <h3 className="font-medium text-gray-700">仪器读数</h3>
                  {currentExperiment.instruments?.map((inst, idx) => (
                    <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex justify-between items-center mb-3">
                        <div>
                          <span className="font-medium">{inst.name}</span>
                          <span className="text-gray-500 text-sm ml-2">
                            ({getInstrumentTypeName(inst.type)}) - 相机 {inst.camera_id}
                          </span>
                        </div>
                        <button
                          onClick={() => captureAndRead(inst.camera_id, inst.type)}
                          disabled={capturingCamera !== null}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                            capturingCamera === inst.camera_id
                              ? 'bg-gray-300 cursor-wait'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {capturingCamera === inst.camera_id ? (
                            <>
                              <RefreshCw size={18} className="animate-spin" />
                              识别中...
                            </>
                          ) : (
                            <>
                              <Camera size={18} />
                              拍照识别
                            </>
                          )}
                        </button>
                      </div>
                      
                      {/* 显示最近的读数 */}
                      {currentExperiment.readings
                        ?.filter(r => r.camera_id === inst.camera_id)
                        .slice(-1)
                        .map(reading => (
                          <div key={reading.id} className="mt-2 p-3 bg-white rounded border">
                            <div className="text-sm text-gray-500 mb-2">
                              {new Date(reading.timestamp).toLocaleString('zh-CN')}
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              {Object.entries(reading.values || {}).map(([key, value]) => (
                                <div key={key} className="flex justify-between">
                                  <span className="text-gray-600">{key}:</span>
                                  <span className="font-medium">{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                    </div>
                  ))}
                </div>

                {/* 读数历史 */}
                {currentExperiment.readings && currentExperiment.readings.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-3">历史记录</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="p-2 text-left">时间</th>
                            <th className="p-2 text-left">仪器</th>
                            <th className="p-2 text-left">读数</th>
                          </tr>
                        </thead>
                        <tbody>
                          {currentExperiment.readings.slice(-10).reverse().map(r => (
                            <tr key={r.id} className="border-t">
                              <td className="p-2">{new Date(r.timestamp).toLocaleString('zh-CN')}</td>
                              <td className="p-2">{getInstrumentTypeName(r.instrument_type)}</td>
                              <td className="p-2">{JSON.stringify(r.values)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* 创建新实验 */
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-xl font-semibold mb-6">创建新实验</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">实验名称</label>
                    <input
                      type="text"
                      value={newExpName}
                      onChange={e => setNewExpName(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="例如：水质检测实验-20260319"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">描述（可选）</label>
                    <textarea
                      value={newExpDesc}
                      onChange={e => setNewExpDesc(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      rows={2}
                      placeholder="实验目的、条件等..."
                    />
                  </div>

                  {/* 仪器配置 */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-sm font-medium text-gray-700">仪器配置</label>
                      <button
                        onClick={addInstrument}
                        className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                      >
                        <Plus size={16} />
                        添加仪器
                      </button>
                    </div>

                    {newInstruments.length === 0 ? (
                      <p className="text-gray-400 text-sm py-4 text-center border-2 border-dashed rounded-lg">
                        点击上方按钮添加仪器
                      </p>
                    ) : (
                      <div className="space-y-3">
                        {newInstruments.map((inst, idx) => (
                          <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                            <select
                              value={inst.type}
                              onChange={e => updateInstrument(idx, 'type', e.target.value)}
                              className="flex-1 px-3 py-2 border rounded"
                            >
                              {instrumentTypes.map(t => (
                                <option key={t.id} value={t.id}>{t.name}</option>
                              ))}
                            </select>
                            <input
                              type="number"
                              value={inst.camera_id}
                              onChange={e => updateInstrument(idx, 'camera_id', parseInt(e.target.value) || 0)}
                              className="w-20 px-3 py-2 border rounded"
                              placeholder="相机ID"
                              min="0"
                              max="8"
                            />
                            <input
                              type="text"
                              value={inst.name}
                              onChange={e => updateInstrument(idx, 'name', e.target.value)}
                              className="flex-1 px-3 py-2 border rounded"
                              placeholder="仪器名称"
                            />
                            <button
                              onClick={() => removeInstrument(idx)}
                              className="p-2 text-red-500 hover:bg-red-50 rounded"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={createExperiment}
                    disabled={loading}
                    className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 font-medium"
                  >
                    {loading ? '创建中...' : '创建实验'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
