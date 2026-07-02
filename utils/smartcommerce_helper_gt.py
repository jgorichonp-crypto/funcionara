"""
SmartCommerce Guatemala Helper: Utilidades para conectar con el catálogo de SmartCommerce
y manejar la autenticación y búsqueda de productos.
"""
import os
import time
import logging
from typing import Optional

logger = logging.getLogger("SmartCommerceHelperGT")

smartcommerce_session = {
    "token": None,
    "expires_at": 0
}

def get_smartcommerce_token(force_refresh: bool = False) -> Optional[str]:
    """
    Inicia sesión en la API de SmartCommerce y retorna el token de autenticación (JWT).
    """
    from curl_cffi import requests as curl_requests
    
    token = smartcommerce_session.get("token")
    expires_at = smartcommerce_session.get("expires_at", 0)
    
    if token and time.time() < expires_at and not force_refresh:
        return token
        
    from config import settings
    email = os.getenv("SMARTCOMMERCE_EMAIL") or settings.smartcommerce_email
    password = os.getenv("SMARTCOMMERCE_PASSWORD") or settings.smartcommerce_password
    
    if not email or not password or "placeholder" in email.lower() or "placeholder" in password.lower():
        raise ValueError("❌ Credenciales de SmartCommerce no configuradas. Por favor agrega SMARTCOMMERCE_EMAIL y SMARTCOMMERCE_PASSWORD en tu archivo .env")
        
    payload = {
        "email": email,
        "password": password
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://app.smartcommerce.lat",
        "Referer": "https://app.smartcommerce.lat/",
        "iss": "smart",
        "sub": "client-web",
        "aud": "sign-in"
    }
    url = "https://api.smartcommerce.lat/api/auth/sign-in"
    
    logger.info("🔑 Conectando con API de SmartCommerce para iniciar sesión...")
    try:
        response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        if response.status_code == 200:
            data = response.json()
            token_payload = data.get("payload", {})
            new_token = token_payload.get("accessToken")
            if new_token:
                smartcommerce_session["token"] = new_token
                smartcommerce_session["expires_at"] = time.time() + 3500  # Token JWT expira en 1 hora (3600 seg)
                logger.info("🎉 Inicio de sesión exitoso en SmartCommerce. Token almacenado en caché.")
                return new_token
            else:
                raise PermissionError(f"Error de login en SmartCommerce (no accessToken): {data.get('message')}")
        else:
            raise ConnectionError(f"Error de conexión en login de SmartCommerce (HTTP {response.status_code}): {response.text[:200]}")
    except Exception as e:
        logger.error(f"❌ Excepción durante el login a SmartCommerce: {str(e)}")
        raise e

async def search_smartcommerce_product(product_name: str) -> dict:
    """
    Busca un producto por nombre en el catálogo de SmartCommerce.
    Devuelve los detalles básicos del primer producto con stock disponible.
    """
    import unicodedata
    import re
    
    if product_name:
        # Remover acentos/tildes y caracteres especiales
        normalized = unicodedata.normalize('NFKD', product_name)
        product_name = "".join([c for c in normalized if not unicodedata.combining(c)])
        product_name = re.sub(r'[^a-zA-Z0-9\s]', '', product_name)
        product_name = " ".join(product_name.split())

    token = get_smartcommerce_token()
    
    # Búsqueda real en la API de SmartCommerce
    url = "https://api.smartcommerce.lat/api/products"
    params = {
        "page": "1",
        "size": "20",
        "search": product_name,
        "sortBy": "createdAt"
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "Origin": "https://app.smartcommerce.lat",
        "Referer": "https://app.smartcommerce.lat/"
    }

    logger.info(f"🔍 Conectando con API de SmartCommerce para buscar: '{product_name}'...")
    
    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.get(url, headers=headers, params=params, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("payload", {}).get("items", []) or []
            
            if products:
                valid_product = None
                for p in products:
                    inventory = p.get("inventory", {}) or {}
                    stock = int(inventory.get("totalAvailable") or inventory.get("totalOnHand") or 0)
                    if stock > 0:
                        valid_product = p
                        break
                
                if valid_product:
                    product_id = valid_product.get("_id")
                    name = valid_product.get("name", product_name)
                    inventory = valid_product.get("inventory", {}) or {}
                    stock_val = int(inventory.get("totalAvailable") or inventory.get("totalOnHand") or 0)
                    orders_val = int(valid_product.get("salesCount") or 0)
                    logger.info(f"✅ ¡Producto encontrado en SmartCommerce! '{name}' -> ID: {product_id} (Stock: {stock_val}, Ventas: {orders_val})")
                    return {"id": product_id, "stock": stock_val, "orders": orders_val, "name": name}
                else:
                    logger.warning(f"⚠️ Encontrado '{product_name}' en SmartCommerce pero no hay unidades disponibles (Stock: 0).")
                    return {"id": None, "stock": 0, "orders": 0, "name": ""}
            else:
                logger.warning(f"⚠️ Producto no hallado en SmartCommerce.")
                return {"id": None, "stock": 0, "orders": 0, "name": ""}
        else:
            raise ConnectionError(f"❌ Error al consultar catálogo en SmartCommerce ({response.status_code}): \n{response.text[:200]}")
    except Exception as e:
        logger.error(f"❌ Error crítico en el catálogo de SmartCommerce: {str(e)}")
        raise e

async def get_smartcommerce_product_by_id(product_id: str) -> Optional[dict]:
    """
    Busca un producto por ID en SmartCommerce y devuelve sus detalles completos.
    """
    if not product_id or product_id == "123456":
        return None
        
    token = get_smartcommerce_token()
    url = f"https://api.smartcommerce.lat/api/products/{product_id}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "Origin": "https://app.smartcommerce.lat",
        "Referer": "https://app.smartcommerce.lat/"
    }
    
    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            p = data.get("payload", {})
            if p and p.get("_id") == product_id:
                inventory = p.get("inventory", {}) or {}
                stock_val = int(inventory.get("totalAvailable") or inventory.get("totalOnHand") or 0)
                images = p.get("images", [])
                url_imagen = images[0] if images else None
                
                return {
                    "id": p.get("_id"),
                    "nombre": p.get("name"),
                    "costo_clp": float(p.get("cost") or 0.0),  # costo en Quetzales/moneda local
                    "price": float(p.get("price") or 0.0),
                    "suggested_price": float(p.get("suggestedPrice") or 0.0),
                    "stock": stock_val,
                    "ventas_locales": int(p.get("salesCount") or 0),
                    "url_imagen": url_imagen
                }
            logger.warning(f"⚠️ Producto con ID {product_id} no se encontró en SmartCommerce.")
            return None
        else:
            raise ConnectionError(f"❌ Error al consultar producto por ID en SmartCommerce ({response.status_code}): \n{response.text[:200]}")
    except Exception as e:
        logger.error(f"❌ Error al consultar producto por ID en SmartCommerce: {str(e)}")
        raise e
