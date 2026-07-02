import asyncio
import logging
import aiohttp
import random
import json
import os
import sys
from config import settings
from utils import smartcommerce_helper_gt as sc_helper
from utils.api_cache import get_cached_response, set_cached_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("MesaTrabajoSC_GT")

# ============================================================================
# CONFIGURACIÓN DE ESTRATEGIA DE BÚSQUEDA
# ============================================================================
# Opciones disponibles:
# 1. "tiktok_shop": Outbound (Buscar viral en TikTok USA -> Traducir -> Validar Stock SmartCommerce GT -> Validar Meta Ads Guatemala)
# 2. "smartcommerce_inverso": Inbound (Buscar productos con stock alto en SmartCommerce GT -> Traducir a inglés -> Validar ventas en TikTok -> Validar Meta Ads Guatemala)
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
    
    limit = 25
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

# --- AGENTE 3: VALIDADOR DE SATURACIÓN (META ADS GUATEMALA VÍA RAPIDAPI) ---
async def agente_meta_ads_gt(producto_nombre: str) -> dict:
    """
    Busca el producto en la Librería de Anuncios de Facebook para Guatemala (GT).
    Usa caché SQLite para evitar consultas repetidas al scraper de RapidAPI.
    """
    cached = get_cached_response("meta_ads_gt", producto_nombre)
    if cached is not None:
        return cached

    rapidapi_key = settings.rapidapi_key
    logger.info(f"👁️ [Agente Meta GT] Consultando FB Ads Library Guatemala para: '{producto_nombre[:40]}...'")
    
    url = "https://facebook-ads-library-scraper-api.p.rapidapi.com/search/ads"
    headers = {
        "x-rapidapi-host": "facebook-ads-library-scraper-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    
    palabras = producto_nombre.split()
    query_corta = " ".join(palabras[:4])
    
    querystring = {
        "query": query_corta,
        "country_code": "GT",  # País Guatemala
        "limit": "50"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=querystring) as response:
                if response.status != 200:
                    logger.error(f"Error en RapidAPI FB Scraper GT: {response.status}")
                    return {"anuncios_gt": 99, "estado": "ERROR"}
                
                json_response = await response.json()
                resultados = json_response.get("searchResults", [])
                total_anuncios = len(resultados)
                anuncios_activos = sum(1 for ad in resultados if ad.get("is_active", False) == True)
                
                estado = "SATURADO"
                
                if total_anuncios > 0 and anuncios_activos == 0:
                    estado = "FRACASO COMPROBADO"
                elif total_anuncios == 0:
                    estado = "OCEANO AZUL"
                elif anuncios_activos <= 5:
                    estado = "OPORTUNIDAD"
                    
                result = {
                    "anuncios_gt": anuncios_activos,
                    "estado": estado
                }
                
                # Almacenar en caché
                set_cached_response("meta_ads_gt", producto_nombre, result)
                return result
    except Exception as e:
        logger.error(f"❌ Excepción en agente_meta_ads_gt: {str(e)}")
        return {"anuncios_gt": 99, "estado": "ERROR"}

# --- AGENTE 4: PLANIFICADOR CREATIVO (GEMINI) ---
async def agente_creador_nichos(nichos_rechazados: list) -> list:
    """Si la lista maestra se agota, Gemini crea nichos nuevos."""
    logger.warning("🧠 [Agente Planificador] La lista de palabras clave se agotó. Usando IA para generar nuevos nichos...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    prompt = f"""
    Eres un experto analista de mercado e-commerce, especializado en predecir productos virales y tendencias de consumo masivo para Guatemala y Latinoamérica.
    Tu objetivo es identificar categorías de productos en inglés que están a punto de explotar en demanda, pero que aún no están masificados.
    Ya intentamos buscar estos nichos pero están saturados o no sirven: {', '.join(nichos_rechazados)}.
    Inventa 3 NICHOS NUEVOS en inglés para buscar. (Ej: 'viral skincare devices', 'smart travel organizers', 'pet mental stimulation toys').
    Responde ÚNICAMENTE con los 3 nichos separados por comas, sin texto extra.
    """
    
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    respuesta = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    nuevos_nichos = [n.strip().strip("'").strip('"') for n in respuesta.split(',')]
                    logger.info(f"💡 [Agente Planificador] ¡Nuevos nichos creados!: {nuevos_nichos}")
                    return nuevos_nichos
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
    Tradúcelo a un concepto genérico corto (máximo 3 palabras) que usaría un guatemalteco para buscarlo en Facebook o comprarlo.
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
    """
    result_map = {}
    nombres_a_traducir = []
    
    for nombre in nombres_ingles:
        cached = get_cached_response("gemini_translator", nombre)
        if cached is not None:
            result_map[nombre] = cached
        else:
            nombres_a_traducir.append(nombre)
            
    if not nombres_a_traducir:
        return [result_map[n] for n in nombres_ingles]
        
    logger.info(f"🌐 [Agente Traductor Lote] Traduciendo {len(nombres_a_traducir)} nombres al español con Gemini...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    prompt = f"""
    Eres un experto en e-commerce latinoamericano.
    Tengo la siguiente lista de nombres de productos importados en inglés:
    {json.dumps(nombres_a_traducir, indent=2)}
    
    Para cada uno de ellos, tradúcelo a un concepto genérico corto (máximo 3 palabras) en español que usaría un guatemalteco para buscarlo en Facebook o comprarlo.
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

# --- AGENTE 6: TRADUCTOR INVERSO (GEMINI) ---
async def agente_traductor_inverso(nombre_espanol: str) -> str:
    """Usa Gemini para traducir un nombre en Español a un término de búsqueda en Inglés."""
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

# --- ESTRATEGIA A: MINERÍA DE CATÁLOGO INVERSO DE SMARTCOMMERCE GT ---
async def agente_smartcommerce_inverso(keyword: str) -> list:
    """
    Inbound: Busca productos directamente en el catálogo de SmartCommerce Guatemala
    y los filtra por stock activo y costo competitivo.
    """
    logger.info(f"📥 [SmartCommerce Inverso GT] Buscando productos locales en catálogo con palabra clave: '{keyword}'...")
    
    token = sc_helper.get_smartcommerce_token()
    if not token:
        raise ValueError("❌ No se pudo obtener el token de autenticación de SmartCommerce. Verifica tus credenciales.")
    
    url = "https://api.smartcommerce.lat/api/products"
    params = {
        "page": "1",
        "size": "50",
        "search": keyword,
        "sortBy": "createdAt"
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "Origin": "https://app.smartcommerce.lat",
        "Referer": "https://app.smartcommerce.lat/"
    }
    
    try:
        from curl_cffi import requests as curl_requests
        loop = asyncio.get_event_loop()
        def make_request():
            return curl_requests.get(url, headers=headers, params=params, impersonate="chrome120", timeout=15)
        
        response = await loop.run_in_executor(None, make_request)
        
        if response.status_code == 200:
            data = response.json()
            raw_products = data.get("payload", {}).get("items", []) or []
            filtered = []
            for p in raw_products:
                # Filtrar solo productos del mercado Guatemala (GT)
                if p.get("countryISO2") != "GT":
                    continue
                    
                name = p.get("name", "")
                cost = float(p.get("cost") or 0.0)
                inventory = p.get("inventory", {}) or {}
                stock = int(inventory.get("totalAvailable") or inventory.get("totalOnHand") or 0)
                orders = int(p.get("salesCount") or 0)
                product_id = p.get("_id")
                
                # Criterios en Guatemala: Stock >= 200 unidades, Costo de compra <= 120 Quetzales
                if stock >= 200 and cost <= 120:
                    filtered.append({
                        "producto_id": product_id,
                        "producto": name,
                        "precio_costo_gtq": cost,
                        "stock": stock,
                        "orders": orders,
                        "supplier_name": p.get("vendorId", {}).get("name") if p.get("vendorId") else "Desconocido"
                    })
            logger.info(f"✅ [SmartCommerce Inverso GT] Encontrados {len(filtered)} productos reales válidos en stock.")
            return filtered
        else:
            error_msg = f"❌ Error de API de SmartCommerce GT: HTTP {response.status_code} - {response.text[:300]}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    except Exception as e:
        logger.error(f"❌ Error al consultar catálogo en SmartCommerce GT: {str(e)}")
        raise e

# ============================================================================
# MEMORIA LOCAL DE LA MESA DE TRABAJO SC GT
# ============================================================================
HISTORIAL_FILE = "historial_memoria_sc_gt.json"

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
            return mem
    return {"nichos_procesados": [], "productos_rechazados": [], "terminos_saturados": [], "descartados_sin_proveedor": [], "descartados_saturados": [], "ganadores_detalle": []}

def guardar_memoria(memoria):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

# ============================================================================
# BUCLE ORQUESTADOR PRINCIPAL AUTÓNOMO GT
# ============================================================================
async def mesa_de_trabajo_autonoma():
    logger.info(f"🚀 INICIANDO MESA DE TRABAJO AUTÓNOMA SMARTCOMMERCE GUATEMALA (GT)")
    logger.info(f"🎯 ESTRATEGIA ACTIVA: {ESTRATEGIA_ACTIVA.upper()}")
    
    memoria = cargar_memoria()
    nichos_procesados = memoria.get("nichos_procesados", [])
    productos_rechazados = memoria.get("productos_rechazados", [])
    terminos_saturados = memoria.get("terminos_saturados", [])
    
    # 1. Definición de Keywords / Nichos según la estrategia
    if ESTRATEGIA_ACTIVA == "smartcommerce_inverso":
        lista_nichos_base = ["mascotas", "cocina", "belleza", "tecnologia", "organizador", "limpieza", "deporte", "hogar", "general"]
    else:
        lista_nichos_base = [
            "viral skincare devices", "smart travel organizers", "pet mental stimulation toys",
            "posture correctors", "heatless hair curlers", "portable neck fans",
            "car seat gap fillers", "LED aesthetic room lights", "ergonomic office cushions",
            "waterproof shoe covers", "anti-theft backpacks", "reusable lint rollers"
        ]
        
    lista_nichos = [n for n in lista_nichos_base if n not in nichos_procesados]
    
    producto_ganador_definitivo = None
    termino_ganador_espanol = None
    sc_id_final = None
    
    while not producto_ganador_definitivo:
        if not lista_nichos:
            lista_nichos = await agente_creador_nichos(nichos_procesados)
            
        nicho_actual = lista_nichos.pop(0)
        if nicho_actual not in nichos_procesados:
            nichos_procesados.append(nicho_actual)
            memoria["nichos_procesados"] = nichos_procesados
            guardar_memoria(memoria)
        
        logger.info(f"\n{'='*70}\n🔄 CICLO | Nicho/Keyword: '{nicho_actual}'\n{'='*70}")
        
        candidatos = []
        
        if ESTRATEGIA_ACTIVA == "smartcommerce_inverso":
            productos_sc = await agente_smartcommerce_inverso(nicho_actual)
            for prod_sc in productos_sc:
                nombre_gt = prod_sc["producto"]
                
                if nombre_gt in terminos_saturados or nombre_gt in productos_rechazados:
                    continue
                
                nombre_en = await agente_traductor_inverso(nombre_gt)
                
                logger.info(f"🔍 [SmartCommerce Inverso GT] Validando viralidad de '{nombre_gt}' (Búsqueda en inglés: '{nombre_en}') en TikTok...")
                productos_tiktok = await agente_tiktok_shop(nombre_en, page=1)
                
                if productos_tiktok:
                    productos_validados = agente_evaluador_negocio(productos_tiktok)
                    if productos_validados:
                        mejor_tiktok = productos_validados[0]
                        candidatos.append({
                            "producto_original": mejor_tiktok["producto"],
                            "producto_espanol": nombre_gt,
                            "ventas_reales": mejor_tiktok["ventas_reales"],
                            "precio_usd": mejor_tiktok["precio_usd"],
                            "dropi_id": prod_sc["producto_id"],  # Mantener clave genérica dropi_id
                            "dropi_ventas": prod_sc.get("orders", 0),
                            "dropi_stock": prod_sc.get("stock", 0),
                            "dropi_search_term_es": nicho_actual,
                            "dropi_search_term_en": None,
                            "costo_gtq": prod_sc["precio_costo_gtq"],
                            "url": mejor_tiktok.get("url")
                        })
                        logger.info(f"🔥 ¡Producto viral comprobado en USA! '{mejor_tiktok['producto']}' ({mejor_tiktok['ventas_reales']:,} ventas).")
                await asyncio.sleep(2)
                
        elif ESTRATEGIA_ACTIVA in ["tiktok_shop"]:
            keywords_en = [nicho_actual]
                
            for kw in keywords_en:
                productos_tiktok = await agente_tiktok_shop(kw, page=1)
                productos_validados = agente_evaluador_negocio(productos_tiktok)
                
                candidatos_lote = []
                for prod in productos_validados:
                    if prod["producto"] not in productos_rechazados:
                        candidatos_lote.append(prod)
                    if len(candidatos_lote) >= 25:
                        break
                        
                if not candidatos_lote:
                    continue
                    
                nombres_ingles = [p["producto"] for p in candidatos_lote]
                nombres_espanol = await agente_traductor_lote_productos(nombres_ingles)
                
                for prod, nombre_es in zip(candidatos_lote, nombres_espanol):
                    if nombre_es in terminos_saturados:
                        continue
                        
                    logger.info(f"📦 [SmartCommerce GT] Iniciando búsqueda para: '{nombre_es}' (TikTok: '{prod['producto']}')")
                    
                    res_es = await sc_helper.search_smartcommerce_product(nombre_es)
                    
                    palabras_en = [w for w in prod["producto"].split() if w.isalnum()]
                    nombre_en_corta = " ".join(palabras_en[:3])
                    res_en = {"id": "123456", "stock": 0, "orders": 0}
                    if nombre_en_corta:
                        logger.info(f"🔍 [SmartCommerce GT] Buscando también con nombre en inglés: '{nombre_en_corta}'...")
                        res_en = await sc_helper.search_smartcommerce_product(nombre_en_corta)
                    
                    res_final = {"id": "123456", "stock": 0, "orders": 0}
                    if res_es["id"] != "123456":
                        res_final = res_es
                        logger.info(f"✅ Encontrado en español. Usando ID: {res_final['id']}")
                    elif res_en["id"] != "123456":
                        res_final = res_en
                        logger.info(f"✅ Encontrado en inglés. Usando ID: {res_final['id']}")
                    else:
                        if len(palabras_en) > 3:
                            nombre_en_muy_corta = " ".join(palabras_en[:2])
                            if nombre_en_muy_corta:
                                logger.info(f"🔍 [SmartCommerce Fallback GT] Ambos fallaron. Intentando más genérico en inglés: '{nombre_en_muy_corta}'...")
                                res_muy_corta = await sc_helper.search_smartcommerce_product(nombre_en_muy_corta)
                                if res_muy_corta["id"] != "123456":
                                    res_final = res_muy_corta
                                    logger.info(f"✅ Encontrado en inglés genérico. Usando ID: {res_final['id']}")
                    
                    sc_id = res_final["id"]
                    if sc_id == "123456":
                        logger.warning(f"⚠️ Saltando '{nombre_es}' (TikTok Original: '{prod['producto']}') porque no está disponible en el catálogo de SmartCommerce Guatemala.")
                        continue
                        
                    candidatos.append({
                        "producto_original": prod["producto"],
                        "producto_espanol": nombre_es,
                        "ventas_reales": prod["ventas_reales"],
                        "precio_usd": prod["precio_usd"],
                        "dropi_id": sc_id,  # Mantener clave genérica dropi_id
                        "dropi_ventas": res_final["orders"],
                        "dropi_stock": res_final["stock"],
                        "dropi_search_term_es": nombre_es,
                        "dropi_search_term_en": nombre_en_corta,
                        "costo_gtq": None,
                        "url": prod.get("url")
                    })
                    await asyncio.sleep(0.5)
        
        # --------------------------------------------------------------------
        # FILTRADO DE SATURACIÓN Y SELECCIÓN FINAL
        # --------------------------------------------------------------------
        for cand in candidatos:
            nombre_es = cand["producto_espanol"]
            
            logger.info(f"👁️ Evaluando saturación publicitaria en Guatemala para: '{nombre_es}' (TikTok Original: '{cand['producto_original']}')...")
            evaluacion_meta = await agente_meta_ads_gt(nombre_es)
            
            estado = evaluacion_meta["estado"]
            ads = evaluacion_meta["anuncios_gt"]
            
            if estado in ["OCEANO AZUL", "OPORTUNIDAD"]:
                logger.info(f"✅ ¡PRODUCTO APROBADO POR META ADS GT! '{nombre_es}' (TikTok Original: '{cand['producto_original']}') ({ads} anuncios activos en Guatemala)")
                
                productos_rechazados.append(cand["producto_original"])
                memoria["productos_rechazados"] = productos_rechazados
                
                ganador_item = {
                    "tiktok_ingles": cand["producto_original"],
                    "producto_espanol": nombre_es,
                    "smartcommerce_id": cand["dropi_id"],
                    "ventas_locales_sc": cand.get("dropi_ventas", 0),
                    "stock_local_sc": cand.get("dropi_stock", 0),
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
                    logger.info(f"💾 Guardado ganador en historial_memoria_sc_gt.json: '{nombre_es}'")
                
                memoria["ganadores_detalle"] = ganadores_detalle
                guardar_memoria(memoria)
                
                producto_ganador_definitivo = cand
                termino_ganador_espanol = nombre_es
                sc_id_final = cand["dropi_id"]
                break
            else:
                if estado == "FRACASO COMPROBADO":
                    logger.warning(f"❌ RECHAZADO: '{nombre_es}' (TikTok Original: '{cand['producto_original']}') tiene historial pero anuncios apagados (Fracaso previo).")
                else:
                    logger.warning(f"❌ RECHAZADO: '{nombre_es}' (TikTok Original: '{cand['producto_original']}') está SATURADO en Guatemala ({ads} anuncios activos).")
                
                productos_rechazados.append(cand["producto_original"])
                if nombre_es not in terminos_saturados:
                    terminos_saturados.append(nombre_es)
                
                descartado_item = {
                    "tiktok_ingles": cand["producto_original"],
                    "producto_espanol": nombre_es,
                    "smartcommerce_id": cand["dropi_id"],
                    "ventas_locales_sc": cand.get("dropi_ventas", 0),
                    "stock_local_sc": cand.get("dropi_stock", 0),
                    "dropi_search_term_es": cand.get("dropi_search_term_es", nombre_es),
                    "dropi_search_term_en": cand.get("dropi_search_term_en", ""),
                    "meta_search_query": " ".join(nombre_es.split()[:4]),
                    "meta_anuncios_activos": ads,
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
                await asyncio.sleep(2)
        
        if producto_ganador_definitivo:
            break
            
        logger.info(f"🤔 REFLEXIÓN: El nicho/keyword '{nicho_actual}' no arrojó ganadores aprobados. Cambiando de nicho...")
        await asyncio.sleep(2)
        
    logger.info(f"\n🏆 ¡SISTEMA DETENIDO! HEMOS ENCONTRADO EL PRODUCTO GANADOR EN GUATEMALA (SMARTCOMMERCE) 🏆")
    logger.info(f"🛍️ Producto (Original): {producto_ganador_definitivo['producto_original']}")
    logger.info(f"🗣️ Nombre Comercial (Guatemala): {termino_ganador_espanol}")
    logger.info(f"📈 Ventas Comprobadas (USA): {producto_ganador_definitivo['ventas_reales']:,}")
    if producto_ganador_definitivo.get("url"):
        logger.info(f"🔗 Enlace TikTok Shop: {producto_ganador_definitivo['url']}")
    
    logger.info("\n📦 --- RESUMEN FINAL ---")
    if sc_id_final and sc_id_final != "123456":
        logger.info(f"🎉 ¡ÉXITO TOTAL! Producto disponible en SmartCommerce Guatemala (ID: {sc_id_final}) y validado como viral.")
        logger.info("💸 Listo para ser importado y vender en Guatemala hoy mismo.")
    else:
        logger.info(f"🚀 ¡GRAN OPORTUNIDAD! Producto altamente viral en USA y sin competencia en Guatemala.")
        logger.info("⚠️ No disponible en SmartCommerce GT. Requiere importación privada.")

if __name__ == "__main__":
    asyncio.run(mesa_de_trabajo_autonoma())
