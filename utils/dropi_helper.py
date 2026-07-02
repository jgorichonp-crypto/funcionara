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
    import sys
    import os
    import unicodedata
    
    if product_name:
        # Remover acentos/tildes y caracteres especiales
        normalized = unicodedata.normalize('NFKD', product_name)
        product_name = "".join([c for c in normalized if not unicodedata.combining(c)])
        product_name = re.sub(r'[^a-zA-Z0-9\s]', '', product_name)
        product_name = " ".join(product_name.split())

    # Asegurar que el path incluya server.py
    sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
    from server import get_dropi_token
    
    token = get_dropi_token()
    
    if not token:
        raise ValueError("❌ No se encontró un token de Dropi válido. La API no está configurada.")

    # Búsqueda real en la API de Dropi Chile usando el endpoint del catálogo web
    url = "https://api.dropi.cl/api/products/index"
    payload = {
        "pageSize": 20,
        "startData": 0,
        "no_count": True,
        "keywords": product_name,
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

    logger.info(f"🔍 Conectando con API de Dropi Chile para buscar: '{product_name}'...")
    
    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("objects", []) or data.get("products", []) or data.get("data", []) or []
            
            if products:
                # Buscar el primer producto que tenga stock disponible (stock > 0)
                valid_product = None
                for p in products:
                    stock = int(p.get("stock") or 0)
                    if stock > 0:
                        valid_product = p
                        break
                
                if valid_product:
                    product_id = valid_product.get("id") or valid_product.get("product_id")
                    name = valid_product.get("name", product_name)
                    stock_val = int(valid_product.get("stock") or 0)
                    orders_val = int(valid_product.get("orders") or 0)
                    price_val = float(valid_product.get("sale_price") or valid_product.get("price") or 0.0)
                    desc_val = str(valid_product.get("description") or valid_product.get("short_description") or "")
                    image_val = ""
                    if valid_product.get("image"):
                        image_val = str(valid_product.get("image"))
                    elif valid_product.get("image_url"):
                        image_val = str(valid_product.get("image_url"))
                    elif isinstance(valid_product.get("images"), list) and valid_product.get("images"):
                        image_val = str(valid_product.get("images")[0])
                        
                    logger.info(f"✅ ¡Producto encontrado en Dropi! '{name}' -> ID: {product_id} (Stock: {stock_val}, Ventas: {orders_val})")
                    return {
                        "id": int(product_id), 
                        "stock": stock_val, 
                        "orders": orders_val, 
                        "name": name,
                        "price": price_val,
                        "description": desc_val,
                        "image": image_val
                    }
                else:
                    logger.warning(f"⚠️ Encontrado '{product_name}' en Dropi pero no hay unidades disponibles (Stock: 0).")
                    return {"id": 123456, "stock": 0, "orders": 0, "name": "", "price": 0.0, "description": "", "image": ""}
            else:
                logger.warning(f"⚠️ Producto no hallado en Dropi Chile. Usando ID 123456 para rechazo.")
                return {"id": 123456, "stock": 0, "orders": 0, "name": "", "price": 0.0, "description": "", "image": ""}
        elif response.status_code == 400 and "permisos" in response.text.lower():
            raise PermissionError("❌ Error de permisos (400) al conectar con la API de Dropi. Verifica tus credenciales.")
        else:
            raise ConnectionError(f"❌ Error al consultar catálogo en Dropi ({response.status_code}): \n{response.text}")
    except Exception as e:
        logger.error(f"❌ Error crítico en el catálogo de Dropi: {str(e)}")
        raise e


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
