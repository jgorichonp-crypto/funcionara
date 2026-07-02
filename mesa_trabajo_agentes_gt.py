import asyncio
import logging
import aiohttp
import random
import json
import os
import sys
from config import settings
from utils import dropi_helper_gt as dropi_helper
from utils import smartcommerce_helper_gt as sc_helper
from utils.api_cache import get_cached_response, set_cached_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("MesaTrabajoGT_Unified")

# ============================================================================
# CONFIGURACIÓN DE ESTRATEGIA DE BÚSQUEDA
# ============================================================================
# Opciones disponibles:
# 1. "tiktok_shop": Outbound (Buscar viral en TikTok USA -> Traducir -> Validar Stock en Dropi GT y SmartCommerce GT -> Validar Meta Ads Guatemala)
# 2. "dropi_inverso": Inbound (Buscar productos en Dropi GT -> Validar ventas en TikTok -> Validar Stock en SmartCommerce GT -> Validar Meta Ads Guatemala)
# 3. "smartcommerce_inverso": Inbound (Buscar productos en SmartCommerce GT -> Validar ventas en TikTok -> Validar Stock en Dropi GT -> Validar Meta Ads Guatemala)
ESTRATEGIA_ACTIVA = "tiktok_shop"  # Cambiar aquí la estrategia deseada

# ============================================================================
# AGENTES DE EXTRACCIÓN Y BÚSQUEDA (CON CACHÉ)
# ============================================================================

# --- AGENTE 1: BUSCADOR DE TIKTOK SHOP (VÍA RAPIDAPI) ---
async def agente_tiktok_shop(query: str, page: int = 1) -> list:
    """Extrae productos de TikTok Shop. Si la API falla, eleva una excepción."""
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
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as response:
            if response.status != 200:
                body = await response.text()
                raise ConnectionError(f"❌ Error en RapidAPI TikTok: HTTP {response.status} - {body[:200]}")
            
            json_response = await response.json()
            if "error" in json_response:
                raise ValueError(f"❌ Error devuelto por RapidAPI TikTok: {json_response['error']}")
                
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
            
            set_cached_response("tiktok_shop", cache_key, productos)
            return productos

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
    Si la API falla, eleva una excepción.
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
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as response:
            if response.status != 200:
                body = await response.text()
                raise ConnectionError(f"❌ Error en RapidAPI FB Scraper GT: HTTP {response.status} - {body[:200]}")
            
            json_response = await response.json()
            resultados = json_response.get("searchResults", [])
            total_anuncios = len(resultados)
            
            # Filtrado preciso de anuncios para descartar falsos positivos de búsqueda
            palabras_clave_busqueda = [w.lower() for w in query_corta.split() if len(w) > 3]
            anuncios_activos = 0
            
            for ad in resultados:
                if ad.get("is_active", False) == True:
                    # Extraer el texto del anuncio
                    ad_text = ""
                    for key in ["adSnapshotText", "ad_snapshot_text", "snapshotText", "adCreativeBody", "ad_creative_body", "title", "body"]:
                        val = ad.get(key)
                        if val:
                            if isinstance(val, list):
                                ad_text += " " + " ".join([str(v) for v in val])
                            else:
                                ad_text += " " + str(val)
                    
                    ad_text = ad_text.lower()
                    
                    # Si no hay texto, contamos por seguridad
                    if not ad_text.strip():
                        anuncios_activos += 1
                        continue
                    
                    # Verificar si realmente habla del producto
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
                        
                        # Debe contener el sustantivo principal (ej: "carrito", "reloj", "masajeador")
                        tiene_sustantivo = sustantivo_principal in ad_text
                        
                        # Si hay más palabras descriptivas, debe contener al menos una de las otras
                        tiene_descriptor = True
                        if otras_palabras:
                            tiene_descriptor = any(op in ad_text for op in otras_palabras)
                            
                        if tiene_sustantivo and tiene_descriptor and not es_falso_positivo:
                            anuncios_activos += 1
                    else:
                        anuncios_activos += 1
            
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
            
            set_cached_response("meta_ads_gt", producto_nombre, result)
            return result

# --- AGENTE 4: PLANIFICADOR CREATIVO (GEMINI) ---
async def agente_creador_nichos(nichos_rechazados: list) -> list:
    """Si la lista maestra se agota, Gemini crea nichos nuevos. Eleva excepción si falla."""
    logger.warning("🧠 [Agente Planificador] La lista de palabras clave se agotó. Usando IA para generar nuevos nichos...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    prompt = f"""
    Eres un experto analista de mercado e-commerce, especializado en predecir productos virales y tendencias de consumo masivo para Guatemala y Latinoamérica.
    Usa la búsqueda de Google para buscar las últimas tendencias virales de dropshipping, TikTok Shop y e-commerce emergente en Estados Unidos y Latinoamérica en 2026.
    Identifica categorías o conceptos de productos virales en inglés que tengan alta demanda pero no estén masificados aún.
    Ya intentamos buscar estos nichos pero están saturados o no sirven: {', '.join(nichos_rechazados)}.
    Genera 5 NICHOS NUEVOS en inglés para buscar. (Ej: 'viral skincare devices', 'smart travel organizers', 'pet mental stimulation toys').
    Responde ÚNICAMENTE con los 5 nichos separados por comas, sin texto extra.
    """
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"googleSearch": {}}]
        }
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise ConnectionError(f"❌ Gemini con error al generar nichos (HTTP {resp.status}) - {body[:200]}")
            result = await resp.json()
            respuesta = result['candidates'][0]['content']['parts'][0]['text'].strip()
            nuevos_nichos = [n.strip().strip("'").strip('"') for n in respuesta.split(',')]
            logger.info(f"💡 [Agente Planificador] ¡Nuevos nichos creados!: {nuevos_nichos}")
            return nuevos_nichos

# --- AGENTE 5: TRADUCTOR PRODUCTO (GEMINI) ---
async def agente_traductor_producto(nombre_ingles: str) -> str:
    """Usa Gemini para extraer el nombre genérico del producto en Español. Eleva excepción si falla."""
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
        async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise ConnectionError(f"❌ Gemini con error al traducir producto (HTTP {resp.status}) - {body[:200]}")
            result = await resp.json()
            traduccion = result['candidates'][0]['content']['parts'][0]['text'].strip()
            traduccion = traduccion.replace('"', '').replace("'", "")
            logger.info(f"✅ [Agente Traductor] '{nombre_ingles}' -> '{traduccion}'")
            set_cached_response("gemini_translator", nombre_ingles, traduccion)
            return traduccion

# --- AGENTE 5.5: TRADUCTOR DE PRODUCTOS EN LOTE (GEMINI) ---
async def agente_traductor_lote_productos(nombres_ingles: list) -> list:
    """
    Traduce una lista de nombres de productos en inglés a español en una sola llamada a Gemini.
    Eleva excepción si falla.
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
        async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise ConnectionError(f"❌ Gemini con error en traducción por lotes (HTTP {resp.status}) - {body[:200]}")
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
            else:
                raise ValueError("❌ La longitud de la lista de traducción por lotes devuelta por Gemini no coincide.")
                
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


# --- AGENTE 6: TRADUCTOR INVERSO (GEMINI) ---
async def agente_traductor_inverso(nombre_espanol: str) -> str:
    """Usa Gemini para traducir un nombre en Español a un término en Inglés. Eleva excepción si falla."""
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
        async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise ConnectionError(f"❌ Gemini con error en traducción inversa (HTTP {resp.status}) - {body[:200]}")
            result = await resp.json()
            traduccion = result['candidates'][0]['content']['parts'][0]['text'].strip()
            traduccion = traduccion.replace('"', '').replace("'", "")
            logger.info(f"✅ [Agente Traductor Inverso] '{nombre_espanol}' -> '{traduccion}'")
            set_cached_response("gemini_translator_inverse", nombre_espanol, traduccion)
            return traduccion

# ============================================================================
# ESTRATEGIAS DE BÚSQUEDA ADICIONALES
# ============================================================================

# --- ESTRATEGIA A: MINERÍA DE CATÁLOGO INVERSO DE DROPI GT ---
async def agente_dropi_inverso(keyword: str) -> list:
    """
    Inbound: Busca productos directamente en el catálogo de Dropi Guatemala
    y los filtra por stock activo y costo competitivo.
    """
    logger.info(f"📥 [Dropi Inverso GT] Buscando productos locales en catálogo con palabra clave: '{keyword}'...")
    
    from utils.dropi_helper_gt import get_dropi_token_gt
    token = get_dropi_token_gt()
    
    if not token:
        raise ValueError("❌ No se pudo obtener el token de autenticación de Dropi Guatemala. Verifica tus credenciales.")
    
    url = "https://api.dropi.gt/api/products/index"
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
        "Origin": "https://app.dropi.com.gt",
        "Referer": "https://app.dropi.com.gt/",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
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
            
            # Criterios en Guatemala: Stock >= 200 unidades, Costo de compra <= 120 Quetzales
            if stock >= 200 and cost <= 120:
                filtered.append({
                    "producto_id": product_id,
                    "producto": name,
                    "precio_costo_gtq": cost,
                    "stock": stock,
                    "orders": orders,
                    "supplier_id": p.get("user_id") or p.get("supplier_id")
                })
        logger.info(f"✅ [Dropi Inverso GT] Encontrados {len(filtered)} productos reales válidos en stock.")
        return filtered
    else:
        error_msg = f"❌ Error de API de Dropi GT: HTTP {response.status_code} - {response.text[:300]}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

# --- ESTRATEGIA B: MINERÍA DE CATÁLOGO INVERSO DE SMARTCOMMERCE GT ---
async def agente_smartcommerce_inverso(keyword: str) -> list:
    """
    Inbound: Busca productos directamente en el catálogo de SmartCommerce Guatemala
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
            if p.get("countryISO2") != "GT":
                continue
            name = p.get("name", "")
            cost = float(p.get("cost") or 0.0)
            inventory = p.get("inventory", {}) or {}
            stock = int(inventory.get("totalAvailable") or inventory.get("totalOnHand") or 0)
            orders = int(p.get("salesCount") or 0)
            product_id = p.get("_id")
            
            # Stock >= 200 unidades, Costo <= 120 Quetzales
            if stock >= 200 and cost <= 120:
                filtered.append({
                    "producto_id": product_id,
                    "producto": name,
                    "precio_costo_gtq": cost,
                    "stock": stock,
                    "orders": orders
                })
        logger.info(f"✅ [SmartCommerce Inverso GT] Encontrados {len(filtered)} productos reales válidos en stock.")
        return filtered
    else:
        error_msg = f"❌ Error de API de SmartCommerce GT: HTTP {response.status_code} - {response.text[:300]}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

# ============================================================================
# MEMORIA LOCAL DE LA MESA DE TRABAJO GT
# ============================================================================
HISTORIAL_FILE = "historial_memoria_gt.json"

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
# BUCLE ORQUESTADOR PRINCIPAL AUTÓNOMO GT
# ============================================================================
async def mesa_de_trabajo_autonoma():
    logger.info(f"🚀 INICIANDO MESA DE TRABAJO CONJUNTA GUATEMALA (GT) - DROPI & SMARTCOMMERCE")
    logger.info(f"🎯 ESTRATEGIA ACTIVA: {ESTRATEGIA_ACTIVA.upper()}")
    
    memoria = cargar_memoria()
    nichos_procesados = memoria.get("nichos_procesados", [])
    productos_rechazados = memoria.get("productos_rechazados", [])
    terminos_saturados = memoria.get("terminos_saturados", [])
    productos_encontrados = memoria.get("productos_encontrados", [])
    
    # 1. Definición de Keywords / Nichos según la estrategia
    if ESTRATEGIA_ACTIVA in ["dropi_inverso", "smartcommerce_inverso"]:
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
        
        if ESTRATEGIA_ACTIVA == "dropi_inverso":
            productos_dropi = await agente_dropi_inverso(nicho_actual)
            for prod_dropi in productos_dropi:
                nombre_gt = prod_dropi["producto"]
                
                if nombre_gt in terminos_saturados or nombre_gt in productos_rechazados:
                    continue
                
                nombre_en = await agente_traductor_inverso(nombre_gt)
                
                logger.info(f"🔍 [Dropi Inverso GT] Validando viralidad de '{nombre_gt}' (Búsqueda en inglés: '{nombre_en}') en TikTok...")
                productos_tiktok = await agente_tiktok_shop(nombre_en, page=1)
                
                if productos_tiktok:
                    productos_validados = agente_evaluador_negocio(productos_tiktok)
                    if productos_validados:
                        mejor_tiktok = productos_validados[0]
                        
                        # Buscar existencia y stock también en SmartCommerce
                        logger.info(f"🔍 [SmartCommerce GT] Validando si el producto '{nombre_gt}' está también disponible en SmartCommerce...")
                        res_sc = await sc_helper.search_smartcommerce_product(nombre_gt)
                        
                        candidatos.append({
                            "producto_original": mejor_tiktok["producto"],
                            "producto_espanol": nombre_gt,
                            "ventas_reales": mejor_tiktok["ventas_reales"],
                            "precio_usd": mejor_tiktok["precio_usd"],
                            
                            "dropi_id": prod_dropi["producto_id"],
                            "dropi_ventas": prod_dropi.get("orders", 0),
                            "dropi_stock": prod_dropi.get("stock", 0),
                            
                            "sc_id": res_sc["id"],
                            "sc_ventas": res_sc["orders"],
                            "sc_stock": res_sc["stock"],
                            
                            "dropi_search_term_es": nicho_actual,
                            "dropi_search_term_en": None,
                            "costo_gtq": prod_dropi["precio_costo_gtq"],
                            "url": mejor_tiktok.get("url")
                        })
                        logger.info(f"🔥 ¡Producto viral comprobado en USA! '{mejor_tiktok['producto']}' ({mejor_tiktok['ventas_reales']:,} ventas).")
                await asyncio.sleep(2)
                
        elif ESTRATEGIA_ACTIVA == "smartcommerce_inverso":
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
                        
                        # Buscar existencia y stock también en Dropi
                        logger.info(f"🔍 [Dropi GT] Validando si el producto '{nombre_gt}' está también disponible en Dropi...")
                        res_dropi = await dropi_helper.search_dropi_product(nombre_gt)
                        
                        candidatos.append({
                            "producto_original": mejor_tiktok["producto"],
                            "producto_espanol": nombre_gt,
                            "ventas_reales": mejor_tiktok["ventas_reales"],
                            "precio_usd": mejor_tiktok["precio_usd"],
                            
                            "dropi_id": res_dropi["id"],
                            "dropi_ventas": res_dropi["orders"],
                            "dropi_stock": res_dropi["stock"],
                            
                            "sc_id": prod_sc["producto_id"],
                            "sc_ventas": prod_sc.get("orders", 0),
                            "sc_stock": prod_sc.get("stock", 0),
                            
                            "dropi_search_term_es": nicho_actual,
                            "dropi_search_term_en": None,
                            "costo_gtq": prod_sc["precio_costo_gtq"],
                            "url": mejor_tiktok.get("url")
                        })
                        logger.info(f"🔥 ¡Producto viral comprobado en USA! '{mejor_tiktok['producto']}' ({mejor_tiktok['ventas_reales']:,} ventas).")
                await asyncio.sleep(2)
                
        elif ESTRATEGIA_ACTIVA == "tiktok_shop":
            keywords_en = [nicho_actual]
                
            for kw in keywords_en:
                productos_tiktok = await agente_tiktok_shop(kw, page=1)
                productos_validados = agente_evaluador_negocio(productos_tiktok)
                
                candidatos_lote = []
                for prod in productos_validados:
                    if prod["producto"] not in productos_rechazados:
                        candidatos_lote.append(prod)
                    if len(candidatos_lote) >= 100:
                        break
                        
                if not candidatos_lote:
                    continue
                    
                nombres_ingles = [p["producto"] for p in candidatos_lote]
                nombres_espanol = await agente_traductor_lote_productos(nombres_ingles)
                
                for prod, nombre_es in zip(candidatos_lote, nombres_espanol):
                    if nombre_es in terminos_saturados:
                        continue
                        
                    logger.info(f"📦 [Validando Catálogos GT] Consultando disponibilidad para: '{nombre_es}' (TikTok: '{prod['producto']}')")
                    
                    # 1. Búsqueda en Dropi GT
                    res_dropi_es = await dropi_helper.search_dropi_product(nombre_es)
                    
                    # Fallback adicional en español si falló el nombre completo
                    palabras_es = nombre_es.split()
                    if res_dropi_es["id"] is None and len(palabras_es) > 2:
                        nombre_es_corta = " ".join(palabras_es[:2])
                        logger.info(f"🔍 [Dropi Fallback GT] Buscando versión genérica en español: '{nombre_es_corta}'...")
                        res_dropi_es_corta = await dropi_helper.search_dropi_product(nombre_es_corta)
                        if res_dropi_es_corta["id"] is not None and res_dropi_es_corta.get("stock", 0) > 0:
                            res_dropi_es = res_dropi_es_corta
                            logger.info(f"✅ Encontrado en Dropi GT genérico: '{nombre_es_corta}'")
                    
                    palabras_en = [w for w in prod["producto"].split() if w.isalnum()]
                    nombre_en_corta = " ".join(palabras_en[:3])
                    
                    res_dropi_en = {"id": None, "stock": 0, "orders": 0}
                    if nombre_en_corta:
                        res_dropi_en = await dropi_helper.search_dropi_product(nombre_en_corta)
                        
                    res_dropi = {"id": None, "stock": 0, "orders": 0}
                    if res_dropi_es["id"] is not None:
                        res_dropi = res_dropi_es
                    elif res_dropi_en["id"] is not None:
                        res_dropi = res_dropi_en
                    else:
                        if len(palabras_en) > 3:
                            nombre_en_muy_corta = " ".join(palabras_en[:2])
                            if nombre_en_muy_corta:
                                res_dropi_muy_corta = await dropi_helper.search_dropi_product(nombre_en_muy_corta)
                                if res_dropi_muy_corta["id"] is not None:
                                    res_dropi = res_dropi_muy_corta
                    
                    # 2. Búsqueda en SmartCommerce GT
                    res_sc_es = await sc_helper.search_smartcommerce_product(nombre_es)
                    
                    # Fallback adicional en español si falló el nombre completo
                    if res_sc_es["id"] is None and len(palabras_es) > 2:
                        nombre_es_corta = " ".join(palabras_es[:2])
                        logger.info(f"🔍 [SmartCommerce Fallback GT] Buscando versión genérica en español: '{nombre_es_corta}'...")
                        res_sc_es_corta = await sc_helper.search_smartcommerce_product(nombre_es_corta)
                        if res_sc_es_corta["id"] is not None and res_sc_es_corta.get("stock", 0) > 0:
                            res_sc_es = res_sc_es_corta
                            logger.info(f"✅ Encontrado en SmartCommerce GT genérico: '{nombre_es_corta}'")
                    
                    res_sc_en = {"id": None, "stock": 0, "orders": 0}
                    if nombre_en_corta:
                        res_sc_en = await sc_helper.search_smartcommerce_product(nombre_en_corta)
                        
                    res_sc = {"id": None, "stock": 0, "orders": 0}
                    if res_sc_es["id"] is not None:
                        res_sc = res_sc_es
                    elif res_sc_en["id"] is not None:
                        res_sc = res_sc_en
                    else:
                        if len(palabras_en) > 3:
                            nombre_en_muy_corta = " ".join(palabras_en[:2])
                            if nombre_en_muy_corta:
                                res_sc_muy_corta = await sc_helper.search_smartcommerce_product(nombre_en_muy_corta)
                                if res_sc_muy_corta["id"] is not None:
                                    res_sc = res_sc_muy_corta
                    
                    # Validación Semántica de Coincidencias con Gemini (Evitar Falsos Positivos)
                    if res_dropi["id"] is not None:
                        nombre_retornado_dropi = res_dropi.get("name", "")
                        if nombre_retornado_dropi:
                            es_concordante = await agente_validador_concordancia_gemini(
                                prod["producto"], nombre_es, nombre_retornado_dropi
                            )
                            if not es_concordante:
                                logger.warning(f"⚠️ [Falso Positivo Evitado] Descartando coincidencia en Dropi: '{nombre_es}' vs '{nombre_retornado_dropi}'")
                                res_dropi = {"id": None, "stock": 0, "orders": 0, "name": ""}

                    if res_sc["id"] is not None:
                        nombre_retornado_sc = res_sc.get("name", "")
                        if nombre_retornado_sc:
                            es_concordante = await agente_validador_concordancia_gemini(
                                prod["producto"], nombre_es, nombre_retornado_sc
                            )
                            if not es_concordante:
                                logger.warning(f"⚠️ [Falso Positivo Evitado] Descartando coincidencia en SmartCommerce: '{nombre_es}' vs '{nombre_retornado_sc}'")
                                res_sc = {"id": None, "stock": 0, "orders": 0, "name": ""}
                    
                    is_in_dropi = res_dropi["id"] is not None
                    is_in_sc = res_sc["id"] is not None
                    
                    if not is_in_dropi and not is_in_sc:
                        logger.warning(f"⚠️ Saltando '{nombre_es}' porque no está disponible en Dropi ni en SmartCommerce Guatemala.")
                        
                        descartado_item = {
                            "tiktok_ingles": prod["producto"],
                            "producto_espanol": nombre_es,
                            "dropi_id": None,
                            "dropi_stock": 0,
                            "dropi_ventas": 0,
                            "smartcommerce_id": None,
                            "smartcommerce_stock": 0,
                            "smartcommerce_ventas": 0,
                            "dropi_search_term_es": nombre_es,
                            "dropi_search_term_en": nombre_en_corta,
                            "meta_search_query": None,
                            "meta_anuncios_activos": None,
                            "ventas_reales_usa": prod.get("ventas_reales", 0),
                            "precio_usd": prod.get("precio_usd"),
                            "url_tiktok_shop": prod.get("url"),
                            "motivo_descarte": "NO_DISPONIBLE_PROVEEDOR"
                        }
                        descartados_sin_proveedor = memoria.get("descartados_sin_proveedor", [])
                        if not any(d["tiktok_ingles"] == prod["producto"] for d in descartados_sin_proveedor):
                            descartados_sin_proveedor.append(descartado_item)
                            memoria["descartados_sin_proveedor"] = descartados_sin_proveedor
                            guardar_memoria(memoria)
                            
                        productos_rechazados.append(prod["producto"])
                        memoria["productos_rechazados"] = productos_rechazados
                        guardar_memoria(memoria)
                        continue
                    
                    logger.info(f"✅ ¡Producto Encontrado! Dropi: {'SÍ' if is_in_dropi else 'NO'} (Stock: {res_dropi['stock']}), SmartCommerce: {'SÍ' if is_in_sc else 'NO'} (Stock: {res_sc['stock']})")
                    
                    candidatos.append({
                        "producto_original": prod["producto"],
                        "producto_espanol": nombre_es,
                        "ventas_reales": prod["ventas_reales"],
                        "precio_usd": prod["precio_usd"],
                        
                        "dropi_id": res_dropi["id"],
                        "dropi_ventas": res_dropi["orders"],
                        "dropi_stock": res_dropi["stock"],
                        
                        "sc_id": res_sc["id"],
                        "sc_ventas": res_sc["orders"],
                        "sc_stock": res_sc["stock"],
                        
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
                logger.info(f"✅ ¡PRODUCTO APROBADO POR META ADS GT! '{nombre_es}' ({ads} anuncios activos en Guatemala)")
                
                productos_encontrados.append(cand["producto_original"])
                memoria["productos_encontrados"] = productos_encontrados
                
                ganador_item = {
                    "tiktok_ingles": cand["producto_original"],
                    "producto_espanol": nombre_es,
                    
                    "dropi_id": cand["dropi_id"],
                    "dropi_stock": cand["dropi_stock"],
                    "dropi_ventas": cand["dropi_ventas"],
                    
                    "smartcommerce_id": cand["sc_id"],
                    "smartcommerce_stock": cand["sc_stock"],
                    "smartcommerce_ventas": cand["sc_ventas"],
                    
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
                    logger.info(f"💾 Guardado ganador en historial_memoria_gt.json: '{nombre_es}'")
                
                memoria["ganadores_detalle"] = ganadores_detalle
                guardar_memoria(memoria)
                
                producto_ganador_definitivo = cand
                termino_ganador_espanol = nombre_es
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
                    "dropi_id": cand["dropi_id"],
                    "dropi_stock": cand["dropi_stock"],
                    "smartcommerce_id": cand["sc_id"],
                    "smartcommerce_stock": cand["sc_stock"],
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
                await asyncio.sleep(2)
        
        if producto_ganador_definitivo:
            break
            
        logger.info(f"🤔 REFLEXIÓN: El nicho/keyword '{nicho_actual}' no arrojó ganadores aprobados. Cambiando de nicho...")
        await asyncio.sleep(2)
        
    logger.info(f"\n🏆 ¡SISTEMA DETENIDO! HEMOS ENCONTRADO EL PRODUCTO GANADOR EN GUATEMALA 🏆")
    logger.info(f"🛍️ Producto (Original): {producto_ganador_definitivo['producto_original']}")
    logger.info(f"🗣️ Nombre Comercial (Guatemala): {termino_ganador_espanol}")
    logger.info(f"📈 Ventas Comprobadas (USA): {producto_ganador_definitivo['ventas_reales']:,}")
    if producto_ganador_definitivo.get("url"):
        logger.info(f"🔗 Enlace TikTok Shop: {producto_ganador_definitivo['url']}")
    
    logger.info("\n📦 --- RESUMEN FINAL DE DISPONIBILIDAD ---")
    
    has_dropi = producto_ganador_definitivo.get("dropi_id") is not None
    has_sc = producto_ganador_definitivo.get("sc_id") is not None
    
    if has_dropi:
        logger.info(f"🎉 Disponible en Dropi Guatemala:")
        logger.info(f"   - ID: {producto_ganador_definitivo['dropi_id']}")
        logger.info(f"   - Stock: {producto_ganador_definitivo['dropi_stock']} unidades")
        logger.info(f"   - Ventas: {producto_ganador_definitivo['dropi_ventas']} órdenes")
        
    if has_sc:
        logger.info(f"🎉 Disponible en SmartCommerce Guatemala:")
        logger.info(f"   - ID: {producto_ganador_definitivo['sc_id']}")
        logger.info(f"   - Stock: {producto_ganador_definitivo['sc_stock']} unidades")
        logger.info(f"   - Ventas: {producto_ganador_definitivo['sc_ventas']} órdenes")
        
    if not has_dropi and not has_sc:
        logger.info("⚠️ El producto no se encuentra disponible localmente en Dropi GT ni en SmartCommerce GT. Requiere importación privada.")

if __name__ == "__main__":
    asyncio.run(mesa_de_trabajo_autonoma())
