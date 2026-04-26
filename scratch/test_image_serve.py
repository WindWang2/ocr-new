import requests

url = "http://localhost:8001/images/F7/20260418/crops/display/20260418170019301_F7-I0_OK_crop_F7_150509.png"
r = requests.get(url)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"Size: {len(r.content)} bytes")
