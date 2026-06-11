import asyncio
import aiohttp
import urllib.parse
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_apify")

async def scrape_facebook_ad_library_apify(keyword: str, apify_token: str) -> list:
    if not apify_token or "your-apify-token" in apify_token.lower() or len(apify_token) < 5:
        logger.warning("⚠️ APIFY_TOKEN no configurado o inválido. Usando fallback simulado para Facebook Ads Library.")
        return []

    encoded_keyword = urllib.parse.quote(keyword)
    search_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={encoded_keyword}&search_type=keyword_unordered"
    
    run_url = f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/runs?token={apify_token}&wait=10"
    payload = {
        "startUrls": [
            { "url": search_url }
        ],
        "resultsLimit": 5
    }
    
    logger.info(f"🚀 Iniciando scraper de Facebook Ads en Apify para: '{keyword}'...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(run_url, json=payload, timeout=20) as response:
                if response.status not in (200, 201):
                    logger.error(f"❌ Error al iniciar Actor en Apify (código {response.status})")
                    return []
                
                res_data = await response.json()
                data = res_data.get("data", {})
                run_id = data.get("id")
                dataset_id = data.get("defaultDatasetId")
                status = data.get("status")
                
                logger.info(f"📡 Actor iniciado. RunID: {run_id} | DatasetID: {dataset_id} | Status: {status}")
                
                # Si no terminó en la espera inicial, hacemos un polling rápido
                if status not in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
                    poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
                    for i in range(5):
                        await asyncio.sleep(3)
                        async with session.get(poll_url) as poll_resp:
                            if poll_resp.status == 200:
                                poll_data = await poll_resp.json()
                                status = poll_data.get("data", {}).get("status")
                                logger.info(f"⏳ Esperando scraper... Estado: {status}")
                                if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
                                    break
                
                if status == "SUCCEEDED" or dataset_id:
                    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}"
                    async with session.get(items_url) as items_resp:
                        if items_resp.status == 200:
                            items = await items_resp.json()
                            logger.info(f"✅ Descargados {len(items)} anuncios reales de Meta Ads Library.")
                            return items
                
                logger.warning(f"⚠️ El scraper no terminó con éxito. Estado final: {status}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Excepción durante la llamada a Apify: {e}")
            return []

async def main():
    # Test fallback
    res = await scrape_facebook_ad_library_apify("Masajeador", "")
    print(f"Fallback results count: {len(res)}")

if __name__ == "__main__":
    asyncio.run(main())
