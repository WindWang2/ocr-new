import sqlite3
import os

db_path = os.path.join("backend", "experiments.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    print(f"\nTable: {table}")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]})")
conn.close()
