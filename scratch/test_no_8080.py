import logging
logging.basicConfig(level=logging.INFO)
from instrument_reader import InstrumentReader
import os

# Create a dummy image if none exists
dummy_image = "scratch/dummy.jpg"
from PIL import Image
if not os.path.exists(dummy_image):
    os.makedirs("scratch", exist_ok=True)
    Image.new('RGB', (100, 100), color='red').save(dummy_image)

reader = InstrumentReader()
print("Starting read_instrument (should not hit 8080)...")
result = reader.read_instrument(dummy_image)
print("Result:", result)
