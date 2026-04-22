import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.database import get_connection

def configure_cameras():
    conn = get_connection()
    cursor = conn.cursor()
    
    enabled_ids = [0, 3, 4, 5, 7, 8]
    disabled_ids = [1, 2, 6]
    
    print(f"Enabling cameras: {enabled_ids}...")
    for cam_id in enabled_ids:
        cursor.execute("UPDATE cameras SET enabled = 1 WHERE camera_id = ?", (cam_id,))
        if cursor.rowcount == 0:
            print(f"Warning: Camera {cam_id} does not exist. Adding it...")
            cursor.execute(
                "INSERT INTO cameras (name, camera_id, mode, enabled) VALUES (?, ?, ?, ?)",
                (f"Camera {cam_id}", cam_id, "single", 1)
            )
            
    print(f"Disabling cameras: {disabled_ids}...")
    for cam_id in disabled_ids:
        cursor.execute("UPDATE cameras SET enabled = 0 WHERE camera_id = ?", (cam_id,))
        if cursor.rowcount == 0:
            print(f"Warning: Camera {cam_id} does not exist. Adding it (disabled)...")
            cursor.execute(
                "INSERT INTO cameras (name, camera_id, mode, enabled) VALUES (?, ?, ?, ?)",
                (f"Camera {cam_id}", cam_id, "single", 0)
            )
            
    conn.commit()
    conn.close()
    print("Configuration complete.")

if __name__ == "__main__":
    configure_cameras()
