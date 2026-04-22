import sqlite3
import os

db_path = 'backend/experiments.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(c.fetchall())
    conn.close()
else:
    print("DB NOT FOUND")
