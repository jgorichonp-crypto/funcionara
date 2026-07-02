"""
Dropi Guatemala Helper: Utilidades para conectar con el catálogo de Dropi Guatemala
y manejar autenticación regional.
"""
import os
import re
import time
import logging
from typing import Optional
from config import settings

logger = logging.getLogger("DropiHelperGT")

dropi_session_gt = {
    "token": None,
    "expires_at": 0
}

def get_dropi_token_gt(force_refresh: bool = False) -> Optional[str]:
    """
    Inicia sesión en la API de Dropi Guatemala y retorna el token de autenticación.
    """
    from curl_cffi import requests as curl_requests
    
    token = dropi_session_gt.get("token")
    expires_at = dropi_session_gt.get("expires_at", 0)
    
    if token and time.time() < expires_at and not force_refresh:
        return token
        
    email = settings.dropi_email_gt
    password = settings.dropi_password_gt
    
    if not email or not password or "placeholder" in email.lower() or "password" in password.lower():
        raise ValueError("❌ Credenciales de Dropi Guatemala no configuradas. Por favor agrega DROPI_EMAIL_GT y DROPI_PASSWORD_GT en tu archivo .env")
        
    # Payload con white_brand_id para Guatemala (1)
    payload = {
        "email": email,
        "password": password,
        "white_brand_id": 1
    }
    headers = {
        "Origin": "https://app.dropi.gt",
        "Referer": "https://app.dropi.gt/",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }
    url = "https://api.dropi.gt/api/login"
    
    logger.info("🔑 Conectando con API de Dropi Guatemala para iniciar sesión...")
    try:
        response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("isSuccess") and data.get("token"):
                new_token = data["token"]
                dropi_session_gt["token"] = new_token
                dropi_session_gt["expires_at"] = time.time() + 12600  # Vence en 3.5 horas
                logger.info("🎉 Inicio de sesión exitoso en Dropi Guatemala. Token almacenado en caché.")
                return new_token
            else:
                raise PermissionError(f"Error de login en Dropi GT: {data.get('message')}")
        else:
            raise ConnectionError(f"Error de conexión en login de Dropi GT (HTTP {response.status_code}): {response.text[:200]}")
    except Exception as e:
        logger.error(f"❌ Excepción durante el login a Dropi Guatemala: {str(e)}")
        raise e

async def search_dropi_product(product_name: str) -> dict:
    """
    Busca un producto por nombre en el catálogo de Dropi Guatemala.
    Requiere una clave API real. Si la API falla, eleva un error.
    """
    import unicodedata
    
    if product_name:
        # Remover acentos/tildes y caracteres especiales
        normalized = unicodedata.normalize('NFKD', product_name)
        product_name = "".join([c for c in normalized if not unicodedata.combining(c)])
        product_name = re.sub(r'[^a-zA-Z0-9\s]', '', product_name)
        product_name = " ".join(product_name.split())

    token = get_dropi_token_gt()
    
    # Búsqueda real en la API de Dropi Guatemala
    url = "https://api.dropi.gt/api/products/index"
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
        "Origin": "https://app.dropi.gt",
        "Referer": "https://app.dropi.gt/",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    logger.info(f"🔍 Conectando con API de Dropi Guatemala para buscar: '{product_name}'...")
    
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
                    logger.info(f"✅ ¡Producto encontrado en Dropi GT! '{name}' -> ID: {product_id} (Stock: {stock_val}, Ventas: {orders_val})")
                    return {"id": int(product_id), "stock": stock_val, "orders": orders_val, "name": name}
                else:
                    logger.warning(f"⚠️ Encontrado '{product_name}' en Dropi GT pero no hay unidades disponibles (Stock: 0).")
                    return {"id": None, "stock": 0, "orders": 0, "name": ""}
            else:
                logger.warning(f"⚠️ Producto no hallado en Dropi Guatemala.")
                return {"id": None, "stock": 0, "orders": 0, "name": ""}
        elif response.status_code == 400 and "permisos" in response.text.lower():
            raise PermissionError("❌ Error de permisos (400) al conectar con la API de Dropi Guatemala. Verifica tus credenciales.")
        else:
            raise ConnectionError(f"❌ Error al consultar catálogo en Dropi GT ({response.status_code}): \n{response.text}")
    except Exception as e:
        logger.error(f"❌ Error crítico en el catálogo de Dropi Guatemala: {str(e)}")
        raise e

async def get_dropi_product_by_id(product_id: int) -> Optional[dict]:
    """
    Busca un producto por ID en Dropi Guatemala y devuelve sus detalles completos.
    """
    token = get_dropi_token_gt()
    url = "https://api.dropi.gt/api/products/index"
    payload = {
        "pageSize": 10,
        "startData": 0,
        "no_count": True,
        "keywords": str(product_id),
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
    
    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("objects", []) or data.get("products", []) or data.get("data", []) or []
            for p in products:
                p_id = p.get("id") or p.get("product_id")
                if int(p_id) == int(product_id):
                    return {
                        "id": int(p_id),
                        "nombre": p.get("name"),
                        "costo_clp": float(p.get("price") or p.get("cost") or p.get("sale_price") or 0.0), # Se mantiene nombre clave costo_clp pero representa Quetzales en este contexto
                        "stock": int(p.get("stock") or 0),
                        "ventas_locales": int(p.get("orders") or 0),
                        "url_imagen": p.get("image") or (p.get("images")[0] if p.get("images") else None)
                    }
            logger.warning(f"⚠️ Producto con ID {product_id} no se encontró en el catálogo indexado de Dropi GT.")
            return None
        elif response.status_code == 400 and "permisos" in response.text.lower():
            raise PermissionError("❌ Error de permisos (400) al conectar con la API de Dropi Guatemala. Verifica tus credenciales.")
        else:
            raise ConnectionError(f"❌ Error al consultar catálogo en Dropi GT ({response.status_code}): \n{response.text}")
    except Exception as e:
        logger.error(f"❌ Error al consultar producto por ID en Dropi GT: {str(e)}")
        raise e
