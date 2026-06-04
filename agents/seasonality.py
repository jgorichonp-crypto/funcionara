"""
Seasonality Intelligence Module
Gestiona la lógica de estacionalidad y hemisferios para búsqueda de productos.
Asegura que los productos encontrados sean relevantes para la época del año en el mercado objetivo.
"""
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SeasonalConfig:
    """Configuración de búsqueda basada en estacionalidad"""
    target_country: str
    target_season: str
    search_countries: List[str]
    search_timeframe: str
    seasonal_keywords: List[str]
    avoid_keywords: List[str]
    reason: str


# ============================================================================
# CONFIGURACIÓN DE HEMISFERIOS Y ESTACIONES
# ============================================================================

HEMISPHERES = {
    "north": {
        "countries": ["US", "UK", "CA", "DE", "FR", "ES", "IT", "MX"],
        "seasons": {
            "summer": [6, 7, 8],         # Junio, Julio, Agosto
            "fall": [9, 10, 11],         # Septiembre, Octubre, Noviembre
            "winter": [12, 1, 2],        # Diciembre, Enero, Febrero
            "spring": [3, 4, 5]          # Marzo, Abril, Mayo
        }
    },
    "south": {
        "countries": ["CL", "AR", "AU", "NZ", "BR", "ZA", "UY"],
        "seasons": {
            "summer": [12, 1, 2],        # Diciembre, Enero, Febrero
            "fall": [3, 4, 5],           # Marzo, Abril, Mayo
            "winter": [6, 7, 8],         # Junio, Julio, Agosto
            "spring": [9, 10, 11]        # Septiembre, Octubre, Noviembre
        }
    }
}


# Keywords por estación
SEASONAL_KEYWORDS = {
    "summer": {
        "include": [
            "beach", "pool", "swimming", "sunglasses", "fan", "cooler",
            "outdoor", "camping", "BBQ", "grill", "ice", "water",
            "playa", "piscina", "verano", "sol", "ventilador"
        ],
        "avoid": [
            "winter", "snow", "heater", "warm", "coat", "jacket",
            "invierno", "nieve", "calefactor", "abrigo"
        ]
    },
    "winter": {
        "include": [
            "heater", "blanket", "warm", "cozy", "hot", "thermal",
            "indoor", "fireplace", "snow", "ski", "coat", "jacket",
            "calefactor", "manta", "caliente", "térmico", "invierno"
        ],
        "avoid": [
            "summer", "beach", "pool", "fan", "cooling", "ice",
            "verano", "playa", "piscina", "ventilador"
        ]
    },
    "spring": {
        "include": [
            "garden", "flowers", "outdoor", "cleaning", "organization",
            "fresh", "renewal", "plants", "decoration",
            "jardín", "flores", "primavera", "limpieza", "plantas"
        ],
        "avoid": [
            "snow", "heavy winter", "extreme cold",
            "nieve", "frío extremo"
        ]
    },
    "fall": {
        "include": [
            "cozy", "home", "organization", "back to school", "autumn",
            "harvest", "pumpkin", "halloween", "thanksgiving",
            "otoño", "hogar", "organización", "vuelta al cole"
        ],
        "avoid": [
            "beach", "extreme heat", "pool",
            "playa", "calor extremo", "piscina"
        ]
    }
}


# Eventos especiales por mes
SPECIAL_EVENTS = {
    1: ["New Year", "Año Nuevo", "Sales", "Rebajas"],
    2: ["Valentine's Day", "San Valentín", "Love", "Amor"],
    3: ["Spring Break", "Women's Day", "Día de la Mujer"],
    4: ["Easter", "Pascua", "Spring", "Primavera"],
    5: ["Mother's Day", "Día de la Madre", "Outdoor"],
    6: ["Father's Day", "Día del Padre", "Summer Start"],
    7: ["Summer", "Verano", "Vacation", "Vacaciones"],
    8: ["Back to School", "Vuelta al Cole", "Summer End"],
    9: ["Fall Start", "Otoño", "Back to Work"],
    10: ["Halloween", "Autumn", "Otoño"],
    11: ["Black Friday", "Cyber Monday", "Thanksgiving"],
    12: ["Christmas", "Navidad", "New Year", "Año Nuevo"]
}


# ============================================================================
# FUNCIONES DE ANÁLISIS
# ============================================================================

def get_hemisphere(country_code: str) -> str:
    """
    Determina el hemisferio de un país.
    
    Args:
        country_code: Código ISO del país (ej: "CL", "US")
        
    Returns:
        "north" o "south"
    """
    for hemisphere, data in HEMISPHERES.items():
        if country_code.upper() in data["countries"]:
            return hemisphere
    
    # Por defecto, asumir hemisferio norte
    logger.warning(f"⚠️ País {country_code} no encontrado, asumiendo hemisferio norte")
    return "north"


def get_current_season(country_code: str, month: int = None) -> str:
    """
    Obtiene la estación actual para un país.
    
    Args:
        country_code: Código ISO del país
        month: Mes (1-12), si None usa el mes actual
        
    Returns:
        Nombre de la estación: "summer", "winter", "spring", "fall"
    """
    if month is None:
        month = datetime.now().month
    
    hemisphere = get_hemisphere(country_code)
    seasons = HEMISPHERES[hemisphere]["seasons"]
    
    for season, months in seasons.items():
        if month in months:
            return season
    
    return "spring"  # Fallback


def get_opposite_season(season: str) -> str:
    """
    Obtiene la estación opuesta.
    
    Args:
        season: Estación actual
        
    Returns:
        Estación opuesta
    """
    opposites = {
        "summer": "winter",
        "winter": "summer",
        "spring": "fall",
        "fall": "spring"
    }
    return opposites.get(season, season)


def calculate_search_timeframe(target_country: str, current_month: int = None) -> Tuple[int, List[str]]:
    """
    Calcula el timeframe óptimo para buscar productos.
    
    Si el target está en hemisferio sur, busca productos de hace 6 meses
    en hemisferio norte (misma estación).
    
    Args:
        target_country: País objetivo de venta
        current_month: Mes actual (1-12)
        
    Returns:
        Tupla (mes_busqueda, países_busqueda)
    """
    if current_month is None:
        current_month = datetime.now().month
    
    target_hemisphere = get_hemisphere(target_country)
    target_season = get_current_season(target_country, current_month)
    
    if target_hemisphere == "south":
        # Hemisferio sur: buscar en hemisferio norte hace 6 meses
        search_month = ((current_month - 6 - 1) % 12) + 1
        search_countries = HEMISPHERES["north"]["countries"][:3]  # Top 3
        
        logger.info(
            f"🌍 Target: {target_country} (Sur) - Estación: {target_season}\n"
            f"   Buscando productos de {get_month_name(search_month)} en {search_countries}"
        )
    else:
        # Hemisferio norte: buscar en mismo hemisferio, mismo mes
        search_month = current_month
        search_countries = HEMISPHERES["north"]["countries"][:3]
        
        logger.info(
            f"🌍 Target: {target_country} (Norte) - Estación: {target_season}\n"
            f"   Buscando productos actuales en {search_countries}"
        )
    
    return search_month, search_countries


def get_month_name(month: int) -> str:
    """Retorna el nombre del mes"""
    months = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    return months.get(month, "Desconocido")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def get_seasonal_search_config(
    target_country: str = "CL",
    current_month: int = None
) -> SeasonalConfig:
    """
    Genera configuración completa de búsqueda basada en estacionalidad.
    
    Esta es la función principal que debes usar en el Scout Agent.
    
    Args:
        target_country: País donde vas a vender (ej: "CL")
        current_month: Mes actual (1-12), si None usa el mes actual
        
    Returns:
        SeasonalConfig con toda la configuración de búsqueda
        
    Example:
        >>> config = get_seasonal_search_config("CL", 7)  # Julio en Chile
        >>> print(config.target_season)  # "winter"
        >>> print(config.search_countries)  # ["US", "UK", "CA"]
        >>> print(config.seasonal_keywords)  # ["heater", "blanket", ...]
    """
    if current_month is None:
        current_month = datetime.now().month
    
    # Determinar estación en país objetivo
    target_season = get_current_season(target_country, current_month)
    target_hemisphere = get_hemisphere(target_country)
    
    # Calcular dónde y cuándo buscar
    search_month, search_countries = calculate_search_timeframe(target_country, current_month)
    
    # Obtener keywords estacionales
    seasonal_keywords = SEASONAL_KEYWORDS[target_season]["include"]
    avoid_keywords = SEASONAL_KEYWORDS[target_season]["avoid"]
    
    # Agregar eventos especiales del mes
    special_events = SPECIAL_EVENTS.get(current_month, [])
    seasonal_keywords.extend(special_events)
    
    # Generar timeframe para búsqueda
    if target_hemisphere == "south":
        timeframe = f"last 6 months in {search_countries[0]}"
        reason = (
            f"Buscando productos de {get_month_name(search_month)} en hemisferio norte "
            f"(misma estación que {get_month_name(current_month)} en {target_country})"
        )
    else:
        timeframe = "last 7 days"
        reason = f"Buscando productos actuales (mismo hemisferio)"
    
    config = SeasonalConfig(
        target_country=target_country,
        target_season=target_season,
        search_countries=search_countries,
        search_timeframe=timeframe,
        seasonal_keywords=seasonal_keywords,
        avoid_keywords=avoid_keywords,
        reason=reason
    )
    
    # Log de configuración
    logger.info("\n" + "="*70)
    logger.info("🌍 CONFIGURACIÓN DE ESTACIONALIDAD")
    logger.info("="*70)
    logger.info(f"📍 País objetivo: {target_country} ({target_hemisphere.upper()})")
    logger.info(f"📅 Mes actual: {get_month_name(current_month)}")
    logger.info(f"🌤️  Estación: {target_season.upper()}")
    logger.info(f"🔍 Buscar en: {', '.join(search_countries)}")
    logger.info(f"⏰ Timeframe: {timeframe}")
    logger.info(f"✅ Keywords: {', '.join(seasonal_keywords[:5])}...")
    logger.info(f"❌ Evitar: {', '.join(avoid_keywords[:5])}...")
    logger.info(f"💡 Razón: {reason}")
    logger.info("="*70 + "\n")
    
    return config


def filter_products_by_season(products: list, seasonal_config: SeasonalConfig) -> list:
    """
    Filtra productos según relevancia estacional.
    
    Args:
        products: Lista de ProductCandidate
        seasonal_config: Configuración de estacionalidad
        
    Returns:
        Lista filtrada de productos relevantes para la estación
    """
    filtered = []
    
    for product in products:
        product_name_lower = product.name.lower()
        
        # Verificar si contiene keywords a evitar
        has_avoid_keywords = any(
            keyword.lower() in product_name_lower 
            for keyword in seasonal_config.avoid_keywords
        )
        
        if has_avoid_keywords:
            logger.debug(
                f"❌ [SEASONALITY] Producto descartado por estacionalidad: {product.name}"
            )
            continue
        
        # Bonus: si contiene keywords estacionales, aumentar score
        has_seasonal_keywords = any(
            keyword.lower() in product_name_lower 
            for keyword in seasonal_config.seasonal_keywords
        )
        
        if has_seasonal_keywords:
            product.score += 5  # Bonus de 5 puntos
            logger.debug(
                f"✅ [SEASONALITY] Producto relevante (+5 pts): {product.name}"
            )
        
        filtered.append(product)
    
    logger.info(
        f"🌤️  [SEASONALITY] Productos filtrados: {len(filtered)}/{len(products)} "
        f"(descartados {len(products) - len(filtered)} por estacionalidad)"
    )
    
    return filtered


# ============================================================================
# EJEMPLOS DE USO
# ============================================================================

if __name__ == "__main__":
    # Ejemplo 1: Julio en Chile (Invierno)
    print("\n" + "="*70)
    print("EJEMPLO 1: Julio en Chile")
    print("="*70)
    config = get_seasonal_search_config("CL", 7)
    print(f"Estación: {config.target_season}")
    print(f"Buscar en: {config.search_countries}")
    print(f"Keywords: {config.seasonal_keywords[:5]}")
    
    # Ejemplo 2: Diciembre en Chile (Verano)
    print("\n" + "="*70)
    print("EJEMPLO 2: Diciembre en Chile")
    print("="*70)
    config = get_seasonal_search_config("CL", 12)
    print(f"Estación: {config.target_season}")
    print(f"Buscar en: {config.search_countries}")
    print(f"Keywords: {config.seasonal_keywords[:5]}")
    
    # Ejemplo 3: Julio en USA (Verano)
    print("\n" + "="*70)
    print("EJEMPLO 3: Julio en USA")
    print("="*70)
    config = get_seasonal_search_config("US", 7)
    print(f"Estación: {config.target_season}")
    print(f"Buscar en: {config.search_countries}")
    print(f"Keywords: {config.seasonal_keywords[:5]}")
