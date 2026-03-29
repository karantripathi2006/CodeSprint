import urllib.request
import json
import sys

data = json.dumps({'username': 'u1', 'password': 'p1'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/register', data=data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
