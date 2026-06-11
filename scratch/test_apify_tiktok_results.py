import asyncio
import aiohttp
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TOKEN = "TU_APIFY_TOKEN"
ACTOR = "clockworks~free-tiktok-scraper"

async def main():
    run_url = f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={TOKEN}"
    payload = {
        "searchQueries": ["TikTokMadeMeBuyIt"],
        "resultsPerPage": 5,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False
    }

    async with aiohttp.ClientSession() as session:
        print(f"Lanzando {ACTOR}...")
        async with session.post(run_url, json=payload, timeout=30) as resp:
            data = await resp.json()
            run_id = data.get("data", {}).get("id")
            dataset_id = data.get("data", {}).get("defaultDatasetId")
            status = data.get("data", {}).get("status")
            print(f"HTTP: {resp.status} | Status: {status} | Run ID: {run_id} | Dataset: {dataset_id}")

        # Esperar hasta 60 segundos
        poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={TOKEN}"
        print("Esperando resultados", end="", flush=True)
        for i in range(15):
            await asyncio.sleep(4)
            print(".", end="", flush=True)
            async with session.get(poll_url) as poll:
                poll_data = await poll.json()
                status = poll_data.get("data", {}).get("status")
                if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
                    break

        print(f"\nStatus final: {status}")

        if status == "SUCCEEDED":
            items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={TOKEN}"
            async with session.get(items_url) as items_resp:
                items = await items_resp.json()
                print(f"\nTotal items recibidos: {len(items)}\n")
                for i, item in enumerate(items[:5]):
                    desc = item.get("text") or item.get("desc") or item.get("description") or ""
                    author = item.get("authorMeta", {}).get("name") or item.get("author", "?")
                    plays = item.get("playCount") or item.get("stats", {}).get("playCount") or "?"
                    likes = item.get("diggCount") or item.get("stats", {}).get("diggCount") or "?"
                    print(f"--- Video #{i+1} ---")
                    print(f"  Texto: {desc[:120]}")
                    print(f"  Autor: {author}")
                    print(f"  Vistas: {plays} | Likes: {likes}")
                    print(f"  Campos disponibles: {list(item.keys())[:10]}")
                    print()
        else:
            print("El actor no terminó a tiempo o fallo.")

asyncio.run(main())
