import sqlite3
import os
import json

db_path = r'C:\Users\wangj.KEVIN\projects\ocr-new\backend\experiments.db'
print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Get Balance config from instrument_type='2' as reference
cursor.execute("SELECT fields_json, keywords_json, prompt_template, description FROM instrument_templates WHERE instrument_type='2'")
row = cursor.fetchone()
if not row:
    print("Error: Could not find template with instrument_type='2'")
    # Try id=2 as fallback
    cursor.execute("SELECT fields_json, keywords_json, prompt_template, description FROM instrument_templates WHERE id=2")
    row = cursor.fetchone()
    if not row:
        conn.close()
        exit(1)

fields, keywords, prompt, desc = row

# 2. Update F1 (instrument_type='1') -> 电子天平1
print("Updating instrument_type='1' to 电子天平1...")
cursor.execute('''
    UPDATE instrument_templates 
    SET name=?, fields_json=?, keywords_json=?, prompt_template=?, description=?
    WHERE instrument_type='1'
''', ('电子天平1', fields, keywords, prompt, '电子分析天平 (1号)'))

# 3. Update F2 (instrument_type='2') -> 电子天平2
print("Updating instrument_type='2' to 电子天平2...")
cursor.execute("UPDATE instrument_templates SET name='电子天平2' WHERE instrument_type='2'")

# 4. Update F3 (instrument_type='3') -> PH仪
print("Updating instrument_type='3' to PH仪...")
cursor.execute("UPDATE instrument_templates SET name='PH仪' WHERE instrument_type='3'")

conn.commit()

# Final Check
print("\n--- Final Status in experiments.db ---")
cursor.execute('SELECT id, name, instrument_type FROM instrument_templates WHERE id IN (1, 2, 3)')
for r in cursor.fetchall():
    print(f"ID {r[0]}: Name={r[1]}, Type={r[2]}")

conn.close()
print("\nSuccessfully updated instrument mapping.")
