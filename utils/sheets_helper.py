"""
utils/sheets_helper.py: Helper para conectar el backend con la planilla de Google Sheets.
Envía peticiones HTTP POST a la URL de Google Apps Script.
"""
import logging
import datetime
from curl_cffi import requests as curl_requests
from config import settings

logger = logging.getLogger("SheetsHelper")


def save_order_to_sheets(
    order_id: str,
    client_name: str,
    phone: str,
    address: str,
    city: str,
    product_name: str,
    price: float,
    rut: str = "",
    email: str = "",
    calle: str = "",
    n_casa: str = "",
    region: str = "",
    comuna: str = "",
    unidades: int = 1
) -> bool:
    """
    Envía un nuevo pedido a Google Sheets vía el Webapp de Google Apps Script.
    """
    url = settings.google_sheet_webapp_url
    if not url or "exec" not in url:
        logger.warning("⚠️ GOOGLE_SHEET_WEBAPP_URL no configurado o inválido. Saltando escritura en Google Sheets.")
        return False

    # Limpiar número de teléfono
    clean_phone = "".join(filter(str.isdigit, phone))
    if len(clean_phone) == 9 and clean_phone.startswith("9"):
        clean_phone = "56" + clean_phone

    payload = {
        "action": "create_order",
        "order_id": order_id,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "client_name": client_name,
        "phone": "+" + clean_phone if not clean_phone.startswith("+") else clean_phone,
        "address": address,
        "city": city,
        "product_name": product_name,
        "price": price,
        "rut": rut,
        "email": email,
        "calle": calle,
        "n_casa": n_casa,
        "region": region,
        "comuna": comuna,
        "unidades": unidades
    }

    try:
        logger.info(f"📊 Guardando pedido {order_id} en Google Sheets...")
        response = curl_requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("status") == "success":
                logger.info(f"✅ Pedido {order_id} guardado en Google Sheets con éxito.")
                return True
            else:
                logger.error(f"❌ Google Sheets respondió con error: {res_data.get('message')}")
        else:
            logger.error(f"❌ Error HTTP al guardar en Google Sheets (Status {response.status_code}): {response.text[:300]}")
    except Exception as e:
        logger.error(f"❌ Excepción al guardar en Google Sheets: {str(e)}")
    return False


def update_order_status_in_sheets(
    order_id: str,
    status: str,
    dropi_id: str = ""
) -> bool:
    """
    Actualiza el estado de un pedido en Google Sheets vía el Webapp de Google Apps Script.
    """
    url = settings.google_sheet_webapp_url
    if not url or "exec" not in url:
        logger.warning("⚠️ GOOGLE_SHEET_WEBAPP_URL no configurado o inválido. Saltando actualización en Google Sheets.")
        return False

    payload = {
        "action": "update_status",
        "order_id": order_id,
        "status": status,
        "dropi_id": dropi_id
    }

    try:
        logger.info(f"📊 Actualizando pedido {order_id} a estado '{status}' en Google Sheets...")
        response = curl_requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("status") == "success":
                logger.info(f"✅ Pedido {order_id} actualizado en Google Sheets con éxito.")
                return True
            else:
                logger.error(f"❌ Google Sheets respondió con error al actualizar: {res_data.get('message')}")
        else:
            logger.error(f"❌ Error HTTP al actualizar en Google Sheets (Status {response.status_code}): {response.text[:300]}")
    except Exception as e:
        logger.error(f"❌ Excepción al actualizar en Google Sheets: {str(e)}")
    return False
