'use client'

import { useState, useEffect } from 'react'
import { Camera as CameraIcon, Cpu, CheckCircle2, AlertCircle, RefreshCw, Save } from 'lucide-react'
import { 
  matchInstruments, 
  getCoreInstrumentTemplates, 
  getInstrumentMapping, 
  updateInstrumentMapping, 
  listEnabledCameras 
} from '@/lib/api'
import { InstrumentTemplate, Camera } from '@/types'

interface InstrumentMatchingProps {
  mockEnabled?: boolean
}

export default function InstrumentMatching({ mockEnabled }: InstrumentMatchingProps) {
  const [loading, setLoading] = useState(true)
  const [matching, setMatching] = useState(false)
  const [saving, setSaving] = useState(false)
  const [templates, setTemplates] = useState<InstrumentTemplate[]>([])
  const [mapping, setMapping] = useState<Record<string, number>>({})
  const [cameras, setCameras] = useState<Camera[]>([])
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // 初始化加载
  useEffect(() => {
    const init = async () => {
      setLoading(true)
      try {
        const [temps, maps, cams] = await Promise.all([
          getCoreInstrumentTemplates(),
          getInstrumentMapping(),
          listEnabledCameras()
        ])
        setTemplates(temps)
        setMapping(maps)
        setCameras(cams)
      } catch (e) {
        setError('加载配置失败: ' + (e as Error).message)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  // 自动重置成功提示
  useEffect(() => {
    if (successMsg) {
      const timer = setTimeout(() => setSuccessMsg(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [successMsg])

  const handleStartMatch = async () => {
    setMatching(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const data = await matchInstruments()
      if (data.success) {
        setMapping(data.mapping)
        setSuccessMsg('自动匹配完成并已保存')
      } else {
        setError(data.detail || '识别过程未发现有效仪器')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setMatching(false)
    }
  }

  const handleSaveMapping = async () => {
    setSaving(true)
    setError(null)
    setSuccessMsg(null)
    try {
      await updateInstrumentMapping(mapping)
      setSuccessMsg('映射配置已手动保存')
    } catch (e) {
      setError('保存失败: ' + (e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const onCameraChange = (instrumentType: string, cameraId: string) => {
    const instId = instrumentType.replace('F', '')
    const newMapping = { ...mapping }
    if (cameraId === 'none') {
      delete newMapping[instId]
    } else {
      newMapping[instId] = parseInt(cameraId)
    }
    setMapping(newMapping)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <RefreshCw size={20} className="text-gray-300 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="text-sm font-semibold text-gray-800">仪器对位</div>
            {mockEnabled && (
              <span className="px-1.5 py-0.5 bg-amber-50 text-amber-600 text-[10px] font-bold rounded border border-amber-100">
                模拟模式
              </span>
            )}
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">
            配置仪器与相机的物理对应关系，支持自动扫描与手动修改
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <button
          onClick={handleStartMatch}
          disabled={matching || saving}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-brand-50 text-brand-600 hover:bg-brand-100 disabled:opacity-50 transition rounded-lg text-xs font-semibold"
        >
          {matching ? <RefreshCw size={14} className="animate-spin" /> : <CameraIcon size={14} />}
          {matching ? '正在对位...' : '一键自动匹配'}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 p-2.5 bg-red-50 text-red-600 rounded-lg border border-red-100">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <div className="text-[11px] leading-relaxed">{error}</div>
        </div>
      )}

      {successMsg && (
        <div className="flex items-center gap-2 p-2.5 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-100 animate-in fade-in slide-in-from-top-1">
          <CheckCircle2 size={14} className="shrink-0" />
          <div className="text-[11px] font-medium">{successMsg}</div>
        </div>
      )}

      {/* 仪器列表 */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm">
        <div className="bg-gray-50/50 px-3 py-2 border-b border-gray-100 flex justify-between items-center">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">仪器信息</span>
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">绑定相机</span>
        </div>
        <div className="divide-y divide-gray-50 max-h-[400px] overflow-y-auto custom-scrollbar">
          {templates.map((temp) => {
            const instIdStr = temp.instrument_type.replace('F', '')
            const currentCamId = mapping[instIdStr]
            
            return (
              <div key={temp.instrument_type} className="flex items-center justify-between p-3 hover:bg-gray-50/30 transition">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-[11px] shadow-sm border ${
                    currentCamId !== undefined 
                      ? 'bg-brand-500 text-white border-brand-600' 
                      : 'bg-gray-100 text-gray-400 border-gray-200'
                  }`}>
                    {temp.instrument_type}
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-gray-700">{temp.name}</div>
                    <div className="text-[9px] text-gray-400 max-w-[140px] truncate">{temp.description || '暂无描述'}</div>
                  </div>
                </div>

                <select
                  value={currentCamId === undefined ? 'none' : currentCamId}
                  onChange={(e) => onCameraChange(temp.instrument_type, e.target.value)}
                  disabled={matching || saving}
                  className="text-[11px] font-medium bg-white border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-500 min-w-[80px]"
                >
                  <option value="none">未绑定</option>
                  {cameras.map(cam => (
                    <option key={cam.camera_id} value={cam.camera_id}>
                      相机 {cam.camera_id}
                    </option>
                  ))}
                </select>
              </div>
            )
          })}
        </div>
        
        {/* 底部保存 */}
        <div className="p-3 bg-gray-50/50 border-t border-gray-100">
          <button
            onClick={handleSaveMapping}
            disabled={matching || saving}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-white text-gray-700 hover:text-brand-600 hover:border-brand-200 border border-gray-200 shadow-sm transition rounded-lg text-xs font-semibold"
          >
            {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
            {saving ? '正在保存...' : '保存手动修改'}
          </button>
        </div>
      </div>
    </div>
  )
}
