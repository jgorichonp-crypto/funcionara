import asyncio
import logging
from config import settings
from agents import run_scout_agent
from agents.scout import scrape_tiktok_creative_center, scrape_facebook_ad_library, scrape_aliexpress_trending

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def test_scout():
    # Forzar salto de RapidAPI para evitar esperas de 429
    settings.rapidapi_key = "placeholder"
    
    try:
        # Solo ejecutar el scraping para imprimir los productos y links rápidamente
        print("\n--- INICIANDO SCRAPING RAPIDO ---")
        
        print("\n1. TIKTOK PRODUCTS:")
        tiktok_prods = await scrape_tiktok_creative_center()
        for i, p in enumerate(tiktok_prods):
            print(f"{i+1}. {p.name} | Link: {p.tiktok_video_url or 'N/A'}")
            
        print("\n2. FACEBOOK ADS PRODUCTS:")
        fb_prods = await scrape_facebook_ad_library("trending products")
        for i, p in enumerate(fb_prods):
            print(f"{i+1}. {p.name} | Link Ad: {p.ad_snapshot_url}")
            
        print("\n3. ALIEXPRESS PRODUCTS:")
        ali_prods = await scrape_aliexpress_trending()
        for i, p in enumerate(ali_prods):
            print(f"{i+1}. {p.name} | Link Ali: {p.supplier_url}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scout())
