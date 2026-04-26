import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")

def fix_d4_shutdown_hallucination():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # D4 - 水质检测仪：增加开机判定
    prompt_d4 = r'''这是水质检测仪屏幕。请先观察屏幕状态。

【状态预检】
- 如果屏幕是全黑的，或者没有任何文字显示，说明仪器处于【关机状态】。此时请停止提取，直接将所有字段设为 null。
- 如果屏幕亮起并显示文字，请提取以下数值。

【提取字段】
1. 空白值 (blank_value)
2. 检测值 (test_value)
3. 吸光度 (absorbance)
4. 含量 (content_mg_l)
5. 透光度 (transmittance)

【重要要求】
- 严禁在黑屏状态下编造任何数字！
- 严禁输出单位。
- 必须严格输出单行 JSON，使用中文键名。

JSON 格式要求：
{"空白值": "数字或null", "检测值": "数字或null", "吸光度": "数字或null", "含量": "数字或null", "透光度": "数字或null"}'''

    cursor.execute('UPDATE instrument_templates SET prompt_template = ? WHERE instrument_type = ?', (prompt_d4, '4'))
    
    conn.commit()
    conn.close()
    print("D4 提示词已更新：增加了黑屏关机状态的识别逻辑。")

if __name__ == "__main__":
    fix_d4_shutdown_hallucination()
