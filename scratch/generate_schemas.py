import json
import os

def main():
    with open('scratch/template_doc_content.json', 'r', encoding='utf-8') as f:
        docs = json.load(f)

    # Simplified extraction of steps for the TS file to avoid massive strings breaking syntax
    # In a real scenario we'd use regex or an LLM, here we just safely escape the text.
    
    schemas_ts = """import { ExperimentType } from '@/types'

export interface ManualParamDef {
  key: string
  label: string
  unit: string
  type: 'number' | 'text'
  placeholder?: string
}

export interface InstrumentFieldDef {
  fieldKey: string
  label: string
  unit: string
  maxReadings: number
  targetInstrumentId: number
  readingKey: string
  description?: string
}

export interface ExperimentSchema {
  type: ExperimentType
  label: string
  description: string
  icon: string
  standard?: string
  manualParams: ManualParamDef[]
  instrumentFields: InstrumentFieldDef[]
  operationSteps?: string
}

export const EXPERIMENT_SCHEMAS: Record<ExperimentType, ExperimentSchema> = {
"""
    
    # 1. surface_tension
    text_st = docs.get('1_yzj_表面张力和界面张力测试.docx', '').replace('`', "'").replace('$', '')
    schemas_ts += """
  surface_tension: {
    type: 'surface_tension',
    label: '表面张力和界面张力测试',
    description: '使用表界面张力仪测定液体的表面张力和界面张力。',
    icon: '💧',
    standard: 'SY/T 5370-2018',
    manualParams: [
      { key: 'test_date', label: '检测日期', unit: '', type: 'text' },
      { key: 'sample_name', label: '被检样品名称', unit: '', type: 'text' },
      { key: 'sample_number', label: '样品编号', unit: '', type: 'text' },
      { key: 'sample_status', label: '样品状态', unit: '', type: 'text' },
      { key: 'room_temp', label: '室内温度', unit: '℃', type: 'number' },
      { key: 'room_humidity', label: '室内湿度', unit: '%', type: 'number' },
    ],
    instrumentFields: [
      { fieldKey: 'surface_tension_val', label: '表面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'interface_tension_val', label: '界面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' }
    ],
    operationSteps: `""" + text_st + """`
  },
"""

    # 2. kinematic_viscosity
    text_kv = docs.get('1_yzj_运动粘度.docx', '').replace('`', "'").replace('$', '')
    schemas_ts += """
  kinematic_viscosity: {
    type: 'kinematic_viscosity',
    label: '运动粘度',
    description: '平氏毛细管粘度计法，测量液体流经时间，计算运动粘度。',
    icon: '🧪',
    standard: 'SY/T 5107-2016',
    manualParams: [
      { key: 'test_date', label: '检测日期', unit: '', type: 'text' },
      { key: 'sample_name', label: '被检样品名称', unit: '', type: 'text' },
      { key: 'sample_number', label: '样品编号', unit: '', type: 'text' },
      { key: 'report_number', label: '报告编号', unit: '', type: 'text' },
      { key: 'room_temp', label: '室内温度', unit: '℃', type: 'number' },
      { key: 'room_humidity', label: '室内湿度', unit: '%', type: 'number' },
    ],
    instrumentFields: [
      { fieldKey: 'flow_time', label: '流经时间', unit: 's', maxReadings: 3, targetInstrumentId: -1, readingKey: '时间' }
    ],
    operationSteps: `""" + text_kv + """`
  },
"""

    # 3. apparent_viscosity
    text_av = docs.get('表观粘度.docx', '').replace('`', "'").replace('$', '')
    schemas_ts += """
  apparent_viscosity: {
    type: 'apparent_viscosity',
    label: '表观粘度',
    description: '使用旋转粘度计测量液体表观粘度。',
    icon: '🔄',
    standard: 'SY/T 5107-2016',
    manualParams: [
      { key: 'test_date', label: '检测日期', unit: '', type: 'text' },
      { key: 'sample_name', label: '被检样品名称', unit: '', type: 'text' },
      { key: 'sample_number', label: '样品编号', unit: '', type: 'text' },
      { key: 'report_number', label: '报告编号', unit: '', type: 'text' },
      { key: 'room_temp', label: '室内温度', unit: '℃', type: 'number' },
      { key: 'room_humidity', label: '室内湿度', unit: '%', type: 'number' },
    ],
    instrumentFields: [
      { fieldKey: 'reading_3rpm', label: '3r/min 读数', unit: '', maxReadings: 3, targetInstrumentId: 8, readingKey: 'actual_reading' },
      { fieldKey: 'reading_6rpm', label: '6r/min 读数', unit: '', maxReadings: 3, targetInstrumentId: 8, readingKey: 'actual_reading' },
      { fieldKey: 'reading_100rpm', label: '100r/min 读数', unit: '', maxReadings: 3, targetInstrumentId: 8, readingKey: 'actual_reading' }
    ],
    operationSteps: `""" + text_av + """`
  },
"""

    # 4. water_mineralization
    text_wm = docs.get('水质矿化度.docx', '').replace('`', "'").replace('$', '')
    schemas_ts += """
  water_mineralization: {
    type: 'water_mineralization',
    label: '水质矿化度',
    description: '使用 TDS 笔测试水质矿化度 (ppm)。',
    icon: '🌊',
    standard: 'N/A',
    manualParams: [
      { key: 'test_date', label: '检测日期', unit: '', type: 'text' },
      { key: 'sample_name', label: '被检样品名称', unit: '', type: 'text' },
      { key: 'sample_number', label: '样品编号', unit: '', type: 'text' },
      { key: 'room_temp', label: '室内温度', unit: '℃', type: 'number' },
      { key: 'room_humidity', label: '室内湿度', unit: '%', type: 'number' },
    ],
    instrumentFields: [
      { fieldKey: 'tds_value', label: 'TDS 矿化度', unit: 'ppm', maxReadings: 3, targetInstrumentId: 4, readingKey: 'test_value' }
    ],
    operationSteps: `""" + text_wm + """`
  },
"""

    # 5. ph_value
    text_ph = docs.get('pH值.docx', '').replace('`', "'").replace('$', '')
    schemas_ts += """
  ph_value: {
    type: 'ph_value',
    label: 'pH值',
    description: '使用 pH 计测定样品的酸碱度。',
    icon: '⚗️',
    standard: 'SY/T 5107-2016',
    manualParams: [
      { key: 'test_date', label: '检测日期', unit: '', type: 'text' },
      { key: 'sample_name', label: '被检样品名称', unit: '', type: 'text' },
      { key: 'sample_number', label: '样品编号', unit: '', type: 'text' },
      { key: 'room_temp', label: '室内温度', unit: '℃', type: 'number' },
      { key: 'room_humidity', label: '室内湿度', unit: '%', type: 'number' },
    ],
    instrumentFields: [
      { fieldKey: 'ph_val', label: 'pH值', unit: '', maxReadings: 3, targetInstrumentId: 3, readingKey: 'ph_value' },
      { fieldKey: 'temperature', label: '溶液温度', unit: '℃', maxReadings: 1, targetInstrumentId: 3, readingKey: 'temperature' }
    ],
    operationSteps: `""" + text_ph + """`
  }
}
"""

    with open('frontend/src/lib/experimentTypes.ts', 'w', encoding='utf-8') as f:
        f.write(schemas_ts)
        
    print("TypeScript definitions written to frontend/src/lib/experimentTypes.ts")

if __name__ == "__main__":
    main()
