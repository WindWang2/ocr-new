import os
from PIL import Image
from pathlib import Path

def setup_mock_images():
    demo_map = {
        0: '1-1.jpg',
        1: '1.jpg',
        2: '2.jpg',
        3: '3.jpg',
        4: '4.jpg',
        5: '5-1.jpg',
        6: '6.jpg',
        7: '7.jpg',
        8: '8.jpg'
    }
    
    for f_id, filename in demo_map.items():
        src = Path('demo') / filename
        if not src.exists():
            print(f"Skipping {f_id}: {src} not found")
            continue
            
        dest_dir = Path('camera_images') / f"F{f_id}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"mock_{f_id}.bmp"
        
        try:
            img = Image.open(src)
            img.save(dest, 'BMP')
            print(f"Converted {filename} to {dest}")
        except Exception as e:
            print(f"Error converting {filename}: {e}")

if __name__ == "__main__":
    setup_mock_images()
