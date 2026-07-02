import json
from curl_cffi import requests as curl_requests

email = "soporte.mundoaura@gmail.com"
password = "Limoncito.3"

login_url = "https://api.smartcommerce.lat/api/auth/sign-in"
login_headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "iss": "smart",
    "sub": "client-web",
    "aud": "sign-in"
}
login_payload = {
    "email": email,
    "password": password
}

def test_by_id():
    resp = curl_requests.post(login_url, headers=login_headers, json=login_payload, impersonate="chrome120")
    if resp.status_code != 200:
        print("Login failed")
        return
    
    token = resp.json()["payload"]["accessToken"]
    
    # Try fetching a specific product by ID
    prod_id = "6a383883856fe6d1a23c44de"
    detail_url = f"https://api.smartcommerce.lat/api/products/{prod_id}"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Fetching details for product {prod_id}...")
    detail_resp = curl_requests.get(detail_url, headers=headers, impersonate="chrome120")
    print(f"Status Code: {detail_resp.status_code}")
    try:
        data = detail_resp.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print("Error/Text:", detail_resp.text)

if __name__ == "__main__":
    test_by_id()
