import re
from curl_cffi import requests as curl_requests

url = "https://app.smartcommerce.lat/sign-in"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def search():
    print("Fetching sign-in page...")
    resp = curl_requests.get(url, headers=headers, impersonate="chrome120")
    if resp.status_code != 200:
        print(f"Failed to fetch sign-in page: {resp.status_code}")
        return
        
    html = resp.text
    # Search for JS script src tags
    js_files = re.findall(r'src="(/[^"]+\.js)"', html)
    # Also look for full URLs
    js_files += re.findall(r'src="(https://[^"]+\.js)"', html)
    
    print(f"Found {len(js_files)} JS files:")
    for js in js_files:
        js_url = js if js.startswith("http") else f"https://app.smartcommerce.lat{js}"
        print(f"Scanning: {js_url}")
        try:
            js_resp = curl_requests.get(js_url, headers=headers, impersonate="chrome120", timeout=15)
            if js_resp.status_code == 200:
                js_content = js_resp.text
                # Search for JWT-like patterns (eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...)
                jwts = re.findall(r'(eyJ[A-Za-z0-9_-]{10,}\.[eE]yJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})', js_content)
                if jwts:
                    print(f"  FOUND JWTs in {js_url}:")
                    for token in jwts:
                        print(f"    Token: {token[:40]}... (len={len(token)})")
                
                # Let's search for "iss", "sub", "client-web", "smart"
                if "client-web" in js_content:
                    print("  FOUND 'client-web' in JS content!")
                    # Find surrounding characters
                    idx = js_content.find("client-web")
                    print(f"    Context: {js_content[max(0, idx-100):min(len(js_content), idx+100)]}")
        except Exception as e:
            print(f"  Error reading {js_url}: {e}")

if __name__ == "__main__":
    search()
