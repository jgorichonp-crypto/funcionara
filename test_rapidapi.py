from config import settings
import requests
import json

url = "https://tiktok-shop-scraper-api.p.rapidapi.com/shop/search"
headers = {
    "x-rapidapi-host": "tiktok-shop-scraper-api.p.rapidapi.com",
    "x-rapidapi-key": settings.rapidapi_key
}
querystring = {"query": "kitchen gadgets", "limit": "5"}

response = requests.get(url, headers=headers, params=querystring)
print(f"Status Code: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(response.text)
