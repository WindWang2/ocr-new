import socket
import json
import time
import os
from pathlib import Path
from PIL import Image

def test_pipeline():
    print("Starting End-to-End Pipeline Test")
    print("------------------------------------")
    
    # 1. Connect to Camera Service
    HOST = '127.0.0.1'
    PORT = 8888
    
    try:
        print(f"Connecting to Camera Service at {HOST}:{PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(120) # 2 minutes timeout for LLM inference
        sock.connect((HOST, PORT))
        
        # 2. Send Trigger Command (F0 - Mixer)
        command = "VTFP,0"
        print(f"Sending command: {command}")
        sock.sendall(command.encode('utf-8'))
        
        # 3. Receive Response
        print("Waiting for response (this may take time)...")
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        sock.close()
        
        result = json.loads(data.decode('utf-8'))
        print("\nReceived Response:")
        
        if result.get("success"):
            print(f"Instrument: {result.get('instrument_name')}")
            print(f"Readings: {result.get('readings')}")
            
            # 4. Verify Crop Image sizing
            crop_path_rel = result.get("cropped_image_path")
            if crop_path_rel:
                # In detect_only, it calculates CiIdx by looking for "camera_images"
                # If relative_crop_path = "/".join(parts[ci_idx+1:])
                # Then we add "camera_images" prefix back.
                crop_abs_path = Path("camera_images") / crop_path_rel
                print(f"Checking crop image at: {crop_abs_path}")
                
                if crop_abs_path.exists():
                    with Image.open(crop_abs_path) as img:
                        w, h = img.size
                        print(f"Crop image dimensions: {w}x{h}")
                        if max(w, h) <= 500:
                            print("Verification SUCCESS: Max dimension <= 500px")
                        else:
                            print(f"Verification FAILED: Max dimension > 500px ({max(w, h)})")
                else:
                    # Try another possible path if the relative path already includes it or is different
                    print(f"File not found at {crop_abs_path}, checking alternative...")
                    alt_path = Path(crop_path_rel)
                    if alt_path.exists():
                        with Image.open(alt_path) as img:
                            print(f"Crop image dimensions (alt): {img.size}")
            else:
                print("No cropped_image_path found in result.")
        else:
            print(f"Pipeline failed: {result.get('error')}")

    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_pipeline()
