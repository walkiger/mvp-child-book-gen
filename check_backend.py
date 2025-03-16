import requests

print("Checking backend status...")
try:
    response = requests.get('http://localhost:8888')
    print(f"Backend is running (status: {response.status_code})")
except Exception as e:
    print(f"Backend is not responding: {e}") 