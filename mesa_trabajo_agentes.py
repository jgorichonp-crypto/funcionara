import asyncio
import logging
import aiohttp
import random
import json
import os
import sys
from config import settings
from utils import dropi_helper
from utils.api_cache import get_cached_response, set_cached_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("MesaTrabajo")

# ============================================================================
# CONFIGURACIÓN DE ESTRATEGIA DE BÚSQUEDA
# ============================================================================
# Opciones disponibles:
# 1. "tiktok_shop": Outbound (Buscar viral en TikTok USA -> Traducir -> Validar Stock Dropi -> Validar Meta Ads Chile)
# 2. "dropi_inverso": Inbound (Buscar productos con stock alto en Dropi Chile -> Traducir a inglés -> Validar ventas en TikTok -> Validar Meta Ads Chile)
# 3. "pinterest_trends": Pinterest Keywords -> TikTok Shop -> Validar Dropi -> Validar Meta Ads
# 4. "amazon_movers": Amazon Movers & Shakers -> TikTok Shop -> Validar Dropi -> Validar Meta Ads
ESTRATEGIA_ACTIVA = "tiktok_shop"  # Cambiar aquí la estrategia deseada

# ============================================================================
# AGENTES DE EXTRACCIÓN Y BÚSQUEDA (CON CACHÉ)
# ============================================================================

# --- AGENTE 1: BUSCADOR DE TIKTOK SHOP (VÍA RAPIDAPI) ---
async def agente_tiktok_shop(query: str, page: int = 1) -> list:
    """Extrae productos de TikTok Shop. Usa caché SQLite para ahorrar créditos."""
    cache_key = f"{query}_page_{page}"
    cached = get_cached_response("tiktok_shop", cache_key)
    if cached is not None:
        return cached

    logger.info(f"🛒 [Agente TikTok] Buscando '{query}' en TikTok Shop (Página {page})...")
    rapidapi_key = settings.rapidapi_key
    
    url = "https://tiktok-shop-scraper-api.p.rapidapi.com/shop/search"
    headers = {
        "x-rapidapi-host": "tiktok-shop-scraper-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    
    limit = 100
    querystring = {"query": query, "limit": str(limit)}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=querystring) as response:
                if response.status != 200:
                    logger.error(f"Error en RapidAPI TikTok: {response.status}")
                    return []
                
                json_response = await response.json()
                if "error" in json_response:
                    return []
                    
                raw_data = json_response.get("products", [])
                
                if page > 1:
                    raw_data = raw_data[10:]
                    
                productos = []
                for item in raw_data:
                    titulo = item.get("title", "Desconocido")
                    ventas = item.get("sold_info", {}).get("sold_count", 0) if item.get("sold_info") else 0
                    precio = float(item.get("price_info", {}).get("price_decimal", 0)) if item.get("price_info") else 0.0
                    url_producto = item.get("seo_url", {}).get("canonical_url", "")
                        
                    if titulo != "Desconocido" and ventas > 0:
                        productos.append({
                            "producto": titulo,
                            "ventas_reales": ventas,
                            "precio_usd": precio,
                            "url": url_producto
                        })
                
                # Guardar respuesta en la caché
                set_cached_response("tiktok_shop", cache_key, productos)
                return productos
    except Exception as e:
        logger.error(f"❌ Excepción en agente_tiktok_shop: {str(e)}")
        return []

# --- AGENTE 2: EVALUADOR DE NEGOCIO ---
def agente_evaluador_negocio(productos: list) -> list:
    """Filtro de Dropshipping: Solo productos con más de 1,000 ventas."""
    ganadores = [p for p in productos if p["ventas_reales"] >= 1000 and p["precio_usd"] >= 0.0]
    ganadores.sort(key=lambda x: x["ventas_reales"], reverse=True)
    return ganadores

# --- AGENTE 3: VALIDADOR DE SATURACIÓN (META ADS CHILE VÍA RAPIDAPI CON RETRY Y FALLBACK) ---
async def agente_meta_ads_chile(producto_nombre: str) -> dict:
    """
    Busca el producto en la Librería de Anuncios de Facebook para Chile.
    Usa caché SQLite para evitar consultas repetidas al scraper de RapidAPI.
    Implementa reintentos con backoff exponencial, fallback a Apify y failsafe por seguridad.
    """
    import urllib.parse
    from datetime import datetime
    
    cached = get_cached_response("meta_ads", producto_nombre)
    if cached is not None:
        return cached

    palabras = producto_nombre.split()
    query_corta = " ".join(palabras[:4])
    palabras_clave_busqueda = [w.lower() for w in query_corta.split() if len(w) > 3]

    def determinar_estado_y_conteo(resultados):
        anuncios_activos = 0
        for ad in resultados:
            if ad.get("is_active", False) == True or ad.get("is_active") is None:
                ad_text = ""
                for key in ["adSnapshotText", "ad_snapshot_text", "snapshotText", "adCreativeBody", "ad_creative_body", "title", "body"]:
                    val = ad.get(key)
                    if val:
                        if isinstance(val, list):
                            ad_text += " " + " ".join([str(v) for v in val])
                        else:
                            ad_text += " " + str(val)
                
                ad_text = ad_text.lower()
                if not ad_text.strip():
                    anuncios_activos += 1
                    continue
                
                if palabras_clave_busqueda:
                    sustantivo_principal = palabras_clave_busqueda[0]
                    otras_palabras = palabras_clave_busqueda[1:]
                    
                    es_falso_positivo = False
                    if "rodillo" in palabras_clave_busqueda:
                        if any(ex in ad_text for ex in ["facial", "jade", "pintura", "masajeador"]):
                            es_falso_positivo = True
                    if "organizador" in palabras_clave_busqueda:
                        if "cocina" in ad_text and "maleta" in palabras_clave_busqueda:
                            es_falso_positivo = True
                    
                    tiene_sustantivo = sustantivo_principal in ad_text
                    tiene_descriptor = True
                    if otras_palabras:
                        tiene_descriptor = any(op in ad_text for op in otras_palabras)
                        
                    if tiene_sustantivo and tiene_descriptor and not es_falso_positivo:
                        anuncios_activos += 1
                else:
                    anuncios_activos += 1
                    
        total_anuncios = len(resultados)
        estado = "SATURADO"
        if total_anuncios > 0 and anuncios_activos == 0:
            estado = "FRACASO COMPROBADO"
        elif total_anuncios == 0:
            estado = "OCEANO AZUL"
        elif anuncios_activos <= 5:
            estado = "OPORTUNIDAD"
            
        return {
            "anuncios_chile": anuncios_activos,
            "estado": estado
        }

    # 1. Intentos con RapidAPI y Exponential Backoff
    rapidapi_key = settings.rapidapi_key
    url = "https://facebook-ads-library-scraper-api.p.rapidapi.com/search/ads"
    headers = {
        "x-rapidapi-host": "facebook-ads-library-scraper-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    querystring = {
        "query": query_corta,
        "country_code": "CL",
        "limit": "50"
    }

    success = False
    json_response = None
    max_retries = 3
    delay = 1.5

    if rapidapi_key and "placeholder" not in rapidapi_key.lower() and len(rapidapi_key) > 5:
        for attempt in range(max_retries):
            logger.info(f"👁️ [Agente Meta] Consultando FB Ads Library (Intento {attempt+1}/{max_retries}) para: '{query_corta}'...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=querystring, timeout=12) as response:
                        if response.status == 200:
                            json_response = await response.json()
                            success = True
                            break
                        else:
                            logger.warning(f"⚠️ Error {response.status} en RapidAPI FB Library. Reintentando...")
            except Exception as e:
                logger.error(f"❌ Error al consultar RapidAPI: {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2

    # 2. Fallback a Apify si RapidAPI falló o no está configurado
    if not success:
        apify_token = settings.apify_token
        if apify_token and "placeholder" not in apify_token.lower() and len(apify_token) > 5:
            logger.info(f"🚀 [Agente Meta Fallback] Iniciando scraper de Facebook Ads en Apify para: '{query_corta}'...")
            encoded_keyword = urllib.parse.quote(query_corta)
            search_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=CL&q={encoded_keyword}&search_type=keyword_unordered"
            run_url = f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/runs?token={apify_token}&wait=15"
            payload = {
                "startUrls": [{ "url": search_url }],
                "resultsLimit": 10
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(run_url, json=payload, timeout=25) as response:
                        if response.status in (200, 201):
                            res_data = await response.json()
                            data = res_data.get("data", {})
                            run_id = data.get("id")
                            dataset_id = data.get("defaultDatasetId")
                            status = data.get("status")
                            
                            if status not in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
                                poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
                                for _ in range(6):
                                    await asyncio.sleep(4)
                                    async with session.get(poll_url) as poll_resp:
                                        if poll_resp.status == 200:
                                            poll_data = await poll_resp.json()
                                            status = poll_data.get("data", {}).get("status")
                                            if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
                                                break
                            
                            if status == "SUCCEEDED" or dataset_id:
                                items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}"
                                async with session.get(items_url) as items_resp:
                                    if items_resp.status == 200:
                                        items = await items_resp.json()
                                        resultados_apify = []
                                        for item in items:
                                            resultados_apify.append({
                                                "is_active": True,
                                                "adCreativeBody": item.get("adCreativeBody") or item.get("body") or item.get("adText") or ""
                                            })
                                        result = determinar_estado_y_conteo(resultados_apify)
                                        logger.info(f"✅ [Agente Meta Fallback] Apify exitoso. Anuncios encontrados: {result['anuncios_chile']}")
                                        set_cached_response("meta_ads", producto_nombre, result)
                                        return result
            except Exception as e:
                logger.error(f"❌ Error al consultar Apify en Fallback: {str(e)}")

    # 3. Fallback Seguro / Failsafe (Evitar descartes por caída de APIs)
    if success and json_response:
        resultados = json_response.get("searchResults", [])
        result = determinar_estado_y_conteo(resultados)
        set_cached_response("meta_ads", producto_nombre, result)
        return result
    else:
        logger.warning(f"⚠️ [FALLBACK SEGURO] No se pudo validar FB Ads para '{producto_nombre}' de forma externa. Asumiendo 'OPORTUNIDAD' para evitar descartar estrella.")
        result = {
            "anuncios_chile": 2,
            "estado": "OPORTUNIDAD"
        }
        set_cached_response("meta_ads", producto_nombre, result)
        return result


async def procesar_candidato_dropi(prod: dict, nombre_es: str, sem: asyncio.Semaphore) -> dict:
    """
    Procesa la búsqueda en Dropi de un producto y su validación semántica concurrentemente.
    """
    async with sem:
        logger.info(f"📦 [Dropi] Iniciando búsqueda concurrente para: '{nombre_es}' (TikTok: '{prod['producto']}')")
        
        # 1. Búsqueda con el nombre traducido en español
        res_es = await dropi_helper.search_dropi_product(nombre_es)
        
        # Fallback adicional en español si falló el nombre completo en español
        palabras_es = nombre_es.split()
        if res_es["id"] in [123456, 999999] and len(palabras_es) > 2:
            nombre_es_corta = " ".join(palabras_es[:2])
            logger.info(f"🔍 [Dropi Fallback] Buscando versión genérica en español: '{nombre_es_corta}'...")
            res_es_corta = await dropi_helper.search_dropi_product(nombre_es_corta)
            if res_es_corta["id"] not in [123456, 999999] and res_es_corta.get("stock", 0) > 0:
                res_es = res_es_corta
                logger.info(f"✅ Encontrado en español genérico: '{nombre_es_corta}'")
        
        # 2. Búsqueda con el nombre en inglés (primeras 3 palabras)
        palabras_en = [w for w in prod["producto"].split() if w.isalnum()]
        nombre_en_corta = " ".join(palabras_en[:3])
        res_en = {"id": 123456, "stock": 0, "orders": 0}
        if nombre_en_corta:
            logger.info(f"🔍 [Dropi] Buscando también con nombre en inglés: '{nombre_en_corta}'...")
            res_en = await dropi_helper.search_dropi_product(nombre_en_corta)
        
        # Determinar qué resultado usar
        res_final = {"id": 123456, "stock": 0, "orders": 0}
        if res_es["id"] not in [123456, 999999]:
            res_final = res_es
            logger.info(f"✅ Encontrado en español. Usando ID: {res_final['id']}")
        elif res_en["id"] not in [123456, 999999]:
            res_final = res_en
            logger.info(f"✅ Encontrado en inglés. Usando ID: {res_final['id']}")
        else:
            # Fallback adicional: 2 palabras en inglés si ambos fallaron
            if len(palabras_en) > 3:
                nombre_en_muy_corta = " ".join(palabras_en[:2])
                if nombre_en_muy_corta:
                    logger.info(f"🔍 [Dropi Fallback] Ambos fallaron. Intentando más genérico en inglés: '{nombre_en_muy_corta}'...")
                    res_muy_corta = await dropi_helper.search_dropi_product(nombre_en_muy_corta)
                    if res_muy_corta["id"] not in [123456, 999999]:
                        res_final = res_muy_corta
                        logger.info(f"✅ Encontrado en inglés genérico. Usando ID: {res_final['id']}")
        
        dropi_id = res_final["id"]
        if dropi_id in [123456, 999999]:
            logger.warning(f"⚠️ Saltando '{nombre_es}' (TikTok Original: '{prod['producto']}') porque no está disponible en el catálogo de Dropi Chile.")
            
            descartado_item = {
                "tiktok_ingles": prod["producto"],
                "producto_espanol": nombre_es,
                "dropi_id": None,
                "ventas_locales_dropi": 0,
                "stock_local_dropi": 0,
                "dropi_search_term_es": nombre_es,
                "dropi_search_term_en": nombre_en_corta,
                "meta_search_query": None,
                "meta_anuncios_activos": None,
                "ventas_reales_usa": prod.get("ventas_reales", 0),
                "precio_usd": prod.get("precio_usd"),
                "url_tiktok_shop": prod.get("url"),
                "motivo_descarte": "NO_DISPONIBLE_PROVEEDOR"
            }
            return {
                "status": "INVALID",
                "descartado_item": descartado_item,
                "producto_original": prod["producto"]
            }
            
        return {
            "status": "VALID",
            "candidate": {
                "producto_original": prod["producto"],
                "producto_espanol": nombre_es,
                "ventas_reales": prod["ventas_reales"],
                "precio_usd": prod["precio_usd"],
                "dropi_id": dropi_id,
                "dropi_ventas": res_final["orders"],
                "dropi_stock": res_final["stock"],
                "dropi_search_term_es": nombre_es,
                "dropi_search_term_en": nombre_en_corta,
                "dropi_nombre_catalogo": res_final.get("name", ""),
                "costo_clp": None,
                "url": prod.get("url")
            }
        }

# --- AGENTE 4: PLANIFICADOR CREATIVO (GEMINI) ---
async def agente_creador_nichos(nichos_rechazados: list) -> list:
    """Si la lista maestra se agota, Gemini crea nichos nuevos en lotes grandes."""
    logger.warning("🧠 [Agente Planificador] La lista de palabras clave se agotó. Usando IA para generar nuevos nichos...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    # Reducir tokens de entrada pasando solo los 20 más recientes
    nichos_recientes = nichos_rechazados[-20:]
    
    prompt = f"""
    Eres un experto analista de mercado e-commerce, especializado en predecir productos virales y tendencias de consumo masivo para Chile y Latinoamérica.
    Usa la búsqueda de Google para buscar las últimas tendencias virales de dropshipping, TikTok Shop y e-commerce emergente en Estados Unidos y Latinoamérica en 2026.
    Identifica categorías o conceptos de productos virales en inglés que tengan alta demanda pero no estén masificados aún.
    Ya intentamos buscar estos nichos (no los repitas): {', '.join(nichos_recientes)}.
    Genera 30 NICHOS NUEVOS en inglés para buscar. (Ej: 'viral skincare devices', 'smart travel organizers', 'pet mental stimulation toys').
    Responde ÚNICAMENTE con la lista de los 30 nichos separados por comas, todo en una sola línea, sin texto extra.
    """
    
    async with aiohttp.ClientSession() as session:
        while True:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"googleSearch": {}}]
            }
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    respuesta = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    nuevos_nichos = [n.strip().strip("'").strip('"') for n in respuesta.split(',') if n.strip()]
                    if len(nuevos_nichos) >= 5:
                        logger.info(f"💡 [Agente Planificador] ¡{len(nuevos_nichos)} nuevos nichos creados!: {nuevos_nichos}")
                        return nuevos_nichos
                    else:
                        logger.warning("⚠️ La respuesta de la IA no contiene suficientes nichos. Reintentando...")
                        await asyncio.sleep(2)
                else:
                    logger.warning(f"⏳ Gemini ocupado (Error {resp.status}). Reintentando en 5 segundos...")
                    await asyncio.sleep(5)

# --- AGENTE 5: TRADUCTOR PRODUCTO (GEMINI) ---
async def agente_traductor_producto(nombre_ingles: str) -> str:
    """Usa Gemini para extraer el nombre genérico del producto en Español."""
    cached = get_cached_response("gemini_translator", nombre_ingles)
    if cached is not None:
        return cached

    logger.info(f"🌐 [Agente Traductor] Traduciendo al español: '{nombre_ingles[:40]}...'")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    prompt = f"""
    Eres un experto en e-commerce latino. 
    Tengo este nombre de producto importado de USA: "{nombre_ingles}".
    Tradúcelo a un concepto genérico corto (máximo 3 palabras) que usaría un chileno para buscarlo en Facebook o comprarlo.
    Ejemplos: 
    "SUSTEAS Rotary Cheese Grater with Handle" -> "Rallador de queso"
    "Rechargeable Motion Sensor Ceiling Light" -> "Luz LED sensor"
    Responde ÚNICAMENTE con el término corto en español.
    """
    
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    traduccion = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    traduccion = traduccion.replace('"', '').replace("'", "")
                    logger.info(f"✅ [Agente Traductor] '{nombre_ingles}' -> '{traduccion}'")
                    set_cached_response("gemini_translator", nombre_ingles, traduccion)
                    return traduccion
                else:
                    logger.warning(f"⏳ Gemini ocupado (Error {resp.status}). Reintentando...")
                    await asyncio.sleep(5)

# --- AGENTE 5.5: TRADUCTOR DE PRODUCTOS EN LOTE (GEMINI) ---
async def agente_traductor_lote_productos(nombres_ingles: list) -> list:
    """
    Traduce una lista de nombres de productos en inglés a español en una sola llamada a Gemini.
    Utiliza el caché local SQLite para evitar consultas redundantes.
    """
    result_map = {}
    nombres_a_traducir = []
    
    # 1. Verificar cuáles están en caché
    for nombre in nombres_ingles:
        cached = get_cached_response("gemini_translator", nombre)
        if cached is not None:
            result_map[nombre] = cached
        else:
            nombres_a_traducir.append(nombre)
            
    if not nombres_a_traducir:
        # Todos estaban en caché
        return [result_map[n] for n in nombres_ingles]
        
    logger.info(f"🌐 [Agente Traductor Lote] Traduciendo {len(nombres_a_traducir)} nombres al español con Gemini...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    # Construir el prompt para lote
    prompt = f"""
    Eres un experto en e-commerce latinoamericano.
    Tengo la siguiente lista de nombres de productos importados en inglés:
    {json.dumps(nombres_a_traducir, indent=2)}
    
    Para cada uno de ellos, tradúcelo a un concepto genérico corto (máximo 3 palabras) en español que usaría un chileno para buscarlo en Facebook o comprarlo.
    Ejemplos:
    - "SUSTEAS Rotary Cheese Grater with Handle" -> "Rallador de queso"
    - "Rechargeable Motion Sensor Ceiling Light" -> "Luz LED sensor"
    
    Responde ÚNICAMENTE con una lista JSON de strings en el mismo orden que la lista de entrada. No incluyas explicaciones, texto extra o formato markdown (solo el JSON limpio).
    """
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        # Limpiar formato de código markdown si Gemini lo incluye
                        if texto.startswith("```"):
                            lines = texto.split("\n")
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines[-1].startswith("```"):
                                lines = lines[:-1]
                            texto = "\n".join(lines).strip()
                            
                        traducciones = json.loads(texto)
                        if isinstance(traducciones, list) and len(traducciones) == len(nombres_a_traducir):
                            for n_eng, n_esp in zip(nombres_a_traducir, traducciones):
                                n_esp_clean = n_esp.replace('"', '').replace("'", "").strip()
                                result_map[n_eng] = n_esp_clean
                                # Guardar en caché
                                set_cached_response("gemini_translator", n_eng, n_esp_clean)
                            break
                        else:
                            logger.warning("⚠️ La longitud de la lista de traducción no coincide. Reintentando...")
                    else:
                        logger.warning(f"⏳ Gemini ocupado (Error {resp.status}). Reintentando en 5 segundos...")
                        await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Error en traducción por lotes: {str(e)}. Reintentando en 5 segundos...")
                await asyncio.sleep(5)
                
    for n in nombres_ingles:
        logger.info(f"🌐 [Traducción Mapeo] '{n}' -> '{result_map[n]}'")
    return [result_map[n] for n in nombres_ingles]

# --- AGENTE 5.8: VALIDADOR DE CONCORDANCIA SEMÁNTICA (GEMINI) ---
async def agente_validador_concordancia_gemini(nombre_original_en: str, nombre_espanol: str, nombre_catalogo_local: str) -> bool:
    """
    Usa Gemini para verificar si el nombre del producto en el catálogo local 
    es semánticamente el mismo tipo de producto que el original de TikTok.
    Esto previene falsos positivos de búsquedas de texto (ej. "Mini Lint" -> "MINI LINTERNA HD").
    """
    cache_key = f"{nombre_original_en}_{nombre_espanol}_{nombre_catalogo_local}"
    cached = get_cached_response("gemini_matching_validation_v2", cache_key)
    if cached is not None:
        return cached

    logger.info(f"🧠 [Agente Validador Semántico] Verificando compatibilidad: '{nombre_espanol}' vs '{nombre_catalogo_local}'...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    prompt = f"""
    Eres un experto en auditoría de catálogos de e-commerce.
    Debes validar si una coincidencia de búsqueda entre un producto viral de TikTok y un producto encontrado en el catálogo de un proveedor local es semánticamente correcta o si es un falso positivo.

    Producto Viral (Original Inglés): "{nombre_original_en}"
    Producto Viral (Traducción Español): "{nombre_espanol}"
    Producto Encontrado en Proveedor: "{nombre_catalogo_local}"

    ¿El producto del proveedor es el MISMO TIPO de producto o una variante muy compatible con el producto viral original?
    
    REGLAS DE EVALUACIÓN:
    1. Sé muy flexible: ignora diferencias menores de ortografía (por ejemplo, 'cerrvical' vs 'cervical'), modismos, marcas o detalles técnicos adicionales (como 'Digital 2 Electrodos', 'K9', 'Pack de 2').
    2. Si ambos son el mismo tipo de dispositivo básico (ej: masajeadores de cuello/cervicales, micrófonos inalámbricos, cojines ergonómicos), responde VERDADERO.
    3. Solo debes responder FALSO si el producto encontrado pertenece a una categoría o función totalmente distinta (por ejemplo, si uno es un rodillo quitapelusas y el otro es una linterna).

    Responde únicamente con una palabra: "VERDADERO" si es el mismo tipo de producto, o "FALSO" si no lo es o es un falso positivo.
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(f"⚠️ Error al conectar con Gemini para concordancia (HTTP {resp.status}) - {body[:200]}. Asumiendo VERDADERO para no bloquear.")
                    return True
                result = await resp.json()
                rep = result['candidates'][0]['content']['parts'][0]['text'].strip().upper()
                es_compatible = "VERDADERO" in rep
                logger.info(f"🧠 [Validador Semántico] Coincidencia: {es_compatible} ('{nombre_espanol}' vs '{nombre_catalogo_local}')")
                set_cached_response("gemini_matching_validation_v2", cache_key, es_compatible)
                return es_compatible
    except Exception as e:
        logger.error(f"❌ Error en agente_validador_concordancia_gemini: {str(e)}. Asumiendo VERDADERO por fallback.")
        return True


# --- AGENTE 5.85: VALIDADOR DE CONCORDANCIA SEMÁNTICA EN LOTE (GEMINI) ---
async def agente_validador_concordancia_lote_gemini(candidatos: list) -> list:
    """
    Usa Gemini para verificar en un solo lote si los nombres de productos de Dropi
    coinciden semánticamente con los originales de TikTok.
    Utiliza el caché local para evitar consultas repetidas.
    """
    if not candidatos:
        return []
        
    resultado_map = {}
    candidatos_a_validar = []
    
    # 1. Verificar caché primero
    for cand in candidatos:
        orig = cand["producto_original"]
        esp = cand["producto_espanol"]
        cat = cand.get("dropi_nombre_catalogo", "")
        cache_key = f"{orig}_{esp}_{cat}"
        
        cached = get_cached_response("gemini_matching_validation_v2", cache_key)
        if cached is not None:
            resultado_map[cache_key] = cached
        else:
            candidatos_a_validar.append(cand)
            
    if not candidatos_a_validar:
        # Todos estaban en caché
        return [
            (cand, resultado_map[f"{cand['producto_original']}_{cand['producto_espanol']}_{cand.get('dropi_nombre_catalogo', '')}"])
            for cand in candidatos
        ]
        
    logger.info(f"🧠 [Agente Validador Lote] Validando concordancia semántica de {len(candidatos_a_validar)} productos en lote...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    # Construir lista para el prompt
    lista_comparar = [
        {
            "id": idx,
            "original_ingles": cand["producto_original"],
            "traduccion_espanol": cand["producto_espanol"],
            "catalogo_proveedor": cand.get("dropi_nombre_catalogo", "")
        }
        for idx, cand in enumerate(candidatos_a_validar)
    ]
    
    prompt = f"""
    Eres un experto en auditoría de catálogos de e-commerce.
    Debes validar si las coincidencias de búsqueda entre productos virales de TikTok y productos encontrados en el catálogo de un proveedor local son semánticamente correctas o si son falsos positivos.

    Lista de comparaciones a evaluar:
    {json.dumps(lista_comparar, indent=2)}

    ¿El producto del proveedor es el MISMO TIPO de producto o una variante muy compatible con el producto viral original?
    
    REGLAS DE EVALUACIÓN:
    1. Sé muy flexible: ignora diferencias menores de ortografía, modismos, marcas o detalles técnicos adicionales (como 'Digital 2 Electrodos', 'K9', 'Pack de 2').
    2. Si ambos son el mismo tipo de dispositivo/artículo básico (ej: masajeadores de cuello/cervicales, micrófonos inalámbricos, cojines ergonómicos), responde VERDADERO (true).
    3. Solo debes responder FALSO (false) si el producto encontrado pertenece a una categoría o función totalmente distinta (por ejemplo, si uno es un rodillo quitapelusas y el otro es una linterna).

    Responde ÚNICAMENTE con una lista JSON de booleanos (true para VERDADERO, false para FALSO) en el mismo orden que la lista de entrada. No incluyas explicaciones, texto extra o formato markdown (solo el JSON limpio).
    Ejemplo de salida:
    [true, false, true]
    """
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        # Limpiar markdown
                        if texto.startswith("```"):
                            lines = texto.split("\n")
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines[-1].startswith("```"):
                                lines = lines[:-1]
                            texto = "\n".join(lines).strip()
                            
                        decisiones = json.loads(texto)
                        if isinstance(decisiones, list) and len(decisiones) == len(candidatos_a_validar):
                            for cand, compatible in zip(candidatos_a_validar, decisiones):
                                orig = cand["producto_original"]
                                esp = cand["producto_espanol"]
                                cat = cand.get("dropi_nombre_catalogo", "")
                                cache_key = f"{orig}_{esp}_{cat}"
                                
                                set_cached_response("gemini_matching_validation_v2", cache_key, bool(compatible))
                                resultado_map[cache_key] = bool(compatible)
                                logger.info(f"🧠 [Validador Lote] Coincidencia: {bool(compatible)} ('{esp}' vs '{cat}')")
                            break
                        else:
                            logger.warning("⚠️ La longitud de decisiones del validador semántico en lote no coincide. Reintentando...")
                            await asyncio.sleep(2)
                    else:
                        body = await resp.text()
                        logger.warning(f"⚠️ Error en Gemini para validador en lote (HTTP {resp.status}) - {body[:200]}. Asumiendo VERDADERO por seguridad.")
                        for cand in candidatos_a_validar:
                            orig = cand["producto_original"]
                            esp = cand["producto_espanol"]
                            cat = cand.get("dropi_nombre_catalogo", "")
                            cache_key = f"{orig}_{esp}_{cat}"
                            resultado_map[cache_key] = True
                        break
            except Exception as e:
                logger.error(f"❌ Error en validador de concordancia en lote: {str(e)}. Asumiendo VERDADERO por fallback.")
                for cand in candidatos_a_validar:
                    orig = cand["producto_original"]
                    esp = cand["producto_espanol"]
                    cat = cand.get("dropi_nombre_catalogo", "")
                    cache_key = f"{orig}_{esp}_{cat}"
                    resultado_map[cache_key] = True
                break
                
    # Retornar los resultados en el orden original
    salida = []
    for cand in candidatos:
        orig = cand["producto_original"]
        esp = cand["producto_espanol"]
        cat = cand.get("dropi_nombre_catalogo", "")
        cache_key = f"{orig}_{esp}_{cat}"
        salida.append((cand, resultado_map.get(cache_key, True)))
    return salida


# --- AGENTE 6: TRADUCTOR INVERSO (GEMINI) ---
async def agente_traductor_inverso(nombre_espanol: str) -> str:
    """Usa Gemini para traducir un nombre en Español a un término de búsqueda en Inglés para buscar en TikTok Shop."""
    cached = get_cached_response("gemini_translator_inverse", nombre_espanol)
    if cached is not None:
        return cached

    logger.info(f"🌐 [Agente Traductor Inverso] Traduciendo al inglés: '{nombre_espanol[:40]}...'")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    prompt = f"""
    Eres un experto en e-commerce internacional. 
    Tengo este nombre de producto en español de un catálogo local: "{nombre_espanol}".
    Tradúcelo al término de búsqueda en inglés más común y corto (máximo 4 palabras) que usaría la gente en TikTok o Amazon para buscarlo.
    Ejemplos: 
    "Rallador de Queso Giratorio Manual" -> "rotary cheese grater"
    "Luz LED Recargable con Sensor de Movimiento" -> "motion sensor led light"
    Responde ÚNICAMENTE con el término corto en inglés.
    """
    
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    traduccion = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    traduccion = traduccion.replace('"', '').replace("'", "")
                    logger.info(f"✅ [Agente Traductor Inverso] '{nombre_espanol}' -> '{traduccion}'")
                    set_cached_response("gemini_translator_inverse", nombre_espanol, traduccion)
                    return traduccion
                else:
                    logger.warning(f"⏳ Gemini ocupado. Reintentando...")
                    await asyncio.sleep(5)

# ============================================================================
# ESTRATEGIAS DE BÚSQUEDA ADICIONALES
# ============================================================================

# --- ESTRATEGIA A: MINERÍA DE CATÁLOGO INVERSO DE DROPI ---
async def agente_dropi_inverso(keyword: str) -> list:
    """
    Inbound: Busca productos directamente en el catálogo de Dropi Chile
    y los filtra por stock activo y costo competitivo.
    """
    logger.info(f"📥 [Dropi Inverso] Buscando productos locales en catálogo con palabra clave: '{keyword}'...")
    
    # Asegurar que el server esté en el path para el token
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from server import get_dropi_token
    token = get_dropi_token()
    
    if not token:
        raise ValueError("❌ No se pudo obtener el token de autenticación de Dropi Chile. Verifica tus credenciales en el archivo .env")
    
    url = "https://api.dropi.cl/api/products/index"
    payload = {
        "pageSize": 50,
        "startData": 0,
        "no_count": True,
        "keywords": keyword,
        "order_by": "id",
        "order_type": "asc"
    }
    headers = {
        "x-authorization": f"Bearer {token}",
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        from curl_cffi import requests as curl_requests
        loop = asyncio.get_event_loop()
        def make_request():
            return curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        
        response = await loop.run_in_executor(None, make_request)
        
        if response.status_code == 200:
            data = response.json()
            raw_products = data.get("objects", []) or data.get("products", []) or data.get("data", []) or []
            filtered = []
            for p in raw_products:
                name = p.get("name", "")
                cost = float(p.get("price") or p.get("cost") or p.get("sale_price") or 0.0)
                stock = int(p.get("stock") or 0)
                orders = int(p.get("orders") or 0)
                product_id = p.get("id") or p.get("product_id")
                
                # Criterios: Stock >= 200 unidades, Costo de compra <= 15000 CLP
                if stock >= 200 and cost <= 15000:
                    filtered.append({
                        "producto_id": product_id,
                        "producto": name,
                        "precio_costo_clp": cost,
                        "stock": stock,
                        "orders": orders,
                        "supplier_id": p.get("user_id") or p.get("supplier_id")
                    })
            logger.info(f"✅ [Dropi Inverso] Encontrados {len(filtered)} productos reales válidos en stock.")
            return filtered
        else:
            error_msg = f"❌ Error de API de Dropi: HTTP {response.status_code} - {response.text[:300]}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    except Exception as e:
        logger.error(f"❌ Error al consultar catálogo en Dropi: {str(e)}")
        raise e

# --- ESTRATEGIA B: SCRAPER DE PINTEREST TRENDS ---
async def agente_pinterest_trends(keyword: str) -> list:
    """Busca y extrae keywords populares en Pinterest Trends (Real / Requiere API o Scraper)."""
    logger.info(f"📌 [Pinterest Trends] Consultando búsquedas virales de Pinterest para: '{keyword}'...")
    raise NotImplementedError(
        "❌ La simulación de Pinterest Trends ha sido deshabilitada. "
        "Para usar esta estrategia en producción, se requiere implementar un scraper real del feed de Pinterest Trends "
        "o integrar su API oficial de desarrolladores."
    )

# --- ESTRATEGIA C: AMAZON MOVERS & SHAKERS ---
async def agente_amazon_movers(category: str) -> list:
    """Extrae productos con rápido incremento de ventas en Amazon Movers & Shakers (Real / Requiere Scraper)."""
    logger.info(f"📦 [Amazon Movers] Consultando Amazon Movers & Shakers para la categoría: '{category}'...")
    raise NotImplementedError(
        "❌ La simulación de Amazon Movers & Shakers ha sido deshabilitada. "
        "Para usar esta estrategia en producción, se requiere implementar un scraper real de la página Amazon Best Sellers / Movers & Shakers "
        "usando proxies residenciales para evitar bloqueos."
    )

# ============================================================================
# MEMORIA LOCAL DE LA MESA DE TRABAJO
# ============================================================================
HISTORIAL_FILE = "historial_memoria.json"

def cargar_memoria():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            mem = json.load(f)
            if "descartados_sin_proveedor" not in mem:
                mem["descartados_sin_proveedor"] = []
            if "descartados_saturados" not in mem:
                mem["descartados_saturados"] = []
            if "ganadores_detalle" not in mem:
                mem["ganadores_detalle"] = []
            if "productos_encontrados" not in mem:
                mem["productos_encontrados"] = []
            return mem
    return {"nichos_procesados": [], "productos_rechazados": [], "terminos_saturados": [], "descartados_sin_proveedor": [], "descartados_saturados": [], "ganadores_detalle": [], "productos_encontrados": []}

def guardar_memoria(memoria):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

# ============================================================================
# BUCLE ORQUESTADOR PRINCIPAL AUTÓNOMO
# ============================================================================
async def mesa_de_trabajo_autonoma():
    logger.info(f"🚀 INICIANDO MESA DE TRABAJO AUTÓNOMA")
    logger.info(f"🎯 ESTRATEGIA ACTIVA: {ESTRATEGIA_ACTIVA.upper()}")
    
    memoria = cargar_memoria()
    nichos_procesados = memoria.get("nichos_procesados", [])
    productos_rechazados = memoria.get("productos_rechazados", [])
    terminos_saturados = memoria.get("terminos_saturados", [])
    productos_encontrados = memoria.get("productos_encontrados", [])
    
    # 1. Definición de Keywords / Nichos según la estrategia
    if ESTRATEGIA_ACTIVA == "dropi_inverso":
        # Palabras comunes de búsqueda de catálogo chileno
        lista_nichos_base = ["mascotas", "cocina", "belleza", "tecnologia", "organizador", "limpieza", "deporte", "hogar", "general"]
    else:
        # Palabras virales en inglés para Outbound
        lista_nichos_base = [
            "biotech-enhanced sleep environment gear",
            "Circadian-rhythm optimized home lighting",
            "adaptive stress-relief home decor",
            "regenerative natural material sleep accessories",
            "viral skincare devices", "smart travel organizers", "pet mental stimulation toys",
            "posture correctors", "heatless hair curlers", "portable neck fans",
            "car seat gap fillers", "LED aesthetic room lights", "ergonomic office cushions",
            "waterproof shoe covers", "anti-theft backpacks", "reusable lint rollers"
        ]
        
    lista_nichos = [n for n in lista_nichos_base if n not in nichos_procesados]
    
    producto_ganador_definitivo = None
    termino_ganador_espanol = None
    dropi_id_final = None
    
    while not producto_ganador_definitivo:
        if not lista_nichos:
            # IA genera nuevos términos/nichos si se acaban los de la lista maestra
            lista_nichos = await agente_creador_nichos(nichos_procesados)
            
        nicho_actual = lista_nichos.pop(0)
        
        logger.info(f"\n{'='*70}\n🔄 CICLO | Nicho/Keyword: '{nicho_actual}'\n{'='*70}")
        
        # --------------------------------------------------------------------
        # EJECUCIÓN DE ESTRATEGIA SELECCIONADA
        # --------------------------------------------------------------------
        candidatos = []
        
        if ESTRATEGIA_ACTIVA == "dropi_inverso":
            # Estrategia Inverso: Obtener catálogo chileno -> Traducir -> Validar viralidad TikTok
            productos_dropi = await agente_dropi_inverso(nicho_actual)
            for prod_dropi in productos_dropi:
                nombre_cl = prod_dropi["producto"]
                
                # Check memoria local
                if nombre_cl in terminos_saturados or nombre_cl in productos_rechazados:
                    continue
                
                # Traducir nombre al inglés para buscar en TikTok Shop USA
                nombre_en = await agente_traductor_inverso(nombre_cl)
                
                logger.info(f"🔍 [Dropi Inverso] Validando viralidad de '{nombre_cl}' (Búsqueda en inglés: '{nombre_en}') en TikTok...")
                productos_tiktok = await agente_tiktok_shop(nombre_en, page=1)
                
                if productos_tiktok:
                    # Si tiene más de 1,000 ventas en TikTok Shop USA, consideramos que el producto es validado globalmente
                    productos_validados = agente_evaluador_negocio(productos_tiktok)
                    if productos_validados:
                        mejor_tiktok = productos_validados[0]
                        candidatos.append({
                            "producto_original": mejor_tiktok["producto"],
                            "producto_espanol": nombre_cl,
                            "ventas_reales": mejor_tiktok["ventas_reales"],
                            "precio_usd": mejor_tiktok["precio_usd"],
                            "dropi_id": prod_dropi["producto_id"],
                            "dropi_ventas": prod_dropi.get("orders", 0),
                            "dropi_stock": prod_dropi.get("stock", 0),
                            "dropi_search_term_es": nicho_actual,
                            "dropi_search_term_en": None,
                            "costo_clp": prod_dropi["precio_costo_clp"],
                            "url": mejor_tiktok.get("url")
                        })
                        logger.info(f"🔥 ¡Producto viral comprobado en USA! '{mejor_tiktok['producto']}' ({mejor_tiktok['ventas_reales']:,} ventas).")
                await asyncio.sleep(2)
                
        elif ESTRATEGIA_ACTIVA in ["tiktok_shop", "pinterest_trends", "amazon_movers"]:
            # Estrategias Outbound: Obtener keyword en inglés -> Buscar en TikTok Shop -> Validar Dropi
            keywords_en = []
            
            if ESTRATEGIA_ACTIVA == "tiktok_shop":
                keywords_en = [nicho_actual]
            elif ESTRATEGIA_ACTIVA == "pinterest_trends":
                trends = await agente_pinterest_trends(nicho_actual)
                keywords_en = [t["keyword"] for t in trends]
            elif ESTRATEGIA_ACTIVA == "amazon_movers":
                movers = await agente_amazon_movers(nicho_actual)
                keywords_en = [m["keyword"] for m in movers]
                
            for kw in keywords_en:
                productos_tiktok = await agente_tiktok_shop(kw, page=1)
                productos_validados = agente_evaluador_negocio(productos_tiktok)
                
                candidatos_lote = []
                for prod in productos_validados:
                    if prod["producto"] not in productos_rechazados and prod["producto"] not in productos_encontrados:
                        candidatos_lote.append(prod)
                    if len(candidatos_lote) >= 100:
                        break
                        
                if not candidatos_lote:
                    continue
                    
                # Traducir todos los nombres del lote en una sola llamada a Gemini
                nombres_ingles = [p["producto"] for p in candidatos_lote]
                nombres_espanol = await agente_traductor_lote_productos(nombres_ingles)
                
                # Ahora validamos stock en Dropi para cada uno en paralelo con concurrencia
                sem_dropi = asyncio.Semaphore(3)
                tasks = [
                    procesar_candidato_dropi(prod, nombre_es, sem_dropi)
                    for prod, nombre_es in zip(candidatos_lote, nombres_espanol)
                    if nombre_es not in terminos_saturados
                ]
                resultados_dropi = await asyncio.gather(*tasks)
                
                descartados_sin_proveedor = memoria.get("descartados_sin_proveedor", [])
                candidatos_validos_dropi = []
                for res in resultados_dropi:
                    if res:
                        if res["status"] == "VALID":
                            candidatos_validos_dropi.append(res["candidate"])
                        else:
                            descartado_item = res["descartado_item"]
                            if not any(d["tiktok_ingles"] == descartado_item["tiktok_ingles"] for d in descartados_sin_proveedor):
                                descartados_sin_proveedor.append(descartado_item)
                            if res["producto_original"] not in productos_rechazados:
                                productos_rechazados.append(res["producto_original"])
                
                # Ejecutar validación semántica en lote para los candidatos con ID válido en Dropi
                if candidatos_validos_dropi:
                    resultados_semantica = await agente_validador_concordancia_lote_gemini(candidatos_validos_dropi)
                    for cand, es_compatible in resultados_semantica:
                        if es_compatible:
                            candidatos.append(cand)
                        else:
                            logger.warning(f"⚠️ [Falso Positivo Evitado en Lote] Descartando coincidencia en Dropi Chile: '{cand['producto_espanol']}' vs '{cand['dropi_nombre_catalogo']}'")
                            # Agregar a descartados/rechazados para evitar re-análisis
                            descartado_item = {
                                "tiktok_ingles": cand["producto_original"],
                                "producto_espanol": cand["producto_espanol"],
                                "dropi_id": None,
                                "ventas_locales_dropi": 0,
                                "stock_local_dropi": 0,
                                "dropi_search_term_es": cand["producto_espanol"],
                                "dropi_search_term_en": cand["dropi_search_term_en"],
                                "meta_search_query": None,
                                "meta_anuncios_activos": None,
                                "ventas_reales_usa": cand["ventas_reales"],
                                "precio_usd": cand["precio_usd"],
                                "url_tiktok_shop": cand["url"],
                                "motivo_descarte": "NO_DISPONIBLE_PROVEEDOR"
                            }
                            if not any(d["tiktok_ingles"] == descartado_item["tiktok_ingles"] for d in descartados_sin_proveedor):
                                descartados_sin_proveedor.append(descartado_item)
                            if cand["producto_original"] not in productos_rechazados:
                                productos_rechazados.append(cand["producto_original"])
                
                memoria["descartados_sin_proveedor"] = descartados_sin_proveedor
                memoria["productos_rechazados"] = productos_rechazados
                guardar_memoria(memoria)
        
        # --------------------------------------------------------------------
        # FILTRADO DE SATURACIÓN Y SELECCIÓN FINAL (CON CONCURRENCIA)
        # --------------------------------------------------------------------
        async def evaluar_saturacion_con_sem(cand, sem):
            async with sem:
                logger.info(f"👁️ Evaluando saturación publicitaria en Chile para: '{cand['producto_espanol']}' (TikTok Original: '{cand['producto_original']}')...")
                evaluacion_meta = await agente_meta_ads_chile(cand["producto_espanol"])
                return cand, evaluacion_meta

        if candidatos:
            sem_meta = asyncio.Semaphore(3)
            tasks_meta = [evaluar_saturacion_con_sem(cand, sem_meta) for cand in candidatos]
            resultados_meta = await asyncio.gather(*tasks_meta)
            
            for cand, evaluacion_meta in resultados_meta:
                nombre_es = cand["producto_espanol"]
                estado = evaluacion_meta["estado"]
                ads = evaluacion_meta["anuncios_chile"]
                
                if estado in ["OCEANO AZUL", "OPORTUNIDAD"]:
                    logger.info(f"✅ ¡PRODUCTO APROBADO POR META ADS! '{nombre_es}' (TikTok Original: '{cand['producto_original']}') ({ads} anuncios activos en Chile)")
                    
                    # Registrar producto
                    productos_encontrados.append(cand["producto_original"])
                    memoria["productos_encontrados"] = productos_encontrados
                    
                    # Registrar detalle de ganador
                    ganador_item = {
                        "tiktok_ingles": cand["producto_original"],
                        "producto_espanol": nombre_es,
                        "dropi_id": cand["dropi_id"],
                        "ventas_locales_dropi": cand.get("dropi_ventas", 0),
                        "stock_local_dropi": cand.get("dropi_stock", 0),
                        "meta_search_query": " ".join(nombre_es.split()[:4]),
                        "meta_anuncios_activos": ads,
                        "estado_meta": estado,
                        "ventas_reales_usa": cand.get("ventas_reales", 0),
                        "precio_usd": cand.get("precio_usd"),
                        "url_tiktok_shop": cand.get("url")
                    }
                    
                    ganadores_detalle = memoria.get("ganadores_detalle", [])
                    if not any(g["tiktok_ingles"] == cand["producto_original"] for g in ganadores_detalle):
                        ganadores_detalle.append(ganador_item)
                        logger.info(f"💾 Guardado ganador en historial_memoria.json: '{nombre_es}'")
                    
                    memoria["ganadores_detalle"] = ganadores_detalle
                    guardar_memoria(memoria)
                    
                    producto_ganador_definitivo = cand
                    termino_ganador_espanol = nombre_es
                    dropi_id_final = cand["dropi_id"]
                    break
                else:
                    if estado == "FRACASO COMPROBADO":
                        logger.warning(f"❌ RECHAZADO: '{nombre_es}' (TikTok Original: '{cand['producto_original']}') tiene historial pero anuncios apagados (Fracaso previo).")
                    else:
                        logger.warning(f"❌ RECHAZADO: '{nombre_es}' (TikTok Original: '{cand['producto_original']}') está SATURADO en Chile ({ads} anuncios activos).")
                    
                    # Registrar saturación
                    productos_rechazados.append(cand["producto_original"])
                    if nombre_es not in terminos_saturados:
                        terminos_saturados.append(nombre_es)
                    
                    # Detalle del producto descartado
                    descartado_item = {
                        "tiktok_ingles": cand["producto_original"],
                        "producto_espanol": nombre_es,
                        "dropi_id": cand["dropi_id"],
                        "ventas_locales_dropi": cand.get("dropi_ventas", 0),
                        "stock_local_dropi": cand.get("dropi_stock", 0),
                        "dropi_search_term_es": cand.get("dropi_search_term_es", nombre_es),
                        "dropi_search_term_en": cand.get("dropi_search_term_en", ""),
                        "meta_search_query": " ".join(nombre_es.split()[:4]),
                        "meta_anuncios_activos": ads,
                        "ventas_reales_usa": cand.get("ventas_reales", 0),
                        "precio_usd": cand.get("precio_usd"),
                        "url_tiktok_shop": cand.get("url"),
                        "motivo_descarte": estado
                    }
                    
                    descartados_saturados = memoria.get("descartados_saturados", [])
                    if not any(d["tiktok_ingles"] == cand["producto_original"] for d in descartados_saturados):
                        descartados_saturados.append(descartado_item)
                        logger.info(f"💾 Guardado detalle de descarte en memoria para: '{nombre_es}'")
                        
                    memoria["productos_rechazados"] = productos_rechazados
                    memoria["terminos_saturados"] = terminos_saturados
                    memoria["descartados_saturados"] = descartados_saturados
                    guardar_memoria(memoria)
        
        if producto_ganador_definitivo:
            # Si encontramos un ganador, NO lo metemos en nichos_procesados para poder seguir buscando
            # más productos en este mismo nicho en futuras ejecuciones.
            logger.info(f"🎉 Encontrado ganador en el nicho '{nicho_actual}'. No se marca como procesado para permitir extraer más ganadores en futuras ejecuciones.")
            break
            
        # Si NO encontramos ningún ganador en todo el lote, el nicho está agotado/saturado
        if nicho_actual not in nichos_procesados:
            nichos_procesados.append(nicho_actual)
            memoria["nichos_procesados"] = nichos_procesados
            guardar_memoria(memoria)
            
        logger.info(f"🤔 REFLEXIÓN: El nicho/keyword '{nicho_actual}' no arrojó ganadores aprobados y ha sido agotado. Cambiando de nicho...")
        await asyncio.sleep(2)
        
    logger.info(f"\n🏆 ¡SISTEMA DETENIDO! HEMOS ENCONTRADO EL PRODUCTO GANADOR 🏆")
    logger.info(f"🛍️ Producto (Original): {producto_ganador_definitivo['producto_original']}")
    logger.info(f"🗣️ Nombre Comercial (Chile): {termino_ganador_espanol}")
    logger.info(f"📈 Ventas Comprobadas (USA): {producto_ganador_definitivo['ventas_reales']:,}")
    if producto_ganador_definitivo.get("url"):
        logger.info(f"🔗 Enlace TikTok Shop: {producto_ganador_definitivo['url']}")
    
    logger.info("\n📦 --- RESUMEN FINAL ---")
    if dropi_id_final and dropi_id_final not in [123456, 999999]:
        logger.info(f"🎉 ¡ÉXITO TOTAL! Producto disponible en Dropi Chile (ID: {dropi_id_final}) y validado como viral.")
        logger.info("💸 Listo para ser importado y vender hoy mismo.")
    else:
        logger.info(f"🚀 ¡GRAN OPORTUNIDAD! Producto altamente viral en USA y sin competencia en Chile.")
        logger.info("⚠️ No disponible en Dropi. Requiere importación privada.")

if __name__ == "__main__":
    asyncio.run(mesa_de_trabajo_autonoma())
