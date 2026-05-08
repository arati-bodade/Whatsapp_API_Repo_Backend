import requests
import json

ports = [3000, 3001, 3002, 8000]

print("Checking ports...")

for port in ports:
    url = f"http://localhost:{port}/"
    try:
        response = requests.get(url, timeout=2)
        content_type = response.headers.get('content-type', '')
        print(f"Port {port}: UP (Status {response.status_code}) | Type: {content_type}")
        if 'text/html' in content_type:
            print(f"  -> Likely Frontend (Title: {response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else 'Unknown'})")
        elif 'application/json' in content_type:
            print(f"  -> Likely API/Engine (Response: {response.text[:100]}...)")
    except requests.exceptions.ConnectionError:
        print(f"Port {port}: DOWN (Connection Refused)")
    except Exception as e:
        print(f"Port {port}: ERROR ({e})")
