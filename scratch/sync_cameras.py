import sqlite3
import os

db_path = r'c:\Users\wangj.KEVIN\projects\ocr-new\backend\experiments.db'
enabled_cameras = [0, 3, 5, 7, 8]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Disable all currently existing cameras
cur.execute("UPDATE cameras SET enabled = 0")

# 2. For each requested camera, update or insert
for cid in enabled_cameras:
    # Check if exists
    cur.execute("SELECT id FROM cameras WHERE camera_id = ?", (cid,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE cameras SET enabled = 1 WHERE camera_id = ?", (cid,))
        print(f"Updated Camera {cid} to enabled.")
    else:
        # Insert as mock camera
        name = f"模拟相机 {cid}"
        cur.execute(
            "INSERT INTO cameras (name, camera_id, mode, enabled) VALUES (?, ?, ?, ?)",
            (name, cid, "single", 1)
        )
        print(f"Inserted and enabled new Camera {cid}.")

conn.commit()
conn.close()
print("Camera configuration sync complete.")
