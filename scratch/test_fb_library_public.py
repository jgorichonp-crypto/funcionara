import asyncio
import aiohttp
import re
import urllib.parse
import json

async def test_fb_ads_library(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    # Target Chile ('CL') and all ads ('all')
    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={encoded_keyword}&search_type=keyword_unordered&media_type=all"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    
    print(f"Requesting public Meta Ads Library for: '{keyword}'...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                print(f"Status code: {response.status}")
                if response.status != 200:
                    print("Failed to load page.")
                    return
                
                html = await response.text()
                print(f"HTML size: {len(html)} bytes")
                
                # Check if we can find keywords like "results" or count indicators in the text
                # We can look for scripts containing JSON data (typically under "require" or "define" in FB scripts)
                # Let's search for "totalCount" or "results" in the script tags
                scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
                print(f"Found {len(scripts)} script tags.")
                
                # Search for count patterns, e.g., "resultsCount" or "count" or "total"
                for idx, script in enumerate(scripts):
                    if "resultsCount" in script or "totalCount" in script or "search_results" in script:
                        print(f"Script #{idx} contains search result keywords! Length: {len(script)}")
                        # Print a snippet
                        print(script[:300])
                
                # Also try simple regex searches on the entire HTML
                count_match = re.search(r'"resultsCount":\s*(\d+)', html)
                if count_match:
                    print(f"Found resultsCount via regex: {count_match.group(1)}")
                else:
                    print("resultsCount not found in raw HTML.")
                    
                # Let's search for "adLibrarySearchResultCount" or similar
                alt_count_match = re.search(r'"count":\s*(\d+)', html)
                if alt_count_match:
                    print(f"Found count via regex: {alt_count_match.group(1)}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_fb_ads_library("Masajeador Pistola Muscular"))
