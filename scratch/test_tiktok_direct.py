import asyncio
import aiohttp
import json

async def test_tiktok():
    url = "https://tiktok-trends-api.p.rapidapi.com/get-trending-feed?trim=true"
    headers = {
        "x-rapidapi-key": "ed4a122b56msh6ad2745cca5d761p1b2bd2jsn16f0eefae65c",
        "x-rapidapi-host": "tiktok-trends-api.p.rapidapi.com"
    }
    
    print("Realizando peticion a TikTok Trends API...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print("Respuesta recibida exitosamente.")
                pretty_json = json.dumps(data, indent=2)
                print("Formato JSON retornado:")
                print(pretty_json[:2000])
            else:
                print(f"Error: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(test_tiktok())
