import sys
import os
from curl_cffi import requests as curl_requests

# Test payloads and endpoints
email = "soporte.mundoaura@gmail.com"
password = "Limoncito.3"

endpoints = [
    "https://api.smartcommerce.lat/api/auth/login",
    "https://api.smartcommerce.lat/api/auth/signin",
    "https://api.smartcommerce.lat/api/auth/sign-in",
    "https://api.smartcommerce.lat/api/login",
    "https://api.smartcommerce.lat/api/signin",
    "https://api.smartcommerce.lat/api/users/login",
]

payloads = [
    {
        "email": email,
        "password": password,
        "iss": "smart",
        "sub": "client-web",
        "aud": "sign-in"
    }
]

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://app.smartcommerce.lat",
    "Referer": "https://app.smartcommerce.lat/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def probe():
    print("Probing SmartCommerce Login Endpoints...")
    for url in endpoints:
        for payload in payloads:
            print(f"Trying URL: {url} | Payload keys: {list(payload.keys())}")
            try:
                response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=10)
                print(f"Status Code: {response.status_code}")
                if response.status_code in [200, 201]:
                    print("SUCCESS!")
                    print(response.json())
                    return True
                else:
                    try:
                        print(f"Response: {response.json()}")
                    except:
                        print(f"Response Text: {response.text[:200]}")
            except Exception as e:
                print(f"Error: {e}")
            print("-" * 50)
    print("All probes failed.")
    return False

if __name__ == "__main__":
    probe()
