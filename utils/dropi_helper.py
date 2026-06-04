"""
Dropi Helper: Utilidades para conectar con el catálogo de Dropi Chile
y actualizar configuraciones de forma dinámica en el archivo .env.
"""
import os
import re
import logging
import aiohttp
from typing import Optional
from config import settings

logger = logging.getLogger("DropiHelper")


async def search_dropi_product(product_name: str) -> int:
    """
    Busca un producto por nombre en el catálogo de Dropi Chile.
    Si hay una clave API real, consulta la base de datos de Dropi.
    De lo contrario, simula la búsqueda y genera un ID ficticio reproducible.
    """
    is_placeholder = (
        not settings.dropi_api_key or 
        settings.dropi_api_key == "your-dropi-api-key-here" or 
        "placeholder" in settings.dropi_api_key.lower()
    )
    
    if is_placeholder:
        # Generar un ID ficticio estable basado en el hash del nombre
        simulated_id = abs(hash(product_name)) % 1000000
        logger.info(
            f"🧪 [SIMULACIÓN DROPI] Buscando '{product_name}' en Dropi Chile...\n"
            f"   - Encontrado: '{product_name}' (Proveedor Asociado)\n"
            f"   - ID Simulado asignado: {simulated_id}"
        )
        return simulated_id

    # Búsqueda real en la API de Dropi Chile
    url = f"https://api.dropi.co/api/v1/products"
    params = {"search": product_name, "limit": 1}
    headers = {
        "Authorization": f"Bearer {settings.dropi_api_key}",
        "Accept": "application/json"
    }

    logger.info(f"🔍 Conectando con API de Dropi Chile para buscar: '{product_name}'...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get("products", []) or data.get("data", []) or []
                    
                    if products:
                        first_product = products[0]
                        product_id = first_product.get("id") or first_product.get("product_id")
                        name = first_product.get("name", product_name)
                        
                        logger.info(f"✅ ¡Producto encontrado en Dropi! '{name}' -> ID: {product_id}")
                        return int(product_id)
                    else:
                        # Si no hay coincidencias exactas, retornar un ID por defecto y avisar
                        logger.warning(
                            f"⚠️ No se encontraron productos coincidentes en el catálogo de Dropi Chile para '{product_name}'. "
                            f"Usando ID por defecto (123456)."
                        )
                        return 123456
                else:
                    response_text = await response.text()
                    logger.error(f"❌ Error al consultar catálogo en Dropi ({response.status}): {response_text}")
                    return 123456
    except Exception as e:
        logger.error(f"❌ Error de conexión al catálogo de Dropi: {str(e)}")
        return 123456


def update_env_file(key: str, value: str) -> None:
    """
    Busca una clave en el archivo .env y actualiza su valor.
    Si no existe la clave, la agrega al final del archivo.
    Preserva comentarios, espacios y el resto de las variables.
    """
    env_path = ".env"
    
    if not os.path.exists(env_path):
        logger.warning(f"⚠️  El archivo {env_path} no existe. No se pudo actualizar {key}.")
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(rf"^({key}\s*=)(.*)$", re.MULTILINE)
        
        if pattern.search(content):
            # Reemplazar el valor de la clave existente
            new_content = pattern.sub(rf"\g<1>{value}", content)
            logger.info(f"📝 Actualizado .env: {key}={value}")
        else:
            # Añadir la clave al final si no existe
            new_content = content.rstrip() + f"\n{key}={value}\n"
            logger.info(f"📝 Agregado a .env: {key}={value}")

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
    except Exception as e:
        logger.error(f"❌ Error al escribir en el archivo .env: {str(e)}")
