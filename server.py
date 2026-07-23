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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from curl_cffi import requests as curl_requests
from config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DropiServer")

app = FastAPI(title="Dropshipping COD Backend")

from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/assets/") or request.url.path.endswith((".webp", ".png", ".jpg", ".js", ".css", ".mp4")):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response

# Montar carpetas de assets
if os.path.exists("generated_assets"):
    app.mount("/generated_assets", StaticFiles(directory="generated_assets"), name="generated_assets")
else:
    logger.warning("⚠️  La carpeta 'generated_assets' no existe. Asegúrate de correr 'python main.py' primero.")

if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
else:
    logger.warning("⚠️  La carpeta 'assets' no existe. Los recursos estáticos no se servirán.")


class OrderRequest(BaseModel):
    name: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    supplier_id: Optional[int] = None
    rut: Optional[str] = None
    email: Optional[str] = None
    calle: Optional[str] = None
    n_casa: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    unidades: Optional[int] = 1


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
    Parsea la entrada 'Región / Comuna' o simplemente 'Comuna' del formulario.
    Retorna (state, city) compatibles con Dropi Chile.
    """
    # Soporta comas además de barras diagonales como separador
    input_str_clean = input_str.replace(",", "/")
    parts = [p.strip() for p in input_str_clean.split("/") if p.strip()]
    
    state_val = "Metropolitana de Santiago"
    city_val = "SANTIAGO"
    
    if len(parts) >= 2:
        state_raw = normalize_text(parts[0])
        city_raw = normalize_text(parts[1])
    else:
        # Si solo ingresó una parte (comuna), tratamos de inferir la región automáticamente
        city_raw = normalize_text(parts[0]) if parts else "SANTIAGO"
        state_raw = ""
        
        # Diccionario de inferencia de región para comunas chilenas fuera de Santiago
        commune_to_region = {
            "VINA DEL MAR": "Valparaíso",
            "VALPARAISO": "Valparaíso",
            "QUILPUE": "Valparaíso",
            "VILLA ALEMANA": "Valparaíso",
            "CONCON": "Valparaíso",
            "SAN ANTONIO": "Valparaíso",
            "QUILLOTA": "Valparaíso",
            "LOS ANDES": "Valparaíso",
            "SAN FELIPE": "Valparaíso",
            "CONCEPCION": "Bío-Bío",
            "TALCAHUANO": "Bío-Bío",
            "SAN PEDRO DE LA PAZ": "Bío-Bío",
            "CHIGUAYANTE": "Bío-Bío",
            "CORONEL": "Bío-Bío",
            "LOTA": "Bío-Bío",
            "LOS ANGELES": "Bío-Bío",
            "TEMUCO": "La Araucanía",
            "PADRE LAS CASAS": "La Araucanía",
            "ANGOL": "La Araucanía",
            "RANCAGUA": "Libertador General Bernardo O'Higgins",
            "MACHALI": "Libertador General Bernardo O'Higgins",
            "SAN FERNANDO": "Libertador General Bernardo O'Higgins",
            "RENGO": "Libertador General Bernardo O'Higgins",
            "TALCA": "Maule",
            "CURICO": "Maule",
            "LINARES": "Maule",
            "COQUIMBO": "Coquimbo",
            "LA SERENA": "Coquimbo",
            "OVALLE": "Coquimbo",
            "ANTOFAGASTA": "Antofagasta",
            "CALAMA": "Antofagasta",
            "IQUIQUE": "Tarapacá",
            "ALTO HOSPICIO": "Tarapacá",
            "ARICA": "Arica y Parinacota",
            "COPIAPO": "Atacama",
            "PUERTO MONTT": "Los Lagos",
            "OSORNO": "Los Lagos",
            "PUERTO VARAS": "Los Lagos",
            "VALDIVIA": "Los Ríos",
            "CHILLAN": "Ñuble",
            "PUNTA ARENAS": "Magallanes y de la Antártica Chilena",
            "COYHAIQUE": "Aysén del General Carlos Ibáñez del Campo"
        }
        
        # Buscar coincidencia exacta o parcial
        found_state = None
        for commune, region in commune_to_region.items():
            if commune in city_raw or city_raw in commune:
                found_state = region
                break
                
        if found_state:
            state_val = found_state
            city_val = city_raw
            return state_val, city_val
        else:
            state_raw = "METROPOLITANA"

    # Mapeo estándar de regiones
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
        state_val = parts[0] if parts else "Metropolitana de Santiago"
        
    city_val = city_raw
    return state_val, city_val


def login_to_dropi() -> Optional[str]:
    """
    Autentica con la API de Dropi Chile usando curl_cffi para evadir el bloqueo TLS/WAF.
    Almacena el token de usuario en la variable global dropi_session.
    """
    email = settings.dropi_email
    password = settings.dropi_password

    if not email or not password or "placeholder" in email.lower():
        logger.warning("⚠️ Credenciales de Dropi Chile no configuradas para inicio de sesión programático.")
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
    obtiene uno nuevo iniciando sesión programática. Si no es posible, usa el dropi_api_key del .env de respaldo.
    """
    token = dropi_session.get("token")
    expires_at = dropi_session.get("expires_at", 0)
    
    # 1. Si tenemos credenciales, intentamos iniciar sesión programática primero (es más fiable)
    if settings.dropi_email and settings.dropi_password and "placeholder" not in settings.dropi_email.lower():
        if not token or time.time() > expires_at or force_refresh:
            token = login_to_dropi()
        if token:
            return token
            
    # 2. Si falla o no está configurada, usar el token estático del .env
    if settings.dropi_api_key and settings.dropi_api_key.startswith("eyJ") and not force_refresh:
        return settings.dropi_api_key
        
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


def send_order_to_dropi_api(order_data: dict) -> Optional[str]:
    """
    Inicia sesión en Dropi Chile y crea la orden de forma real con estado APROBADO.
    Retorna el ID de la orden creada en Dropi si tiene éxito.
    """
    token = get_dropi_token()
    
    # 1. Si no hay token de sesión (modo simulación o credenciales incorrectas)
    if not token:
        logger.info(
            f"🧪 [MODO SIMULACIÓN] Creando orden ficticia en Dropi Chile:\n"
            f"  - Producto ID: {settings.dropi_product_id}\n"
            f"  - Nombre: {settings.dropi_product_name}\n"
            f"  - Cliente: {order_data.get('name')}\n"
            f"  - Fono: {order_data.get('phone')}\n"
            f"  - Destino: {order_data.get('address')}, {order_data.get('city')}"
        )
        return "SIM-COD-" + str(int(time.time()))[-5:]
        
    logger.info(f"🚀 Iniciando envío de orden real a Dropi Chile (Producto ID: {settings.dropi_product_id})...")
    
    # 2. Configurar fallbacks para detalles de producto
    p_id = order_data.get("product_id") or settings.dropi_product_id
    product_name = order_data.get("product_name") or (settings.dropi_product_name or "Producto de Tienda")
    product_price = order_data.get("product_price") or (settings.dropi_product_price or 19990.0)
    supplier_id = order_data.get("supplier_id") or (settings.dropi_supplier_id or 2924)
    
    # Intentar obtener información de producto del catálogo dinámicamente si es posible
    headers = {
        "x-authorization": f"Bearer {token}",
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json"
    }
    
    product_url = f"https://api.dropi.cl/api/products/{p_id}"
    logger.info(f"🔍 Intentando obtener detalles del producto desde: {product_url}")
    
    try:
        prod_resp = curl_requests.get(product_url, headers=headers, impersonate="chrome120", timeout=10)
        if prod_resp.status_code == 200:
            prod_data = prod_resp.json()
            if prod_data.get("isSuccess") and prod_data.get("objects"):
                prod_obj = prod_data["objects"]
                product_name = prod_obj.get("name", product_name)
                if not settings.dropi_product_price:
                    product_price = float(prod_obj.get("sale_price") or prod_obj.get("price") or product_price)
                supplier_id = prod_obj.get("user_id") or prod_obj.get("supplier_id") or supplier_id
                logger.info(f"✅ Detalles del producto recuperados: '{product_name}' - Proveedor ID: {supplier_id}")
    except Exception as e:
        logger.warning(f"⚠️ Error de conexión al buscar detalles del producto: {str(e)}. Usando fallbacks.")
        
    # 3. Formatear nombres y geografía
    name_parts = order_data["name"].strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else " "
    
    state_val, city_val = get_geographic_details(order_data["city"])
    logger.info(f"🗺️ Geografía mapeada: Región = '{state_val}', Comuna = '{city_val}'")
    
    # 4. Formatear la orden
    url = "https://api.dropi.cl/api/orders/myorders"
    payload = {
        "total_order": product_price,
        "notes": "Pedido creado automáticamente y confirmado por WhatsApp",
        "name": first_name,
        "surname": last_name,
        "dir": order_data["address"],
        "country": "CL",
        "state": state_val,
        "city": city_val,
        "phone": order_data["phone"],
        "client_email": "cliente_landing@mundoaura.cl",
        "payment_method_id": 1,  # COD / Pago contra entrega
        "status": "APROBADO",   # APROBADO ya que fue validado por WhatsApp
        "type": "FINAL_ORDER",
        "rate_type": "CON RECAUDO",
        "products": [
            {
                "id": int(p_id),
                "name": product_name,
                "quantity": 1,
                "price": product_price
            }
        ],
        "calculate_costs_and_shiping": True,
        "supplier_id": supplier_id,
        "shop_order_id": int(time.time())
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
            dropi_order_id = str(dropi_order_id or "OK")
            logger.info(f"✅ Pedido creado en Dropi con éxito. ID: {dropi_order_id}")
            return dropi_order_id
        else:
            logger.error(f"❌ Error en API de Dropi: {msg}")
            raise Exception(f"Dropi devolvió error: {msg}")
    except Exception as e:
        logger.error(f"❌ Excepción al conectar con Dropi: {str(e)}")
        raise e


@app.post("/api/order")
async def create_order(order: OrderRequest, background_tasks: BackgroundTasks):
    """
    Recibe los datos del cliente, genera un ID temporal, registra en la base de datos
    local y en Google Sheets como PENDIENTE, y encola la confirmación de WhatsApp.
    """
    temp_id = f"TEMP-{int(time.time())}"
    logger.info(f"📥 Pedido inicial recibido: {order.name} - {order.phone} - {order.city} - Email: {order.email}. Asignado ID temporal: {temp_id}")
    
    # Configurar detalles de producto
    p_id = order.product_id if order.product_id else settings.dropi_product_id
    product_name = order.product_name if order.product_name else (settings.dropi_product_name or "Producto de Tienda")
    product_price = order.product_price if order.product_price else (settings.dropi_product_price or 19990.0)
    
    # 1. Guardar en la base de datos local (En segundo plano)
    from database import save_order
    background_tasks.add_task(
        save_order,
        dropi_order_id=temp_id,
        client_name=order.name,
        phone=order.phone,
        address=order.address,
        city=order.city,
        product_name=product_name,
        price=product_price,
        status="PENDING_CONFIRMATION"
    )

    
    # 2. Guardar en Google Sheets vía Apps Script (En segundo plano)
    from utils.sheets_helper import save_order_to_sheets
    background_tasks.add_task(
        save_order_to_sheets,
        order_id=temp_id,
        client_name=order.name,
        phone=order.phone,
        address=order.address,
        city=order.city,
        product_name=f"{product_name} ({p_id})",
        price=product_price,
        rut=order.rut or "",
        email=order.email or "",
        calle=order.calle or "",
        n_casa=order.n_casa or "",
        region=order.region or "",
        comuna=order.comuna or "",
        unidades=order.unidades or 1
    )
    
    # 3. Enviar confirmación por WhatsApp (En segundo plano)
    from agents.crm import send_order_confirmation_request
    background_tasks.add_task(
        send_order_confirmation_request,
        {
            "client_name": order.name,
            "phone": order.phone,
            "product_name": product_name,
            "price": product_price,
            "address": order.address,
            "city": order.city,
            "dropi_order_id": temp_id
        }
    )
    
    return {
        "status": "success",
        "message": "Pedido recibido. Pendiente de confirmación por WhatsApp.",
        "order_id": temp_id,
        "debug_email": order.email
    }



@app.on_event("startup")
def startup_event():
    """Inicializa la base de datos al arrancar el servidor."""
    from database import init_db
    init_db()


@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint webhook para escuchar respuestas de WhatsApp.
    Soporta Evolution API (JSON) y Twilio (Form data).
    """
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        payload = await request.json()
        logger.info(f"📥 Webhook WhatsApp JSON recibido: {payload}")
        
        # Evolution API (event: messages.upsert)
        event = payload.get("event")
        if event == "messages.upsert":
            data = payload.get("data", {})
            key = data.get("key", {})
            from_me = key.get("fromMe", False)
            if from_me:
                return {"status": "ignored", "reason": "sent_by_me"}
                
            remote_jid = key.get("remoteJid", "")
            phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
            
            message_data = data.get("message", {})
            reply_text = ""
            if "conversation" in message_data:
                reply_text = message_data["conversation"]
            elif "extendedTextMessage" in message_data:
                reply_text = message_data["extendedTextMessage"].get("text", "")
            elif "buttonsResponseMessage" in message_data:
                reply_text = message_data["buttonsResponseMessage"].get("selectedButtonId", "") or message_data["buttonsResponseMessage"].get("selectedDisplayText", "")
                
            if phone and reply_text:
                from agents.crm import process_incoming_reply
                background_tasks.add_task(process_incoming_reply, phone, reply_text)
                return {"status": "processing"}
                
    elif "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        logger.info(f"📥 Webhook WhatsApp Form recibido: {dict(form_data)}")
        
        # Twilio WhatsApp Webhook
        from_number = form_data.get("From", "")  # Ej: whatsapp:+56912345678
        body = form_data.get("Body", "")
        
        if from_number and body:
            phone = from_number.replace("whatsapp:", "").replace("+", "").strip()
            from agents.crm import process_incoming_reply
            background_tasks.add_task(process_incoming_reply, phone, body)
            return {"status": "processing"}
            
    return {"status": "ignored"}


class TestReplyRequest(BaseModel):
    phone: str
    text: str


@app.post("/api/test/whatsapp-reply")
async def test_whatsapp_reply(reply: TestReplyRequest, background_tasks: BackgroundTasks):
    """Endpoint de simulación para emular la respuesta de un cliente en WhatsApp."""
    logger.info(f"🧪 [SIMULACIÓN WEBHOOK] Recibida respuesta test para +{reply.phone}: '{reply.text}'")
    from agents.crm import process_incoming_reply
    background_tasks.add_task(process_incoming_reply, reply.phone, reply.text)
    return {
        "status": "success",
        "message": f"Simulación de respuesta en cola para +{reply.phone}"
    }


@app.get("/api/admin/orders")
def admin_get_orders():
    """Endpoint auxiliar para ver la lista de órdenes registradas localmente."""
    from database import get_all_orders
    return {"orders": get_all_orders()}


if __name__ == "__main__":
    import uvicorn
    logger.info("⚡ Iniciando servidor local en http://localhost:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)


# Integración Khipu (Pago Online)
# pykhipu import moved inside function for serverless safety

KHIPU_RECEIVER_ID = "523231"
KHIPU_SECRET = "8a6b3479d14d5247d8e04aae1b9ac0d3380782de"

@app.post("/api/create_khipu_payment")
async def create_khipu_payment(order: OrderRequest):
    """Crea una orden en Google Sheets y genera un link de pago con Khipu."""
    try:
        temp_id = f"TEMP-{int(time.time())}"
        p_name = order.product_name if order.product_name else "Pizarra Mágica LED 12\""
        try:
            if isinstance(order.product_price, (int, float)):
                p_price = float(order.product_price)
            elif isinstance(order.product_price, str):
                p_price = float(order.product_price.replace('$', '').replace('.', '').replace(',', '').strip())
            else:
                p_price = 24990.0
        except Exception:
            p_price = 24990.0
        
        # 1. Guardar orden inicial en Google Sheets como PENDIENTE_PAGO_ONLINE
        from utils.sheets_helper import save_order_to_sheets
        try:
            save_order_to_sheets(
                order_id=temp_id,
                client_name=order.name,
                phone=order.phone,
                address=order.address,
                city=order.city,
                product_name=p_name,
                price=p_price,
                rut=order.rut or "-",
                email=order.email or "-",
                calle=order.address,
                n_casa="-",
                region=order.region or "-",
                comuna=order.city or "-",
                unidades=order.unidades or 1
            )
        except Exception as e_sheet:
            logger.error(f"Error al guardar en Sheets antes de Khipu: {e_sheet}")

        # 2. Generar link de pago en Khipu
        try:
            from pykhipu.client import Client
            client = Client(receiver_id=KHIPU_RECEIVER_ID, secret=KHIPU_SECRET)
        except ImportError:
            logger.error("Librería pykhipu no disponible en Vercel runtime.")
            raise HTTPException(status_code=500, detail="Módulo de pago Khipu no disponible en runtime.")
        res = client.payments.post(
            subject=f"Mundo Aura - {p_name}",
            currency="CLP",
            amount=int(p_price),
            return_url="https://mundoaura.cl/?payment=success",
            cancel_url="https://mundoaura.cl/?payment=cancel",
            custom=temp_id,
            payer_email=order.email if (order.email and "@" in order.email) else "soporte.mundoaura@gmail.com"
        )
        logger.info(f"Creado pago Khipu ID: {res.payment_id} URL: {res.payment_url}")
        return {
            "status": "success",
            "payment_id": res.payment_id,
            "payment_url": res.payment_url
        }
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'errors') and e.errors:
            err_details = [getattr(item, 'message', str(item)) for item in e.errors]
            error_msg = ", ".join(err_details)
        
        if "excede el" in error_msg.lower() or "5000" in error_msg:
            error_msg = "Khipu está activando el límite para montos superiores a $5.000. Por favor usa 'Paga en Casa' mientras Khipu aprueba el límite."

        logger.error(f"Error al crear pago Khipu: {error_msg}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": error_msg}
        )
