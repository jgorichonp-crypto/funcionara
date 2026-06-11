from curl_cffi import requests
import re

def test():
    query = "masajeador-pistola"
    url = f"https://listado.mercadolibre.cl/{query}"
    print(f"Querying with curl_cffi: {url}")
    
    # curl_cffi usa impersonate='chrome120' para imitar perfectamente un navegador real
    response = requests.get(url, impersonate="chrome120")
    print("Status:", response.status_code)
    
    if response.status_code == 200:
        html = response.text
        print("HTML Length:", len(html))
        with open("scratch/ml_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Wrote page to scratch/ml_page.html")

test()
