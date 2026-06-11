import asyncio
import logging
import aiohttp
import random
import json
from config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("MesaTrabajo")

# --- AGENTE 1: BUSCADOR DE TIKTOK SHOP (VÍA RAPIDAPI) ---
async def agente_tiktok_shop(query: str, page: int = 1) -> list:
    """Extrae productos de TikTok Shop. Simulamos paginación pidiendo más resultados."""
    logger.info(f"🛒 [Agente TikTok] Buscando '{query}' (Página {page})...")
    rapidapi_key = "TU_RAPIDAPI_KEY"
    
    url = "https://tiktok-shop-scraper-api.p.rapidapi.com/shop/search"
    headers = {
        "x-rapidapi-host": "tiktok-shop-scraper-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    
    # Si es página 2, pedimos más límite para simular que avanzamos en la lista
    limit = 10 if page == 1 else 20 
    querystring = {"query": query, "limit": str(limit)}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as response:
            if response.status != 200:
                logger.error("Error en RapidAPI.")
                return []
            
            json_response = await response.json()
            if "error" in json_response:
                return []
                
            raw_data = json_response.get("products", [])
            
            # Si estamos en la página 2, ignoramos los primeros 10 para ver productos nuevos
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
            return productos

# --- AGENTE 2: EVALUADOR DE NEGOCIO ---
def agente_evaluador_negocio(productos: list) -> list:
    """Filtro de Dropshipping: Solo productos con más de 1,000 ventas."""
    ganadores = [p for p in productos if p["ventas_reales"] >= 1000 and p["precio_usd"] >= 0.0]
    ganadores.sort(key=lambda x: x["ventas_reales"], reverse=True)
    return ganadores

# --- AGENTE 3: VALIDADOR DE SATURACIÓN (META ADS CHILE VÍA RAPIDAPI) ---
async def agente_meta_ads_chile(producto_nombre: str) -> dict:
    """
    Busca el producto en la Librería de Anuncios de Facebook para Chile.
    Usa la API 'Facebook Ads Library Scraper API' de RapidAPI.
    """
    rapidapi_key = "TU_RAPIDAPI_KEY"
    logger.info(f"👁️ [Agente Meta] Consultando FB Ads Library Chile para: '{producto_nombre[:40]}...'")
    
    url = "https://facebook-ads-library-scraper-api.p.rapidapi.com/search/ads"
    headers = {
        "x-rapidapi-host": "facebook-ads-library-scraper-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    
    # Para la API de Facebook, a veces los nombres muy largos traen cero resultados.
    # Tomamos solo las primeras 3 o 4 palabras clave más importantes del nombre del producto.
    palabras = producto_nombre.split()
    query_corta = " ".join(palabras[:4])
    
    querystring = {
        "query": query_corta,
        "country_code": "CL",
        "limit": "50"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as response:
            if response.status != 200:
                logger.error(f"Error en RapidAPI FB Scraper: {response.status}")
                return {"anuncios_chile": 99, "estado": "ERROR"}
            
            json_response = await response.json()
            
            # La API de RapidAPI devuelve un 'total_count' y una lista en 'data'
            anuncios_activos = json_response.get("total_count", 0)
            
            # Verificamos si no vinieron ads
            if anuncios_activos == 0 and "data" in json_response:
                anuncios_activos = len(json_response.get("data", []))
            
            estado = "SATURADO"
            if anuncios_activos == 0:
                estado = "OCEANO AZUL"
            elif anuncios_activos <= 5:
                estado = "OPORTUNIDAD"
                
            return {
                "anuncios_chile": anuncios_activos,
                "estado": estado
            }

# --- AGENTE 4: PLANIFICADOR CREATIVO (GEMINI) ---
async def agente_creador_nichos(nichos_rechazados: list) -> list:
    """Si la lista maestra se agota, Gemini crea nichos nuevos."""
    logger.warning("🧠 [Agente Planificador] La lista de palabras clave se agotó. Usando IA para inventar nuevos nichos...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=TU_GEMINI_API_KEY"
    
    prompt = f"""
    Eres un experto buscando productos de dropshipping.
    Ya intentamos buscar estos nichos pero están saturados o no sirven: {', '.join(nichos_rechazados)}.
    Inventa 3 NICHOS NUEVOS, específicos y extraños en inglés. (Ej: 'posture correctors', 'rainproof shoe covers').
    Responde ÚNICAMENTE con los 3 nichos separados por comas, sin texto extra.
    """
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
            if resp.status == 200:
                result = await resp.json()
                respuesta = result['candidates'][0]['content']['parts'][0]['text'].strip()
                nuevos_nichos = [n.strip() for n in respuesta.split(',')]
                logger.info(f"💡 [Agente Planificador] ¡Nuevos nichos creados!: {nuevos_nichos}")
                return nuevos_nichos
    return ["car accessories gadgets", "outdoor camping survival"]


async def agente_traductor_producto(nombre_ingles: str) -> str:
    """Usa Gemini para extraer el nombre genérico del producto en Español (ideal para buscar en Meta Ads)."""
    logger.info(f"🌐 [Agente Traductor] Convirtiendo al español: '{nombre_ingles[:40]}...'")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=TU_GEMINI_API_KEY"
    
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
                    # Limpiamos posibles comillas de la respuesta
                    traduccion = traduccion.replace('"', '').replace("'", "")
                    logger.info(f"✅ [Agente Traductor] Nombre genérico a buscar: '{traduccion}'")
                    return traduccion
                else:
                    logger.warning(f"⏳ [Agente Traductor] Google Gemini ocupado (Error {resp.status}). Reintentando en 5 segundos para no arruinar la evaluación...")
                    await asyncio.sleep(5)


import os
import json

HISTORIAL_FILE = "historial_memoria.json"

def cargar_memoria():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nichos_procesados": [], "productos_rechazados": []}

def guardar_memoria(memoria):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

# --- EL LOOP INFINITO DE REFLEXIÓN ---
async def mesa_de_trabajo_autonoma():
    logger.info("🚀 INICIANDO MESA DE TRABAJO AUTÓNOMA (LOOP INFINITO CON MEMORIA)")
    
    # Cargamos el cerebro (memoria) de sesiones pasadas
    memoria = cargar_memoria()
    nichos_procesados = memoria.get("nichos_procesados", [])
    productos_rechazados = memoria.get("productos_rechazados", [])
    terminos_saturados = memoria.get("terminos_saturados", []) # <-- NUEVO
    
    # La Lista Maestra Inicial (solo usamos los que no están en memoria)
    lista_nichos_base = ["kitchen gadgets", "smart home improvement", "pet anxiety relief"]
    lista_nichos = [n para n in lista_nichos_base if n not in nichos_procesados]
    
    producto_ganador_definitivo = None
    termino_ganador_espanol = None
    
    while not producto_ganador_definitivo:
        # Si nos quedamos sin ideas, la IA inventa más
        if not lista_nichos:
            lista_nichos = await agente_creador_nichos(nichos_procesados)
            
        nicho_actual = lista_nichos.pop(0)
        if nicho_actual not in nichos_procesados:
            nichos_procesados.append(nicho_actual)
            memoria["nichos_procesados"] = nichos_procesados
            guardar_memoria(memoria)
        
        logger.info(f"\n{'='*70}\n🔄 NUEVO CICLO | Nicho Objetivo: '{nicho_actual}'\n{'='*70}")
        
        for pagina in [1, 2]:
            logger.info(f"📄 Explorando página {pagina} de TikTok Shop...")
            
            await asyncio.sleep(3) 
            
            productos_crudos = await agente_tiktok_shop(nicho_actual, page=pagina)
            
            if not productos_crudos:
                logger.warning("No hay productos aquí.")
                continue
                
            productos_validos = agente_evaluador_negocio(productos_crudos)
            
            if not productos_validos:
                logger.warning("Hay productos, pero ninguno supera las 1,000 ventas. Descartados.")
                continue
                
            for prod in productos_validos[:2]:
                
                if prod["producto"] in productos_rechazados:
                    logger.info(f"⏭️  [Memoria] Saltando producto en inglés ya analizado: '{prod['producto'][:30]}...'")
                    continue
                
                # 1. TRADUCCIÓN E INTELIGENCIA
                termino_espanol = await agente_traductor_producto(prod["producto"])
                
                # CHECK DE MEMORIA MAESTRO: ¿Ya sabemos que esta palabra en español está saturada?
                if termino_espanol in terminos_saturados:
                    logger.info(f"⏭️  [Memoria Meta Ads] Saltando '{termino_espanol}', ya sabemos que está SATURADO en Chile.")
                    continue
                
                # 2. BÚSQUEDA EN META ADS CON EL TÉRMINO EN ESPAÑOL
                await asyncio.sleep(2) 
                evaluacion_meta = await agente_meta_ads_chile(termino_espanol)
                
                estado = evaluacion_meta["estado"]
                ads = evaluacion_meta["anuncios_chile"]
                
                if estado in ["OCEANO AZUL", "OPORTUNIDAD"]:
                    logger.info(f"✅ ¡PRODUCTO APROBADO POR META ADS! ({ads} anuncios en Chile para '{termino_espanol}')")
                    logger.info(f"  👉 Nombre Original: {prod['producto']}")
                    logger.info(f"  👉 Ventas Globales: {prod['ventas_reales']:,}")
                    producto_ganador_definitivo = prod
                    termino_ganador_espanol = termino_espanol
                    break
                else:
                    logger.warning(f"❌ RECHAZADO: '{termino_espanol}' tiene demasiados anuncios en Chile ({ads}).")
                    # Guardamos el producto en inglés y la palabra en español para nunca más tocarlos
                    productos_rechazados.append(prod["producto"])
                    if termino_espanol not in terminos_saturados:
                        terminos_saturados.append(termino_espanol)
                        
                    memoria["productos_rechazados"] = productos_rechazados
                    memoria["terminos_saturados"] = terminos_saturados
                    guardar_memoria(memoria)
            
            if producto_ganador_definitivo:
                break
                
        if producto_ganador_definitivo:
            break # Rompe el While Loop infinito!
            
        logger.info(f"🤔 REFLEXIÓN: El nicho '{nicho_actual}' está quemado o no sirve. Cambiando de estrategia...")
        await asyncio.sleep(2) # Pausa dramática entre nichos
        
    logger.info(f"\n🏆 ¡SISTEMA DETENIDO! HEMOS ENCONTRADO EL PRODUCTO PERFECTO PARA CHILE 🏆")
    logger.info(f"🛍️ Producto (Original): {producto_ganador_definitivo['producto']}")
    logger.info(f"🗣️ Nombre Comercial (Chile): {termino_ganador_espanol}")
    logger.info(f"📈 Ventas Comprobadas (EE.UU): {producto_ganador_definitivo['ventas_reales']:,}")
    logger.info("Siguiente paso sugerido: Enviar este producto al Agente Dropi para verificar stock en bodega chilena.")

if __name__ == "__main__":
    asyncio.run(mesa_de_trabajo_autonoma())
