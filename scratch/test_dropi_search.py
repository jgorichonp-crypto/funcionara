import asyncio
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestDropiSearch")

# Asegurar path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from server import get_dropi_token

async def test_search():
    token = get_dropi_token()
    if not token:
        logger.error("No se pudo obtener token de Dropi")
        return
        
    url = "https://api.dropi.cl/api/products/search"
    params = {"q": "mascotas"}
    headers = {
        "x-authorization": f"Bearer {token}",
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json"
    }
    
    from curl_cffi import requests as curl_requests
    logger.info(f"Haciendo petición a: {url} con q='mascotas'")
    
    response = curl_requests.get(url, headers=headers, params=params, impersonate="chrome120", timeout=15)
    logger.info(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Estructura del JSON: {list(data.keys())}")
        
        # Guardar en archivo para inspeccionar
        with open("scratch/dropi_response.json", "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        products = data.get("products", []) or data.get("data", []) or data.get("objects", []) or []
        logger.info(f"Total productos encontrados: {len(products)}")
        if products:
            logger.info(f"Primer producto keys: {list(products[0].keys())}")
            logger.info(f"Primer producto: {products[0]}")
    else:
        logger.error(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_search())
