import requests
import json

url = "https://facebook-ads-library-scraper-api.p.rapidapi.com/search/ads"
headers = {
    "x-rapidapi-host": "facebook-ads-library-scraper-api.p.rapidapi.com",
    "x-rapidapi-key": "ed4a122b56msh6ad2745cca5d761p1b2bd2jsn16f0eefae65c"
}
# Probamos con el producto que estaba quemado para ver si arroja resultados (ej: "Rechargeable Motion Sensor Ceiling Light" o "Rotary Cheese Grater")
querystring = {
    "query": "Rechargeable Motion Sensor Ceiling Light", 
    "country_code": "CL", 
    "limit": "50"
}

response = requests.get(url, headers=headers, params=querystring)
print(f"Status Code: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(response.text)
