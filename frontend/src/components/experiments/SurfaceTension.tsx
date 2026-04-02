'use client'
/**
 * 表面张力和界面张力实验视图
 * 执行标准：SY/T 5370-2018（表面及界面张力测定方法，铂金环法）
 * 文件编号：WLD/CNAS-QP7080004　版次：A/3
 * 仪器：F5（表界面张力仪）
 */
import { ExperimentViewProps } from '@/types'
import { EXPERIMENT_SCHEMAS } from '@/lib/experimentTypes'
import CaptureSlot from '@/components/ExperimentDetail/CaptureSlot'
import ResultSummary from '@/components/ExperimentDetail/ResultSummary'

export default function SurfaceTension({ experiment, onRefresh }: ExperimentViewProps) {
  const schema = EXPERIMENT_SCHEMAS.surface_tension
  const p = experiment.manual_params

  const getCameraId = (fieldKey: string) => {
    const config = experiment.camera_configs.find(c => c.field_key === fieldKey)
    const def = schema.cameraFields.find(f => f.fieldKey === fieldKey)
    return config?.camera_id ?? def?.defaultCameraId ?? 5
  }

  const getReading = (fieldKey: string, slotIndex: number) =>
    experiment.readings.find(r => r.field_key === fieldKey && r.run_index === slotIndex) ?? null

  const waterField     = schema.cameraFields.find(f => f.fieldKey === 'water_surface_tension')!
  const surfaceField   = schema.cameraFields.find(f => f.fieldKey === 'fluid_surface_tension')!
  const interfaceField = schema.cameraFields.find(f => f.fieldKey === 'fluid_interface_tension')!

  return (
    <div className="space-y-5">

      {/* ── 记录头：公司信息 + 文件编号 */}
      <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
        <div className="bg-gray-50 px-5 py-3 border-b border-gray-100 text-center">
          <div className="font-bold text-gray-800 text-sm">四川省威沃敦石油科技股份有限公司</div>
          <div className="text-[11px] text-gray-500 mt-0.5">油气增产技术检测中心</div>
        </div>
        <div className="px-5 py-3 flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-gray-700">检测原始记录</div>
            <div className="text-[11px] text-gray-400 mt-0.5">
              文件编号 File：WLD/CNAS-QP7080004　版次 Edition：A/3
            </div>
          </div>
          <div className="text-[11px] text-gray-400">
            编号 NO.：<span className="font-medium text-gray-600">{p.report_number ? String(p.report_number) : '—'}</span>
          </div>
        </div>
      </div>

      {/* ── 基础信息表 */}
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm mb-3">
          <ParamRow label="检测日期"   value={p.test_date}    unit="" />
          <ParamRow label="被检样品名称" value={p.sample_name} unit="" />
          <ParamRow label="样品编号"   value={p.sample_number} unit="" />
          <ParamRow label="样品状态"   value={p.sample_state}  unit="" />
          <ParamRow label="配液编号"   value={p.formula_number} unit="" />
          <ParamRow label="检测报告编号" value={p.report_number} unit="" />
        </div>
        {p.formula_description && (
          <div className="text-sm border-t border-gray-100 pt-2">
            <span className="text-gray-400">配方说明：</span>
            <span className="font-medium text-gray-700 ml-1">{String(p.formula_description)}</span>
          </div>
        )}
      </div>

      {/* ── 性能检测区块标题 */}
      <div className="rounded-xl border border-cyan-200 bg-cyan-50/40 px-4 py-2.5 flex items-center justify-between">
        <div>
          <span className="text-xs font-bold text-cyan-800 uppercase tracking-wider">性能检测</span>
          <span className="text-sm font-semibold text-cyan-700 ml-3">表面张力和界面张力</span>
        </div>
        <span className="text-[11px] text-cyan-500">执行标准：表面及界面张力测定方法 SY/T 5370-2018</span>
      </div>

      {/* ── 环境条件 */}
      <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">环境条件</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <ParamRow label="室内温度" value={p.room_temperature} unit="℃" />
          <ParamRow label="室内湿度" value={p.room_humidity}    unit="%" />
          <ParamRow label="25℃ 破胶液密度" value={p.sample_density}   unit="g/cm³" />
          <ParamRow label="25℃ 煤油密度"   value={p.kerosene_density} unit="g/cm³" />
        </div>
      </div>

      {/* ── 操作规程 */}
      <div className="rounded-xl border border-cyan-100 bg-cyan-50/20 overflow-hidden">
        <div className="px-4 py-2.5 border-b border-cyan-100 bg-cyan-50/50">
          <span className="text-xs font-semibold text-cyan-700">操作规程</span>
          <span className="text-[11px] text-cyan-400 ml-2">SY/T 5370-2018 · 铂金环法</span>
        </div>
        <div className="px-4 py-3 text-[12px] text-gray-600 leading-relaxed space-y-3">

          {/* 样品准备 */}
          <p className="font-medium text-gray-700">一、样品准备</p>
          <p>
            配制浓度为 <strong>0.3%</strong> 的助排剂水溶液 500 mL：
            用移液管吸取 1.5 mL 助排剂置于装有 400 mL 蒸馏水的 500 mL 容量瓶中，
            用蒸馏水稀释至刻度后摇匀，备用。
          </p>

          {/* 测试操作 */}
          <p className="font-medium text-gray-700 pt-1">二、测试</p>

          {/* 1. 设备检查及调试 */}
          <p className="font-semibold text-gray-700">1、设备检查及调试</p>
          <ol className="list-none space-y-1 pl-2">
            <li>① 先检查设备的电源连接是否正常。</li>
            <li>② 在正式测试前先将主机开机 45 分钟，机器测量系统需要通电稳定。</li>
            <li>③ 检查设备的水平位置，若检测到主机水平位置出现偏差时，屏幕右上角会显示偏差图标，水平位置正常则不显示。水平调整方法：转动机器水平调节旋钮，直到红圈位于蓝色圆点中间，调整完成。</li>
            <li>④ 每天第一次使用或移动过机器，应先对机器进行砝码校准操作。</li>
          </ol>
          <div className="bg-white/70 rounded-lg px-3 py-2.5 border border-cyan-100 ml-2">
            <p className="font-semibold text-gray-600 mb-1.5">砝码校准操作步骤</p>
            <ol className="list-decimal list-inside space-y-1 text-gray-500 pl-1">
              <li>将延长钩放置到机器挂钩下，点击去皮键，显示数值显示 0.0。</li>
              <li>点击校准键，显示"CAL"字符，并提示"请挂上校正砝码"，将校准砝码挂在延长钩下。</li>
              <li>若砝码挂上后有晃动，用镊子轻轻靠在砝码旁边让其静止。等待约 5 秒，提示"正在校正中，请稍后……"。</li>
              <li>继续等待约 6 秒，显示 500.0（允许 ±0.1 偏差），并提示"校正完成，请取下砝码"。</li>
              <li>取下砝码，显示数值显示 0.0（允许 ±0.1 偏差），砝码校准完成。若取下砝码显示值超出 ±0.1 范围，请重新执行步骤 2~5。</li>
            </ol>
          </div>

          {/* 2. 样品测试 */}
          <p className="font-semibold text-gray-700 pt-1">2、样品测试</p>

          {/* ① 表面张力测试 */}
          <p className="font-medium text-cyan-700">① 表面张力测试</p>
          <ol className="list-decimal list-inside space-y-1 pl-2">
            <li>每次测试前应确保铂金环及玻璃器皿干净（非常重要）。用镊子夹取铂金环，用流水冲洗，注意与水流保持一定角度，尽量让水流洗净环面且不使外形变形。若上次实验测试样品为油性，请使用专用去油溶剂清洗铂金环。装样品的玻璃器皿同样需处理干净备用。</li>
            <li>取少量样品对玻璃器皿内壁进行预润湿，润湿后将样品倒掉，以确保所测数据的有效性。重新往器皿内倒入 7 mm 至 10 mm 高度的样品，将器皿放在托盘上待测。</li>
            <li>酒精灯烧铂金环，一般与水平面呈 45° 角进行，直到铂金丝灼烧变成红炽状态为止，灼烧时间约 20–30 秒。等待约 10 秒，让铂金环冷却至室温，将铂金环挂在延长钩下待测。</li>
            <li>上升速度和下降速度默认 10 mm/min，可设置范围 1~300 mm/min。必须在未启动测试之前才允许修改，启动测试之后不支持修改。</li>
            <li>关闭玻璃移门，点击"上升键"托盘缓慢向上提升，目视使铂金环浸入被测样品内约 2 mm 深度后，点击"上升中"键使托盘停止运行。点击"去皮键"，测试数值显示归零。</li>
            <li>环法测表面张力，上层密度默认为 0，下层密度输入被测样品密度值；测界面张力时按被测样品实际密度值设置上下层。</li>
            <li>点击"启动测试键"机器开始自动测量数据，左侧区实时显示测量曲线（蓝色线），下降键自动切换至"下降中"状态，启动测试键自动切换至"停止测试键"状态。</li>
            <li>"表/界面张力"数值实时显示，随托盘缓慢下降数值逐渐变大。当铂金环与被测液体即将分离时，显示数值为最大值，此数值即为最终结果，将被保留显示在屏幕上。</li>
            <li>随着托盘继续下降，铂金环与被测液体分离开，"停止测试键"自动切换至"启动测试键"状态，托盘自动停止下降，代表测量结束。此时命令按键区所有按键均可执行操作。</li>
            <li>若需要重复多次测试，结果显示上不需清零，重复步骤 7）~9），按照要求记录数据。最后计算平均值。</li>
          </ol>
          <p className="text-[11px] text-amber-600 bg-amber-50 rounded px-2 py-1 ml-2">
            注：当被测样品粘度超过 200 mPa·s 时，建议不能使用铂金环法测量，否则测量数据不真实。
          </p>

          {/* ② 界面张力测试 */}
          <p className="font-medium text-cyan-700 pt-1">② 界面张力测试</p>
          <ol className="list-decimal list-inside space-y-1 pl-2">
            <li>检查是否按要求清洗玻璃器皿及铂金环，并将铂金环灼烧完成，若忽略此步骤将直接影响测试数据准确性。</li>
            <li>测试玻璃器皿内倒入约 5~7 mm 高度的下层液体。将器皿放置在托盘上，点击"上升键"，目视使铂金环浸入下层液体内约 3 mm 高度后，点击"上升中"键使托盘停止运行。</li>
            <li>将上层液体沿杯壁（建议用移液管滴入）缓慢倒入测试玻璃器皿内，高度约 18 mm。（注意，此刻不能触碰到铂金环）</li>
            <li>分别设置上下层液体密度值（上层密度为测试煤油的密度，下层为测试样品的密度）后，点击"去皮键"，"表/界面张力"数据显示归零。</li>
            <li>关闭玻璃移门，点击"启动测试键"，机器开始自动测量数据，左侧区实时显示测量曲线（蓝色线），启动测试键自动切换至"停止测试键"状态。</li>
            <li>启动测试键切换至停止测试键状态后，代表机器已进入测量状态。此时命令按键区只有"去皮键"和"停止测试键"可执行操作，其余按键无反应。</li>
            <li>"表/界面张力"数值实时显示，随托盘缓慢下降数值逐渐变大。当铂金环从下层液体中缓慢穿过上下界面层、即将拉破界面液膜时，显示数值为最大值，此数值即为最终结果，将被保留显示在屏幕上。</li>
            <li>托盘继续下降，铂金环拉破界面液膜，"停止测试键"自动切换至"启动测试键"状态，托盘自动停止下降，代表测量结束。此时命令按键区所有按键均可执行操作。</li>
            <li>如需重复测试，需重复步骤 1）~8），按照要求记录数据。最后计算平均值。</li>
          </ol>

          {/* 密度提示 */}
          <div className="bg-white/70 rounded-lg px-3 py-2 border border-cyan-100 text-[11px] text-gray-500 mt-1">
            <p>25℃ 试样密度：<strong>{p.sample_density ?? '—'}</strong> g/cm³
              &nbsp;·&nbsp;
              25℃ 煤油密度：<strong>{p.kerosene_density ?? '—'}</strong> g/cm³
            </p>
          </div>
        </div>
      </div>

      {/* ── 第1节：纯水表面张力 */}
      <Section title="① 纯水表面张力测试值" subtitle="验证铂金环状态，标准值约 72.8 mN/m (20℃)" color="blue">
        <CaptureSlot
          experimentId={experiment.id}
          fieldKey="water_surface_tension"
          cameraId={getCameraId('water_surface_tension')}
          slotIndex={0}
          readingKey={waterField.readingKey}
          label="表面张力"
          unit="mN/m"
          reading={getReading('water_surface_tension', 0)}
          onComplete={onRefresh}
          cameraLabel={`F${getCameraId('water_surface_tension')} · 表界面张力仪`}
        />
      </Section>

      {/* ── 第2节：破胶液表面张力（5次） */}
      <Section
        title="② 表面张力测试值"
        subtitle={`试样密度 ${p.sample_density ?? '—'} g/cm³ · 5次实验取算术平均`}
        color="cyan"
      >
        <div className="grid grid-cols-1 gap-3">
          {Array.from({ length: surfaceField.maxReadings }, (_, i) => (
            <CaptureSlot
              key={i}
              experimentId={experiment.id}
              fieldKey="fluid_surface_tension"
              cameraId={getCameraId('fluid_surface_tension')}
              slotIndex={i}
              readingKey="tension"
              label={`实验 ${i + 1}`}
              unit="mN/m"
              reading={getReading('fluid_surface_tension', i)}
              onComplete={onRefresh}
              cameraLabel={`F${getCameraId('fluid_surface_tension')} · 表界面张力仪`}
            />
          ))}
        </div>
        <AverageRow
          readings={experiment.readings.filter(r => r.field_key === 'fluid_surface_tension')}
          unit="mN/m"
          label="算术平均值"
        />
      </Section>

      {/* ── 第3节：破胶液界面张力（2次） */}
      <Section
        title="③ 界面张力测试值"
        subtitle={`煤油密度 ${p.kerosene_density ?? '—'} g/cm³ · 2次实验取算术平均`}
        color="teal"
      >
        <div className="grid grid-cols-1 gap-3">
          {Array.from({ length: interfaceField.maxReadings }, (_, i) => (
            <CaptureSlot
              key={i}
              experimentId={experiment.id}
              fieldKey="fluid_interface_tension"
              cameraId={getCameraId('fluid_interface_tension')}
              slotIndex={i}
              readingKey="tension"
              label={`实验 ${i + 1}`}
              unit="mN/m"
              reading={getReading('fluid_interface_tension', i)}
              onComplete={onRefresh}
              cameraLabel={`F${getCameraId('fluid_interface_tension')} · 表界面张力仪`}
            />
          ))}
        </div>
        <AverageRow
          readings={experiment.readings.filter(r => r.field_key === 'fluid_interface_tension')}
          unit="mN/m"
          label="算术平均值"
        />
      </Section>

      <ResultSummary
        type="surface_tension"
        readings={experiment.readings}
        manualParams={p}
      />

      {/* ── 签署区 */}
      <div className="rounded-xl border border-gray-100 bg-gray-50/60 p-4 space-y-3">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">签署信息</h3>
        {p.remarks && (
          <div className="text-sm">
            <span className="text-gray-400">备注：</span>
            <span className="text-gray-700 ml-1">{String(p.remarks)}</span>
          </div>
        )}
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <ParamRow label="检测人"   value={p.operator_name} unit="" />
          <ParamRow label="检测时间" value={p.operator_time} unit="" />
          <ParamRow label="审核人"   value={p.reviewer_name} unit="" />
          <ParamRow label="审核日期" value={p.reviewer_date} unit="" />
        </div>
      </div>

    </div>
  )
}

function Section({ title, subtitle, color, children }: {
  title: string; subtitle?: string; color: 'blue' | 'cyan' | 'teal'; children: React.ReactNode
}) {
  const styles = {
    blue: 'border-blue-100 from-blue-50/80 to-blue-50/40 text-blue-700',
    cyan: 'border-cyan-100 from-cyan-50/80 to-cyan-50/40 text-cyan-700',
    teal: 'border-teal-100 from-teal-50/80 to-teal-50/40 text-teal-700',
  }
  return (
    <div className="border border-gray-100 rounded-2xl overflow-hidden">
      <div className={`px-5 py-3 border-b bg-gradient-to-r ${styles[color]}`}>
        <div className="font-semibold text-sm">{title}</div>
        {subtitle && <div className="text-[11px] mt-0.5 opacity-70">{subtitle}</div>}
      </div>
      <div className="p-4 space-y-3">{children}</div>
    </div>
  )
}

function AverageRow({ readings, unit, label }: { readings: { value: number }[]; unit: string; label: string }) {
  if (readings.length === 0) return null
  const avg = readings.reduce((s, r) => s + r.value, 0) / readings.length
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-50/80 rounded-xl border border-gray-100 mt-1">
      <span className="text-xs font-medium text-gray-500">{label}</span>
      <span className="font-bold text-gray-800 tabular-nums">
        {avg.toFixed(4)}<span className="text-xs font-normal text-gray-400 ml-1">{unit}</span>
      </span>
    </div>
  )
}

function ParamRow({ label, value, unit }: { label: string; value: unknown; unit: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium text-gray-700 tabular-nums">
        {value != null && value !== '' ? String(value) : '—'}
        {unit && value != null && value !== '' && <span className="text-gray-300 text-xs ml-1">{unit}</span>}
      </span>
    </div>
  )
}
