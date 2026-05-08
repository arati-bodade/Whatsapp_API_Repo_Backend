import requests
reseller_id = "f2a4f6ee-6d04-4dfc-bf4e-1bd2ef6c58e4" # from screenshot
url = f"http://localhost:8000/api/reseller-analytics/dashboard/{reseller_id}"
try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Graph Data present: {'graph_data' in data}")
    if 'graph_data' in data:
        print(f"Graph Data length: {len(data['graph_data'])}")
        print(f"Sample: {data['graph_data'][:1]}")
except Exception as e:
    print(f"Error: {e}")
