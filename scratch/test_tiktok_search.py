import asyncio
import aiohttp
import json

async def test_search():
    # Probar endpoint /search/keyword con query
    url = "https://tiktok-trends-api.p.rapidapi.com/search/keyword"
    headers = {
        "x-rapidapi-key": "YOUR_RAPIDAPI_KEY",
        "x-rapidapi-host": "tiktok-trends-api.p.rapidapi.com"
    }
    
    # Probamos varios parametros comunes: "query", "keyword", "search"
    params = {"query": "amazon finds", "keyword": "amazon finds", "limit": 3}
    
    print("Realizando busqueda de productos en TikTok Trends API...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params, timeout=15) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print("Respuesta recibida exitosamente.")
                pretty_json = json.dumps(data, indent=2)
                print(pretty_json[:2000])
            else:
                print(f"Error: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(test_search())
