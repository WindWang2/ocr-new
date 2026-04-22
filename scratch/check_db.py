import sqlite3
import json

try:
    conn = sqlite3.connect('experiments.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # Try different table names that might exist
    for table_name in ['config', 'system_config', 'settings']:
        try:
            cur.execute(f"SELECT key, value FROM {table_name}")
            rows = cur.fetchall()
            print(f"Content of {table_name}:")
            for row in rows:
                print(f"  {row[0]}: {row[1]}")
        except:
            pass
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
