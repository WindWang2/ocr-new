'use client'

import { useState, useEffect } from 'react'
import { Camera, Plus, Trash2, Download, RefreshCw, FileText, Beaker, ChevronDown, ChevronUp } from 'lucide-react'

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
  confidence?: number
}

interface Experiment {
  id: string
  name: string
  description: string
  instruments: Instrument[]
  created_at: string
  readings: Reading[]
  cameras?: number[]  // 新增：关联相机列表
}

export default function Home() {
  // 状态
  const [instrumentTypes, setInstrumentTypes] = useState<InstrumentType[]>([])
  const [experiments, setExperiments] = useState<Record<string, Experiment>>({})
  const [currentExperiment, setCurrentExperiment] = useState<Experiment | null>(null)
  const [loading, setLoading] = useState(false)
  const [capturingCamera, setCapturingCamera] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [availableCameras] = useState<number[]>([0, 1, 2, 3, 4, 5, 6, 7, 8])  // 可用相机列表

  // 新实验表单
  const [newExpName, setNewExpName] = useState('')
  const [newExpDesc, setNewExpDesc] = useState('')
  const [newInstruments, setNewInstruments] = useState<Instrument[]>([])
  const [newCameras, setNewCameras] = useState<number[]>([])  // 新增：选中的相机列表

  // 编辑模式
  const [isEditing, setIsEditing] = useState(false)
  const [editExpName, setEditExpName] = useState('')
  const [editExpDesc, setEditExpDesc] = useState('')
  const [editCameras, setEditCameras] = useState<number[]>([])
  const [editInstruments, setEditInstruments] = useState<Instrument[]>([])

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
    if (newInstruments.length === 0 && newCameras.length === 0) {
      setError('请至少添加一个相机或仪器')
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
          cameras: newCameras,  // 新增：传递相机列表
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
        setNewCameras([])
      } else {
        setError('创建实验失败')
      }
    } catch (e) {
      setError('网络错误')
    }
    setLoading(false)
  }

  // 更新实验（编辑模式）
  const updateExperiment = async () => {
    if (!currentExperiment) return
    
    setLoading(true)
    setError(null)
    try {
      // 调用更新接口（如果后端支持）
      const res = await fetch(`${API_BASE}/api/experiments/${currentExperiment.id}`, {
        method: 'PUT',  // 假设后端支持 PUT
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editExpName,
          description: editExpDesc,
          cameras: editCameras,
          instruments: editInstruments
        })
      })
      
      // 如果后端不支持 PUT，则重新创建
      if (!res.ok) {
        // 兼容方案：删除旧实验创建新实验（需要后端支持删除）
        // 这里简单处理：直接更新本地状态
        const updatedExp = {
          ...currentExperiment,
          name: editExpName,
          description: editExpDesc,
          cameras: editCameras,
          instruments: editInstruments
        }
        setCurrentExperiment(updatedExp)
        setExperiments(prev => ({ ...prev, [currentExperiment.id]: updatedExp }))
      } else {
        const data = await res.json()
        setCurrentExperiment(data.experiment)
        setExperiments(prev => ({ ...prev, [currentExperiment.id]: data.experiment }))
      }
      setIsEditing(false)
    } catch (e) {
      setError('更新失败')
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
            confidence: data.reading?.confidence,
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

  // 批量读取所有相机
  const captureAllCameras = async () => {
    const cameras = currentExperiment?.cameras || currentExperiment?.instruments?.map(i => i.camera_id) || []
    for (const cameraId of cameras) {
      const instrument = currentExperiment?.instruments?.find(i => i.camera_id === cameraId)
      if (instrument) {
        await captureAndRead(cameraId, instrument.type)
      }
    }
  }

  const loadExperiment = async (expId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/experiments/${expId}`)
      const data = await res.json()
      setCurrentExperiment(data)
      // 初始化编辑状态
      setEditExpName(data.name)
      setEditExpDesc(data.description || '')
      setEditCameras(data.cameras || [])
      setEditInstruments(data.instruments || [])
    } catch (e) {
      console.error('加载实验失败', e)
    }
  }

  const exportExperiment = async (expId: string) => {
    window.open(`${API_BASE}/api/experiments/${expId}/export`, '_blank')
  }

  // 仪器管理
  const addInstrument = () => {
    const usedCameras = newInstruments.map(i => i.camera_id)
    const availableCam = availableCameras.find(c => !usedCameras.includes(c)) || 0
    setNewInstruments(prev => [...prev, {
      camera_id: availableCam,
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

  // 相机选择管理
  const toggleCamera = (cameraId: number) => {
    setNewCameras(prev => 
      prev.includes(cameraId) 
        ? prev.filter(c => c !== cameraId)
        : [...prev, cameraId]
    )
  }

  const toggleEditCamera = (cameraId: number) => {
    setEditCameras(prev => 
      prev.includes(cameraId) 
        ? prev.filter(c => c !== cameraId)
        : [...prev, cameraId]
    )
  }

  const getInstrumentTypeName = (typeId: string) => {
    return instrumentTypes.find(t => t.id === typeId)?.name || typeId
  }

  // 计算相机读数汇总
  const getCameraSummary = (exp: Experiment) => {
    const summary: Record<number, { count: number, latest: Reading | null }> = {}
    const cameraSet = new Set(exp.instruments?.map(i => i.camera_id) || [])
    const allCameras = Array.from(cameraSet)
    
    for (const cam of allCameras) {
      const camReadings = exp.readings?.filter(r => r.camera_id === cam) || []
      summary[cam] = {
        count: camReadings.length,
        latest: camReadings.length > 0 ? camReadings[camReadings.length - 1] : null
      }
    }
    return summary
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
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">关闭</button>
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
                  {Object.values(experiments).map(exp => {
                    const summary = getCameraSummary(exp)
                    const totalReadings = Object.values(summary).reduce((sum, s) => sum + s.count, 0)
                    const cameraCount = exp.cameras?.length || exp.instruments?.length || 0
                    return (
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
                          {cameraCount} 个相机 · {totalReadings} 条读数
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* 右侧：实验详情/创建 */}
          <div className="md:col-span-2">
            {currentExperiment ? (
              /* 实验详情 */
              <div className="bg-white rounded-xl shadow-sm p-6">
                {isEditing ? (
                  /* 编辑模式 */
                  <>
                    <div className="flex justify-between items-start mb-6">
                      <h2 className="text-xl font-semibold">编辑实验</h2>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => setIsEditing(false)}
                          className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                        >
                          取消
                        </button>
                        <button 
                          onClick={updateExperiment}
                          disabled={loading}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                        >
                          {loading ? '保存中...' : '保存'}
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">实验名称</label>
                        <input
                          type="text"
                          value={editExpName}
                          onChange={e => setEditExpName(e.target.value)}
                          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                        <textarea
                          value={editExpDesc}
                          onChange={e => setEditExpDesc(e.target.value)}
                          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                          rows={2}
                        />
                      </div>

                      {/* 相机选择 */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">关联相机</label>
                        <div className="flex flex-wrap gap-2">
                          {availableCameras.map(cam => (
                            <button
                              key={cam}
                              onClick={() => toggleEditCamera(cam)}
                              className={`px-3 py-1 rounded-full text-sm transition ${
                                editCameras.includes(cam)
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                              }`}
                            >
                              相机 {cam}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* 仪器配置 */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-sm font-medium text-gray-700">仪器配置</label>
                          <button
                            onClick={() => setEditInstruments(prev => [...prev, {
                              camera_id: editInstruments.length,
                              type: 'electronic_balance',
                              name: `仪器 ${prev.length + 1}`
                            }])}
                            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                          >
                            <Plus size={16} />
                            添加仪器
                          </button>
                        </div>

                        <div className="space-y-3">
                          {editInstruments.map((inst, idx) => (
                            <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                              <select
                                value={inst.type}
                                onChange={e => {
                                  const newInsts = [...editInstruments]
                                  newInsts[idx] = { ...inst, type: e.target.value }
                                  setEditInstruments(newInsts)
                                }}
                                className="flex-1 px-3 py-2 border rounded"
                              >
                                {instrumentTypes.map(t => (
                                  <option key={t.id} value={t.id}>{t.name}</option>
                                ))}
                              </select>
                              <input
                                type="number"
                                value={inst.camera_id}
                                onChange={e => {
                                  const newInsts = [...editInstruments]
                                  newInsts[idx] = { ...inst, camera_id: parseInt(e.target.value) || 0 }
                                  setEditInstruments(newInsts)
                                }}
                                className="w-20 px-3 py-2 border rounded"
                                min="0"
                                max="8"
                              />
                              <input
                                type="text"
                                value={inst.name}
                                onChange={e => {
                                  const newInsts = [...editInstruments]
                                  newInsts[idx] = { ...inst, name: e.target.value }
                                  setEditInstruments(newInsts)
                                }}
                                className="flex-1 px-3 py-2 border rounded"
                              />
                              <button
                                onClick={() => setEditInstruments(prev => prev.filter((_, i) => i !== idx))}
                                className="p-2 text-red-500 hover:bg-red-50 rounded"
                              >
                                <Trash2 size={18} />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  /* 查看模式 */
                  <>
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <h2 className="text-xl font-semibold">{currentExperiment.name}</h2>
                        <p className="text-gray-500 text-sm mt-1">{currentExperiment.description}</p>
                        <div className="flex gap-2 mt-2">
                          {currentExperiment.cameras?.map(cam => (
                            <span key={cam} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              相机 {cam}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => setIsEditing(true)}
                          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                        >
                          编辑
                        </button>
                        <button 
                          onClick={() => exportExperiment(currentExperiment.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                        >
                          <Download size={18} />
                          导出 CSV
                        </button>
                      </div>
                    </div>

                    {/* 读数汇总卡片 */}
                    {currentExperiment.readings && currentExperiment.readings.length > 0 && (
                      <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
                        <h3 className="font-medium text-gray-700 mb-3">📊 读数汇总</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(getCameraSummary(currentExperiment)).map(([cam, data]) => (
                            <div key={cam} className="bg-white p-3 rounded-lg shadow-sm">
                              <div className="text-lg font-bold text-blue-600">相机 {cam}</div>
                              <div className="text-2xl font-semibold">{data.count}</div>
                              <div className="text-xs text-gray-500">条读数</div>
                              {data.latest && (
                                <div className="mt-2 pt-2 border-t text-xs">
                                  <div className="text-gray-500">最新:</div>
                                  <div className="font-medium">
                                    {Object.entries(data.latest.values || {}).map(([k, v]) => `${k}: ${v}`).join(', ')}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 批量读取按钮 */}
                    {(currentExperiment.cameras?.length || 0) > 0 && (
                      <div className="mb-6">
                        <button
                          onClick={captureAllCameras}
                          disabled={capturingCamera !== null}
                          className={`flex items-center gap-2 px-6 py-3 rounded-lg ${
                            capturingCamera !== null
                              ? 'bg-gray-300 cursor-wait'
                              : 'bg-indigo-600 text-white hover:bg-indigo-700'
                          }`}
                        >
                          {capturingCamera !== null ? (
                            <>
                              <RefreshCw size={20} className="animate-spin" />
                              批量读取中...
                            </>
                          ) : (
                            <>
                              <Camera size={20} />
                              批量读取所有相机
                            </>
                          )}
                        </button>
                      </div>
                    )}

                    {/* 仪器列表 */}
                    <div className="space-y-4 mb-6">
                      <h3 className="font-medium text-gray-700">仪器读数</h3>
                      {currentExperiment.instruments?.length === 0 ? (
                        <p className="text-gray-400 text-sm py-4 text-center border-2 border-dashed rounded-lg">
                          暂无仪器配置
                        </p>
                      ) : (
                        currentExperiment.instruments?.map((inst, idx) => {
                          const camReadings = currentExperiment.readings?.filter(r => r.camera_id === inst.camera_id) || []
                          return (
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
                              {camReadings.slice(-1).map(reading => (
                                <div key={reading.id} className="mt-2 p-3 bg-white rounded border">
                                  <div className="flex justify-between text-sm text-gray-500 mb-2">
                                    <span>{new Date(reading.timestamp).toLocaleString('zh-CN')}</span>
                                    {reading.confidence && (
                                      <span>置信度: {(reading.confidence * 100).toFixed(1)}%</span>
                                    )}
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
                          )
                        })
                      )}
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
                                <th className="p-2 text-left">相机</th>
                                <th className="p-2 text-left">仪器</th>
                                <th className="p-2 text-left">读数</th>
                              </tr>
                            </thead>
                            <tbody>
                              {currentExperiment.readings.slice(-20).reverse().map(r => (
                                <tr key={r.id} className="border-t">
                                  <td className="p-2">{new Date(r.timestamp).toLocaleString('zh-CN')}</td>
                                  <td className="p-2">相机 {r.camera_id}</td>
                                  <td className="p-2">{getInstrumentTypeName(r.instrument_type)}</td>
                                  <td className="p-2">{JSON.stringify(r.values)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </>
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

                  {/* 相机选择 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">关联相机（可选）</label>
                    <div className="flex flex-wrap gap-2">
                      {availableCameras.map(cam => (
                        <button
                          key={cam}
                          onClick={() => toggleCamera(cam)}
                          className={`px-3 py-1 rounded-full text-sm transition ${
                            newCameras.includes(cam)
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {newCameras.includes(cam) ? '✓ ' : ''}相机 {cam}
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">选择实验关联的相机，用于批量操作</p>
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
