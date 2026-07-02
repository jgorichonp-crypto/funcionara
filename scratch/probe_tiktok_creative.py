import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_endpoint(path, params=None):
    url = f"https://tiktok-creative-center-api.p.rapidapi.com{path}"
    headers = {
        "x-rapidapi-key": "YOUR_RAPIDAPI_KEY",
        "x-rapidapi-host": "tiktok-creative-center-api.p.rapidapi.com"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                print(f"Testing {path} -> Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Success! Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    # print first 300 chars of response
                    import json
                    print(json.dumps(data)[:500])
                    return True
                else:
                    text = await response.text()
                    print(f"Error {response.status}: {text[:200]}")
        except Exception as e:
            print(f"Exception for {path}: {e}")
    return False

async def main():
    # Test verified path from RapidAPI documentation
    paths = [
        "/api/trending/keyword/posts"
    ]
    
    for path in paths:
        await test_endpoint(path, {"keyword": "heater", "country": "US", "limit": "2", "period": "7"})
        await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(main())
