import os

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
      { fieldKey: 'surface_tension_val', label: '表面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'interface_tension_val', label: '界面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' }
    ],
    operationSteps: `一、 准备与校准
1. **设备通电**：主机开机 45 分钟以稳定测量系统。
2. **水平校准**：调节底部旋钮，确保水准泡红圈位于蓝点中间（屏幕无倾斜警报）。
3. **砝码校准**：每天首次使用需挂载 500g 砝码进行去皮和标定，允许误差 ±0.1g。

二、 样品与器具处理
1. **铂金环清洗**：用流水冲洗或专用溶剂去油。**必须**用酒精灯灼烧至红炽状态（20-30秒），冷却 10 秒后挂载。
2. **器皿润洗**：用少量样品润洗玻璃器皿内壁后倒掉，随后倒入 7-10mm 高度样品。

三、 表面张力测试
1. **参数设置**：默认升降速度 10mm/min，上层密度默认为 0，下层输入样品实际密度。
2. **环浸没**：关闭移门，手动上升托盘至铂金环浸入液面约 2mm，点击“去皮”归零。
3. **自动测试**：点击“启动测试”，托盘自动下降。铂金环与液面分离瞬间的**最大数值**即为表面张力结果。

四、 界面张力测试
1. **分层注液**：先倒入下层液体（约 5-7mm），将铂金环浸入 3mm。再用移液管沿壁缓慢注入上层液体（如煤油，约 18mm），**严禁触碰铂金环**。
2. **设置密度**：分别设置上下层液体的实际密度。
3. **自动拉脱**：启动测试，铂金环从下层穿过界面，拉破界面液膜时的最大值即为界面张力。

【注意事项】
- 当样品粘度 > 200mPa.s 时，不建议使用铂金环法。
- 测试过程中严禁震动实验台。`,
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
      { fieldKey: 'flow_time', label: '流经时间', unit: 's', maxReadings: 3, targetInstrumentId: -1, readingKey: '时间' }
    ],
    operationSteps: `一、 准备与清洗
1. **毛细管选择**：选取适当内径的平氏毛细管粘度计，保证液体流动时间 > 200s（最细内径不得小于 350s）。
2. **清洗烘干**：使用溶剂油/石油醚洗涤，必须放入烘箱烘干。内壁需无挂液、无杂质。

二、 装样与恒温
1. **润洗与装液**：用待测液清洗三遍。将粘度计倒置，用洗耳球将液体吸至测定球 D 处，**绝对禁止气泡**。
2. **水浴恒温**：将粘度计垂直置于 25℃ 恒温水浴中，静置 10 分钟。

三、 测试操作
1. **提液**：用洗耳球将液体缓慢吸至上方刻度线 C 以上 5-10mm 处，立即捏紧乳胶管防回流。
2. **自然流下与计时**：松开乳胶管，液体靠重力自然下落。眼睛平视刻度线，当**弯月面最低点**通过标线 C 时开始计时。
3. **结束计时**：当弯月面最低点通过标线 D 时停止计时，记录流经时间 t。

四、 数据处理
1. **平行测定**：重复吸液、计时操作 3 次。
2. **误差判定**：3 次流出时间的极差需 ≤ 平均值的 0.2%，否则需重新装样测试。
3. **清洗复位**：倒出样品，使用溶剂反复冲洗并烘干，垂直悬挂保存。`,
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
    operationSteps: `一、 组装与注液
1. **安装部件**：检查并确保浮子与外套筒干净无损。向上推动并逆时针旋转安装浮子；顺时针旋转安装外套筒至最高位置。
2. **固定浆杯**：向浆杯注入约 350mL 待测液（至内置刻度线）。将浆杯放于托盘，对齐三个孔隙后上提，使液面与外转筒液位线平齐，拧紧星型把手。

二、 测试操作
1. **仪表清零**：接通电源，按显示屏中的“清零”键。
2. **阶梯测速**：要求从最低剪切速率到最高逐一变化。
3. **记录数据**：分别测试 3r/min、6r/min、100r/min 下的剪切速率，**必须在每个转速稳定 20s 后**记录读数。

三、 拆卸与清洗
1. **取出浆杯**：测试结束后松开把手取下浆杯。
2. **拆卸清洗**：逆时针转动拆除外套筒；向下拉动并逆时针旋转取下浮子。立即用清水清洗并彻底擦干。

【流体校准提示】
- 需使用 ASTM 标准的校准液（20, 50, 100, 200 cP）。
- 设定 300 转运行 3 分钟进行温度平衡，记录 300转/600转 的读数与温度计读数，对比对照表验证仪器精度。`,
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
    operationSteps: `一、 探头纯水校准
1. **纯水归零**：取下笔帽装入 2/3 纯净水，将探头浸入并晃动排气泡。
2. **长按校准**：开机等待 3 秒，若显示 ≠ 0ppm，长按开关键 5-8 秒进入校准模式，自动归零。擦干备用。

二、 水样检测操作
1. **取样与浸没**：可直接将探头伸入水杯，或用笔帽装待测水（勿碰杯底杯壁）。
2. **消除气泡**：探头浸入水中后，轻轻晃动 1-2 秒以排出金属针上的微小气泡。
3. **静置读数**：静置 3-5 秒，待数值稳定后读取 TDS 值（即水中总溶解固体矿化度，单位 ppm）。

三、 超量程稀释处理
1. **异常显示**：若屏幕显示 "Err" 或 "OL"，代表矿化度 > 9990 ppm，必须稀释。
2. **稀释用水**：**绝对禁止使用自来水**，必须使用 TDS < 10 ppm 的 RO 纯水。
3. **10倍定量稀释**：取 10mL 待测水样 + 90mL RO 纯水，充分混匀后检测。结果乘以 10 即为原水 TDS。
4. **百倍稀释**：若 10倍稀释仍超限，取 1mL 水样 + 99mL 纯水，结果乘以 100。

【维护与保养】
- 测试完毕后，必须用纯水冲洗探头并用软纸巾吸干，盖上笔帽防止氧化腐蚀。
- 若数值乱跳，请重新清洗并归零校准。`,
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
      { fieldKey: 'ph_val', label: 'pH值', unit: '', maxReadings: 3, targetInstrumentId: 3, readingKey: 'ph_value' },
      { fieldKey: 'temperature', label: '溶液温度', unit: '℃', maxReadings: 1, targetInstrumentId: 3, readingKey: 'temperature' }
    ],
    operationSteps: `一、 开机与清洗
1. **探头检查**：开机前必须确保仪器后侧电极插口已连接测量电极或短路插头。
2. **摘帽清洗**：取下电极下端保护瓶，拉下上端橡皮套露出小孔。使用蒸馏水彻底清洗电极球泡。

二、 标准溶液标定（校准）
1. **进入标定**：按“标定”键。将洗净的电极放入缓冲溶液 1（如 pH 6.86），并用温度计测量溶液实际温度。
2. **温度补偿**：按“设置”键，输入当前温度值并确认。
3. **完成单点**：待屏幕读数稳定后，按“确认”完成第 1 点标定，仪器会自动识别当前标准液。
4. **多点标定**：重复清洗并更换缓冲溶液（pH4.00, pH9.18）。仪器最多支持 3 点标定。若仅需单点，直接按“取消”退出。

三、 样品测量
1. **模式确认**：按“设置”进入菜单，确保处于正确的测量模式（功能“1”和功能“2”手动温度补偿）。
2. **浸没与调温**：将清洗干净的电极放入待测溶液，用温度计测量温度并输入到仪器中。
3. **静置读数**：按“测量”键，等待屏幕右上角数据稳定标志“满格”后，记录 pH 读数。

【电极保养禁忌】
- 测量结束后，**切忌将电极长期浸泡在蒸馏水中**。
- 必须将电极插回保护瓶，且瓶内需保持有适量外参比补充液，以维持电极球泡的湿润。`,
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
    instrumentFields: []
  }
}
export const EXPERIMENT_TYPE_LIST = Object.values(EXPERIMENT_SCHEMAS);
"""

with open('frontend/src/lib/experimentTypes.ts', 'w', encoding='utf-8') as f:
    f.write(schemas_ts)

print("Optimized schemas with flowcharts generated.")
