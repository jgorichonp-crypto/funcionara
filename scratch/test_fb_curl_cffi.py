import asyncio
import urllib.parse
from curl_cffi.requests import AsyncSession

async def test_fb_curl_cffi(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    # Target Chile ('CL') and all ads ('all')
    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={encoded_keyword}&search_type=keyword_unordered&media_type=all"
    
    print(f"Requesting public Meta Ads Library for: '{keyword}' using curl_cffi Chrome impersonation...")
    async with AsyncSession(impersonate="chrome") as session:
        try:
            response = await session.get(url, timeout=15)
            print(f"Status code: {response.status_code}")
            html = response.text
            print(f"HTML size: {len(html)} bytes")
            
            # Look for script tags or count indicators
            import re
            count_match = re.search(r'"resultsCount":\s*(\d+)', html)
            if count_match:
                print(f"✅ Found resultsCount: {count_match.group(1)}")
            else:
                print("resultsCount key not found in html.")
                
            # Search for 'totalCount'
            total_match = re.search(r'"totalCount":\s*(\d+)', html)
            if total_match:
                print(f"✅ Found totalCount: {total_match.group(1)}")
                
            # Search for '"count":'
            cnt_match = re.search(r'"count":\s*(\d+)', html)
            if cnt_match:
                print(f"✅ Found count: {cnt_match.group(1)}")
                
            # Let's save a snippet of the script payloads
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
            print(f"Found {len(scripts)} scripts.")
            for i, s in enumerate(scripts):
                if "resultsCount" in s or "totalCount" in s or "adLibrarySearchResultCount" in s:
                    print(f"Script #{i} contains keywords! Snippet:")
                    print(s[:400])
                    
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_fb_curl_cffi("Masajeador Pistola Muscular"))
