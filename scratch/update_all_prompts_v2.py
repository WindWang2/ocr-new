import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def update_all_prompts():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 策略：严格禁止示例数值，使用抽象描述
    
    prompts = {
        # D0 - 混调器
        "0": r'''这是实验室混料机屏幕。
1. 首先识别左侧菜单栏，判断是 "自动" (图标带A) 还是 "手动" 模式。
2. 如果是自动模式，提取：段一转速、段一时间、段二转速、段二时间、段三转速、段三时间、剩余时长、当前转速。
3. 如果是手动模式，提取对应的设定转速、当前转速等。

【重要】严格按以下JSON输出，禁止输出任何示例数字，必须输出你从图中实时观察到的数字字符串：
{"mode": "自动/手动", "seg1_speed": "提取到的数字", "seg1_time": "提取到的数字", "seg2_speed": "提取到的数字", "seg2_time": "提取到的数字", "seg3_speed": "提取到的数字", "seg3_time": "提取到的数字", "remaining_time": "提取到的数字", "current_speed": "提取到的数字"}''',

        # D1 & D2 - 天平
        "1": r'''这是电子分析天平。请仔细观察屏幕中心的数字。
注意：LED数码管的小数点非常微小，通常在倒数第2位或第3位之前。

【重要】输出JSON格式：
{"重量": "仅输出观察到的数字文本，严禁含有单位或占位符"}''',
        "2": r'''这是电子分析天平。请仔细观察屏幕中心的数字。
注意：LED数码管的小数点非常微小，通常在倒数第2位或第3位之前。

【重要】输出JSON格式：
{"重量": "仅输出观察到的数字文本，严禁含有单位或占位符"}''',

        # D3 - PH计
        "3": r'''这是PH计屏幕。
请提取三个核心数值：
1. 主显示的 PH值 (大字)。
2. 温度值 (通常在PH值下方，带°C单位)。
3. PTS百分比 (通常在右下角)。

【重要】输出JSON格式：
{"ph_value": "数字", "temperature": "数字", "pts": "数字"}''',

        # D5 - 张力仪 (重灾区)
        "5": r'''这是表界面张力仪。请忽略左侧黑色图形区，聚焦右侧的参数列表。
从上到下依次提取每行文字右侧的数值：
- 表/界面张力 (tension)
- 温度 (temperature) -> 如果是 N/A 请填 null
- 上层密度 (upper_density)
- 下层密度 (lower_density)
- 上升速度 (rise_speed)
- 下降速度 (fall_speed)
- F 值 (f_value) -> 位于屏幕最下方，两个圆形按钮中间。

【重要】严禁抄袭任何示例！必须根据实时图片提取。如果图片模糊，请根据文字位置定位其右侧的数字。
JSON格式：
{"张力": "数字", "温度": "数字或null", "上层密度": "数字", "下层密度": "数字", "上升速度": "数字", "下降速度": "数字", "F值": "数字"}''',

        # D6 - 扭矩搅拌器
        "6": r'''这是电动搅拌器。屏幕有三行：
1. 第一行：当前转速 (rotation_speed)。
2. 第二行：扭矩 (torque)。
3. 第三行：运行时间 (time)，格式为 MM:SS。

【重要】仔细观察运行时间的每一位，不要遗漏。
JSON格式：
{"rotation_speed": "数字", "torque": "数字", "time": "MM:SS"}''',

        # D7 - 水浴锅
        "7": r'''这是水浴锅温控表。有两个红色/绿色数字显示。
1. 上方较大的数字：当前温度 (temperature)。
2. 下方较小的数字：设定时间或温度 (time)。

注意：请务必识别小数点。
JSON格式：
{"temperature": "数字", "time": "数字"}''',

        # D8 - 旋转粘度计
        "8": r'''这是旋转粘度计。请寻找屏幕上最重要的几个读数：
- 实时读数/粘度 (actual_reading)
- 最大量程 (max_reading)
- 最小量程 (min_reading)
- 当前转速 (rotation_speed)
- 表面粘度 (apparent_viscosity)

【重要】输出JSON格式：
{"actual_reading": "数字", "max_reading": "数字", "min_reading": "数字", "rotation_speed": "数字", "apparent_viscosity": "数字"}'''
    }

    for inst_id, prompt in prompts.items():
        cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt, inst_id))
    
    conn.commit()
    conn.close()
    print("所有仪器 Prompt 已更新：已彻底移除数字示例，强化了提取逻辑。")

if __name__ == "__main__":
    update_all_prompts()
