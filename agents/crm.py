"""
crm.py: Agente CRM para gestionar las confirmaciones de pedidos por WhatsApp.
Maneja plantillas de mensajes, llamadas a las APIs de WhatsApp y actualización
del estado de órdenes en Dropi Chile.
"""
import logging
import aiohttp
from curl_cffi import requests as curl_requests
from config import settings
from database import get_pending_order_by_phone, update_order_status

logger = logging.getLogger("CRMAgent")


async def send_whatsapp_message(to_phone: str, text: str) -> bool:
    """
    Envía un mensaje de WhatsApp al cliente usando el proveedor configurado.
    Soporta 'mock' (simulado), 'evolution' (Evolution API) y 'twilio'.
    """
    provider = settings.whatsapp_provider.lower()
    
    # Limpiar número de teléfono (solo dígitos)
    clean_phone = "".join(filter(str.isdigit, to_phone))
    
    if provider == "mock":
        logger.info(
            f"🧪 [SIMULACIÓN WHATSAPP] Enviando mensaje a +{clean_phone}:\n"
            f"--------------------------------------------------\n"
            f"{text}\n"
            f"--------------------------------------------------"
        )
        return True

    elif provider == "evolution":
        # Integración con Evolution API (Gateway self-hosted común en LatAm)
        url = f"{settings.whatsapp_api_url}/message/sendText/{settings.whatsapp_instance}"
        headers = {
            "apikey": settings.whatsapp_api_token,
            "Content-Type": "application/json"
        }
        payload = {
            "number": clean_phone,
            "options": {
                "delay": 1000,
                "presence": "composing"
            },
            "textMessage": {
                "text": text
            }
        }
        
        logger.info(f"📱 Enviando mensaje vía Evolution API a +{clean_phone}...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Mensaje enviado exitosamente a +{clean_phone} por Evolution API.")
                        return True
                    else:
                        resp_text = await response.text()
                        logger.error(f"❌ Error de Evolution API (Status {response.status}): {resp_text}")
        except Exception as e:
            logger.error(f"❌ Excepción al enviar mensaje con Evolution API: {str(e)}")
            
    elif provider == "twilio":
        # Integración con Twilio WhatsApp API
        # Auth se compone de Account SID (settings.whatsapp_instance) y Auth Token (settings.whatsapp_api_token)
        account_sid = settings.whatsapp_instance
        auth_token = settings.whatsapp_api_token
        from_number = settings.whatsapp_phone_number_id  # Ej: whatsapp:+14155238886
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        # Twilio requiere que el número destino empiece con whatsapp:+
        formatted_to = f"whatsapp:+{clean_phone}" if not clean_phone.startswith("whatsapp:") else clean_phone
        formatted_from = f"whatsapp:{from_number}" if not from_number.startswith("whatsapp:") else from_number
        
        payload = {
            "From": formatted_from,
            "To": formatted_to,
            "Body": text
        }
        
        logger.info(f"📱 Enviando mensaje vía Twilio a {formatted_to}...")
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(account_sid, auth_token)
                async with session.post(url, auth=auth, data=payload, timeout=10) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Mensaje enviado exitosamente a {formatted_to} por Twilio.")
                        return True
                    else:
                        resp_text = await response.text()
                        logger.error(f"❌ Error de Twilio API (Status {response.status}): {resp_text}")
        except Exception as e:
            logger.error(f"❌ Excepción al enviar mensaje con Twilio: {str(e)}")
            
    return False


async def update_dropi_order_status(dropi_order_id: str, new_status: str) -> bool:
    """
    Modifica el estado de una orden en Dropi Chile.
    Transiciona el pedido PENDIENTE a APROBADO o CANCELADO.
    """
    # Importación diferida para evitar importación circular
    from server import get_dropi_token
    
    token = get_dropi_token()
    if not token:
        logger.info(f"🧪 [SIMULACIÓN DROPI] Actualizando orden {dropi_order_id} a '{new_status}' en Dropi Chile.")
        return True

    # Dropi Chile API para actualizar orden
    # Se envía un PUT a la ruta de la orden específica para cambiar su estado
    url = f"https://api.dropi.cl/api/orders/myorders/{dropi_order_id}"
    
    # Mapeo del estado interno al esperado por Dropi
    # Dropi espera estados como "APROBADO", "CANCELADO", "PENDIENTE"
    dropi_status = "APROBADO" if new_status == "CONFIRMED" else "CANCELADO"
    
    headers = {
        "x-authorization": f"Bearer {token}",
        "Origin": "https://app.dropi.cl",
        "Referer": "https://app.dropi.cl/",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }
    
    payload = {
        "status": dropi_status
    }
    
    logger.info(f"🚀 Enviando actualización de orden a Dropi (Orden ID: {dropi_order_id}, Estado: {dropi_status})...")
    
    try:
        # Usar curl_cffi para evitar bloqueos Cloudflare TLS
        response = curl_requests.put(url, headers=headers, json=payload, impersonate="chrome120", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("isSuccess"):
                logger.info(f"✅ Orden {dropi_order_id} actualizada en Dropi con éxito.")
                return True
            else:
                logger.error(f"❌ Dropi rechazó la actualización de la orden: {data.get('message')}")
        else:
            logger.error(f"❌ Error al actualizar orden en Dropi (Status {response.status_code}): {response.text[:300]}")
    except Exception as e:
        logger.error(f"❌ Excepción al actualizar orden en Dropi: {str(e)}")
        
    return False


async def send_order_confirmation_request(order: dict) -> bool:
    """
    Construye y envía la plantilla persuasiva de confirmación de pedido.
    """
    price_formatted = f"{int(order['price']):,}".replace(",", ".")
    
    # Plantilla optimizada en español de Chile para COD
    message_text = (
        f"¡Hola *{order['client_name']}*! 🇨🇱✨\n\n"
        f"Recibimos tu pedido de *{order['product_name']}*.\n"
        f"💰 *Total a pagar:* ${price_formatted} CLP\n"
        f"🚚 *Envío:* GRATIS (Pago Contra Entrega/Al recibir en tu casa)\n"
        f"📍 *Destino:* {order['address']}, *{order['city']}*\n\n"
        f"Para validar tus datos y preparar tu despacho de inmediato, por favor responde a este mensaje con una opción:\n\n"
        f"1️⃣ Si respondes *1* (o dices 'sí', 'confirmo'): tu pedido se enviará hoy.\n"
        f"2️⃣ Si respondes *2* (o dices 'cancelar'): anularemos el pedido si fue un error.\n\n"
        f"¡Muchas gracias por preferirnos! 😊"
    )
    
    return await send_whatsapp_message(order["phone"], message_text)


async def process_incoming_reply(from_phone: str, reply_text: str) -> bool:
    """
    Procesa las respuestas de WhatsApp de los clientes.
    Identifica si es confirmación o cancelación y ejecuta la acción en Dropi.
    """
    clean_text = reply_text.strip().lower()
    logger.info(f"📥 Procesando respuesta de +{from_phone}: '{reply_text}'")
    
    # 1. Buscar si hay una orden pendiente de confirmación para este número
    order = get_pending_order_by_phone(from_phone)
    if not order:
        logger.warning(f"⚠️ No se encontró ningún pedido pendiente para el teléfono +{from_phone}.")
        # Mensaje por defecto cuando no hay orden pendiente
        await send_whatsapp_message(
            from_phone, 
            "Hola. No encontramos ningún pedido pendiente con este número. Si necesitas ayuda con una compra, por favor escríbenos directamente."
        )
        return False
        
    dropi_order_id = order["dropi_order_id"]
    client_name = order["client_name"]
    product_name = order["product_name"]
    
    # 2. Determinar la acción según el texto de respuesta
    confirm_keywords = ["1", "si", "sí", "confirmar", "confirmo", "ok", "bueno", "dale", "sipo", "correcto"]
    cancel_keywords = ["2", "no", "cancelar", "cancela", "anular", "anula", "rechazar", "rechazo"]
    
    is_confirm = any(kw in clean_text for kw in confirm_keywords) or clean_text == "1"
    is_cancel = any(kw in clean_text for kw in cancel_keywords) or clean_text == "2"
    
    if is_confirm:
        logger.info(f"✅ El cliente {client_name} ha CONFIRMADO el pedido {dropi_order_id} ({product_name}).")
        
        # Actualizar base de datos local
        update_order_status(dropi_order_id, "CONFIRMED")
        
        # Sincronizar estado con Dropi Chile
        await update_dropi_order_status(dropi_order_id, "CONFIRMED")
        
        # Enviar confirmación al cliente
        msg = (
            f"¡Excelente *{client_name}*! 🎉 Tu pedido ha sido confirmado con éxito.\n"
            f"Lo estamos preparando para despacharlo de inmediato. Próximamente te enviaremos el link de seguimiento de tu entrega.\n"
            f"¡Que tengas un excelente día! 🚚📦"
        )
        await send_whatsapp_message(from_phone, msg)
        return True
        
    elif is_cancel:
        logger.info(f"❌ El cliente {client_name} ha CANCELADO el pedido {dropi_order_id} ({product_name}).")
        
        # Actualizar base de datos local
        update_order_status(dropi_order_id, "CANCELLED")
        
        # Sincronizar estado con Dropi Chile
        await update_dropi_order_status(dropi_order_id, "CANCELLED")
        
        # Enviar mensaje de confirmación de cancelación
        msg = (
            f"Entendido *{client_name}*. Hemos cancelado tu pedido de {product_name}.\n"
            f"Lamentamos que no puedas recibirlo esta vez. Si deseas realizar otra compra en el futuro, serás muy bienvenido. ¡Saludos!"
        )
        await send_whatsapp_message(from_phone, msg)
        return True
        
    else:
        # No entendió la respuesta, enviar ayuda
        logger.info(f"❓ Respuesta no concluyente de {client_name}: '{reply_text}'. Pidiendo aclaración.")
        msg = (
            f"Disculpa, no pudimos entender tu respuesta. 🥺\n\n"
            f"Por favor responde únicamente con una opción:\n"
            f"1️⃣ para *CONFIRMAR* tu pedido de {product_name}.\n"
            f"2️⃣ para *CANCELAR* tu pedido.\n\n"
            f"¡Muchas gracias!"
        )
        await send_whatsapp_message(from_phone, msg)
        return False
