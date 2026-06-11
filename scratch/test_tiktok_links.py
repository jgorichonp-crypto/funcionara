"""
Muestra los links directos a los videos de TikTok encontrados
para que puedas ver el producto exacto y buscarlo en Meta.
"""
import sys, os, asyncio, aiohttp, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings

TOKEN = settings.apify_token
ACTOR = "clockworks~free-tiktok-scraper"

QUERIES = ["TikTokMadeMeBuyIt", "AmazonFinds", "HomeHacks"]

async def main():
    run_url = f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={TOKEN}"
    payload = {
        "searchQueries": QUERIES,
        "resultsPerPage": 5,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False
    }

    async with aiohttp.ClientSession() as session:
        print("Lanzando TikTok scraper en Apify...\n")
        async with session.post(run_url, json=payload, timeout=30) as resp:
            data = await resp.json()
            run_id = data.get("data", {}).get("id")
            dataset_id = data.get("data", {}).get("defaultDatasetId")
            status = data.get("data", {}).get("status")
            print(f"Run ID: {run_id} | Dataset: {dataset_id} | Status: {status}")

        # Esperar hasta 60s
        poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={TOKEN}"
        print("Esperando resultados", end="", flush=True)
        for _ in range(15):
            await asyncio.sleep(4)
            print(".", end="", flush=True)
            async with session.get(poll_url) as poll:
                p = await poll.json()
                status = p.get("data", {}).get("status")
                if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
                    break

        print(f"\nStatus: {status}\n")

        if status != "SUCCEEDED":
            print("El actor no termino a tiempo.")
            return

        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={TOKEN}"
        async with session.get(items_url) as resp:
            items = await resp.json()

        SEP = "=" * 65
        print(f"\n{SEP}")
        print(f"  VIDEOS DE TIKTOK ENCONTRADOS ({len(items)} videos reales)")
        print(SEP)

        # Ordenar por vistas
        def get_views(item):
            return item.get("playCount") or item.get("videoPlayCount") or 0

        items_sorted = sorted(items, key=get_views, reverse=True)

        for i, item in enumerate(items_sorted, 1):
            desc = item.get("text") or item.get("desc") or ""
            views = get_views(item)
            likes = item.get("diggCount") or item.get("likeCount") or 0
            comments = item.get("commentCount") or 0
            shares = item.get("shareCount") or 0
            video_url = item.get("webVideoUrl") or ""
            author = (item.get("authorMeta") or {}).get("name") or item.get("authorName") or "?"
            hashtags = [w for w in desc.split() if w.startswith("#")]

            # Engagement rate
            eng = round((likes + comments + shares) / views, 3) if views > 0 else 0

            print(f"\n#{i} {'='*55}")
            print(f"  Descripcion : {desc[:100]}")
            print(f"  Autor       : @{author}")
            print(f"  Vistas      : {views:,}")
            print(f"  Likes       : {likes:,} | Comentarios: {comments:,} | Shares: {shares:,}")
            print(f"  Engagement  : {eng:.1%}")
            print(f"  Hashtags    : {' '.join(hashtags[:5])}")
            print(f"")
            if video_url:
                print(f"  >> VER VIDEO EN TIKTOK:")
                print(f"     {video_url}")
            else:
                print(f"  >> No hay URL directa del video")
            print(f"")
            print(f"  >> BUSCAR ESTE PRODUCTO EN META ADS (despues de ver el video):")
            print(f"     https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&search_type=keyword_unordered")
            print(f"     (usa el nombre del PRODUCTO que ves en el video, no el titulo del video)")

        print(f"\n{SEP}")
        print("  INSTRUCCIONES:")
        print("  1. Haz clic en el link del video de TikTok")
        print("  2. Identifica el producto exacto que se vende")
        print("  3. Ve a Meta Ads Library y busca ese nombre de producto")
        print("  4. Filtra por Chile y Todos los anuncios")
        print(SEP)

asyncio.run(main())
