import { ExperimentType } from '@/types'

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
  flowchartSvg?: string
}

export const EXPERIMENT_SCHEMAS: Record<ExperimentType, ExperimentSchema> = {
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
      { fieldKey: 'water_surface_tension', label: '纯水表面张力测试', unit: 'mN/m', maxReadings: 2, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'fluid_surface_tension', label: '表面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'fluid_interface_tension', label: '界面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' }
    ],
    operationSteps: `一、样品准备：使用现场配置的样
二、测试： 
1、设备检查及调试 
1) 先检查设备的电源连接是否正常； 
2) 在正式测试前先将主机开机45分钟，机器测量系统需要通电稳定； 
3) 检查设备的水平位置，若检测到主机水平位置出现偏差时，屏幕右上角会显示警告图标，反之水平位置正常则不显示；（水平调整方法：转动机器水平调节旋钮，直到红圈位于蓝色圆点中间，调整完成） 
4) 每天第一次使用或移动过机器，应先对机器进行砝码校准操作； 

砝码校准操作步骤：
1) 将延长钩放置到机器挂钩下，点击去皮键，显示数值显示0.0。 
2) 点击校准键，显示数值显示“CAL”字符，并提示“请挂上校正砝码”，按提示操作，将校准砝码放置挂在延长钩下。 
3) 若砝码挂上后有晃动，请用镊子轻轻靠在砝码旁边，让其静止不晃动。等待约5秒，提示“正在校正中，请稍后......”。 
4) 按提示继续等待约6秒，显示数字显示500.0（允许±0.1偏差），并提示“校正完成，请取下砝码”。 
5) 按提示操作取下砝码，显示数值显示0.0（允许±0.1偏差），砝码校准完成。若取下砝码，显示数值超出0.1至-0.1范围，请重新执行2）至5）点操作。 

2、样品测试 
①表面张力测试 
1) 每次测试前应确保铂金环及玻璃器皿的干净（非常重要）。 用镊子夹取铂金环，并用流水冲洗，冲洗时应注意与水流保持一定的角度，原则为尽量做到让水流洗干净环的表面且不能让水流冲压使得外形发生变形。若上次实验时测试样品为油性，请使用专门去油性溶剂清洗铂金环，这种方法更能保证清洗效果最佳。装样品的玻璃器皿也需遵从铂金环清洗方式，处理干净待用。 
2) 取少量样品对玻璃器皿内壁进行预润湿，润湿后将样品倒掉，以确保所测数据的有效性。重新往器皿内倒入7mm至10mm高度的样品，将器皿放在托盘上待测。 
3) 酒精灯烧铂金环，一般为与水平面呈45度角进行，直到铂金环的铂金丝灼烧变成红炽状态为止，灼烧时间约为20－30秒。等待约10秒，让铂金环冷却至室温，将铂金环放置挂在延长钩下待测。 
4) 上升速度和下降速度默认10mm/min，点击数字可根据需要进行设置速度，可设置范围1至300mm/min。设置速度，必须在未启动测试之前才允许修改，启动测试之后不支持修改。 
5) 关闭玻璃移门，点击“上升键”托盘缓慢向上提升，目视使铂金环浸入到被测样品内约2mm深度后，点击“上升中”键托盘停止运行。点击“去皮键”，测试数值显示归零。 
6) 环法测试表面张力，上层密度默认为0，下层密度，输入被测样品密度值。测试界面张力上下层密度，按被测样品实际密度值设置。 
7) 点击“启动测试键”机器开始自动测量数据，左侧区实时显示测量曲线，用蓝色线表示，下降键自动切换至下降中状态，启动测试键自动切换至停止测试键状态。 
8) “表/界面张力”数据此时实时显示，随着托盘缓慢下降，显示数值逐渐变大。当铂金环与被测液体即将分离时，显示数值为最大值，此数值即为最终结果，将被保留显示在屏幕上。 
9) 随着托盘继续下降，铂金环与被测液体分离开，停止测试键自动切换至启动测试键状态，托盘自动停止下降，代表测量结束。此时命令按键区，所有按键均可执行操作。 
10) 若需要重复多次测试数据，结果显示上不需清零，重复步骤7）~9），按照要求记录数据。最后计算平均值。 
【注意事项】当被测样品粘度超过200mPa.s时，建议不能使用铂金环法测量，否则测量数据不真实。 

②界面张力测试 
1) 检查是否按要求，清洗玻璃器皿及铂金环，并将铂金环灼烧完成过，若忽略此步骤将直接影响测试数据准确性。 
2) 测试玻璃器皿内倒入约5至7mm高度的下层液体。将器皿放置在托盘上点击“上升键”，目视使铂金环浸入下层液体内约3mm高度后,点击“上升中”键托盘停止运行。 
3) 将上层液体延杯壁（建议用移液管滴入）缓慢倒入测试玻璃器皿内，高度约18mm。（注意，此刻不能触碰到铂金环） 
4) 分别设置上下层液体密度值（上层密度为测试煤油的密度，下层为测试样品的密度）后，点击“去皮键”，“表/界面张力”数据显示归零。 
5) 关闭玻璃移门，点击“启动测试键”，机器开始自动测量数据，左侧区实时显示测量曲线，用蓝色线条表示，下降键自动切换至下降中状态，启动测试键自动切换至停止测试键状态。 
6) 启动测试键切换至停止测试键状态后，代表机器已经进入到测量状态。此时命令按键区，只有去皮键和停止测试键可以执行操作，其余按键点击无反应。 
7) “表/界面张力”数据此时实时显示，随着托盘缓慢下降，显示数值逐渐变大。当铂金环从下层液体中缓慢穿过上下界面层时，即将拉破界面液膜时，显示数值为最大值，此数值即为最终结果，将被保留显示在屏幕上。 
8) 盘托继续下降，铂金环拉破界面液膜，停止测试键自动切换至启动测试键状态，托盘自动停止下降，代表测量结束。此时命令按键区，所有按键均可执行操作。 
9) 如需重复测试，需重复步骤1）~8），按照要求记录数据。最后计算平均值。`,
    flowchartSvg: `<svg viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6"/>
    </marker>
  </defs>
  <g fill="none" stroke="#3b82f6" stroke-width="2">
    <rect x="10" y="35" width="120" height="50" rx="8" fill="#eff6ff"/>
    <text x="70" y="60" fill="#1e3a8a" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">设备/砝码校准</text>
    <line x1="130" y1="60" x2="160" y2="60" marker-end="url(#arrow)"/>
    
    <rect x="170" y="35" width="120" height="50" rx="8" fill="#eff6ff"/>
    <text x="230" y="60" fill="#1e3a8a" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">灼烧铂金环</text>
    <line x1="290" y1="60" x2="320" y2="60" marker-end="url(#arrow)"/>
    
    <rect x="330" y="35" width="120" height="50" rx="8" fill="#eff6ff"/>
    <text x="390" y="60" fill="#1e3a8a" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">润洗与注样</text>
    <line x1="450" y1="60" x2="480" y2="60" marker-end="url(#arrow)"/>
    
    <rect x="490" y="35" width="120" height="50" rx="8" fill="#eff6ff"/>
    <text x="550" y="60" fill="#1e3a8a" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">浸没并去皮</text>
    <line x1="610" y1="60" x2="640" y2="60" marker-end="url(#arrow)"/>
    
    <rect x="650" y="35" width="130" height="50" rx="8" fill="#dbeafe"/>
    <text x="715" y="60" fill="#1d4ed8" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">自动拉脱读数</text>
  </g>
</svg>`
  },

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
      { fieldKey: 'flow_time', label: '流经时间', unit: 's', maxReadings: 3, targetInstrumentId: 8, readingKey: '时间' }
    ],
    operationSteps: `一、样品准备：现场样品或根据配方要求配置
二、测试： 
1、准备 
1) 选取适当内径的平氏毛细管粘度计，使得流动时间在200s以上，最细内径的流动时间不得小于350s。 
2) 粘度计常数确认：使用前核对出厂标定常数K，若常数K值标识被丢失，该粘度计则不能使用。 
3) 平氏毛细管粘度计测试前处理：在测定试样粘度前，必须将粘度计用溶剂油或石油醚洗涤，如果粘度计沾有污垢，用铬酸洗液、水、蒸馏水或95%乙醇依次洗涤。然后放入烘箱中烘干或用通过棉花过滤过的热空气吹干。 
4) 检查毛细管内壁无挂液、无气泡、无杂质，透光均匀。 

2、操作 
1) 对平式毛细管粘度计进行润洗：用待测液清洗三遍。 
2) 将清洗后整个平式毛细管粘度计倒过来，C处在液面以下。 
3) 用手堵住图A处，在B处用洗耳球将基液吸到D处后，立即停止并倒立过来。 
4) 消泡：用手堵住图B处，用洗耳球吹液至测定球D处。（【注意事项】气泡绝对禁止：气泡会堵塞毛细管、改变流速，装样、吸液全程防气泡） 
5) 用乳胶管连接细管端（毛细管出口），用洗耳球缓慢吸液，将液体吸至测定球上刻度线C处以上 5~10mm处，立即捏紧乳胶管，停止吸液、防止回流。 
6) 松开洗耳球，让液体在重力作用下自然下落，全程保持粘度计垂直不动，严禁触碰、倾斜。基液自然流下，眼睛平视刻度线，测量基液弯月面最低点通过计时球C处时，使用秒表开始计时； 
7) 当基液流经D处时，停止计时，记录秒表时间t； 
8) 平行测定3次，重复吸液、计时操作（重复步骤5-7），测定 3 次，记录秒表时间。 
9) 误差判定：3次流出时间的极差≤平均值的0.2%；若超差，需重新装样、清洁后再测。 
10) 根据运动粘度计算公式进行计算：ν = C * t。 

3、处理 
1) 立即倒出剩余样品，用溶剂油或石油醚反复冲洗粘度计，再用无水乙醇冲净，放入烘箱中烘干或用通过棉花过滤过的热空气吹干。 
2) 粘度计垂直悬挂在专用架上，避免磕碰、弯曲毛细管。 
3) 清理台面，记录测定数据。`,
    flowchartSvg: `<svg viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981"/></marker></defs>
  <g fill="none" stroke="#10b981" stroke-width="2">
    <rect x="10" y="35" width="120" height="50" rx="8" fill="#ecfdf5"/>
    <text x="70" y="60" fill="#064e3b" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">清洗与选管</text>
    <line x1="130" y1="60" x2="160" y2="60" marker-end="url(#arr2)"/>
    
    <rect x="170" y="35" width="120" height="50" rx="8" fill="#ecfdf5"/>
    <text x="230" y="60" fill="#064e3b" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">无气泡装液</text>
    <line x1="290" y1="60" x2="320" y2="60" marker-end="url(#arr2)"/>
    
    <rect x="330" y="35" width="120" height="50" rx="8" fill="#ecfdf5"/>
    <text x="390" y="60" fill="#064e3b" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">恒温水浴10min</text>
    <line x1="450" y1="60" x2="480" y2="60" marker-end="url(#arr2)"/>
    
    <rect x="490" y="35" width="120" height="50" rx="8" fill="#ecfdf5"/>
    <text x="550" y="60" fill="#064e3b" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">吸液至C刻度上</text>
    <line x1="610" y1="60" x2="640" y2="60" marker-end="url(#arr2)"/>
    
    <rect x="650" y="35" width="130" height="50" rx="8" fill="#d1fae5"/>
    <text x="715" y="60" fill="#047857" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">C至D自然流下计时</text>
  </g>
</svg>`
  },

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
    operationSteps: `一、样品准备：使用现场配置的样
二、测试： 
1) 接通电源，打开开关，检查旋转粘度计是否正常工作，触摸屏是否正常显示。 
2) 检查浮子的干净度，安装浮子，在向上推动浮子的同时逆时针旋转。 
3) 检查外套筒的干净度，安装外套筒，顺时针转动外套筒，使其向上旋转到最高位置。 
4) 向浆杯中注入待测液约350mL（浆杯内置刻度线处），将浆杯放置在托盘上，托盘底座有三个与浆杯对应的孔隙须对齐，然后将托盘上提，带浆杯内液体与外转筒液位线对齐后拧紧星型把手进行固定。 
5) 按显示屏中的清零键，将当前粘度值清零。 
6) 用旋转粘度计测量黏度，要求从最低剪切速率到最高剪切速率逐一变化，转速分别测试3r/min、6r/min、100r/min下的剪切速率，记录在每个剪切速率稳定后20s的读数。 
7) 测量结束后，取出浆杯；卸下外转筒，逆时针转动外套筒，外套筒慢慢的被拆除；拆除浮子时，向下拉动浮子的同时逆时针旋转，取下浮子，进行清洗、擦干。 

三、校准 
采用流体校准 
校准液体可以是20,50,100,200和500cP。所有符合ASTM标准的每一瓶液体都配有一个粘度温度对照表。（根据测试粘度情况对标准液进行购买） 
1) 在把外套筒和浮子浸入标准液之前要保证被检测的仪器是干净的。如果有必要的话，拆除外套筒，彻底清洗浮子。确保浮子轴和外套筒是完好无损的。（注意标准液标签上的批号必须与粘度/温度图上的数字匹配。） 
2) 将校准液加至浆杯的液位线处，把浆杯放在仪器的托盘上。向上提升托盘，直到浸到外转筒液位线处。 
3) 将温度计放入被测样品中，选择一个安全位置防止破碎。 
4) 开机设定300转运行3分钟，平衡浮子、外套筒、样品与环境的温度。 
5) 记录300转、600转时刻度盘上的读数，温度计的读数精确到0.1°C 。 
6) 与标准液的数值进行比对。`,
    flowchartSvg: `<svg viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="arr3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6"/></marker></defs>
  <g fill="none" stroke="#8b5cf6" stroke-width="2">
    <rect x="10" y="35" width="120" height="50" rx="8" fill="#f5f3ff"/>
    <text x="70" y="60" fill="#4c1d95" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">安装浮子/套筒</text>
    <line x1="130" y1="60" x2="160" y2="60" marker-end="url(#arr3)"/>
    
    <rect x="170" y="35" width="120" height="50" rx="8" fill="#f5f3ff"/>
    <text x="230" y="60" fill="#4c1d95" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">注液对齐刻度</text>
    <line x1="290" y1="60" x2="320" y2="60" marker-end="url(#arr3)"/>
    
    <rect x="330" y="35" width="120" height="50" rx="8" fill="#f5f3ff"/>
    <text x="390" y="60" fill="#4c1d95" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">仪表触屏清零</text>
    <line x1="450" y1="60" x2="480" y2="60" marker-end="url(#arr3)"/>
    
    <rect x="490" y="35" width="120" height="50" rx="8" fill="#f5f3ff"/>
    <text x="550" y="60" fill="#4c1d95" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">逐级设定转速</text>
    <line x1="610" y1="60" x2="640" y2="60" marker-end="url(#arr3)"/>
    
    <rect x="650" y="35" width="130" height="50" rx="8" fill="#ede9fe"/>
    <text x="715" y="60" fill="#5b21b6" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">稳定20s后读数</text>
  </g>
</svg>`
  },

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
    operationSteps: `一、样品准备：现场水样
二、测试： 
1、校准 
1) 取下前端检测笔帽，笔帽装2/3 容量纯净水。 
2) 按笔身开关键开机，将检测探头（金属针 + 温度传感器）完全浸入水中，轻轻晃动赶走气泡。 
3) 等待数值稳定（约 3~5 秒），若显示≠0ppm：长按开关键 5~8 秒，进入校准模式，自动归零，完成校准。 
4) 校准后用纯水冲洗探头，擦干备用。

2、操作 
步骤 1：装水 / 取水 
- 方法 A（笔帽装水）：笔帽装待测水至2/3，避免溢出。 
- 方法 B（直接浸入）：直接将探头伸入水杯内，探头完全浸没、不碰杯底 / 杯壁。 

步骤 2：开机检测 
1) 按开关键开机，屏幕显示 TDS 值（ppm）+ 温度（℃，自动温补）。 
2) 探头浸入水中，轻轻晃动 1~2 秒排气泡，静置等待数值稳定（约 3~5 秒）。 
3) 稳定后读取数值：TDS 值 = 水中总溶解固体（矿化度），单位 ppm（mg/L）。 
4) 若测试的矿化度大于9990的量程后，显示“Err”/“OL”，即为超量程。需要进行稀释测试。 

5) 水样稀释步骤 
- 步骤 ①：准备稀释用水。必须使用 TDS＜10 ppm 的纯净水 / RO 纯水（【注意事项】绝对不能用自来水，会引入杂质导致误差）。 
- 步骤 ②：进行定量稀释（推荐 10 倍稀释）。（1）取 1 份（如 10mL）待测水样倒入干净容器。（2）加入 9 份（如 90mL）RO 纯水，充分混匀。此时总稀释倍数为 10 倍（1:9）。若稀释 10 倍后仍超量程，可继续稀释至 100 倍（1mL 水样 + 99mL 纯水），逐级稀释。 
- 步骤 ③：检测稀释后的水样。（1）将混合均匀的稀释液，按正常步骤用 TDS 笔检测。（2）读取稳定后的 TDS 值（记为 t）。 
- 步骤 ④：反算原水实际 TDS。10 倍稀释：原水 TDS = t×10；100 倍稀释：原水 TDS = t×100。

步骤 3：读数与记录 
- 自来水：一般 100~400ppm 
- RO 纯水：0~50ppm 
- 矿泉水：100~300ppm 
数值稳定后，记录数据。 

步骤 4：关机与清洁 
1) 检测完，按开关键关机（无操作约 1 分钟自动关机）。
2) 用纯净水 / 自来水冲洗探头，用干净软布 / 纸巾擦干，盖上笔帽，避免残留水渍、杂质腐蚀探针。 

3、异常处理 
1) 数值乱跳 / 不稳：探头有水渍 / 杂质→冲洗擦干；气泡未排→晃动；未校准→重新归零。 
2) 不开机：电池装反 / 没电→检查正负极、换电池。 
3) 数值偏高：探头污染→用酒精棉轻擦，再纯水冲洗校准。`,
    flowchartSvg: `<svg viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="arr4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#0ea5e9"/></marker></defs>
  <g fill="none" stroke="#0ea5e9" stroke-width="2">
    <rect x="10" y="35" width="120" height="50" rx="8" fill="#f0f9ff"/>
    <text x="70" y="60" fill="#075985" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">纯水归零校准</text>
    <line x1="130" y1="60" x2="160" y2="60" marker-end="url(#arr4)"/>
    
    <rect x="170" y="35" width="120" height="50" rx="8" fill="#f0f9ff"/>
    <text x="230" y="60" fill="#075985" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">探头浸入水样</text>
    <line x1="290" y1="60" x2="320" y2="60" marker-end="url(#arr4)"/>
    
    <rect x="330" y="35" width="120" height="50" rx="8" fill="#f0f9ff"/>
    <text x="390" y="60" fill="#075985" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">轻晃排气泡</text>
    <line x1="450" y1="60" x2="480" y2="60" marker-end="url(#arr4)"/>
    
    <rect x="490" y="35" width="120" height="50" rx="8" fill="#f0f9ff"/>
    <text x="550" y="60" fill="#075985" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">静置3-5s读数</text>
    <line x1="610" y1="60" x2="640" y2="60" marker-end="url(#arr4)"/>
    
    <rect x="650" y="35" width="130" height="50" rx="8" fill="#e0f2fe" stroke-dasharray="4"/>
    <text x="715" y="52" fill="#0369a1" stroke="none" text-anchor="middle" font-size="12" font-weight="bold">若超量程(Err)</text>
    <text x="715" y="70" fill="#0369a1" stroke="none" text-anchor="middle" font-size="12" font-weight="bold">使用纯水10倍稀释</text>
  </g>
</svg>`
  },

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
      { fieldKey: 'ph_measurement', label: 'pH值与温度综合测量', unit: '', maxReadings: 3, targetInstrumentId: 3, readingKey: 'ph_value' }
    ],
    operationSteps: `一、样品准备：现场样品
二、测试： 
1、准备 
1) 每次开机前，检查仪器后面的电极插口，必须保证连接有测量电极或者短路插头。 
2) 接通电源，打开开机键。 
3) 准备标准缓冲溶液：pH4.00、pH6.86、pH9.18 标液，进行标定。 
4) 将电极下端的保护瓶取下，拉下电极上端橡皮套，使其露出上端小孔，用蒸馏水清洗电极。 

2、标定 
1) 按“标定”键进入标定状态。 
2) 将洗净后电极放入标准缓冲溶液 1（如 pH6.86 标液）中，同时用温度计测量溶液温度。 
3) 按“设置”键，通过“▲”或“▼”设置当前温度。 
4) 按“确认”键完成温度值设置后，仪器返回标定状态。待读数稳定后，按“确认”键完成 1 点标定，此时仪器识别标液 1 并显示当前温度下的标准 pH 值。 
5) 若需多点标定，请更换其他标准缓冲溶液，重复 2.2、2.3、2.4 标定操作过程。本仪器支持最多3点标定，标定完3个标液时，仪器会自动结束标定，返回测量状态。备注：若只需1点标定（电极斜率为100%），完成1点标定后，按“取消”键离开标定状态，进入测量状态。 

3、测量 
1) 按“设置”键，通过“▲”或“▼”选择读数模式功能“1”。 
2) 按“确认”键进行读数模式设置，再通过“▲”或“▼” 选择读数模式，按“确认”键完成设置。 
3) 将电极清洗干净，放入被测溶液中，同时用温度计测量溶液温度。 
4) 按“设置”键，通过“▲”或“▼”选择手动温度设置 功能“2”。 
5) 按“确认”键进行温度设置，再通过“▲”或“▼”设置 当前温度值。 
6) 按“确认”键完成温度值设置后，仪器返回测量状态。按“测量”键开始测量，待数据稳定标志满格，即可读数。 
7) 【注意事项】测量结束后应及时将电极保护瓶套上，保护瓶内应放少量外参比补充液，保持电极球泡的湿润，切忌将电极长期浸泡在蒸馏水中。 
8) 清洁仪器外壳，请用沾有水及温和清洁剂的毛巾轻轻擦拭即可。`,
    flowchartSvg: `<svg viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="arr5" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e"/></marker></defs>
  <g fill="none" stroke="#f43f5e" stroke-width="2">
    <rect x="10" y="35" width="120" height="50" rx="8" fill="#fff1f2"/>
    <text x="70" y="60" fill="#9f1239" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">蒸馏水洗电极</text>
    <line x1="130" y1="60" x2="160" y2="60" marker-end="url(#arr5)"/>
    
    <rect x="170" y="35" width="120" height="50" rx="8" fill="#fff1f2"/>
    <text x="230" y="60" fill="#9f1239" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">标准液多点标定</text>
    <line x1="290" y1="60" x2="320" y2="60" marker-end="url(#arr5)"/>
    
    <rect x="330" y="35" width="120" height="50" rx="8" fill="#fff1f2"/>
    <text x="390" y="60" fill="#9f1239" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">浸入待测液</text>
    <line x1="450" y1="60" x2="480" y2="60" marker-end="url(#arr5)"/>
    
    <rect x="490" y="35" width="120" height="50" rx="8" fill="#fff1f2"/>
    <text x="550" y="60" fill="#9f1239" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">输入手动温度</text>
    <line x1="610" y1="60" x2="640" y2="60" marker-end="url(#arr5)"/>
    
    <rect x="650" y="35" width="130" height="50" rx="8" fill="#ffe4e6"/>
    <text x="715" y="60" fill="#be123c" stroke="none" text-anchor="middle" font-size="14" font-weight="bold">标志满格读数</text>
  </g>
</svg>`
  },

  test: {
    type: 'test',
    label: '全场景仪表测试',
    description: '系统全量化验证：按批次查看并触发 D0~D8 所有仪表',
    icon: '🔬',
    manualParams: [],
    instrumentFields: [
      { fieldKey: 'F0', label: 'D0 · 混调器', unit: '', maxReadings: 1, targetInstrumentId: 0, readingKey: '' },
      { fieldKey: 'F1', label: 'D1 · 电子天平1', unit: '', maxReadings: 1, targetInstrumentId: 1, readingKey: '' },
      { fieldKey: 'F2', label: 'D2 · 电子天平2', unit: '', maxReadings: 1, targetInstrumentId: 2, readingKey: '' },
      { fieldKey: 'F3', label: 'D3 · PH计', unit: '', maxReadings: 1, targetInstrumentId: 3, readingKey: '' },
      { fieldKey: 'F4', label: 'D4 · 水质检测仪', unit: '', maxReadings: 1, targetInstrumentId: 4, readingKey: '' },
      { fieldKey: 'F5', label: 'D5 · 表界面张力仪', unit: '', maxReadings: 1, targetInstrumentId: 5, readingKey: '' },
      { fieldKey: 'F6', label: 'D6 · 扭矩搅拌器', unit: '', maxReadings: 1, targetInstrumentId: 6, readingKey: '' },
      { fieldKey: 'F7', label: 'D7 · 水浴锅', unit: '', maxReadings: 1, targetInstrumentId: 7, readingKey: '' },
      { fieldKey: 'F8', label: 'D8 · 6速粘度计', unit: '', maxReadings: 1, targetInstrumentId: 8, readingKey: '' }
    ]
  }
}

export const EXPERIMENT_TYPE_LIST = Object.values(EXPERIMENT_SCHEMAS);
