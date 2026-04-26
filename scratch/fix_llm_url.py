import sqlite3
import json
import os

db_path = os.path.join("backend", "experiments.db")

def fix_db():
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_config WHERE key = 'llm_config'")
    row = cursor.fetchone()
    if row:
        config = json.loads(row[0])
        # 移除可能存在的 /v1 后缀，因为代码会自动补全
        if config['base_url'].endswith('/v1'):
            config['base_url'] = config['base_url'][:-3]
            cursor.execute("UPDATE system_config SET value = ? WHERE key = 'llm_config'", (json.dumps(config),))
            conn.commit()
            print(f"数据库 LLM URL 已修正: {config['base_url']}")
    conn.close()

if __name__ == "__main__":
    fix_db()
