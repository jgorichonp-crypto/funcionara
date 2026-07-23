import json
import asyncio
import aiohttp
from agentes.config import settings, logger
from agentes.tools import (
    obtener_estado_memoria,
    buscar_productos_virales_tiktok,
    validar_inventario_proveedor_lote,
    analizar_saturacion_anuncios_lote,
    registrar_ganador,
    registrar_nicho_procesado,
    registrar_producto_rechazado
)

# Mapeo de nombres de funciones a corrutinas reales de herramientas
TOOLS_MAP = {
    "obtener_estado_memoria": obtener_estado_memoria,
    "buscar_productos_virales_tiktok": buscar_productos_virales_tiktok,
    "validar_inventario_proveedor_lote": validar_inventario_proveedor_lote,
    "analizar_saturacion_anuncios_lote": analizar_saturacion_anuncios_lote,
    "registrar_ganador": registrar_ganador,
    "registrar_nicho_procesado": registrar_nicho_procesado,
    "registrar_producto_rechazado": registrar_producto_rechazado
}

# Declaración de herramientas en formato OpenAPI 3.0 para la API de Gemini
TOOL_DECLARATIONS = [
    {
        "name": "obtener_estado_memoria",
        "description": "Obtiene el estado actual del historial (nichos ya procesados, ganadores recientes y productos descartados o rechazados). Úsalo obligatoriamente al inicio.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "buscar_productos_virales_tiktok",
        "description": "Busca productos populares en TikTok Shop en base a un término de búsqueda en inglés (keyword). Retorna los candidatos con altas ventas.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Término de búsqueda en inglés, ej: 'magnetic desk organizers'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "validar_inventario_proveedor_lote",
        "description": "Toma un lote de candidatos (máximo 15) encontrados en TikTok, traduce sus nombres a español, busca su stock/ventas en Dropi Chile en paralelo, y realiza validación semántica en lote para descartar falsos positivos. Retorna los que sí tienen proveedor válido.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "candidatos": {
                    "type": "ARRAY",
                    "description": "Lista de objetos de candidatos de TikTok",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "producto": {"type": "STRING"},
                            "ventas_reales": {"type": "INTEGER"},
                            "precio_usd": {"type": "NUMBER"},
                            "url": {"type": "STRING"}
                        },
                        "required": ["producto", "ventas_reales", "precio_usd"]
                    }
                }
            },
            "required": ["candidatos"]
        }
    },
    {
        "name": "analizar_saturacion_anuncios_lote",
        "description": "Toma una lista de productos que sí tienen inventario disponible en el proveedor chileno y analiza su nivel de saturación publicitaria en Facebook Ads Library Chile en paralelo. Retorna el conteo de anuncios activos.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "candidatos": {
                    "type": "ARRAY",
                    "description": "Lista de candidatos con inventario validado",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "producto_original": {"type": "STRING"},
                            "producto_espanol": {"type": "STRING"},
                            "ventas_reales": {"type": "INTEGER"},
                            "precio_usd": {"type": "NUMBER"},
                            "dropi_id": {"type": "INTEGER"},
                            "dropi_ventas": {"type": "INTEGER"},
                            "dropi_stock": {"type": "INTEGER"},
                            "dropi_search_term_es": {"type": "STRING"},
                            "dropi_search_term_en": {"type": "STRING"},
                            "dropi_nombre_catalogo": {"type": "STRING"},
                            "url": {"type": "STRING"}
                        },
                        "required": ["producto_original", "producto_espanol", "dropi_id"]
                    }
                }
            },
            "required": ["candidatos"]
        }
    },
    {
        "name": "registrar_ganador",
        "description": "Registra oficialmente un producto aprobado como ganador en la memoria local (historial_memoria.json). Úsalo cuando encuentres un producto con estado OCEANO AZUL u OPORTUNIDAD.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "producto": {
                    "type": "OBJECT",
                    "description": "Objeto completo del producto validado por Meta Ads",
                    "properties": {
                        "producto_original": {"type": "STRING"},
                        "producto_espanol": {"type": "STRING"},
                        "ventas_reales": {"type": "INTEGER"},
                        "precio_usd": {"type": "NUMBER"},
                        "dropi_id": {"type": "INTEGER"},
                        "dropi_ventas": {"type": "INTEGER"},
                        "dropi_stock": {"type": "INTEGER"},
                        "meta_anuncios_activos": {"type": "INTEGER"},
                        "estado_meta": {"type": "STRING"},
                        "url": {"type": "STRING"},
                        "dias_anuncio_mas_antiguo": {"type": "INTEGER"}
                    },
                    "required": ["producto_original", "producto_espanol", "dropi_id", "meta_anuncios_activos", "estado_meta"]
                }
            },
            "required": ["producto"]
        }
    },
    {
        "name": "registrar_nicho_procesado",
        "description": "Marca un nicho o concepto general de búsqueda como completamente procesado en la memoria local para no volver a repetirlo.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "nicho": {
                    "type": "STRING",
                    "description": "El nombre del nicho/categoría procesada, ej: 'biotech-enhanced sleep environment gear'"
                }
            },
            "required": ["nicho"]
        }
    },
    {
        "name": "registrar_producto_rechazado",
        "description": "Marca un producto original en inglés como rechazado para que no se vuelva a analizar en futuros ciclos.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "producto_ingles": {
                    "type": "STRING",
                    "description": "El nombre completo del producto original de TikTok"
                }
            },
            "required": ["producto_ingles"]
        }
    }
]

SYSTEM_PROMPT = """
Eres el Agente Orquestador Manager de la mesa de trabajo de e-commerce y dropshipping en Chile (año 2026).
Tu misión es encontrar y registrar al menos 10 productos ganadores virales con alta demanda y baja/media competencia para vender localmente.

FUNCIONAMIENTO DE LA MESA DE TRABAJO:
1. Debes consultar obligatoriamente el historial de memoria al iniciar usando 'obtener_estado_memoria'. Esto te dirá qué nichos ya están agotados/procesados y qué productos ya fueron encontrados o rechazados.
2. Identifica un nicho de productos virales en inglés que no haya sido procesado en la lista 'nichos_procesados'. Concéntrate EXCLUSIVAMENTE en categorías comerciales de juguetes, juegos y artículos infantiles (como juguetes educativos, juegos interactivos, figuras de acción, manualidades y cosas para niños o bebés) en preparación para la temporada del Día del Niño. Evita a toda costa nichos fuera de este tema infantil o abstractos (como 'sensory-friendly' de salud, 'spatial computing', 'AI assistants' o similares) ya que no tendrán stock en proveedores locales en Chile.
3. Busca candidatos usando 'buscar_productos_virales_tiktok'.
4. Si encuentras productos candidatos de TikTok (con ventas >= 10000), valida su inventario y disponibilidad con el proveedor chileno usando 'validar_inventario_proveedor_lote'. Esta herramienta también realiza automáticamente el Cruce de Tendencias (AliExpress/Amazon) y el Filtro de Estacionalidad de Google Trends, descartando automáticamente lo que no tenga tracción global o esté fuera de temporada.
5. Para los productos que pasen esta validación, evalúa su nivel de saturación de publicidad activa en Chile usando 'analizar_saturacion_anuncios_lote'. Esto también analizará la antigüedad de los anuncios de la competencia para descartar mercados dominados.
6. Determina el estado final:
   - Si un producto resulta estar en estado 'OCEANO AZUL' (0 anuncios activos) o 'OPORTUNIDAD' (<= 5 anuncios activos y sin anuncios longevos de la competencia), ¡Felicidades! Es un producto ganador viable. Llama a 'registrar_ganador'.
   - NO detengas tu ejecución tras registrar un ganador. Continúa proponiendo nuevos nichos infantiles y analizando candidatos hasta haber registrado al menos 10 productos ganadores en total en la memoria.
   - Si los productos están 'SATURADOS', 'SATURADO_COMPETENCIA_LONGEVA' o no tienen stock/tracción, el sistema los descartará y registrará automáticamente. Debes continuar con otros candidatos o marcar el nicho entero como procesado usando 'registrar_nicho_procesado'.
   - Si un ciclo termina sin ganadores, continúa de forma autónoma con otro nicho infantil creativo y repite el proceso hasta hallar más ganadores.
   - Solo cuando hayas registrado al menos 10 productos ganadores infantiles en la memoria (o te quedes sin pasos/nichos viables), finaliza tu ejecución resumiendo los 10 ganadores encontrados al usuario.

Sé extremadamente ordenado, piensa en voz alta antes de cada llamada de herramientas explicando tu estrategia y mantén la ejecución activa hasta cumplir el objetivo.
"""

def podar_historial(messages: list, max_keep: int = 12) -> list:
    """
    Poda el historial de mensajes para evitar que crezca indefinidamente y gaste demasiados tokens.
    Mantiene siempre las primeras 3 entradas (SYSTEM_PROMPT, confirmación inicial y tarea)
    y las últimas `max_keep` entradas, asegurándose de no romper la estructura de llamadas de función de Gemini.
    """
    if len(messages) <= 3 + max_keep:
        return messages
        
    idx = len(messages) - max_keep
    # Si la primera entrada del bloque que vamos a conservar es una respuesta de función ('function'),
    # debemos retroceder hasta incluir también la llamada de función ('model') correspondiente.
    while idx > 3 and messages[idx].get("role") == "function":
        idx -= 1
            
    return messages[:3] + messages[idx:]

async def ejecutar_orquestador_agentes(nicho_inicial: str = None):
    logger.info("🤖 INICIANDO ORQUESTADOR DE AGENTES AUTÓNOMOS (Opción B)")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.gemini_api_key}"
    
    # Mensajes de la conversación (historial del agente)
    messages = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "Entendido. Iniciaré la mesa de trabajo de agentes autónomos para buscar un producto ganador en Chile."}]}
    ]
    
    user_task = "Mesa de trabajo, inicia la búsqueda."
    if nicho_inicial:
        user_task += f" Prioriza iniciar con el nicho/keyword: '{nicho_inicial}'."
        
    messages.append({"role": "user", "parts": [{"text": user_task}]})
    
    limite_pasos = 500  # Aumentado para dar suficiente margen para encontrar 10 ganadores
    paso = 0
    nuevos_ganadores_registrados = 0
    
    async with aiohttp.ClientSession() as session:
        while paso < limite_pasos:
            paso += 1
            
            # Podar el historial para ahorrar tokens y reducir costos drásticamente
            messages = podar_historial(messages, max_keep=12)
            
            total_chars = sum(len(str(m)) for m in messages)
            max_char = max(len(str(m)) for m in messages) if messages else 0
            logger.info(f"📊 Historial de mensajes: {len(messages)} mensajes. Caracteres aprox: {total_chars}. Mayor mensaje: {max_char} chars.")
            
            logger.info(f"🤖 [Paso {paso}] Consultando al Agente Orquestador (Ganadores registrados esta sesión: {nuevos_ganadores_registrados}/10)...")
            
            payload = {
                "contents": messages,
                "tools": [{"functionDeclarations": TOOL_DECLARATIONS}]
            }
            
            intentos_api = 0
            max_intentos_api = 5
            backoff_base = 2
            exito_api = False
            result = None
            
            while intentos_api < max_intentos_api:
                try:
                    async with session.post(url, json=payload, timeout=30) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            exito_api = True
                            break
                        elif resp.status in [500, 503, 429]:
                            body = await resp.text()
                            intentos_api += 1
                            delay = backoff_base ** intentos_api
                            logger.warning(f"⚠️ Gemini retornó HTTP {resp.status} (Intento {intentos_api}/{max_intentos_api}). Reintentando en {delay}s... Detalle: {body[:200]}")
                            await asyncio.sleep(delay)
                        else:
                            body = await resp.text()
                            logger.error(f"Error no reintentable consultando Gemini: HTTP {resp.status} - {body}")
                            break
                except Exception as e:
                    intentos_api += 1
                    delay = backoff_base ** intentos_api
                    logger.warning(f"⚠️ Error de conexión/timeout con Gemini (Intento {intentos_api}/{max_intentos_api}): {e}. Reintentando en {delay}s...")
                    await asyncio.sleep(delay)
                    
            if not exito_api or not result:
                logger.error("❌ Fallaron todos los intentos de comunicación con Gemini. Deteniendo orquestador.")
                break
                
            # Obtener la respuesta del modelo
            candidate = result.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            if not parts:
                logger.warning("El modelo devolvió una respuesta vacía.")
                break
                
            # Guardar el mensaje del modelo en el historial
            messages.append(content)
            
            # Revisar si hay llamadas a funciones (herramientas)
            function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]
            
            if not function_calls:
                # Si no hay llamadas de herramientas, verificar si se alcanzó la meta de ganadores
                if nuevos_ganadores_registrados < 10:
                    logger.info(f"⚠️ El agente intentó finalizar prematuramente con {nuevos_ganadores_registrados}/10 ganadores. Solicitando continuar...")
                    messages.append({
                        "role": "user",
                        "parts": [{"text": f"Aún no has completado la meta de 10 productos ganadores. Llevas {nuevos_ganadores_registrados} ganadores registrados en esta sesión. Por favor, continúa buscando más candidatos o explora nuevos nichos para encontrar los restantes."}]
                    })
                    continue
                else:
                    texto_final = parts[0].get("text", "")
                    logger.info(f"🤖 [Orquestador Finalizó] {texto_final}")
                    print(f"\n🏆 INFORME FINAL DEL ORQUESTADOR:\n{texto_final}\n")
                    break
                
            # Procesar cada llamada de función secuencialmente (Gemini suele hacer una por turno)
            for call in function_calls:
                func_name = call.get("name")
                args = call.get("args", {})
                
                logger.info(f"🤖 [Orquestador] Decisión de Acción: invocar '{func_name}' con parámetros {args}")
                
                if func_name in TOOLS_MAP:
                    # Ejecutar la herramienta correspondiente
                    try:
                        if asyncio.iscoroutinefunction(TOOLS_MAP[func_name]):
                            tool_result = await TOOLS_MAP[func_name](**args)
                        else:
                            tool_result = TOOLS_MAP[func_name](**args)
                    except Exception as e:
                        logger.error(f"Error ejecutando herramienta '{func_name}': {e}")
                        tool_result = {"status": "error", "message": str(e)}
                        
                    logger.info(f"🔧 [Herramienta Output] Completado '{func_name}'")
                    
                    # Si registramos con éxito un ganador, incrementamos el contador
                    if func_name == "registrar_ganador" and isinstance(tool_result, dict) and tool_result.get("status") == "success":
                        nuevos_ganadores_registrados += 1
                        logger.info(f"🏆 [Progreso] Ganadores registrados en esta sesión: {nuevos_ganadores_registrados}/10")
                    
                    # Retornar el resultado de la función a Gemini en el siguiente turno
                    messages.append({
                        "role": "function",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": func_name,
                                    "response": tool_result
                                }
                            }
                        ]
                    })
                else:
                    logger.error(f"Herramienta '{func_name}' no disponible en el mapa de herramientas.")
                    messages.append({
                        "role": "function",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": func_name,
                                    "response": {"status": "error", "message": "Tool not found"}
                                }
                            }
                        ]
                    })
                        
            # Añadir un delay mínimo entre pasos
            await asyncio.sleep(1)
            
        if paso >= limite_pasos:
            logger.warning("Se alcanzó el límite de pasos del agente. Deteniendo por seguridad.")
