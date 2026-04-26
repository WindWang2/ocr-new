import { Reading, ManualParams } from '@/types'

export interface KinematicResult {
  avgTime: number | null      // τ
  viscosity: number | null    // ν = C × τ
}

export interface ApparentResult {
  run1: number | null         // η₁
  run2: number | null         // η₂
  average: number | null
}

export interface SurfaceResult {
  surfaceAvg: number | null   // 表面张力均值
  interfaceAvg: number | null // 界面张力均值
}

export function calcKinematic(readings: Reading[], params: ManualParams): KinematicResult {
  const times = readings.filter(r => r.field_key === 'flow_time').map(r => r.value)
  if (times.length === 0) return { avgTime: null, viscosity: null }
  const avgTime = times.reduce((a, b) => a + b, 0) / times.length
  const C = Number(params.capillary_coeff) || 0
  return {
    avgTime: round4(avgTime),
    viscosity: C > 0 ? round4(C * avgTime) : null,
  }
}

export function calcApparent(readings: Reading[]): ApparentResult {
  const eta = (runIndex: number): number | null => {
    const r = readings.find(r => r.field_key === 'reading_100rpm' && r.run_index === runIndex)
    if (!r) return null
    return round4((r.value * 5.077) / 1.704)
  }
  const r1 = eta(1)
  const r2 = eta(2)
  const average = r1 !== null && r2 !== null ? round4((r1 + r2) / 2) : null
  return { run1: r1, run2: r2, average }
}

export function calcSurface(readings: Reading[]): SurfaceResult {
  const fst = readings.filter(r => r.field_key === 'fluid_surface_tension').map(r => r.value)
  const fit = readings.filter(r => r.field_key === 'fluid_interface_tension').map(r => r.value)
  return {
    surfaceAvg: fst.length > 0 ? round4(fst.reduce((a, b) => a + b, 0) / fst.length) : null,
    interfaceAvg: fit.length > 0 ? round4(fit.reduce((a, b) => a + b, 0) / fit.length) : null,
  }
}

function round4(n: number): number {
  return Math.round(n * 10000) / 10000
}
