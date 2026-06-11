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

# Let's inspect the 400 responses of filter and search
endpoints = [
    ('GET', 'https://api.dropi.cl/api/products/filter?search=cepillo', None),
    ('GET', 'https://api.dropi.cl/api/products/search?q=cepillo', None),
    ('POST', 'https://api.dropi.cl/api/products/filter', {"search": "cepillo"}),
    ('POST', 'https://api.dropi.cl/api/products/search', {"q": "cepillo"}),
    ('POST', 'https://api.dropi.cl/api/products/search', {"search": "cepillo"}),
    ('POST', 'https://api.dropi.cl/api/products/filter', {"name": "cepillo"}),
]

for method, url, payload in endpoints:
    print(f"\n--- TESTING {method} {url} with payload {payload} ---")
    if method == 'GET':
        resp = requests.get(url, headers=headers, impersonate='chrome120', timeout=10)
    else:
        resp = requests.post(url, headers=headers, json=payload, impersonate='chrome120', timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
