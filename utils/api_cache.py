"""
api_cache.py: Sistema de caché local basado en SQLite para peticiones de APIs externas.
Evita duplicar llamadas a RapidAPI, Gemini, etc. si se consulta el mismo término en menos de 48 horas.
"""
import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any

logger = logging.getLogger("APICache")
DB_PATH = "api_cache.db"

def init_cache_db():
    """Inicializa la base de datos de caché si no existe."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                cache_key TEXT NOT NULL,
                response_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(api_name, cache_key)
            )
        """)
        # Crear índice para acelerar búsquedas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_key ON cache_entries(api_name, cache_key)")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Error al inicializar la BD de caché: {str(e)}")

# Inicializar al importar
init_cache_db()

def get_cached_response(api_name: str, cache_key: str, max_age_hours: int = 48) -> Optional[Any]:
    """
    Busca una respuesta en caché. Si existe y es más reciente que max_age_hours, la retorna.
    """
    # Normalizar la llave (quitar espacios de más y pasarlo a minúsculas)
    normalized_key = " ".join(cache_key.strip().lower().split())
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT response_data, created_at FROM cache_entries WHERE api_name = ? AND cache_key = ?",
            (api_name, normalized_key)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            response_data_str, created_at_str = row
            # En SQLite CURRENT_TIMESTAMP se almacena como YYYY-MM-DD HH:MM:SS
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            
            # Calcular antigüedad
            age = datetime.utcnow() - created_at
            if age < timedelta(hours=max_age_hours):
                logger.info(f"💾 [CACHE HIT] Usando respuesta de caché para {api_name} -> '{normalized_key}' (Antigüedad: {age.total_seconds()/3600:.1f} horas)")
                return json.loads(response_data_str)
            else:
                logger.info(f"⏳ [CACHE EXPIRED] Caché expirada para {api_name} -> '{normalized_key}' (Antigüedad: {age.total_seconds()/3600:.1f} horas)")
        return None
    except Exception as e:
        logger.error(f"❌ Error al consultar caché: {str(e)}")
        return None

def set_cached_response(api_name: str, cache_key: str, response_data: Any) -> None:
    """
    Almacena o actualiza una respuesta en la caché con el timestamp actual.
    """
    normalized_key = " ".join(cache_key.strip().lower().split())
    response_data_str = json.dumps(response_data, ensure_ascii=False)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cache_entries (api_name, cache_key, response_data, created_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(api_name, cache_key) DO UPDATE SET
                response_data = excluded.response_data,
                created_at = datetime('now')
        """, (api_name, normalized_key, response_data_str))
        conn.commit()
        conn.close()
        logger.debug(f"📝 [CACHE SET] Guardado en caché {api_name} -> '{normalized_key}'")
    except Exception as e:
        logger.error(f"❌ Error al guardar en caché: {str(e)}")
