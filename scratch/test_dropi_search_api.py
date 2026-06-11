import sys
import os
import json
sys.path.append(os.path.abspath(os.path.dirname('server.py')))
from server import login_to_dropi
from curl_cffi import requests

token = login_to_dropi()
if not token:
    print('Login failed')
    sys.exit(1)

headers = {
    'x-authorization': f'Bearer {token}',
    'Origin': 'https://app.dropi.cl',
    'Referer': 'https://app.dropi.cl/',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Let's try to probe with POST
url = 'https://api.dropi.cl/api/products'
payloads = [
    {"search": "cepillo"},
    {"name": "cepillo"},
    {"q": "cepillo"},
    {"filters": {"search": "cepillo"}},
    {"search_type": "simple", "search": "cepillo"}
]

print("--- TESTING POST ON /api/products ---")
for p in payloads:
    print(f"Payload: {p}")
    resp = requests.post(url, headers=headers, json=p, impersonate='chrome120', timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("Success! Keys:", resp.json().keys())
        # Print a snippet of results
        data = resp.json()
        if 'objects' in data:
            print(f"Found {len(data['objects'])} items!")
            if len(data['objects']) > 0:
                print("First item:", data['objects'][0].get('id'), data['objects'][0].get('name'))
        break
    else:
        print(f"Response: {resp.text[:300]}")

# Let's also check other potential search endpoints with GET / POST
print("\n--- TESTING GET with query parameters ---")
get_urls = [
    'https://api.dropi.cl/api/products?name=cepillo',
    'https://api.dropi.cl/api/products/filter?search=cepillo',
    'https://api.dropi.cl/api/products/search?q=cepillo'
]
for u in get_urls:
    print(f"GET {u}")
    resp = requests.get(u, headers=headers, impersonate='chrome120', timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("Success! Keys:", resp.json().keys() if isinstance(resp.json(), dict) else type(resp.json()))
        break
