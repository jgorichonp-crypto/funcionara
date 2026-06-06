"""
database.py: Módulo para manejar la persistencia de pedidos de manera híbrida.
Si está definida DATABASE_URL, se conecta a PostgreSQL (Supabase).
De lo contrario, usa SQLite localmente (orders.db).
"""
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from config import settings

logger = logging.getLogger("Database")
DB_NAME = "orders.db"

# Intentar importar dependencias de PostgreSQL de manera segura
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def is_postgres() -> bool:
    """Verifica si la configuración indica el uso de PostgreSQL."""
    return POSTGRES_AVAILABLE and settings.database_url is not None and settings.database_url.strip() != ""


def get_db_connection():
    """Retorna una conexión a la base de datos (PostgreSQL o SQLite) según la configuración."""
    if is_postgres():
        return psycopg2.connect(settings.database_url)
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """Inicializa las tablas en la base de datos activa (SQLite o PostgreSQL)."""
    if is_postgres():
        # Sintaxis PostgreSQL
        query = """
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            dropi_order_id VARCHAR(255) UNIQUE,
            client_name VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            address TEXT NOT NULL,
            city VARCHAR(100) NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            price NUMERIC(12, 2) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING_CONFIRMATION',
            created_at VARCHAR(100) NOT NULL,
            updated_at VARCHAR(100) NOT NULL
        );
        """
        engine = "PostgreSQL (Supabase)"
    else:
        # Sintaxis SQLite
        query = """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dropi_order_id TEXT UNIQUE,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING_CONFIRMATION',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
        engine = "SQLite (Local)"

    try:
        if is_postgres():
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                conn.commit()
        else:
            with get_db_connection() as conn:
                conn.execute(query)
                conn.commit()
        logger.info(f"✅ Base de datos [{engine}] inicializada correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al inicializar la base de datos [{engine}]: {str(e)}")


def save_order(
    dropi_order_id: str,
    client_name: str,
    phone: str,
    address: str,
    city: str,
    product_name: str,
    price: float,
    status: str = "PENDING_CONFIRMATION"
) -> bool:
    """Registra un nuevo pedido en la base de datos activa."""
    now_str = datetime.now().isoformat()
    
    # Limpiar el teléfono para estandarizar
    clean_phone = "".join(filter(str.isdigit, phone))
    if len(clean_phone) == 9 and clean_phone.startswith("9"):
        clean_phone = "56" + clean_phone
        
    placeholder = "%s" if is_postgres() else "?"
    query = f"""
    INSERT INTO orders (
        dropi_order_id, client_name, phone, address, city, 
        product_name, price, status, created_at, updated_at
    ) VALUES ({', '.join([placeholder]*10)})
    """
    
    try:
        if is_postgres():
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        query,
                        (dropi_order_id, client_name, clean_phone, address, city, 
                         product_name, price, status, now_str, now_str)
                    )
                conn.commit()
        else:
            with get_db_connection() as conn:
                conn.execute(
                    query,
                    (dropi_order_id, client_name, clean_phone, address, city, 
                     product_name, price, status, now_str, now_str)
                )
                conn.commit()
        logger.info(f"💾 Pedido {dropi_order_id} guardado en BD local (Cliente: {client_name}, Fono: {clean_phone})")
        return True
    except (sqlite3.IntegrityError, psycopg2.IntegrityError if is_postgres() else Exception) as e:
        # Captura de error de unicidad
        logger.warning(f"⚠️ El pedido {dropi_order_id} ya estaba registrado en la base de datos.")
        return False
    except Exception as e:
        logger.error(f"❌ Error al guardar pedido en BD: {str(e)}")
        return False


def get_pending_order_by_phone(phone: str) -> Optional[Dict]:
    """
    Busca la orden más reciente con estado 'PENDING_CONFIRMATION'
    para un número de teléfono específico.
    """
    clean_phone = "".join(filter(str.isdigit, phone))
    if len(clean_phone) == 9 and clean_phone.startswith("9"):
        clean_phone = "56" + clean_phone

    placeholder = "%s" if is_postgres() else "?"
    query = f"""
    SELECT * FROM orders 
    WHERE phone = {placeholder} AND status = 'PENDING_CONFIRMATION'
    ORDER BY id DESC LIMIT 1
    """
    
    try:
        if is_postgres():
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (clean_phone,))
                    row = cur.fetchone()
                    if row:
                        return dict(row)
        else:
            with get_db_connection() as conn:
                row = conn.execute(query, (clean_phone,)).fetchone()
                if row:
                    return dict(row)
    except Exception as e:
        logger.error(f"❌ Error al consultar orden por teléfono: {str(e)}")
    return None


def update_order_status(dropi_order_id: str, status: str) -> bool:
    """Actualiza el estado de confirmación de una orden."""
    now_str = datetime.now().isoformat()
    placeholder = "%s" if is_postgres() else "?"
    query = f"""
    UPDATE orders 
    SET status = {placeholder}, updated_at = {placeholder} 
    WHERE dropi_order_id = {placeholder}
    """
    
    try:
        rowcount = 0
        if is_postgres():
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (status, now_str, dropi_order_id))
                    rowcount = cur.rowcount
                conn.commit()
        else:
            with get_db_connection() as conn:
                cursor = conn.execute(query, (status, now_str, dropi_order_id))
                conn.commit()
                rowcount = cursor.rowcount
                
        if rowcount > 0:
            logger.info(f"🔄 Pedido {dropi_order_id} actualizado localmente a estado: {status}")
            return True
        else:
            logger.warning(f"⚠️ No se encontró el pedido {dropi_order_id} para actualizar estado.")
    except Exception as e:
        logger.error(f"❌ Error al actualizar estado del pedido en BD: {str(e)}")
    return False


def get_all_orders() -> List[Dict]:
    """Retorna todas las órdenes registradas en la base de datos."""
    query = "SELECT * FROM orders ORDER BY id DESC"
    try:
        if is_postgres():
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
        else:
            with get_db_connection() as conn:
                rows = conn.execute(query).fetchall()
                return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"❌ Error al obtener todos los pedidos: {str(e)}")
        return []
