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
    'Accept': 'application/json'
}

u1 = 'https://api.dropi.cl/api/products/filter?search=cepillo'
u2 = 'https://api.dropi.cl/api/products/search?q=cepillo'

for u in [u1, u2]:
    print(f"\nGET {u}")
    resp = requests.get(u, headers=headers, impersonate='chrome120', timeout=10)
    print("Status:", resp.status_code)
    print("Body:", resp.text[:1000])
