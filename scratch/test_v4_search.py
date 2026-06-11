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

url = 'https://api.dropi.cl/api/products/v4/index'
payload = {
  "per_page": 5,
  "pageSize": 5,
  "page": 1,
  "search": "Masaje",
  "category_id": None,
  "provider_id": None,
  "sort_by": "created_at",
  "sort_order": "desc",
  "white_brand_id": 4
}

print("POSTING to", url)
resp = requests.post(url, headers=headers, json=payload, impersonate='chrome120', timeout=15)
print("Status:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print("Success! Keys:", data.keys())
    if 'objects' in data:
        items = data['objects']
        print(f"Found {len(items)} items!")
        for i, item in enumerate(items):
            print(f"[{i}] ID: {item.get('id')}, Name: {item.get('name')}, Price: {item.get('sale_price')}, Supplier ID: {item.get('supplier_id') or item.get('user_id')}")
else:
    print("Body:", resp.text)
