import asyncio
import aiohttp
import urllib.parse
import json

async def test_fb_async_search(keyword):
    url = "https://www.facebook.com/ads/library/async/search_ads/"
    
    # Payload similar to what the public browser search sends
    payload = {
        "active_status": "active",
        "ad_type": "all",
        "countries[0]": "CL",
        "q": keyword,
        "search_type": "keyword_unordered",
        "media_type": "all",
        "__a": "1",  # Crucial: tells FB to return JSON instead of HTML
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.facebook.com",
        "Referer": f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={urllib.parse.quote(keyword)}&search_type=keyword_unordered"
    }
    
    print(f"Querying FB async search for: '{keyword}'...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=payload, timeout=15) as response:
                print(f"Status code: {response.status}")
                text = await response.text()
                print(f"Response snippet (first 500 chars):")
                print(text[:500])
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_fb_async_search("Masajeador Pistola Muscular"))
