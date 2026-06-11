import sys
import os
sys.path.append(os.path.abspath(os.path.dirname('server.py')))
from server import login_to_dropi
from curl_cffi import requests

token = login_to_dropi()
headers = {
    'x-authorization': f'Bearer {token}',
    'Origin': 'https://app.dropi.cl',
    'Referer': 'https://app.dropi.cl/',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

endpoints = [
    'https://api.dropi.cl/api/products/v4/index',
    'https://api.dropi.cl/api/products/v4/catalog',
    'https://api.dropi.cl/api/products/v4/search',
    'https://api.dropi.cl/api/catalog/products',
    'https://api.dropi.cl/api/catalog/v4/index',
    'https://api.dropi.cl/api/catalog/search',
    'https://api.dropi.cl/api/public-catalog',
    'https://api.dropi.cl/api/products/public',
    'https://api.dropi.cl/api/products/catalog'
]

payload = {
  "per_page": 5,
  "pageSize": 5,
  "page": 1,
  "search": "cepillo",
  "sort_by": "created_at",
  "sort_order": "desc"
}

for url in endpoints:
    print(f"\nProbing POST {url}")
    try:
        resp = requests.post(url, headers=headers, json=payload, impersonate='chrome120', timeout=5)
        print("POST Status:", resp.status_code)
        if resp.status_code != 404:
            print("POST Response:", resp.text[:200])
    except Exception as e:
        print("POST Error:", str(e))
        
    print(f"Probing GET {url}")
    try:
        resp = requests.get(url, headers=headers, impersonate='chrome120', timeout=5)
        print("GET Status:", resp.status_code)
        if resp.status_code != 404:
            print("GET Response:", resp.text[:200])
    except Exception as e:
        print("GET Error:", str(e))
