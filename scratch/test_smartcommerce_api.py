import json
from curl_cffi import requests as curl_requests

email = "soporte.mundoaura@gmail.com"
password = "Limoncito.3"

login_url = "https://api.smartcommerce.lat/api/auth/sign-in"
login_headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://app.smartcommerce.lat",
    "Referer": "https://app.smartcommerce.lat/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "iss": "smart",
    "sub": "client-web",
    "aud": "sign-in"
}
login_payload = {
    "email": email,
    "password": password
}

def test_api():
    print("Logging in to SmartCommerce...")
    try:
        resp = curl_requests.post(login_url, headers=login_headers, json=login_payload, impersonate="chrome120")
        print(f"Login Status: {resp.status_code}")
        data = resp.json()
        if resp.status_code != 200:
            print("Login failed:", data)
            return
        
        payload = data.get("payload", {})
        access_token = payload.get("accessToken")
        refresh_token = payload.get("refreshToken")
        print("Login successful!")
        print(f"Access Token: {access_token[:50]}...")
        
        # Now let's try calling products endpoint
        products_url = "https://api.smartcommerce.lat/api/products?page=1&size=5&sortBy=createdAt"
        products_headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Authorization": f"Bearer {access_token}"
        }
        
        print("\nFetching products...")
        prod_resp = curl_requests.get(products_url, headers=products_headers, impersonate="chrome120")
        print(f"Products Status: {prod_resp.status_code}")
        prod_data = prod_resp.json()
        
        if prod_resp.status_code == 200:
            payload_data = prod_data.get("payload", {})
            items = payload_data.get("items", [])
            print(f"Successfully retrieved {len(items)} products:")
            if items:
                print("First product JSON:")
                print(json.dumps(items[0], indent=2))
            for item in items:
                print(f"- {item.get('name')} | Price: {item.get('salePrice')} | Stock: {item.get('stock') or item.get('quantity')}")
        else:
            print("Failed to get products:", prod_data)
            
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    test_api()
