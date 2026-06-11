"""
Scout completo con detalles por fuente:
1. Productos encontrados en TikTok
2. Productos encontrados en Meta Ads
3. Cruce TikTok -> Meta
4. Producto ganador final
"""
import sys, os, asyncio, logging, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

from agents.scout import scrape_tiktok_creative_center, scrape_facebook_ad_library

SEP = "=" * 65

def print_sep(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def print_product(i, p):
    print(f"\n  #{i} | {p.name}")
    print(f"      Fuente     : {p.source}")
    print(f"      Vistas TT  : {p.tiktok_views:,}")
    print(f"      Engagement : {p.ad_engagement_rate:.1%}")
    print(f"      Tendencia  : +{p.trend_growth_pct}%")
    margin = round(p.suggested_price / p.cost, 1) if p.cost > 0 else 0
    print(f"      Costo/Precio: ${p.cost} -> ${p.suggested_price} ({margin}X)")
    print(f"      Buscar Meta: https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={p.name.replace(' ', '+')}&search_type=keyword_unordered")

async def main():
    # ================================================================
    # PASO 1: TIKTOK
    # ================================================================
    print_sep("PASO 1: BUSCANDO PRODUCTOS EN TIKTOK")
    print("  Fuente primaria : RapidAPI TikTok Trends")
    print("  Fallback        : Apify clockworks~free-tiktok-scraper")
    print("\n  Buscando... (puede tardar 1-2 minutos)")

    seasonal = ["heater", "blanket", "warm", "cozy"]
    tiktok_products = await scrape_tiktok_creative_center(seasonal_keywords=seasonal)

    # Separar reales de simulados
    real_tiktok = [p for p in tiktok_products if "simulat" not in p.source and p.source != "tiktok"]
    apify_tiktok = [p for p in tiktok_products if p.source == "tiktok_apify"]
    sim_tiktok   = [p for p in tiktok_products if p.source == "tiktok" or "simulat" in p.source]

    print(f"\n  Total encontrados: {len(tiktok_products)}")
    print(f"    - Via Apify TikTok (REALES) : {len(apify_tiktok)}")
    print(f"    - Via RapidAPI (REALES)     : {len(real_tiktok)}")
    print(f"    - Simulados (fallback)      : {len(sim_tiktok)}")

    if apify_tiktok:
        print("\n  [REALES VIA APIFY TIKTOK]")
        for i, p in enumerate(apify_tiktok, 1):
            print_product(i, p)
    elif real_tiktok:
        print("\n  [REALES VIA RAPIDAPI]")
        for i, p in enumerate(real_tiktok, 1):
            print_product(i, p)
    else:
        print("\n  [SIMULADOS - RapidAPI y Apify sin datos reales esta vez]")
        for i, p in enumerate(sim_tiktok, 1):
            print_product(i, p)

    # ================================================================
    # PASO 2: META ADS (busqueda general)
    # ================================================================
    print_sep("PASO 2: BUSCANDO PRODUCTOS EN META ADS")
    print("  Fuente: Apify facebook-ads-scraper")
    print("  Busqueda: 'trending products' en Chile")
    print("\n  Buscando... (puede tardar 30-60 segundos)")

    meta_products = await scrape_facebook_ad_library("trending products")

    real_meta = [p for p in meta_products if p.source == "facebook"]
    sim_meta  = [p for p in meta_products if p.source != "facebook"]

    print(f"\n  Total encontrados: {len(meta_products)}")
    print(f"    - Anuncios REALES via Apify : {len(real_meta)}")
    print(f"    - Simulados (fallback)      : {len(sim_meta)}")

    if real_meta:
        print("\n  [ANUNCIOS REALES EN META - Top 5]")
        for i, p in enumerate(real_meta[:5], 1):
            print(f"\n  #{i} | {p.name}")
            print(f"      Longevidad anuncio : {p.ad_longevity_days} dias activo")
            print(f"      Impresiones est.   : {p.ad_estimated_impressions:,}")
            print(f"      Precio sugerido    : ${p.suggested_price}")
            if p.ad_snapshot_url:
                print(f"      Link directo Meta  : {p.ad_snapshot_url}")
            print(f"      Buscar en Meta     : https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={p.name.replace(' ', '+')}&search_type=keyword_unordered")

    # ================================================================
    # PASO 3: CRUCE TIKTOK -> META
    # ================================================================
    print_sep("PASO 3: CRUCE - TIKTOK GANADORES vs META ADS")
    print("  Verificando si los top productos de TikTok")
    print("  tienen publicidad activa en Meta Ads...")

    top_tiktok = sorted(tiktok_products, key=lambda p: p.tiktok_views, reverse=True)[:3]
    cruce_resultados = []

    for p in top_tiktok:
        print(f"\n  Buscando '{p.name}' en Meta Ads...")
        meta_validation = await scrape_facebook_ad_library(p.name)
        tiene_meta = any(m.source == "facebook" for m in meta_validation)
        max_lon = max((m.ad_longevity_days for m in meta_validation if m.source == "facebook"), default=0)

        cruce_resultados.append({
            "producto": p,
            "en_meta": tiene_meta,
            "longevidad_max": max_lon,
            "meta_items": [m for m in meta_validation if m.source == "facebook"]
        })

        if tiene_meta:
            print(f"    ENCONTRADO EN META - {max_lon} dias activo")
            print(f"    Buscar: https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={p.name.replace(' ', '+')}&search_type=keyword_unordered")
        else:
            print(f"    NO encontrado en Meta (posible nicho sin competencia)")

    # ================================================================
    # PASO 4: GANADOR FINAL
    # ================================================================
    print_sep("PASO 4: PRODUCTO GANADOR FINAL")

    # Criterio: en ambas plataformas y mayor longevidad en Meta = mas ventas
    con_meta = [r for r in cruce_resultados if r["en_meta"]]
    sin_meta = [r for r in cruce_resultados if not r["en_meta"]]

    if con_meta:
        ganador_data = max(con_meta, key=lambda r: (r["longevidad_max"], r["producto"].tiktok_views))
        criterio = "VALIDADO EN TIKTOK + META ADS (maximo potencial)"
    elif sin_meta:
        ganador_data = max(sin_meta, key=lambda r: r["producto"].tiktok_views)
        criterio = "VIRAL EN TIKTOK sin competencia en Meta (nicho virgen)"
    else:
        print("  No hay datos suficientes para determinar ganador.")
        return

    g = ganador_data["producto"]

    print(f"""
  PRODUCTO GANADOR: {g.name}
  Criterio        : {criterio}

  --- TIKTOK ---
  Vistas          : {g.tiktok_views:,}
  Engagement      : {g.ad_engagement_rate:.1%}
  Tendencia       : +{g.trend_growth_pct}%

  --- META ADS ---
  Publicidad activa: {'SI' if ganador_data['en_meta'] else 'NO'}
  Dias activo max  : {ganador_data['longevidad_max']} dias

  --- NEGOCIO ---
  Costo proveedor  : ${g.cost}
  Precio de venta  : ${g.suggested_price}
  Margen           : {round(g.suggested_price / g.cost, 1) if g.cost > 0 else 0}X

  --- LINKS PARA INVESTIGAR ---
  TikTok Search    : https://www.tiktok.com/search?q={g.name.replace(' ', '+')}
  Meta Ads Library : https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={g.name.replace(' ', '+')}&search_type=keyword_unordered
  AliExpress       : https://www.aliexpress.com/wholesale?SearchText={g.name.replace(' ', '+')}
""")

    print(SEP)
    print("  TODOS LOS PRODUCTOS EN META ADS:")
    for item in ganador_data["meta_items"][:3]:
        print(f"    - {item.name} | {item.ad_longevity_days} dias | {item.ad_snapshot_url or 'sin link'}")
    print(SEP)

if __name__ == "__main__":
    asyncio.run(main())
