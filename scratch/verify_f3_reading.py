import asyncio
import sys
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.main import _core_run_test_capture

async def verify_f3():
    print("Verifying F3 (PH仪) readings...")
    # exp_id=1 (assume an experiment exists or use a dummy)
    # field_key="F3_ph"
    # camera_id=3 (based on mapping)
    
    result = _core_run_test_capture(
        exp_id=1,
        field_key="F3_ph",
        camera_id=3,
        target_instrument_id=3
    )
    
    print("Result:", result)
    if result.get("success"):
        print("F3 Verification: SUCCESS")
        print("Readings:", result.get("all_ocr"))
    else:
        print("F3 Verification: FAILED")
        print("Detail:", result.get("detail"))

if __name__ == "__main__":
    # We need an experiment in the DB for this to work
    from backend.models.database import create_experiment
    try:
        exp_id = create_experiment("Verification Exp", "test")
        print(f"Created verification experiment: {exp_id}")
    except Exception as e:
        exp_id = 1 # Fallback
        
    asyncio.run(verify_f3())
