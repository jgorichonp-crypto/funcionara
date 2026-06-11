"""
Supplier Validation Module
Valida la confiabilidad y calidad de proveedores en AliExpress.
Analiza historial, reputación, tiempos de respuesta y stock.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SupplierValidationResult:
    """Resultado de la validación del proveedor"""
    supplier_url: str
    supplier_name: str = ""
    supplier_id: str = ""
    
    # Métricas de confiabilidad
    years_in_platform: float = 0.0
    total_transactions: int = 0
    positive_feedback_pct: float = 0.0
    dispute_rate_pct: float = 0.0
    
    # Métricas de servicio
    response_time_hours: float = 0.0
    shipping_speed_score: float = 0.0  # 0-5
    communication_score: float = 0.0   # 0-5
    
    # Métricas de producto
    products_in_stock: int = 0
    min_order_quantity: int = 1
    accepts_returns: bool = False
    return_rate_pct: float = 0.0
    
    # Análisis de confiabilidad
    reliability_score: float = 0.0  # 0-100
    reliability_level: str = "unknown"  # excellent, good, fair, poor
    is_reliable: bool = False
    
    # Banderas de alerta
    red_flags: List[str] = None
    warnings: List[str] = None
    
    # Recomendación
    recommendation: str = ""
    
    def __post_init__(self):
        if self.red_flags is None:
            self.red_flags = []
        if self.warnings is None:
            self.warnings = []


# ============================================================================
# CONFIGURACIÓN DE UMBRALES
# ============================================================================

RELIABILITY_THRESHOLDS = {
    "years_in_platform": {
        "excellent": 3.0,   # >3 años
        "good": 2.0,        # 2-3 años
        "fair": 1.0,        # 1-2 años
        "poor": 1.0         # <1 año
    },
    "positive_feedback": {
        "excellent": 98.0,  # >98%
        "good": 95.0,       # 95-98%
        "fair": 90.0,       # 90-95%
        "poor": 90.0        # <90%
    },
    "dispute_rate": {
        "excellent": 1.0,   # <1%
        "good": 2.0,        # 1-2%
        "fair": 5.0,        # 2-5%
        "poor": 5.0         # >5%
    },
    "response_time": {
        "excellent": 12.0,  # <12 horas
        "good": 24.0,       # 12-24 horas
        "fair": 48.0,       # 24-48 horas
        "poor": 48.0        # >48 horas
    },
    "transactions": {
        "excellent": 10000, # >10k transacciones
        "good": 5000,       # 5k-10k
        "fair": 1000,       # 1k-5k
        "poor": 1000        # <1k
    }
}


# ============================================================================
# FUNCIONES DE SCRAPING Y ANÁLISIS
# ============================================================================

async def scrape_supplier_profile(supplier_url: str) -> Dict:
    """
    Scraping del perfil del proveedor en AliExpress.
    
    En producción usar:
    - BeautifulSoup o Selenium
    - URL del store del vendedor
    - Extraer: años en plataforma, feedback, transacciones
    
    Args:
        supplier_url: URL del producto en AliExpress
        
    Returns:
        Dict con datos del proveedor
    """
    logger.info(f"👤 [SUPPLIER] Analizando perfil del proveedor...")
    await asyncio.sleep(1.0)
    
    # Extraer ID del supplier de la URL (simulado)
    # En producción: extraer del HTML de la página
    import random
    
    supplier_id = "unknown"
    if "/item/" in supplier_url:
        try:
            parts = supplier_url.split("/item/")[1].split(".html")[0].split("?")[0]
            supplier_id = "".join(c for c in parts if c.isdigit())
        except Exception:
            supplier_id = "unknown"
            
    if not supplier_id or not supplier_id.isdigit():
        # Generar un ID aleatorio numérico para evitar errores en simulación
        supplier_id = str(random.randint(1000000000, 9999999999))
    
    # Simulación de datos del proveedor
    # En producción: scraping real de AliExpress
    
    # Proveedores "buenos" (IDs que terminan en números altos)
    if int(supplier_id[-1]) >= 7:
        profile = {
            "supplier_id": supplier_id,
            "supplier_name": f"Premium Electronics Store {supplier_id[:4]}",
            "years_in_platform": 4.5,
            "total_transactions": 15000,
            "positive_feedback_pct": 98.5,
            "dispute_rate_pct": 0.8,
            "response_time_hours": 8.0,
            "shipping_speed_score": 4.8,
            "communication_score": 4.9
        }
    # Proveedores "regulares"
    elif int(supplier_id[-1]) >= 4:
        profile = {
            "supplier_id": supplier_id,
            "supplier_name": f"Global Trade Co {supplier_id[:4]}",
            "years_in_platform": 2.2,
            "total_transactions": 6500,
            "positive_feedback_pct": 95.8,
            "dispute_rate_pct": 2.1,
            "response_time_hours": 18.0,
            "shipping_speed_score": 4.3,
            "communication_score": 4.2
        }
    # Proveedores "malos"
    else:
        profile = {
            "supplier_id": supplier_id,
            "supplier_name": f"New Seller {supplier_id[:4]}",
            "years_in_platform": 0.8,
            "total_transactions": 450,
            "positive_feedback_pct": 88.5,
            "dispute_rate_pct": 6.2,
            "response_time_hours": 52.0,
            "shipping_speed_score": 3.5,
            "communication_score": 3.2
        }
    
    logger.info(f"  ✅ Proveedor: {profile['supplier_name']}")
    logger.info(f"     Años en plataforma: {profile['years_in_platform']}")
    logger.info(f"     Transacciones: {profile['total_transactions']:,}")
    logger.info(f"     Feedback positivo: {profile['positive_feedback_pct']}%")
    
    return profile


async def scrape_supplier_inventory(supplier_url: str) -> Dict:
    """
    Analiza el inventario y políticas del proveedor.
    
    Args:
        supplier_url: URL del producto
        
    Returns:
        Dict con datos de inventario
    """
    logger.info(f"📦 [SUPPLIER] Analizando inventario y políticas...")
    await asyncio.sleep(0.6)
    
    # Simulación de datos de inventario
    # En producción: scraping de la página del producto
    
    inventory = {
        "products_in_stock": 850,
        "min_order_quantity": 1,
        "accepts_returns": True,
        "return_rate_pct": 2.5,
        "ships_to_chile": True,
        "estimated_delivery_days": 15
    }
    
    logger.info(f"  ✅ Stock: {inventory['products_in_stock']} unidades")
    logger.info(f"     Acepta devoluciones: {'Sí' if inventory['accepts_returns'] else 'No'}")
    logger.info(f"     Envía a Chile: {'Sí' if inventory['ships_to_chile'] else 'No'}")
    
    return inventory


async def analyze_supplier_reviews(supplier_url: str) -> Dict:
    """
    Analiza las reviews del proveedor para detectar patrones.
    
    Args:
        supplier_url: URL del producto
        
    Returns:
        Dict con análisis de reviews
    """
    logger.info(f"⭐ [SUPPLIER] Analizando reviews del proveedor...")
    await asyncio.sleep(0.8)
    
    # Simulación de análisis de reviews
    # En producción: scraping y NLP de reviews
    
    reviews_analysis = {
        "total_reviews": 3200,
        "avg_rating": 4.7,
        "common_complaints": [
            "Envío lento (8% de reviews)",
            "Empaque mejorable (3% de reviews)"
        ],
        "common_praises": [
            "Producto como se describe (92% de reviews)",
            "Buena comunicación (85% de reviews)",
            "Empaque seguro (78% de reviews)"
        ],
        "recent_negative_trend": False
    }
    
    logger.info(f"  ✅ Reviews: {reviews_analysis['total_reviews']:,} | Rating: {reviews_analysis['avg_rating']}⭐")
    
    return reviews_analysis


# ============================================================================
# CÁLCULO DE CONFIABILIDAD
# ============================================================================

def calculate_reliability_score(profile: Dict, inventory: Dict) -> float:
    """
    Calcula score de confiabilidad 0-100.
    
    Distribución:
    - Años en plataforma: 20 pts
    - Feedback positivo: 25 pts
    - Tasa de disputas: 20 pts
    - Tiempo de respuesta: 15 pts
    - Transacciones totales: 10 pts
    - Stock y políticas: 10 pts
    
    Args:
        profile: Datos del perfil del proveedor
        inventory: Datos de inventario
        
    Returns:
        Score de confiabilidad 0-100
    """
    score = 0.0
    
    # 1. Años en plataforma (20 pts)
    years = profile["years_in_platform"]
    if years >= 3.0:
        score += 20
    elif years >= 2.0:
        score += 15
    elif years >= 1.0:
        score += 10
    else:
        score += 5
    
    # 2. Feedback positivo (25 pts)
    feedback = profile["positive_feedback_pct"]
    if feedback >= 98.0:
        score += 25
    elif feedback >= 95.0:
        score += 20
    elif feedback >= 90.0:
        score += 12
    else:
        score += 5
    
    # 3. Tasa de disputas (20 pts) - Inverso: menos es mejor
    disputes = profile["dispute_rate_pct"]
    if disputes < 1.0:
        score += 20
    elif disputes < 2.0:
        score += 15
    elif disputes < 5.0:
        score += 8
    else:
        score += 2
    
    # 4. Tiempo de respuesta (15 pts) - Menos es mejor
    response = profile["response_time_hours"]
    if response < 12.0:
        score += 15
    elif response < 24.0:
        score += 12
    elif response < 48.0:
        score += 6
    else:
        score += 2
    
    # 5. Transacciones totales (10 pts)
    transactions = profile["total_transactions"]
    if transactions >= 10000:
        score += 10
    elif transactions >= 5000:
        score += 8
    elif transactions >= 1000:
        score += 5
    else:
        score += 2
    
    # 6. Stock y políticas (10 pts)
    stock_score = 0
    if inventory["products_in_stock"] >= 500:
        stock_score += 5
    elif inventory["products_in_stock"] >= 100:
        stock_score += 3
    else:
        stock_score += 1
    
    if inventory["accepts_returns"]:
        stock_score += 3
    
    if inventory["min_order_quantity"] == 1:
        stock_score += 2
    
    score += min(stock_score, 10)
    
    return round(score, 2)


def determine_reliability_level(score: float) -> str:
    """
    Determina nivel de confiabilidad basado en score.
    
    Args:
        score: Score de confiabilidad 0-100
        
    Returns:
        Nivel: "excellent", "good", "fair", "poor"
    """
    if score >= 80:
        return "excellent"
    elif score >= 65:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"


def identify_red_flags(profile: Dict, inventory: Dict) -> List[str]:
    """
    Identifica banderas rojas críticas.
    
    Args:
        profile: Datos del perfil
        inventory: Datos de inventario
        
    Returns:
        Lista de banderas rojas
    """
    red_flags = []
    
    # Proveedor muy nuevo
    if profile["years_in_platform"] < 0.5:
        red_flags.append("🚩 Proveedor MUY NUEVO (<6 meses) - Alto riesgo")
    
    # Feedback muy bajo
    if profile["positive_feedback_pct"] < 85.0:
        red_flags.append(f"🚩 Feedback BAJO ({profile['positive_feedback_pct']}%) - Mala reputación")
    
    # Tasa de disputas alta
    if profile["dispute_rate_pct"] > 5.0:
        red_flags.append(f"🚩 Tasa de disputas ALTA ({profile['dispute_rate_pct']}%) - Problemas frecuentes")
    
    # Tiempo de respuesta muy lento
    if profile["response_time_hours"] > 72.0:
        red_flags.append(f"🚩 Respuesta MUY LENTA (>{profile['response_time_hours']}h) - Mal servicio")
    
    # Pocas transacciones
    if profile["total_transactions"] < 100:
        red_flags.append(f"🚩 Pocas transacciones ({profile['total_transactions']}) - Sin historial")
    
    # Stock bajo
    if inventory["products_in_stock"] < 50:
        red_flags.append(f"🚩 Stock BAJO ({inventory['products_in_stock']} unidades) - Riesgo de agotarse")
    
    # No acepta devoluciones
    if not inventory["accepts_returns"]:
        red_flags.append("🚩 NO acepta devoluciones - Riesgo para clientes")
    
    return red_flags


def identify_warnings(profile: Dict, inventory: Dict) -> List[str]:
    """
    Identifica advertencias (no críticas pero importantes).
    
    Args:
        profile: Datos del perfil
        inventory: Datos de inventario
        
    Returns:
        Lista de advertencias
    """
    warnings = []
    
    # Proveedor relativamente nuevo
    if 0.5 <= profile["years_in_platform"] < 1.5:
        warnings.append(f"⚠️  Proveedor relativamente nuevo ({profile['years_in_platform']:.1f} años)")
    
    # Feedback aceptable pero no excelente
    if 90.0 <= profile["positive_feedback_pct"] < 95.0:
        warnings.append(f"⚠️  Feedback aceptable pero mejorable ({profile['positive_feedback_pct']}%)")
    
    # Tiempo de respuesta lento
    if 24.0 < profile["response_time_hours"] <= 48.0:
        warnings.append(f"⚠️  Tiempo de respuesta lento ({profile['response_time_hours']}h)")
    
    # Stock moderado
    if 50 <= inventory["products_in_stock"] < 200:
        warnings.append(f"⚠️  Stock moderado ({inventory['products_in_stock']} unidades) - Monitorear")
    
    # Tasa de devoluciones alta
    if inventory["return_rate_pct"] > 5.0:
        warnings.append(f"⚠️  Tasa de devoluciones alta ({inventory['return_rate_pct']}%)")
    
    return warnings


def generate_supplier_recommendation(result: SupplierValidationResult) -> str:
    """
    Genera recomendación basada en validación del proveedor.
    
    Args:
        result: Resultado de la validación
        
    Returns:
        Recomendación de acción
    """
    level = result.reliability_level
    score = result.reliability_score
    
    if level == "excellent":
        return (
            f"✅ PROVEEDOR EXCELENTE (Score: {score}/100)\n"
            f"   Alta confiabilidad. Proveedor ideal para trabajar.\n"
            f"   Puedes proceder con confianza."
        )
    elif level == "good":
        return (
            f"✅ PROVEEDOR BUENO (Score: {score}/100)\n"
            f"   Confiabilidad sólida. Proveedor recomendado.\n"
            f"   Monitorea las primeras órdenes."
        )
    elif level == "fair":
        return (
            f"⚠️  PROVEEDOR ACEPTABLE (Score: {score}/100)\n"
            f"   Confiabilidad moderada. Proceder con precaución.\n"
            f"   Considera buscar alternativas mejores."
        )
    else:  # poor
        return (
            f"🔴 PROVEEDOR NO CONFIABLE (Score: {score}/100)\n"
            f"   Baja confiabilidad. EVITAR este proveedor.\n"
            f"   Busca proveedores alternativos."
        )


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

async def validate_supplier(supplier_url: str) -> SupplierValidationResult:
    """
    Valida la confiabilidad de un proveedor de AliExpress.
    
    Proceso:
    1. Scraping del perfil del proveedor
    2. Análisis de inventario y políticas
    3. Análisis de reviews
    4. Cálculo de score de confiabilidad
    5. Identificación de banderas rojas
    6. Generación de recomendación
    
    Args:
        supplier_url: URL del producto en AliExpress
        
    Returns:
        SupplierValidationResult con análisis completo
    """
    logger.info("\n" + "="*70)
    logger.info("🔍 VALIDACIÓN DE PROVEEDOR")
    logger.info("="*70)
    logger.info(f"URL: {supplier_url}")
    logger.info("")
    
    # Scraping paralelo de datos del proveedor
    profile, inventory, reviews = await asyncio.gather(
        scrape_supplier_profile(supplier_url),
        scrape_supplier_inventory(supplier_url),
        analyze_supplier_reviews(supplier_url)
    )
    
    # Calcular score de confiabilidad
    reliability_score = calculate_reliability_score(profile, inventory)
    reliability_level = determine_reliability_level(reliability_score)
    is_reliable = reliability_level in ["excellent", "good"]
    
    # Identificar problemas
    red_flags = identify_red_flags(profile, inventory)
    warnings = identify_warnings(profile, inventory)
    
    # Crear resultado
    result = SupplierValidationResult(
        supplier_url=supplier_url,
        supplier_name=profile["supplier_name"],
        supplier_id=profile["supplier_id"],
        years_in_platform=profile["years_in_platform"],
        total_transactions=profile["total_transactions"],
        positive_feedback_pct=profile["positive_feedback_pct"],
        dispute_rate_pct=profile["dispute_rate_pct"],
        response_time_hours=profile["response_time_hours"],
        shipping_speed_score=profile["shipping_speed_score"],
        communication_score=profile["communication_score"],
        products_in_stock=inventory["products_in_stock"],
        min_order_quantity=inventory["min_order_quantity"],
        accepts_returns=inventory["accepts_returns"],
        return_rate_pct=inventory["return_rate_pct"],
        reliability_score=reliability_score,
        reliability_level=reliability_level,
        is_reliable=is_reliable,
        red_flags=red_flags,
        warnings=warnings
    )
    
    # Generar recomendación
    result.recommendation = generate_supplier_recommendation(result)
    
    # Log de resultados
    logger.info("\n" + "-"*70)
    logger.info("📊 RESULTADOS DE LA VALIDACIÓN")
    logger.info("-"*70)
    logger.info(f"Proveedor: {result.supplier_name}")
    logger.info(f"Score de Confiabilidad: {reliability_score}/100")
    logger.info(f"Nivel: {reliability_level.upper()}")
    logger.info(f"¿Confiable?: {'SÍ ✅' if is_reliable else 'NO ❌'}")
    logger.info("")
    logger.info("Métricas Clave:")
    logger.info(f"  • Años en plataforma: {profile['years_in_platform']}")
    logger.info(f"  • Transacciones: {profile['total_transactions']:,}")
    logger.info(f"  • Feedback positivo: {profile['positive_feedback_pct']}%")
    logger.info(f"  • Tasa de disputas: {profile['dispute_rate_pct']}%")
    logger.info(f"  • Tiempo de respuesta: {profile['response_time_hours']}h")
    logger.info(f"  • Stock: {inventory['products_in_stock']} unidades")
    logger.info("")
    
    if red_flags:
        logger.warning("🚩 BANDERAS ROJAS:")
        for flag in red_flags:
            logger.warning(f"  {flag}")
        logger.info("")
    
    if warnings:
        logger.info("⚠️  ADVERTENCIAS:")
        for warning in warnings:
            logger.info(f"  {warning}")
        logger.info("")
    
    logger.info(result.recommendation)
    logger.info("="*70 + "\n")
    
    return result


# ============================================================================
# FUNCIÓN DE FILTRADO
# ============================================================================

def should_reject_supplier(
    validation_result: SupplierValidationResult,
    strict_mode: bool = True
) -> bool:
    """
    Determina si un proveedor debe ser rechazado.
    
    Args:
        validation_result: Resultado de la validación
        strict_mode: Si True, rechaza "fair" y "poor"
                    Si False, solo rechaza "poor"
        
    Returns:
        True si debe rechazarse, False si puede continuar
    """
    # Siempre rechazar si hay banderas rojas críticas
    if len(validation_result.red_flags) > 0:
        return True
    
    # Rechazar según nivel de confiabilidad
    if strict_mode:
        return validation_result.reliability_level in ["fair", "poor"]
    else:
        return validation_result.reliability_level == "poor"


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    async def test():
        # Ejemplo 1: Proveedor bueno
        result1 = await validate_supplier("https://www.aliexpress.com/item/1005004892341567.html")
        print(f"\nProveedor 1 rechazado: {should_reject_supplier(result1)}")
        
        # Ejemplo 2: Proveedor malo
        result2 = await validate_supplier("https://www.aliexpress.com/item/1005001234567890.html")
        print(f"\nProveedor 2 rechazado: {should_reject_supplier(result2)}")
    
    asyncio.run(test())
