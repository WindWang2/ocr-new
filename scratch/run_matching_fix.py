import asyncio
import sys
import os
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.main import match_instruments
from backend.models.database import get_config, set_config

async def main():
    print("Starting instrument matching...")
    # Trigger matching
    result = await match_instruments()
    
    if result.get("success"):
        print("Match result: SUCCESS")
        print("Summary:")
        for item in result.get("summary", []):
            print(f"  Instrument {item['instrument_id']} ({item['instrument_name']}) -> Camera {item['camera_id']} (Conf: {item['confidence']:.4f})")
    else:
        print("Match result: FAILED")
        print("Detail:", result.get("detail"))
        
    print("\nScan Details:")
    for res in result.get("scan_details", []):
        msg = f"  Camera {res['camera_id']}: {res['status']}"
        if res['status'] == "success":
            inst_list = [f"ID {i['class_id']} ({i['confidence']:.2f})" for i in res.get("instruments", [])]
            msg += f" - Detected: {inst_list}"
        elif res.get("error"):
            msg += f" - Error: {res['error']}"
        print(msg)
    
    # Check new mapping
    mapping = get_config("instrument_camera_mapping")
    print("\nFinal Config Mapping:", mapping)

if __name__ == "__main__":
    asyncio.run(main())
