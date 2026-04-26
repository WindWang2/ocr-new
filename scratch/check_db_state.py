import sqlite3
import json

def check():
    conn = sqlite3.connect('backend/experiments.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- System Config ---")
    cursor.execute("SELECT * FROM system_config")
    for row in cursor.fetchall():
        print(f"{row['key']}: {row['value']}")
        
    print("\n--- Instrument Templates ---")
    cursor.execute("SELECT instrument_type, name FROM instrument_templates")
    for row in cursor.fetchall():
        print(f"ID {row['instrument_type']}: {row['name']}")
        
    print("\n--- Recent Readings ---")
    cursor.execute("SELECT field_key, camera_id, value, image_path FROM experiment_readings ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f"Field: {row['field_key']}, Cam: {row['camera_id']}, Val: {row['value']}, Path: {row['image_path']}")
        
    conn.close()

if __name__ == "__main__":
    check()
