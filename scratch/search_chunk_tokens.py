import re
from curl_cffi import requests as curl_requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

files = [
    "main-3BHIDNAZ.js",
    "polyfills-ZKZZ6ZDY.js",
    "chunk-ZSBREDOO.js",
    "chunk-PQSXNCKT.js",
    "chunk-4SHWECNL.js",
    "chunk-ECSM4O7R.js",
    "chunk-L43BMVHK.js",
    "chunk-URY624AI.js",
    "chunk-HRTJCIHT.js",
    "chunk-T6NYIGUE.js",
    "chunk-OQ3Y27HV.js",
    "chunk-I2NEU6OK.js"
]

def search():
    print("Scanning JS bundles...")
    for f in files:
        url = f"https://app.smartcommerce.lat/{f}"
        print(f"Scanning {url}...")
        try:
            resp = curl_requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
            if resp.status_code == 200:
                content = resp.text
                
                # Check for "iss", "sub", "client-web", "smart" context
                if "client-web" in content:
                    idx = content.find("client-web")
                    print(f"  FOUND 'client-web' context in {f}!")
                    print(f"  Context: {content[max(0, idx-150):min(len(content), idx+150)]}")
                
                # Look for JWTs
                jwts = re.findall(r'(eyJ[A-Za-z0-9_-]{10,}\.[eE]yJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})', content)
                if jwts:
                    print(f"  FOUND JWTs in {f}:")
                    for token in jwts:
                        print(f"    Token: {token[:60]}... (len={len(token)})")
            else:
                print(f"  Failed: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  Error: {e}")
            
if __name__ == "__main__":
    search()
