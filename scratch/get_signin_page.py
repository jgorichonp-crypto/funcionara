from curl_cffi import requests as curl_requests

url = "https://app.smartcommerce.lat/sign-in"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = curl_requests.get(url, headers=headers, impersonate="chrome120")
with open("scratch/signin.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("Saved signin.html")
