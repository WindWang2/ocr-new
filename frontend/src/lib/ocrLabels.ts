/** OCR 英文键 → 中文标签映射 */
export const OCR_KEY_LABELS: Record<string, string> = {
  // D0 混调器
  seg1_speed:      '段一转速',
  seg1_time:       '段一时间',
  seg2_speed:      '段二转速',
  seg2_time:       '段二时间',
  seg3_speed:      '段三转速',
  seg3_time:       '段三时间',
  total_time:      '总时长',
  remaining_time:  '剩余时长',
  current_segment: '当前段数',
  current_speed:   '当前转速',
  high_speed:      '高速转速',
  high_time:       '高速时间',
  low_speed:       '低速转速',
  low_time:        '低速时间',
  // D1/D2 天平
  weight:          '重量',
  // D3 pH计
  ph_value:        'pH值',
  pts:             'PTS值',
  // D4 水质检测仪
  blank_value:     '空白值',
  test_value:      '检测值',
  absorbance:      '吸光度',
  content_mg_l:    '含量(mg/L)',
  transmittance:   '透光度',
  // D5 表界面张力仪
  tension:         '张力',
  interfacial_tension: '界面张力',
  contact_angle:   '接触角',
  upper_density:   '上层密度',
  lower_density:   '下层密度',
  rise_speed:      '上升速度',
  fall_speed:      '下降速度',
  // D6 搅拌器
  rotation_speed:  '转速',
  torque:          '扭矩',
  // D7 水浴锅
  temperature:     '温度',
  time:            '时间',
  // D8 6速粘度计
  actual_reading:  '实际读数',
  max_reading:     '最大读数',
  min_reading:     '最小读数',
  shear_rate:      '剪切速率',
  shear_stress:    '剪切应力',
  apparent_viscosity: '表观粘度',
  avg_5s:          '5秒均值',
}

export function ocrLabel(key: string): string {
  return OCR_KEY_LABELS[key] ?? key
}
