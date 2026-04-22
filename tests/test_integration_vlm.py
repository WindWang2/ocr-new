import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from instrument_reader import InstrumentReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integration():
    print(f"\n{'='*50}")
    print(f"GLM-OCR Integration Test")
    print(f"{'='*50}")

    # Initialize InstrumentReader (will use Config defaults: provider=local_vlm)
    try:
        reader = InstrumentReader()
        
        # Select a test image
        test_image = r"C:\Users\wangj.KEVIN\projects\ocr-new\camera_images\F3\000_143804.jpg"
        
        if not os.path.exists(test_image):
            print(f"Error: Test image not found at {test_image}")
            return

        print(f"Running full pipeline (Detect -> Crop -> Local VLM Read) on: {test_image}")
        
        # The instrument type for F3 should ideally be determined by YOLO
        # For this test, we call the main read_instrument method
        result = reader.read_instrument(test_image)
        
        print(f"\n{'='*20} Integration Result {'='*20}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"{'='*59}")
        
        if result.get("success"):
            print("\nSUCCESS: Integration verified.")
        else:
            print(f"\nFAILURE: {result.get('error')}")
            
    except Exception as e:
        print(f"Integration failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()
