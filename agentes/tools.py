import os
import json
import asyncio
import aiohttp
import logging
import base64
from typing import Optional
from agentes.config import settings, logger, HISTORIAL_FILE
from utils import dropi_helper
from utils.api_cache import get_cached_response, set_cached_response

# ============================================================================
# UTILS & MEMORY
# ============================================================================

def cargar_memoria() -> dict:
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                mem = json.load(f)
                for key in ["nichos_procesados", "productos_rechazados", "terminos_saturados", 
                            "descartados_sin_proveedor", "descartados_saturados", 
                            "ganadores_detalle", "productos_encontrados",
                            "descartados_baja_traccion_global", "descartados_estacionales",
                            "descartados_competencia_longeva"]:
                    if key not in mem:
                        mem[key] = []
                return mem
        except Exception as e:
            logger.error(f"❌ Error crítico al cargar memoria (JSON corrupto o inaccesible): {e}")
            raise e
            
    return {
        "nichos_procesados": [],
        "productos_rechazados": [],
        "terminos_saturados": [],
        "descartados_sin_proveedor": [],
        "descartados_saturados": [],
        "ganadores_detalle": [],
        "productos_encontrados": [],
        "descartados_baja_traccion_global": [],
        "descartados_estacionales": [],
        "descartados_competencia_longeva": []
    }

def guardar_memoria(memoria: dict):
    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(memoria, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error guardando memoria: {e}")

# ============================================================================
# AGENT TOOLS
# ============================================================================

async def obtener_estado_memoria() -> dict:
    """
    Obtiene el estado actual de la memoria histórica (nichos procesados, cantidad de productos rechazados/encontrados
    y ganadores recientes). Úsalo al inicio para saber qué nichos evitar.
    """
    mem = cargar_memoria()
    return {
        "nichos_procesados": mem["nichos_procesados"],
        "total_productos_encontrados": len(mem["productos_encontrados"]),
        "total_productos_rechazados": len(mem["productos_rechazados"]),
        "ganadores_recientes": [g["producto_espanol"] for g in mem["ganadores_detalle"][-10:]]
    }

async def registrar_nicho_procesado(nicho: str) -> dict:
    """
    Registra un nicho como procesado en la memoria para no volver a evaluarlo.
    """
    mem = cargar_memoria()
    if nicho not in mem["nichos_procesados"]:
        mem["nichos_procesados"].append(nicho)
        guardar_memoria(mem)
        logger.info(f"💾 Guardado nicho procesado en memoria: '{nicho}'")
    return {"status": "success", "nicho": nicho}

async def registrar_producto_rechazado(producto_ingles: str) -> dict:
    """
    Registra un producto en inglés como rechazado en la memoria para no volver a evaluarlo.
    """
    mem = cargar_memoria()
    if producto_ingles not in mem["productos_rechazados"]:
        mem["productos_rechazados"].append(producto_ingles)
        guardar_memoria(mem)
        logger.info(f"💾 Guardado producto rechazado en memoria: '{producto_ingles}'")
    return {"status": "success", "producto": producto_ingles}

async def registrar_ganador(producto: dict) -> dict:
    """
    Registra un producto ganador aprobado con éxito por el orquestador en el archivo de memoria.
    Recibe un diccionario con los campos del ganador.
    """
    mem = cargar_memoria()
    # Evitar duplicados en detalle (por título de TikTok o por ID de Dropi)
    ya_existe = any(
        g["tiktok_ingles"] == producto.get("producto_original") or 
        (g.get("dropi_id") is not None and g.get("dropi_id") == producto.get("dropi_id"))
        for g in mem["ganadores_detalle"]
    )
    if not ya_existe:
        ganador_item = {
            "tiktok_ingles": producto.get("producto_original"),
            "producto_espanol": producto.get("producto_espanol"),
            "dropi_id": producto.get("dropi_id"),
            "ventas_locales_dropi": producto.get("dropi_ventas", 0),
            "stock_local_dropi": producto.get("dropi_stock", 0),
            "meta_search_query": producto.get("producto_espanol"),
            "meta_anuncios_activos": producto.get("meta_anuncios_activos", 0),
            "estado_meta": producto.get("estado_meta", "OPORTUNIDAD"),
            "ventas_reales_usa": producto.get("ventas_reales", 0),
            "precio_usd": producto.get("precio_usd", 0.0),
            "url_tiktok_shop": producto.get("url"),
            "dias_anuncio_mas_antiguo": producto.get("dias_anuncio_mas_antiguo", 0)
        }
        mem["ganadores_detalle"].append(ganador_item)
        if producto.get("producto_original") not in mem["productos_encontrados"]:
            mem["productos_encontrados"].append(producto.get("producto_original"))
        guardar_memoria(mem)
        logger.info(f"🏆 ¡REGISTRADO PRODUCTO GANADOR!: '{producto.get('producto_espanol')}'")
        return {"status": "success", "producto": producto.get("producto_espanol")}
    return {"status": "already_exists"}

async def buscar_productos_virales_tiktok(query: str, page: int = 1) -> dict:
    """
    Busca productos virales en TikTok Shop para una palabra clave.
    Retorna solo aquellos productos con ventas comprobadas de más de 10,000 unidades en EE.UU.
    """
    cache_key = f"{query}_page_{page}"
    cached = get_cached_response("tiktok_shop", cache_key)
    
    if cached is not None:
        logger.info(f"💾 [CACHE HIT] TikTok Shop -> '{cache_key}'")
        productos = cached
    else:
        logger.info(f"🛒 [Agente TikTok] Buscando '{query}' en TikTok Shop...")
        rapidapi_key = settings.rapidapi_key
        url = "https://tiktok-shop-scraper-api.p.rapidapi.com/shop/search"
        headers = {
            "x-rapidapi-host": "tiktok-shop-scraper-api.p.rapidapi.com",
            "x-rapidapi-key": rapidapi_key
        }
        querystring = {"query": query, "limit": "100"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=querystring, timeout=15) as response:
                    if response.status != 200:
                        return {"status": "error", "message": f"HTTP {response.status}", "products": []}
                    json_resp = await response.json()
                    raw_data = json_resp.get("products", [])
                    if page > 1:
                        raw_data = raw_data[10:]
                        
                    productos = []
                    for item in raw_data:
                        titulo = item.get("title", "Desconocido")
                        ventas = item.get("sold_info", {}).get("sold_count", 0) if item.get("sold_info") else 0
                        precio = float(item.get("price_info", {}).get("price_decimal", 0)) if item.get("price_info") else 0.0
                        url_prod = item.get("seo_url", {}).get("canonical_url", "")
                        
                        image_url_tk = ""
                        if item.get("cover"):
                            cov = item.get("cover")
                            if isinstance(cov, dict):
                                image_url_tk = cov.get("url", "") or (cov.get("url_list", [""])[0] if cov.get("url_list") else "")
                            else:
                                image_url_tk = str(cov)
                        elif item.get("image"):
                            image_url_tk = str(item.get("image"))
                            
                        if titulo != "Desconocido" and ventas >= 10000:
                            productos.append({
                                "producto": titulo,
                                "ventas_reales": ventas,
                                "precio_usd": precio,
                                "url": url_prod,
                                "imagen_tiktok": image_url_tk
                            })
                    set_cached_response("tiktok_shop", cache_key, productos)
        except Exception as e:
            return {"status": "error", "message": str(e), "products": []}
            
    # Filtrar según los ya rechazados o encontrados
    mem = cargar_memoria()
    excluidos = set(mem["productos_rechazados"] + mem["productos_encontrados"])
    candidatos = [p for p in productos if p["producto"] not in excluidos]
    candidatos.sort(key=lambda x: x["ventas_reales"], reverse=True)
    
    return {
        "status": "success",
        "total_encontrados": len(productos),
        "candidatos_nuevos": candidatos[:15]  # Devolver máximo 15 principales para no sobrecargar
    }

# ============================================================================
# BATCH HELPERS (TRANSLATION & VALIDATION)
# ============================================================================

async def agente_traductor_lote_productos(nombres_ingles: list) -> list:
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
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    prompt = f"""
    Eres un experto en e-commerce latinoamericano.
    Traduce esta lista de productos de inglés a un concepto genérico corto (máx 3 palabras) en español para Chile:
    {json.dumps(nombres_a_traducir, indent=2)}
    Responde ÚNICAMENTE con una lista JSON de strings en el mismo orden. No incluyas markdown ni explicaciones.
    """
    
    async with aiohttp.ClientSession() as session:
        for _ in range(3):
            try:
                async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                        if texto.startswith("```"):
                            lines = texto.split("\n")
                            if lines[0].startswith("```"): lines = lines[1:]
                            if lines[-1].startswith("```"): lines = lines[:-1]
                            texto = "\n".join(lines).strip()
                        decisiones = json.loads(texto)
                        if isinstance(decisiones, list) and len(decisiones) == len(nombres_a_traducir):
                            for n_en, n_es in zip(nombres_a_traducir, decisiones):
                                set_cached_response("gemini_translator", n_en, n_es)
                                result_map[n_en] = n_es
                            break
            except Exception as e:
                logger.error(f"Error en traductor lote: {e}")
            await asyncio.sleep(2)
            
    return [result_map.get(n, n[:20]) for n in nombres_ingles]

async def descargar_imagen_base64(url: str, session: aiohttp.ClientSession) -> Optional[dict]:
    if not url or not url.startswith("http"):
        return None
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                content_type = resp.headers.get("Content-Type", "")
                mime_type = "image/jpeg"
                if "png" in content_type.lower():
                    mime_type = "image/png"
                elif "webp" in content_type.lower():
                    mime_type = "image/webp"
                data = await resp.read()
                if len(data) > 0:
                    b64_str = base64.b64encode(data).decode("utf-8")
                    return {"mime_type": mime_type, "data": b64_str}
    except Exception as e:
        logger.debug(f"No se pudo descargar la imagen {url}: {e}")
    return None

async def verificar_imagen_concordancia_gemini(cand: dict) -> bool:
    url_tk = cand.get("imagen_tiktok")
    url_dr = cand.get("dropi_imagen")
    if not url_tk or not url_dr:
        return True # Si no hay imágenes, asumimos que el texto es suficiente
        
    cache_key = f"img_{url_tk}_{url_dr}"
    cached = get_cached_response("gemini_image_validation", cache_key)
    if cached is not None:
        return cached
        
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
    
    async with aiohttp.ClientSession() as session:
        # Descargar ambas imágenes en paralelo
        task_tk = descargar_imagen_base64(url_tk, session)
        task_dr = descargar_imagen_base64(url_dr, session)
        img_tk, img_dr = await asyncio.gather(task_tk, task_dr)
        
        if not img_tk or not img_dr:
            return True
            
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Compara visualmente estas dos imágenes de producto de e-commerce. "
                                    "La primera es el producto anunciado en redes sociales (TikTok), la segunda es el producto en el catálogo local. "
                                    "¿Representan visualmente el mismo artículo en cuanto a diseño, tipo y función principal? "
                                    "Si uno es un accesorio para auto y el otro es para el hogar, o son diseños completamente disímiles, responde false. "
                                    "Responde ÚNICAMENTE con 'true' o 'false'."
                        },
                        {
                            "inlineData": {
                                "mimeType": img_tk["mime_type"],
                                "data": img_tk["data"]
                            }
                        },
                        {
                            "inlineData": {
                                "mimeType": img_dr["mime_type"],
                                "data": img_dr["data"]
                            }
                        }
                    ]
                }
            ]
        }
        
        for _ in range(3):
            try:
                async with session.post(url_api, json=payload, timeout=20) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip().lower()
                        es_compatible = "true" in texto
                        set_cached_response("gemini_image_validation", cache_key, es_compatible)
                        return es_compatible
            except Exception as e:
                logger.error(f"Error en validación de imagen Gemini: {e}")
            await asyncio.sleep(2)
            
    return True

async def agente_validador_concordancia_lote_gemini(candidatos: list) -> list:
    if not candidatos: return []
    resultado_map = {}
    candidatos_a_validar = []
    
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
        salida = [
            (cand, resultado_map[f"{cand['producto_original']}_{cand['producto_espanol']}_{cand.get('dropi_nombre_catalogo', '')}"])
            for cand in candidatos
        ]
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
        lista_comparar = [
            {
                "id": idx,
                "original_ingles": cand["producto_original"],
                "traduccion_espanol": cand["producto_espanol"],
                "catalogo_proveedor": cand.get("dropi_nombre_catalogo", ""),
                "descripcion_proveedor": cand.get("dropi_descripcion", "")[:500],
                "precio_venta_tiktok_usd": cand["precio_usd"],
                "precio_costo_dropi_clp": cand.get("costo_clp", 0.0)
            }
            for idx, cand in enumerate(candidatos_a_validar)
        ]
        
        prompt = f"""
        Eres un auditor de catálogos de e-commerce y experto en sourcing de productos.
        Valida si estas coincidencias de búsqueda entre el producto de TikTok y el del catálogo local son correctas (MISMO TIPO de artículo básico, mismas características críticas) o si son falsos positivos.
        
        Reglas estrictas de descarte:
        1. Si un artículo de TikTok es eléctrico, automático, recargable o robótico, y el de Dropi es manual o simple (o viceversa), es un FALSO POSITIVO (debe ser false). Ejemplo: cojín cervical robótico/masajeador vs cojín de espuma simple.
        2. Si el producto de TikTok es para un entorno o uso altamente específico (ej. organizador para el asiento del auto, tapabarros de bicicleta) y el de Dropi es un artículo genérico (ej. organizador de clóset multiuso para el hogar), es un FALSO POSITIVO (debe ser false).
        3. Si hay una discrepancia enorme de precio (ej. el precio de costo de Dropi en CLP equivale a menos del 5% del valor de venta de TikTok en USD), sospecha que el artículo de Dropi es una pieza/repuesto o un artículo mucho más simple, por lo tanto marca false.
        
        Lista de comparación:
        {json.dumps(lista_comparar, indent=2, ensure_ascii=False)}
        
        Responde ÚNICAMENTE con una lista JSON de booleanos (true/false) en el mismo orden de los elementos. Sin markdown ni texto extra.
        Ejemplo: [true, false, true]
        """
        
        async with aiohttp.ClientSession() as session:
            for _ in range(3):
                try:
                    async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                        if resp.status == 200:
                            res_json = await resp.json()
                            texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                            if texto.startswith("```"):
                                lines = texto.split("\n")
                                if lines[0].startswith("```"): lines = lines[1:]
                                if lines[-1].startswith("```"): lines = lines[:-1]
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
                                break
                except Exception as e:
                    logger.error(f"Error en validador lote: {e}")
                await asyncio.sleep(2)
                
        salida = []
        for cand in candidatos:
            orig = cand["producto_original"]
            esp = cand["producto_espanol"]
            cat = cand.get("dropi_nombre_catalogo", "")
            cache_key = f"{orig}_{esp}_{cat}"
            salida.append((cand, resultado_map.get(cache_key, True)))
            
    # 2. Validación de imágenes en paralelo para los compatibles por texto
    tareas_img = []
    indices_compatibles = []
    for idx, (cand, compatible) in enumerate(salida):
        if compatible:
            tareas_img.append(verificar_imagen_concordancia_gemini(cand))
            indices_compatibles.append(idx)
            
    if tareas_img:
        resultados_img = await asyncio.gather(*tareas_img)
        for idx, es_compatible_img in zip(indices_compatibles, resultados_img):
            cand = salida[idx][0]
            if not es_compatible_img:
                logger.warning(f"📸 [Falso Positivo por Imagen] '{cand['producto_espanol']}' y '{cand['dropi_nombre_catalogo']}' no coinciden visualmente.")
            salida[idx] = (cand, es_compatible_img)
            
    return salida

async def procesar_candidato_dropi(prod: dict, nombre_es: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        import re
        palabras_ingles = [w for w in prod["producto"].split() if len(w) > 3]
        nombre_en_corta = " ".join(palabras_ingles[:3])
        nombre_en_muy_corta = " ".join(palabras_ingles[:2])
        
        res_final = {"id": 123456, "stock": 0, "orders": 0, "name": ""}
        
        # 1. Búsqueda en Español Completa
        res_es = await dropi_helper.search_dropi_product(nombre_es)
        if res_es["id"] not in [123456, 999999]:
            res_final = res_es
        else:
            # 2. Búsqueda en Español Corta (hasta 3 palabras clave)
            palabras_es = [w for w in nombre_es.split() if len(w) > 3]
            nombre_es_corta = " ".join(palabras_es[:3]) if palabras_es else ""
            res_es_c = await dropi_helper.search_dropi_product(nombre_es_corta) if nombre_es_corta else {"id": 123456}
            if res_es_c.get("id") not in [123456, 999999]:
                res_final = res_es_c
            else:
                # 3. Búsqueda en Español Muy Corta (2 palabras clave)
                nombre_es_muy_corta = " ".join(palabras_es[:2]) if len(palabras_es) >= 2 else ""
                res_es_mc = await dropi_helper.search_dropi_product(nombre_es_muy_corta) if nombre_es_muy_corta else {"id": 123456}
                if res_es_mc.get("id") not in [123456, 999999]:
                    res_final = res_es_mc
                else:
                    # 4. Búsqueda en Inglés Corta
                    res_en = await dropi_helper.search_dropi_product(nombre_en_corta)
                    if res_en["id"] not in [123456, 999999]:
                        res_final = res_en
                    else:
                        # 5. Búsqueda en Inglés Muy Corta
                        if nombre_en_muy_corta:
                            res_muy_corta = await dropi_helper.search_dropi_product(nombre_en_muy_corta)
                            if res_muy_corta["id"] not in [123456, 999999]:
                                res_final = res_muy_corta
        
        dropi_id = res_final["id"]
        stock_val = res_final.get("stock", 0)
        
        # Filtro de stock mínimo: descartar si hay menos de 30 unidades
        if dropi_id in [123456, 999999]:
            motivo = "NO_DISPONIBLE_PROVEEDOR"
        elif stock_val < 30:
            motivo = "BAJO_STOCK"
        else:
            motivo = None
            
        if motivo:
            descartado_item = {
                "tiktok_ingles": prod["producto"],
                "producto_espanol": nombre_es,
                "dropi_id": None if dropi_id in [123456, 999999] else dropi_id,
                "ventas_locales_dropi": res_final.get("orders", 0),
                "stock_local_dropi": stock_val,
                "dropi_search_term_es": nombre_es,
                "dropi_search_term_en": nombre_en_corta,
                "meta_search_query": None,
                "meta_anuncios_activos": None,
                "ventas_reales_usa": prod.get("ventas_reales", 0),
                "precio_usd": prod.get("precio_usd"),
                "url_tiktok_shop": prod.get("url"),
                "motivo_descarte": motivo
            }
            if motivo == "BAJO_STOCK":
                logger.warning(f"⚠️ [Bajo Stock] '{nombre_es}' en Dropi tiene solo {stock_val} unidades. Se descarta.")
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
                "imagen_tiktok": prod.get("imagen_tiktok", ""),
                "dropi_id": dropi_id,
                "dropi_ventas": res_final["orders"],
                "dropi_stock": stock_val,
                "dropi_search_term_es": nombre_es,
                "dropi_search_term_en": nombre_en_corta,
                "dropi_nombre_catalogo": res_final.get("name", ""),
                "dropi_descripcion": res_final.get("description", ""),
                "dropi_imagen": res_final.get("image", ""),
                "costo_clp": res_final.get("price", 0.0),
                "url": prod.get("url")
            }
        }

# ============================================================================
# TRACTION & SEASONALITY HELPERS
# ============================================================================

async def consultar_traccion_global_web(producto_ingles: str) -> bool:
    import urllib.parse
    import re
    
    # 1. Limpieza inicial del título
    clean_title = re.sub(r'[\d\-\|\#\【\】\［\］\[\]\(\)\★\☆\•\✔\✓\＆\&]', ' ', producto_ingles)
    # Remover marcas comunes o términos promocionales
    clean_title = re.sub(r'\b(super brand day|deals for you|deals|summervibes|summerwins|upgrade|new|professional|innovative|trending|viral|smart)\b', '', clean_title, flags=re.IGNORECASE)
    
    palabras = [w for w in clean_title.split() if len(w) > 2]
    # Tomar las primeras 4 palabras significativas
    term_search = " ".join(palabras[:4])
    
    if not term_search:
        return True # fail-safe si queda vacío
        
    query = f'(site:aliexpress.com OR site:amazon.com) {term_search}'
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    amzn_count = html.count("amazon.com")
                    alie_count = html.count("aliexpress.com")
                    
                    if amzn_count + alie_count >= 2:
                        return True
    except Exception as e:
        logger.error(f"Error consultando tracción Yahoo para {producto_ingles}: {e}")
        return True # Fail-safe para no descartar si falla la red
        
    return False

async def consultar_estacionalidad_trends(producto_espanol: str) -> bool:
    import urllib.parse
    kw = producto_espanol.lower()
    url = f"https://trends.google.com/trends/api/explore?hl=es&tz=240&req=%7B%22comparisonItem%22%3A%5B%7B%22keyword%22%3A%22{urllib.parse.quote(kw)}%22%2C%22geo%22%3A%22CL%22%2C%22time%22%3A%22today+12-m%22%7D%5D%2C%22category%22%3A0%2C%22property%22%3A%22%22%7D"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=8) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if text.startswith(")]}'"):
                        text = text[4:]
                    data = json.loads(text)
                    widgets = data.get("widgets", [])
                    if widgets:
                        return True
    except Exception as e:
        logger.warning(f"Error consultando Google Trends: {e}. Usando validador estacional alternativo.")
        
    from datetime import datetime
    mes_actual = datetime.now().month
    
    conceptos_invierno = ["calefactor", "calefaccion", "estufa", "termico", "invierno", "frio", "manta electrica", "calentador"]
    conceptos_verano = ["ventilador", "enfriador", "piscina", "playa", "verano", "calor", "aire acondicionado", "quitasol"]
    
    if mes_actual in [12, 1, 2, 3]:
        if any(c in kw for c in conceptos_invierno):
            logger.info(f"❄️ [Filtro Estacional] Producto de invierno '{producto_espanol}' detectado en pleno verano chileno.")
            return False
            
    if mes_actual in [6, 7, 8, 9]:
        if any(c in kw for c in conceptos_verano):
            logger.info(f"☀️ [Filtro Estacional] Producto de verano '{producto_espanol}' detectado en pleno invierno chileno.")
            return False
            
    return True

def es_producto_duplicado(nombre_nuevo: str, nombres_existentes: list) -> bool:
    """
    Compara el nombre en español de un candidato con los nombres de productos
    ya registrados o descartados para evitar registrar variantes semánticas
    del mismo producto (ej: 'Aspiradora portátil auto' vs 'Aspiradora 4 en 1').
    """
    import re
    def normalizar(texto):
        texto = texto.lower().strip()
        texto = texto.translate(str.maketrans("áéíóúü", "aeiouu"))
        texto = re.sub(r'[^\w\s]', '', texto)
        return [w for w in texto.split() if w]

    palabras_nuevo = normalizar(nombre_nuevo)
    if not palabras_nuevo:
        return False
        
    primer_palabra_nueva = palabras_nuevo[0]
    
    # Nombres genéricos que sí se pueden repetir (ej. organizador de cocina vs organizador de auto)
    palabras_genericas = {"organizador", "soporte", "caja", "set", "bolsa", "kit", "dispensador", "limpiador", "foco", "tabla"}
    
    for exist in nombres_existentes:
        palabras_exist = normalizar(exist)
        if not palabras_exist:
            continue
        
        primer_palabra_exist = palabras_exist[0]
        
        # 1. Si la primera palabra coincide y NO es genérica, es duplicado
        if primer_palabra_nueva == primer_palabra_exist and primer_palabra_nueva not in palabras_genericas:
            return True
            
        # 2. Si comparten al menos 2 palabras clave importantes
        stop_words = {"de", "para", "con", "en", "el", "la", "los", "las", "un", "una", "y", "o", "a", "al", "del", "por", "sin", "muy", "doble", "portatil", "inalambrica", "inalambrico", "multiuso"}
        keywords_nuevo = {w for w in palabras_nuevo if w not in stop_words}
        keywords_exist = {w for w in palabras_exist if w not in stop_words}
        
        if len(keywords_nuevo.intersection(keywords_exist)) >= 2:
            return True
            
    return False

async def validar_inventario_proveedor_lote(candidatos: list) -> dict:
    """
    Toma una lista de candidatos obtenidos de TikTok (mínimo 1, máximo 15),
    traduce automáticamente los nombres en lote a español, busca su stock y precio
    en Dropi Chile (en paralelo) y realiza una validación semántica inteligente en lote.
    También valida tracción global (AliExpress/Amazon) y estacionalidad en Google Trends.
    Retorna la lista de candidatos que SÍ están disponibles y coinciden correctamente.
    """
    if not candidatos:
        return {"status": "success", "candidatos_disponibles": []}
        
    logger.info(f"📦 [Sourcing Agent] Evaluando disponibilidad en Dropi para {len(candidatos)} candidatos...")
    
    nombres_ingles = [c["producto"] for c in candidatos]
    nombres_espanol = await agente_traductor_lote_productos(nombres_ingles)
    
    # Cargar memoria para filtrar por traducción en español ya evaluada anteriormente o por ID de Dropi procesado
    mem = cargar_memoria()
    terminos_procesados_es = set()
    dropi_ids_procesados = set()
    nombres_existentes_es = []
    for cat in ["descartados_sin_proveedor", "descartados_saturados", 
                 "descartados_baja_traccion_global", "descartados_estacionales", 
                 "descartados_competencia_longeva"]:
        for item in mem.get(cat, []):
            if "producto_espanol" in item and item["producto_espanol"]:
                terminos_procesados_es.add(item["producto_espanol"].lower().strip())
                nombres_existentes_es.append(item["producto_espanol"])
            if "dropi_id" in item and item["dropi_id"] is not None:
                dropi_ids_procesados.add(item["dropi_id"])
    for item in mem.get("ganadores_detalle", []):
        if "producto_espanol" in item and item["producto_espanol"]:
            terminos_procesados_es.add(item["producto_espanol"].lower().strip())
            nombres_existentes_es.append(item["producto_espanol"])
        if "dropi_id" in item and item["dropi_id"] is not None:
            dropi_ids_procesados.add(item["dropi_id"])
            
    candidatos_filtrados = []
    nombres_espanol_filtrados = []
    mem_modificada = False
    
    for prod, nombre_es in zip(candidatos, nombres_espanol):
        nombre_clean = nombre_es.lower().strip()
        if nombre_clean in terminos_procesados_es or es_producto_duplicado(nombre_es, nombres_existentes_es):
            logger.info(f"⏭️ [Saltando Duplicado Semántico] '{nombre_es}' ya ha sido procesado o es muy similar a uno existente.")
            if prod["producto"] not in mem["productos_rechazados"]:
                mem["productos_rechazados"].append(prod["producto"])
                mem_modificada = True
        else:
            candidatos_filtrados.append(prod)
            nombres_espanol_filtrados.append(nombre_es)
            
    if mem_modificada:
        guardar_memoria(mem)
        
    if not candidatos_filtrados:
        return {"status": "success", "candidatos_disponibles": []}
        
    sem_dropi = asyncio.Semaphore(3)
    tasks = [
        procesar_candidato_dropi(prod, nombre_es, sem_dropi)
        for prod, nombre_es in zip(candidatos_filtrados, nombres_espanol_filtrados)
    ]
    resultados_dropi = await asyncio.gather(*tasks)
    
    candidatos_validos_dropi = []
    descartados_sin_proveedor = []
    
    for res in resultados_dropi:
        if res:
            if res["status"] == "VALID":
                cand = res["candidate"]
                dropi_id = cand["dropi_id"]
                if dropi_id in dropi_ids_procesados:
                    logger.info(f"⏭️ [Saltando Duplicado por ID] '{cand['producto_espanol']}' (Dropi ID: {dropi_id}) ya fue procesado/registrado anteriormente.")
                    if cand["producto_original"] not in mem["productos_rechazados"]:
                        mem["productos_rechazados"].append(cand["producto_original"])
                        mem_modificada = True
                else:
                    candidatos_validos_dropi.append(cand)
            else:
                desc = res["descartado_item"]
                descartados_sin_proveedor.append(desc)
                if desc["tiktok_ingles"] not in mem["productos_rechazados"]:
                    mem["productos_rechazados"].append(desc["tiktok_ingles"])
                    
    # Guardar descartados sin proveedor inmediatos y memoria modificada
    if descartados_sin_proveedor or mem_modificada:
        for d in descartados_sin_proveedor:
            if not any(x["tiktok_ingles"] == d["tiktok_ingles"] for x in mem["descartados_sin_proveedor"]):
                mem["descartados_sin_proveedor"].append(d)
        guardar_memoria(mem)
        
    candidatos_finales = []
    if candidatos_validos_dropi:
        concordantes = await agente_validador_concordancia_lote_gemini(candidatos_validos_dropi)
        for cand, es_compatible in concordantes:
            if es_compatible:
                candidatos_finales.append(cand)
            else:
                logger.warning(f"⚠️ [Falso Positivo Evitado] '{cand['producto_espanol']}' no coincide semánticamente con '{cand['dropi_nombre_catalogo']}'")
                desc = {
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
                if not any(x["tiktok_ingles"] == desc["tiktok_ingles"] for x in mem["descartados_sin_proveedor"]):
                    mem["descartados_sin_proveedor"].append(desc)
                if cand["producto_original"] not in mem["productos_rechazados"]:
                    mem["productos_rechazados"].append(cand["producto_original"])
                    
        # --- NUEVOS FILTROS: TRACCION GLOBAL Y ESTACIONALIDAD ---
        candidatos_verificados = []
        for cand in candidatos_finales:
            tiene_traccion = await consultar_traccion_global_web(cand["producto_original"])
            es_viable_estacional = await consultar_estacionalidad_trends(cand["producto_espanol"])
            
            if not tiene_traccion:
                logger.warning(f"⚠️ [Baja Tracción Global] '{cand['producto_espanol']}' no muestra suficiente actividad en Amazon o AliExpress. Se descarta.")
                desc = {
                    "tiktok_ingles": cand["producto_original"],
                    "producto_espanol": cand["producto_espanol"],
                    "dropi_id": cand["dropi_id"],
                    "ventas_locales_dropi": cand["dropi_ventas"],
                    "stock_local_dropi": cand["dropi_stock"],
                    "dropi_search_term_es": cand["producto_espanol"],
                    "dropi_search_term_en": cand["dropi_search_term_en"],
                    "ventas_reales_usa": cand["ventas_reales"],
                    "precio_usd": cand["precio_usd"],
                    "url_tiktok_shop": cand["url"],
                    "motivo_descarte": "BAJA_TRACCION_GLOBAL"
                }
                if not any(x["tiktok_ingles"] == desc["tiktok_ingles"] for x in mem["descartados_baja_traccion_global"]):
                    mem["descartados_baja_traccion_global"].append(desc)
                if cand["producto_original"] not in mem["productos_rechazados"]:
                    mem["productos_rechazados"].append(cand["producto_original"])
            elif not es_viable_estacional:
                logger.warning(f"⚠️ [Estacionalidad] '{cand['producto_espanol']}' está fuera de temporada o tiene tendencia baja en Chile. Se descarta.")
                desc = {
                    "tiktok_ingles": cand["producto_original"],
                    "producto_espanol": cand["producto_espanol"],
                    "dropi_id": cand["dropi_id"],
                    "ventas_locales_dropi": cand["dropi_ventas"],
                    "stock_local_dropi": cand["dropi_stock"],
                    "dropi_search_term_es": cand["producto_espanol"],
                    "dropi_search_term_en": cand["dropi_search_term_en"],
                    "ventas_reales_usa": cand["ventas_reales"],
                    "precio_usd": cand["precio_usd"],
                    "url_tiktok_shop": cand["url"],
                    "motivo_descarte": "ESTACIONAL"
                }
                if not any(x["tiktok_ingles"] == desc["tiktok_ingles"] for x in mem["descartados_estacionales"]):
                    mem["descartados_estacionales"].append(desc)
                if cand["producto_original"] not in mem["productos_rechazados"]:
                    mem["productos_rechazados"].append(cand["producto_original"])
            else:
                candidatos_verificados.append(cand)
                
        candidatos_finales = candidatos_verificados
        guardar_memoria(mem)
        
    # Limpiar campos pesados para no sobrecargar el historial de tokens de Gemini
    for cand in candidatos_finales:
        cand.pop("dropi_descripcion", None)
        cand.pop("dropi_imagen", None)
        cand.pop("imagen_tiktok", None)
        
    return {
        "status": "success",
        "candidatos_disponibles": candidatos_finales
    }

# ============================================================================
# META ADS SATURATION
# ============================================================================

async def agente_meta_ads_chile(producto_nombre: str) -> dict:
    import urllib.parse
    cached = get_cached_response("meta_ads", producto_nombre)
    if cached is not None:
        return cached

    palabras = producto_nombre.split()
    query_corta = " ".join(palabras[:4])
    palabras_clave_busqueda = [w.lower() for w in query_corta.split() if len(w) > 3]

    def determinar_estado_y_conteo(resultados):
        from datetime import datetime
        anuncios_activos = 0
        dias_maximo = 0
        fecha_actual = datetime.now()
        
        for ad in resultados:
            if ad.get("is_active", False) == True or ad.get("is_active") is None:
                ad_text = ""
                for key in ["adSnapshotText", "ad_snapshot_text", "snapshotText", "adCreativeBody", "ad_creative_body", "title", "body"]:
                    val = ad.get(key)
                    if val:
                        if isinstance(val, list): ad_text += " " + " ".join([str(v) for v in val])
                        else: ad_text += " " + str(val)
                ad_text = ad_text.lower()
                if not ad_text.strip():
                    anuncios_activos += 1
                    continue
                
                # Check match
                es_coincidencia = False
                if palabras_clave_busqueda:
                    sustantivo_principal = palabras_clave_busqueda[0]
                    otras_palabras = palabras_clave_busqueda[1:]
                    es_falso_positivo = False
                    if "rodillo" in palabras_clave_busqueda and any(ex in ad_text for ex in ["facial", "jade", "pintura", "masajeador"]):
                        es_falso_positivo = True
                    if "organizador" in palabras_clave_busqueda and "cocina" in ad_text and "maleta" in palabras_clave_busqueda:
                        es_falso_positivo = True
                    
                    tiene_sustantivo = sustantivo_principal in ad_text
                    tiene_descriptor = any(op in ad_text for op in otras_palabras) if otras_palabras else True
                    if tiene_sustantivo and tiene_descriptor and not es_falso_positivo:
                        es_coincidencia = True
                else:
                    es_coincidencia = True
                    
                if es_coincidencia:
                    anuncios_activos += 1
                    
                    # Calcular edad de este anuncio coincidente
                    for key in ["ad_delivery_start_time", "delivery_start_time", "start_time", "start_date"]:
                        val_date = ad.get(key)
                        if val_date:
                            try:
                                if isinstance(val_date, int) or (isinstance(val_date, str) and val_date.isdigit()):
                                    ts = int(val_date)
                                    if ts > 1e11: ts = ts / 1000
                                    dt = datetime.fromtimestamp(ts)
                                else:
                                    date_str = str(val_date)[:10]
                                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                                dias = (fecha_actual - dt).days
                                if dias > dias_maximo:
                                    dias_maximo = dias
                            except Exception:
                                pass
                                
        total_anuncios = len(resultados)
        estado = "SATURADO"
        if total_anuncios > 0 and anuncios_activos == 0: 
            estado = "FRACASO COMPROBADO"
        elif total_anuncios == 0: 
            estado = "OCEANO AZUL"
        elif anuncios_activos <= 5: 
            if dias_maximo > 45:
                estado = "SATURADO_COMPETENCIA_LONGEVA"
            else:
                estado = "OPORTUNIDAD"
        else:
            if dias_maximo > 45:
                estado = "SATURADO_COMPETENCIA_LONGEVA"
            else:
                estado = "SATURADO"
                
        return {"anuncios_chile": anuncios_activos, "estado": estado, "dias_anuncio_mas_antiguo": dias_maximo}

    rapidapi_key = settings.rapidapi_key
    url = "https://facebook-ads-library-scraper-api.p.rapidapi.com/search/ads"
    headers = {
        "x-rapidapi-host": "facebook-ads-library-scraper-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    querystring = {"query": query_corta, "country_code": "CL", "limit": "50"}

    success = False
    json_response = None
    max_retries = 3
    delay = 1.5

    if rapidapi_key and "placeholder" not in rapidapi_key.lower() and len(rapidapi_key) > 5:
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=querystring, timeout=12) as response:
                        if response.status == 200:
                            json_response = await response.json()
                            success = True
                            break
            except Exception as e:
                logger.error(f"Error RapidAPI Ads: {e}")
            await asyncio.sleep(delay)

    if not success or not json_response or "error" in json_response:
        # Fallback a fail-safe
        res = {"anuncios_chile": 0, "estado": "OCEANO AZUL"}
        set_cached_response("meta_ads", producto_nombre, res)
        return res

    res = determinar_estado_y_conteo(json_response.get("ads", []))
    set_cached_response("meta_ads", producto_nombre, res)
    return res

async def analizar_saturacion_anuncios_lote(candidatos: list) -> dict:
    """
    Toma una lista de candidatos validados y verifica en paralelo (concurrencia 3)
    la saturación de anuncios activos en Facebook Ads Library Chile para cada uno.
    Retorna el estado de saturación y conteo de anuncios de cada producto.
    """
    if not candidatos:
        return {"status": "success", "resultados": []}
        
    logger.info(f"👁️ [Traffic Agent] Analizando saturación en Meta Ads para {len(candidatos)} productos...")
    
    async def evaluar(cand, sem):
        async with sem:
            res = await agente_meta_ads_chile(cand["producto_espanol"])
            cand_copia = dict(cand)
            cand_copia["meta_anuncios_activos"] = res["anuncios_chile"]
            cand_copia["estado_meta"] = res["estado"]
            cand_copia["dias_anuncio_mas_antiguo"] = res.get("dias_anuncio_mas_antiguo", 0)
            return cand_copia

    sem = asyncio.Semaphore(3)
    tasks = [evaluar(c, sem) for c in candidatos]
    resultados = await asyncio.gather(*tasks)
    
    # Procesar descartados saturados e incorporarlos a memoria
    mem = cargar_memoria()
    resultados_finales = []
    
    for r in resultados:
        if r["estado_meta"] == "SATURADO_COMPETENCIA_LONGEVA":
            logger.warning(f"⚠️ [Competencia Longeva] '{r['producto_espanol']}' tiene anuncios activos de larga duración ({r['dias_anuncio_mas_antiguo']} días). Se descarta.")
            desc = {
                "tiktok_ingles": r["producto_original"],
                "producto_espanol": r["producto_espanol"],
                "dropi_id": r["dropi_id"],
                "ventas_locales_dropi": r["dropi_ventas"],
                "stock_local_dropi": r["dropi_stock"],
                "dropi_search_term_es": r["dropi_search_term_es"],
                "dropi_search_term_en": r["dropi_search_term_en"],
                "meta_search_query": r["producto_espanol"],
                "meta_anuncios_activos": r["meta_anuncios_activos"],
                "dias_anuncio_mas_antiguo": r["dias_anuncio_mas_antiguo"],
                "ventas_reales_usa": r["ventas_reales"],
                "precio_usd": r["precio_usd"],
                "url_tiktok_shop": r["url"],
                "motivo_descarte": "COMPETENCIA_LONGEVA"
            }
            if not any(x["tiktok_ingles"] == desc["tiktok_ingles"] for x in mem["descartados_competencia_longeva"]):
                mem["descartados_competencia_longeva"].append(desc)
            if r["producto_original"] not in mem["productos_rechazados"]:
                mem["productos_rechazados"].append(r["producto_original"])
        elif r["estado_meta"] in ["SATURADO", "FRACASO COMPROBADO"]:
            desc = {
                "tiktok_ingles": r["producto_original"],
                "producto_espanol": r["producto_espanol"],
                "dropi_id": r["dropi_id"],
                "ventas_locales_dropi": r["dropi_ventas"],
                "stock_local_dropi": r["dropi_stock"],
                "dropi_search_term_es": r["dropi_search_term_es"],
                "dropi_search_term_en": r["dropi_search_term_en"],
                "meta_search_query": r["producto_espanol"],
                "meta_anuncios_activos": r["meta_anuncios_activos"],
                "ventas_reales_usa": r["ventas_reales"],
                "precio_usd": r["precio_usd"],
                "url_tiktok_shop": r["url"],
                "motivo_descarte": "SATURADO"
            }
            if not any(x["tiktok_ingles"] == desc["tiktok_ingles"] for x in mem["descartados_saturados"]):
                mem["descartados_saturados"].append(desc)
            if r["producto_original"] not in mem["productos_rechazados"]:
                mem["productos_rechazados"].append(r["producto_original"])
        else:
            resultados_finales.append(r)
            
    guardar_memoria(mem)
    
    # Limpiar campos pesados para no sobrecargar el historial de tokens de Gemini
    for r in resultados_finales:
        r.pop("dropi_descripcion", None)
        r.pop("dropi_imagen", None)
        r.pop("imagen_tiktok", None)
        
    return {
        "status": "success",
        "candidatos_viables": resultados_finales
    }
