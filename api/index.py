"""
Función Serverless para Vercel.
Recibe pedidos de la Landing Page y los envía de forma segura a Dropi Chile.
"""
import logging
import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VercelDropi")

app = FastAPI()


class OrderRequest(BaseModel):
    name: str
    phone: str
    address: str
    city: str


@app.post("/api/order")
async def create_order(order: OrderRequest):
    """
    Endpoint seguro de procesamiento de pedidos COD.
    """
    logger.info(f"📥 Pedido Vercel recibido: {order.name} - {order.phone} - {order.city}")
    
    # 1. Comprobar si tenemos configurada la clave real de Dropi
    is_placeholder = (
        not settings.dropi_api_key or 
        settings.dropi_api_key == "your-dropi-api-key-here" or 
        "placeholder" in settings.dropi_api_key.lower()
    )
    
    if is_placeholder:
        # Modo Simulado (No hay API key configurada)
        logger.info("[MODO SIMULACIÓN] Creando orden ficticia en Dropi Chile")
        return {
            "status": "success",
            "message": "Pedido simulado registrado exitosamente en Dropi Chile (Modo Desarrollo en Vercel)",
            "order_id": "VERCEL-SIM-COD-12345"
        }
        
    # Modo Producción (Llamada real a la API de Dropi Chile)
    logger.info(f"🚀 Iniciando proceso de envío de orden real a Dropi Chile (Producto ID: {settings.dropi_product_id})...")
    
    headers = {
        "dropi-integration-key": settings.dropi_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 1. Obtener detalles del producto (nombre, precio, proveedor) desde Dropi para armar un payload perfecto
    product_name = "Producto de Tienda"
    product_price = 0.0
    supplier_id = None
    import json
    
    product_url = f"https://api.dropi.cl/integrations/products/{settings.dropi_product_id}"
    logger.info(f"🔍 Obteniendo datos del producto desde: {product_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(product_url, headers=headers, timeout=10) as prod_resp:
                if prod_resp.status == 200:
                    prod_data = await prod_resp.json()
                    if prod_data.get("isSuccess") and prod_data.get("objects"):
                        prod_obj = prod_data["objects"]
                        product_name = prod_obj.get("name", product_name)
                        product_price = float(prod_obj.get("sale_price") or prod_obj.get("price") or 0.0)
                        supplier_id = prod_obj.get("user_id") or prod_obj.get("supplier_id")
                        logger.info(f"✅ Datos del producto recuperados: '{product_name}' - Precio: {product_price} - Proveedor ID: {supplier_id}")
                    else:
                        logger.warning("⚠️ La API de Dropi no retornó un objeto de producto válido en la búsqueda.")
                else:
                    logger.warning(f"⚠️ No se pudieron obtener detalles del producto (Status {prod_resp.status}). Usando valores por defecto.")
    except Exception as e:
        logger.error(f"❌ Error al consultar detalles del producto en Dropi: {str(e)}")

    # 2. Formatear la orden con el formato exacto requerido por el endpoint /orders/myorders de la API de Integraciones
    name_parts = order.name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # URL de creación de órdenes
    url = "https://api.dropi.cl/integrations/orders/myorders"
    
    payload = {
        "total_order": product_price,
        "notes": "Pedido creado automáticamente desde Landing Page (Vercel)",
        "name": first_name,
        "surname": last_name,
        "dir": order.address,
        "country": "CL",
        "state": order.city,
        "city": order.city,
        "phone": order.phone,
        "client_email": "cliente_landing@funcionara.cl",
        "payment_method_id": 1,  # COD / Contra Entrega
        "status": "PENDIENTE CONFIRMACION",
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
        "shop_order_id": 99999  # ID de orden ficticio de la tienda
    }
    
    logger.info(f"🚀 Enviando orden a: {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                response_text = await response.text()
                status_code = response.status
                
                # Intentar parsear respuesta Dropi
                try:
                    response_json = json.loads(response_text)
                    is_success = response_json.get("isSuccess", False)
                    msg = response_json.get("message", "")
                except Exception:
                    is_success = status_code in [200, 201]
                    msg = response_text
                
                if is_success:
                    data = response_json if 'response_json' in locals() else {}
                    objects = data.get("objects", {})
                    dropi_order_id = None
                    if isinstance(objects, dict):
                        dropi_order_id = objects.get("id")
                    if not dropi_order_id and isinstance(data, dict):
                        dropi_order_id = data.get("order_id") or data.get("id")
                    dropi_order_id = dropi_order_id or "OK"
                    
                    logger.info(f"✅ Pedido creado en Dropi con éxito. ID: {dropi_order_id}")
                    return {
                        "status": "success",
                        "message": "Pedido registrado exitosamente en Dropi Chile.",
                        "order_id": dropi_order_id
                    }
                else:
                    logger.error(f"❌ Error en API de Dropi (Status {status_code}): {response_text}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "error",
                            "message": f"Dropi API devolvió error: {msg}",
                            "detail": response_text
                        }
                    )
    except Exception as e:
        logger.error(f"❌ Excepción al conectar con Dropi: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con el proveedor Dropi: {str(e)}"
        )
