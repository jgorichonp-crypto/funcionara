import asyncio
import aiohttp
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TOKEN = "TU_APIFY_TOKEN"

KNOWN_ACTORS = [
    "clockworks~tiktok-scraper",
    "clockworks~free-tiktok-scraper",
    "apify~tiktok-scraper",
    "novi~tiktok-scraper",
    "epctex~tiktok-scraper",
    "microworkers~tiktok-search-scraper",
]

async def test_actor(session, actor_id):
    """Intenta lanzar el actor con un payload mínimo y retorna el status HTTP."""
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={TOKEN}"
    payload = {
        "searchQueries": ["TikTokMadeMeBuyIt"],
        "resultsPerPage": 3,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    }
    try:
        async with session.post(url, json=payload, timeout=10) as resp:
            body = await resp.json()
            status = body.get("data", {}).get("status", "?")
            run_id = body.get("data", {}).get("id", "?")
            return resp.status, status, run_id
    except Exception as e:
        return -1, str(e), None

async def main():
    async with aiohttp.ClientSession() as session:
        print("Probando actores de TikTok en Apify...\n")
        for actor in KNOWN_ACTORS:
            http_code, run_status, run_id = await test_actor(session, actor)
            ok = "OK" if http_code in (200, 201) else "FAIL"
            print(f"[{ok}] {actor}")
            print(f"   HTTP: {http_code} | Run Status: {run_status} | Run ID: {run_id}\n")

asyncio.run(main())
