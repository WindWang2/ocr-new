import sys
import json
import logging
import time
from pathlib import Path
from instrument_reader import InstrumentReader
from backend.services.llm_provider import get_global_provider

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def verify_pipeline(image_path, target_id=None):
    if not Path(image_path).exists():
        print(f"Error: Image not found at {image_path}")
        return

    print(f"\n{'='*60}")
    print(f"Verifying Full Pipeline for: {image_path}")
    print(f"Target Instrument ID: {target_id if target_id is not None else 'Auto'}")
    print(f"{'='*60}")

    # Initialize Reader
    provider = get_global_provider()
    reader = InstrumentReader(provider=provider)

    # Run detection and reading
    print("\n[Step 1 & 2] Detecting and Reading...")
    start_time = time.time()
    result = reader.read_instrument(image_path, target_class_id=target_id)
    total_ms = (time.time() - start_time) * 1000

    if not result.get("success"):
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        return

    print(f"✅ Success! (Processed in {total_ms:.1f}ms)")
    
    # Check data
    print(f"\n[Result Data]")
    print(json.dumps(result.get("readings", {}), indent=2, ensure_ascii=False))

    print(f"\n[Metadata Verification]")
    print(f"Instrument:      {result.get('instrument_name')} ({result.get('instrument_type')})")
    print(f"Confidence:      {result.get('confidence')}")
    print(f"Method:          {result.get('method')}")
    
    # Check if recognition path exists in det info
    if "recognition_image_path" in result:
        print(f"Recognition Path: {result['recognition_image_path']}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        img = sys.argv[1]
        tid = int(sys.argv[2]) if len(sys.argv) > 2 else None
        verify_pipeline(img, tid)
    else:
        print("Usage: python test_full_pipeline.py <image_path> [target_id]")
