import asyncio
import aiohttp

async def test():
    query = "masajeador-pistola"
    url = f"https://listado.mercadolibre.cl/{query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Querying: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print("Status:", response.status)
            if response.status == 200:
                html = await response.text()
                print("HTML Length:", len(html))
                print("HTML prefix:\n", html[:1000])

asyncio.run(test())
