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
    'Accept': 'application/json'
}

# Try different search endpoints
urls_to_try = [
    'https://api.dropi.cl/api/products?search=cepillo',
    'https://api.dropi.cl/api/catalog?search=cepillo',
    'https://api.dropi.cl/api/search/products?q=cepillo'
]

for url in urls_to_try:
    print(f'\nTrying {url}')
    resp = requests.get(url, headers=headers, impersonate='chrome120', timeout=10)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print('Keys:', data.keys() if isinstance(data, dict) else type(data))
        if isinstance(data, dict) and data.get('objects'):
            items = data['objects']
            print(f'Found {len(items)} items!')
            if len(items) > 0:
                item = items[0]
                print(f'First item ID: {item.get("id")}, Name: {item.get("name")}, Supplier: {item.get("user_id")}')
            break
        elif isinstance(data, list) and len(data) > 0:
            print(f'Found list of {len(data)} items!')
            item = data[0]
            print(f'First item ID: {item.get("id")}, Name: {item.get("name")}, Supplier: {item.get("user_id")}')
            break
