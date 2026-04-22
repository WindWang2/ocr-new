import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.database import get_connection, get_config
from backend.services.mock_camera import MockCameraClient
from instrument_reader import DynamicInstrumentLibrary

def investigate_f3():
    print("--- F3 (PH仪) Investigation ---")
    
    # 1. Check instrument-camera mapping
    mapping = get_config("instrument_camera_mapping", default={})
    print(f"Current mapping: {mapping}")
    f3_cam = mapping.get("3")
    print(f"Instrument F3 is mapped to Camera: {f3_cam}")
    
    # 2. Check F3 Template
    print("\nChecking Template for F3...")
    template = DynamicInstrumentLibrary.get_template("3")
    if template:
        print(f"Name: {template.get('name')}")
        print(f"Fields: {template.get('fields')}")
        print(f"Whitelist exists: {3 in DynamicInstrumentLibrary.get_pydantic_model_for_instrument('ph_meter').model_fields if hasattr(DynamicInstrumentLibrary, 'get_pydantic_model_for_instrument') else 'N/A'}")
    else:
        print("Error: Template for F3 not found in DB!")

    # 3. Check Mock Image for Camera 3
    if f3_cam is not None:
        print(f"\nChecking images for Camera {f3_cam}...")
        image_dir = get_config("image_dir", default=None)
        client = MockCameraClient(camera_id=int(f3_cam), image_dir=image_dir)
        image_path = client._find_latest_image()
        print(f"Latest image for Camera {f3_cam}: {image_path}")
        
        if image_path and "crops" in str(image_path):
            print("WARNING: Latest image is a CROP! This might cause YOLO detection failure.")
            
            # List all images to see if there's a full one
            parent_dir = Path(image_path).parent
            if "crops" in parent_dir.name:
                parent_dir = parent_dir.parent
            
            print(f"Scanning parent directory: {parent_dir}")
            extensions = {".jpg", ".jpeg", ".png", ".bmp"}
            all_images = [p for p in parent_dir.glob("*") if p.is_file() and p.suffix.lower() in extensions]
            print(f"Found {len(all_images)} images in parent dir.")
            for img in sorted(all_images, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                print(f"  - {img.name} (Modified: {img.stat().st_mtime})")

if __name__ == "__main__":
    investigate_f3()
