"""
test_crm.py: Script de verificación para probar el Agente CRM y la Base de Datos SQLite.
"""
import asyncio
import os
import sys
import logging

# Configurar logging para ver las trazas
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TestCRM")

# 1. Asegurar que estamos en el path correcto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, save_order, get_pending_order_by_phone, get_all_orders, update_order_status, is_postgres
from agents.crm import process_incoming_reply, send_order_confirmation_request

# Limpiar BD anterior para pruebas limpias (solo si no es Postgres)
if not is_postgres() and os.path.exists("orders.db"):
    try:
        os.remove("orders.db")
        logger.info("🗑️ Base de datos orders.db anterior eliminada para testing.")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo eliminar orders.db: {e}")


async def run_tests():
    logger.info("🎬 Iniciando pruebas del Agente CRM...")
    
    # Prueba 1: Inicializar Base de Datos
    init_db()
    if not is_postgres() and not os.path.exists("orders.db"):
        logger.error("❌ Falló: La base de datos orders.db no se creó.")
        sys.exit(1)
    logger.info("✅ Prueba 1 completada: Base de datos creada.")
    
    # Prueba 2: Registrar un pedido
    dropi_id = "TEST-ORDER-123"
    client_name = "Juan Pérez"
    phone = "56987654321"
    address = "Av. Providencia 1234, Depto 50"
    city = "Providencia"
    product = "Proyector Galaxy LED"
    price = 45000.0
    
    saved = save_order(
        dropi_order_id=dropi_id,
        client_name=client_name,
        phone=phone,
        address=address,
        city=city,
        product_name=product,
        price=price
    )
    
    if not saved:
        logger.error("❌ Falló: No se pudo registrar la orden en la base de datos.")
        sys.exit(1)
        
    orders = get_all_orders()
    if len(orders) != 1 or orders[0]["dropi_order_id"] != dropi_id:
        logger.error("❌ Falló: La orden recuperada no coincide con la guardada.")
        sys.exit(1)
    logger.info("✅ Prueba 2 completada: Orden registrada y recuperada exitosamente.")
    
    # Prueba 3: Recuperar orden pendiente por teléfono
    pending = get_pending_order_by_phone(phone)
    if not pending or pending["dropi_order_id"] != dropi_id:
        logger.error("❌ Falló: No se encontró la orden pendiente por teléfono.")
        sys.exit(1)
    logger.info("✅ Prueba 3 completada: Orden pendiente encontrada por teléfono.")
    
    # Prueba 4: Enviar solicitud de confirmación (Simulación)
    sent = await send_order_confirmation_request(pending)
    if not sent:
        logger.error("❌ Falló: No se pudo enviar el mensaje simulado de confirmación.")
        sys.exit(1)
    logger.info("✅ Prueba 4 completada: Solicitud de confirmación generada correctamente.")
    
    # Prueba 5: Simular respuesta de confirmación del cliente ("1")
    logger.info("🔄 Simulando respuesta del cliente: '1' (Confirmar)...")
    processed = await process_incoming_reply(phone, "1")
    if not processed:
        logger.error("❌ Falló: process_incoming_reply devolvió False para confirmación válida.")
        sys.exit(1)
        
    # Verificar que el estado cambió a CONFIRMED en la base de datos
    updated_order = get_all_orders()[0]
    if updated_order["status"] != "CONFIRMED":
        logger.error(f"❌ Falló: El estado no cambió a CONFIRMED. Estado actual: {updated_order['status']}")
        sys.exit(1)
    logger.info("✅ Prueba 5 completada: Confirmación procesada y estado de orden actualizado a CONFIRMED.")
    
    # Prueba 6: Simular respuesta de cancelación del cliente en una segunda orden
    dropi_id_2 = "TEST-ORDER-456"
    phone_2 = "56999999999"
    save_order(
        dropi_order_id=dropi_id_2,
        client_name=f"María Gómez",
        phone=phone_2,
        address="Calle Larga 89",
        city="Santiago Centro",
        product_name=product,
        price=price
    )
    
    logger.info("🔄 Simulando respuesta del cliente 2: 'no, quiero cancelar'...")
    processed_2 = await process_incoming_reply(phone_2, "no, quiero cancelar")
    if not processed_2:
        logger.error("❌ Falló: process_incoming_reply devolvió False para cancelación válida.")
        sys.exit(1)
        
    updated_order_2 = [o for o in get_all_orders() if o["dropi_order_id"] == dropi_id_2][0]
    if updated_order_2["status"] != "CANCELLED":
        logger.error(f"❌ Falló: El estado no cambió a CANCELLED. Estado actual: {updated_order_2['status']}")
        sys.exit(1)
    logger.info("✅ Prueba 6 completada: Cancelación procesada y estado de orden actualizado a CANCELLED.")
    
    logger.info("\n" + "="*60)
    logger.info("🎉 ¡TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE! 🎉")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
