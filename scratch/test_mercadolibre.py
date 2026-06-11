import asyncio
import aiohttp
import json

async def test():
    query = "masajeador pistola"
    url = f"https://api.mercadolibre.com/sites/MLC/search?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Querying: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("Total results:", data.get("paging", {}).get("total"))
                results = data.get("results", [])
                print("Got", len(results), "results in current page")
                if results:
                    top = results[0]
                    print("Top item title:", top.get("title"))
                    print("Top item price:", top.get("price"))
                    print("Top item sold_quantity:", top.get("sold_quantity"))
            else:
                print("Failed status:", response.status)

asyncio.run(test())
