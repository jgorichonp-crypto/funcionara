import sys
import os
import json
import asyncio

# Ensure path imports correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from server import get_dropi_token
from curl_cffi import requests as curl_requests

async def main():
    token = get_dropi_token()
    if not token:
        print("❌ Login failed or token not found.")
        return

    url = "https://api.dropi.cl/api/products/index"
    headers = {
        "x-authorization": f"Bearer {token}",
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Let's search for different query terms
    queries = ["Cubo antiestrés", "Stress Cube", "JOYIN", "JOYIN 4 Pack", "antiestres", "56319"]

    for query in queries:
        print(f"\n==================================================")
        print(f"Searching Dropi for: '{query}'...")
        print(f"==================================================")
        
        payload = {
            "pageSize": 10,
            "startData": 0,
            "no_count": True,
            "keywords": query,
            "order_by": "id",
            "order_type": "asc"
        }
        
        try:
            response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                products = data.get("objects", []) or data.get("products", []) or data.get("data", []) or []
                print(f"Found {len(products)} products.")
                for idx, p in enumerate(products):
                    p_id = p.get("id") or p.get("product_id")
                    p_name = p.get("name")
                    p_price = p.get("price") or p.get("sale_price") or p.get("cost")
                    p_stock = p.get("stock")
                    print(f"  [{idx+1}] ID: {p_id} | Name: '{p_name}' | Stock: {p_stock} | Price: {p_price}")
                    print(f"  Full details: {json.dumps(p, indent=4, ensure_ascii=False)}")
            else:
                print(f"Error response: {response.text[:200]}")
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
