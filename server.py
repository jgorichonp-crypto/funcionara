"""
Servidor Backend de Enlace Seguro para Landing Page y Dropi Chile.
Protege las claves de API y maneja la lógica de pedidos tanto en local como en producción.
Utiliza curl_cffi con impersonación de Chrome para evadir bloqueos de TLS/WAF de Cloudflare.
"""
import os
import logging
import json
import time
import unicodedata
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from curl_cffi import requests as curl_requests
from config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DropiServer")

app = FastAPI(title="Dropshipping COD Backend")

# Montar carpeta de assets generados para poder servir la imagen del producto
if os.path.exists("generated_assets"):
    app.mount("/generated_assets", StaticFiles(directory="generated_assets"), name="generated_assets")
else:
    logger.warning("⚠️  La carpeta 'generated_assets' no existe. Asegúrate de correr 'python main.py' primero.")


class OrderRequest(BaseModel):
    name: str
    phone: str
    address: str
    city: str


# Sesión de usuario persistida en memoria para Dropi Chile
dropi_session = {
    "token": None,
    "expires_at": 0
}


def normalize_text(text: str) -> str:
    """Elimina tildes y caracteres especiales, convirtiendo a mayúsculas."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.strip().upper()


def get_geographic_details(input_str: str):
    """
    Parsea la entrada 'Región / Comuna' del formulario de la landing page.
    Retorna (state, city) compatibles con Dropi Chile.
    """
    state_val = "Metropolitana de Santiago"
    city_val = "SANTIAGO"
    
    parts = [p.strip() for p in input_str.split("/") if p.strip()]
    
    if len(parts) >= 2:
        state_raw = normalize_text(parts[0])
        city_raw = normalize_text(parts[1])
        
        # Mapeo simple de regiones comunes de Chile
        if "METROPOLITANA" in state_raw or "RM" in state_raw or "SANTIAGO" in state_raw:
            state_val = "Metropolitana de Santiago"
        elif "VALPARAISO" in state_raw:
            state_val = "Valparaíso"
        elif "BIO" in state_raw:
            state_val = "Bío-Bío"
        elif "OHIGGINS" in state_raw or "BERNARDO" in state_raw:
            state_val = "Libertador General Bernardo O'Higgins"
        elif "MAULE" in state_raw:
            state_val = "Maule"
        elif "ARAUCANIA" in state_raw:
            state_val = "La Araucanía"
        elif "LOS LAGOS" in state_raw:
            state_val = "Los Lagos"
        elif "COQUIMBO" in state_raw:
            state_val = "Coquimbo"
        elif "ANTOFAGASTA" in state_raw:
            state_val = "Antofagasta"
        elif "TARAPACA" in state_raw:
            state_val = "Tarapacá"
        elif "ATACAMA" in state_raw:
            state_val = "Atacama"
        elif "LOS RIOS" in state_raw:
            state_val = "Los Ríos"
        elif "ARICA" in state_raw:
            state_val = "Arica y Parinacota"
        elif "NUBLE" in state_raw:
            state_val = "Ñuble"
        elif "AYSEN" in state_raw or "IBANEZ" in state_raw:
            state_val = "Aysén del General Carlos Ibáñez del Campo"
        elif "MAGALLANES" in state_raw:
            state_val = "Magallanes y de la Antártica Chilena"
        else:
            state_val = parts[0]
            
        city_val = city_raw
    elif len(parts) == 1:
        city_val = normalize_text(parts[0])
        
    return state_val, city_val


def login_to_dropi() -> Optional[str]:
    """
    Autentica con la API de Dropi Chile usando curl_cffi para evadir el bloqueo TLS/WAF.
    Almacena el token de usuario en la variable global dropi_session.
    """
    email = settings.dropi_email
    password = settings.dropi_password
    
    if not email or not password or "placeholder" in email.lower() or "placeholder" in password.lower():
        logger.warning("🧪 No hay credenciales de Dropi configuradas o son placeholders. Operando en modo simulación.")
        return None
        
    payload = {
        "email": email,
        "password": password,
        "white_brand_id": 4  # ID de marca blanca para Dropi Chile
    }
    
    headers = {
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }
    
    url = "https://api.dropi.cl/api/login"
    logger.info("🔑 Iniciando sesión programática en Dropi Chile...")
    
    try:
        response = curl_requests.post(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("isSuccess") and data.get("token"):
                token = data["token"]
                dropi_session["token"] = token
                # Expiración real en 4 horas (14400s). Limite de seguridad 3.5 horas.
                dropi_session["expires_at"] = time.time() + 12600
                logger.info("🎉 Inicio de sesión exitoso. Nuevo token almacenado en memoria.")
                return token
            else:
                logger.error(f"❌ Error en la respuesta de login: {data.get('message') or data.get('status')}")
        else:
            logger.error(f"❌ Error de login (Status {response.status_code}): {response.text[:300]}")
    except Exception as e:
        logger.error(f"❌ Excepción durante el login a Dropi: {str(e)}")
    return None


def get_dropi_token(force_refresh: bool = False) -> Optional[str]:
    """
    Retorna el token actual en memoria. Si no existe, si está por expirar o si force_refresh es True,
    obtiene uno nuevo iniciando sesión.
    """
    token = dropi_session.get("token")
    expires_at = dropi_session.get("expires_at", 0)
    
    if not token or time.time() > expires_at or force_refresh:
        token = login_to_dropi()
        
    return token


@app.get("/")
async def serve_landing():
    """Sirve la landing page autogenerada index.html."""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    else:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "Landing page index.html no encontrada. Ejecuta 'python main.py' para generarla."
            }
        )


@app.post("/api/order")
def create_order(order: OrderRequest):
    """
    Recibe los datos del cliente, inicia sesión en Dropi de forma automática y crea
    la orden usando la API de usuario. Se ejecuta síncronamente en el pool de hilos de FastAPI.
    """
    logger.info(f"📥 Pedido recibido: {order.name} - {order.phone} - {order.city}")
    
    # Obtener token de sesión
    token = get_dropi_token()
    
    # 1. Si no hay token de sesión (modo simulación o credenciales incorrectas)
    if not token:
        logger.info(
            f"🧪 [MODO SIMULACIÓN] Registrando orden ficticia en Dropi Chile:\n"
            f"  - Producto ID: {settings.dropi_product_id}\n"
            f"  - Nombre: {settings.dropi_product_name}\n"
            f"  - Cliente: {order.name}\n"
            f"  - Fono: {order.phone}\n"
            f"  - Destino: {order.address}, {order.city}"
        )
        return {
            "status": "success",
            "message": "Pedido simulado registrado exitosamente en Dropi Chile (Modo Desarrollo)",
            "order_id": "SIM-COD-98274"
        }
        
    logger.info(f"🚀 Iniciando envío de orden real a Dropi Chile (Producto ID: {settings.dropi_product_id})...")
    
    # 2. Configurar fallbacks para detalles de producto
    product_name = settings.dropi_product_name or "Producto de Tienda"
    product_price = settings.dropi_product_price or 19990.0
    supplier_id = settings.dropi_supplier_id or 2924
    
    # Intentar obtener información de producto del catálogo dinámicamente si es posible
    headers = {
        "x-authorization": f"Bearer {token}",
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json"
    }
    
    product_url = f"https://api.dropi.cl/api/products/{settings.dropi_product_id}"
    logger.info(f"🔍 Intentando obtener detalles del producto desde: {product_url}")
    
    try:
        prod_resp = curl_requests.get(product_url, headers=headers, impersonate="chrome120", timeout=10)
        if prod_resp.status_code == 200:
            prod_data = prod_resp.json()
            if prod_data.get("isSuccess") and prod_data.get("objects"):
                prod_obj = prod_data["objects"]
                product_name = prod_obj.get("name", product_name)
                # Usar el precio de venta sugerido o el del env si está configurado
                if not settings.dropi_product_price:
                    product_price = float(prod_obj.get("sale_price") or prod_obj.get("price") or product_price)
                supplier_id = prod_obj.get("user_id") or prod_obj.get("supplier_id") or supplier_id
                logger.info(f"✅ Detalles del producto recuperados: '{product_name}' - Proveedor ID: {supplier_id}")
            else:
                logger.warning(f"⚠️ La respuesta de Dropi no tiene datos de producto válidos: {prod_data.get('message')}")
        else:
            logger.warning(f"⚠️ No se pudo obtener información del producto (Status {prod_resp.status_code}). Usando valores estáticos/fallback.")
    except Exception as e:
        logger.warning(f"⚠️ Error de conexión al buscar detalles del producto: {str(e)}. Usando fallbacks.")
        
    # 3. Formatear nombres y geografía
    name_parts = order.name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else " "
    
    state_val, city_val = get_geographic_details(order.city)
    logger.info(f"🗺️ Geografía mapeada: Región = '{state_val}', Comuna = '{city_val}'")
    
    # 4. Formatear la orden
    url = "https://api.dropi.cl/api/orders/myorders"
    payload = {
        "total_order": product_price,
        "notes": "Pedido creado automáticamente desde Landing Page",
        "name": first_name,
        "surname": last_name,
        "dir": order.address,
        "country": "CL",
        "state": state_val,
        "city": city_val,
        "phone": order.phone,
        "client_email": "cliente_landing@mundoaura.cl",
        "payment_method_id": 1,  # COD / Pago contra entrega
        "status": "PENDIENTE",   # Borrador / Pendiente de confirmación manual
        "type": "FINAL_ORDER",
        "rate_type": "CON RECAUDO",
        "products": [
            {
                "id": int(settings.dropi_product_id),
                "name": product_name,
                "quantity": 1,
                "price": product_price
            }
        ],
        "calculate_costs_and_shiping": True,
        "supplier_id": supplier_id,
        "shop_order_id": int(time.time())  # Genera ID de orden secuencial
    }
    
    def send_post_request(auth_token):
        headers_order = {
            "x-authorization": f"Bearer {auth_token}",
            "Origin": "https://app.dropi.cl",
            "Referer": "https://app.dropi.cl/",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }
        return curl_requests.post(url, headers=headers_order, json=payload, impersonate="chrome120", timeout=15)
        
    logger.info(f"🚀 Enviando orden a Dropi: {url}...")
    try:
        response = send_post_request(token)
        
        # Si el token expiró durante la transacción (401/403), refrescamos token y reintentamos
        if response.status_code in [401, 403]:
            logger.info("🔄 Token de sesión expirado. Intentando refrescar token...")
            token = get_dropi_token(force_refresh=True)
            if token:
                response = send_post_request(token)
                
        response_text = response.text
        status_code = response.status_code
        logger.info(f"📥 Respuesta de Dropi recibida (Status {status_code})")
        
        try:
            response_json = response.json()
            is_success = response_json.get("isSuccess", False)
            msg = response_json.get("message") or response_json.get("data_error") or "Error desconocido"
        except Exception:
            is_success = status_code in [200, 201]
            msg = response_text
            
        if is_success:
            objects = response_json.get("objects", {})
            dropi_order_id = None
            if isinstance(objects, dict):
                dropi_order_id = objects.get("id")
            if not dropi_order_id and isinstance(response_json, dict):
                dropi_order_id = response_json.get("order_id") or response_json.get("id")
            dropi_order_id = dropi_order_id or "OK"
            
            logger.info(f"✅ Pedido creado en Dropi con éxito. ID: {dropi_order_id}")
            return {
                "status": "success",
                "message": "Pedido registrado exitosamente en Dropi Chile.",
                "order_id": dropi_order_id
            }
        else:
            logger.error(f"❌ Error en API de Dropi: {msg}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Dropi devolvió error: {msg}",
                    "detail": response_text
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Excepción al conectar con Dropi: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con el proveedor Dropi: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    logger.info("⚡ Iniciando servidor local en http://localhost:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
