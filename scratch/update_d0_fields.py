import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def update_d0_missing_fields():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    prompt_d0 = r'''这是超级吴菌混调器的控制屏幕。请先根据左侧菜单高亮状态判断模式。

【模式判定】
- 左侧第一个按钮 (A) 高亮：自动模式。
- 左侧第二个按钮 (手形) 高亮：手动模式。

【提取指南】
1. 自动模式：
   - 顶部表格：提取“段一、段二、段三”中“转速(转)”和“时间(S)”下方的数字。
   - 中间行：提取“总共时长(S)”右侧数字，以及“剩余时长(S)”右侧数字。
   - 底部行：提取“当前段数”右侧数字，以及“当前转速(转)”右侧数字。

2. 手动模式：
   - 顶部表格：提取“高速、低速”中“转速(转)”和“时间(S)”下方的数字。
   - 底部行：提取“剩余时间(S)”和“当前转速(转)”中间的数字。

【重要】严禁复读占位符。必须输出你看到的真实数值，不存在则填 null。
输出 JSON 格式（自动模式全量字段）：
{"模式": "自动", "段一转速": "10000", "段一时间": "20", "段二转速": "16000", "段二时间": "20", "段三转速": "22000", "段三时间": "20", "总共时长": "60", "剩余时长": "1", "当前段数": "1", "当前转速": "0"}'''

    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d0, '0'))
    
    conn.commit()
    conn.close()
    print("D0 提示词已补全：增加了‘总共时长’和‘当前段数’字段。")

if __name__ == "__main__":
    update_d0_missing_fields()
