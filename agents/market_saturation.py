"""
Market Saturation Analysis Module
Analiza la saturación del mercado local para evitar productos con demasiada competencia.
Scraping de Mercado Libre, tiendas chilenas y marketplaces locales.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class MarketSaturationResult:
    """Resultado del análisis de saturación de mercado"""
    product_name: str
    target_country: str
    
    # Competencia en marketplaces
    mercadolibre_sellers: int = 0
    mercadolibre_avg_price: float = 0.0
    mercadolibre_top_seller_sales: int = 0
    
    # Competencia en tiendas retail
    retail_stores_count: int = 0  # Falabella, Paris, Ripley, etc.
    retail_avg_price: float = 0.0
    
    # Competencia en Google Shopping
    google_shopping_results: int = 0
    
    # Análisis de saturación
    saturation_level: str = "unknown"  # low, medium, high, very_high
    saturation_score: float = 0.0  # 0-100 (0=sin competencia, 100=saturado)
    is_saturated: bool = False
    
    # Recomendaciones
    recommendation: str = ""
    competitive_advantage: List[str] = None
    
    def __post_init__(self):
        if self.competitive_advantage is None:
            self.competitive_advantage = []


# ============================================================================
# CONFIGURACIÓN DE UMBRALES
# ============================================================================

SATURATION_THRESHOLDS = {
    "mercadolibre_sellers": {
        "low": 10,      # <10 vendedores = baja competencia
        "medium": 30,   # 10-30 = competencia media
        "high": 50,     # 30-50 = alta competencia
        "very_high": 50 # >50 = muy saturado
    },
    "retail_presence": {
        "low": 1,       # 0-1 tiendas retail
        "medium": 3,    # 2-3 tiendas
        "high": 5,      # 4-5 tiendas
        "very_high": 5  # >5 tiendas (todas las grandes)
    },
    "google_shopping": {
        "low": 20,      # <20 resultados
        "medium": 50,   # 20-50 resultados
        "high": 100,    # 50-100 resultados
        "very_high": 100 # >100 resultados
    }
}


# ============================================================================
# FUNCIONES DE SCRAPING POR FUENTE
# ============================================================================

async def scrape_mercadolibre_chile(product_name: str) -> Dict:
    """
    Scraping de Mercado Libre Chile para analizar competencia.
    
    En producción usar:
    - URL: https://listado.mercadolibre.cl/PRODUCT_NAME
    - BeautifulSoup o Scrapy
    - Extraer: número de vendedores, precios, ventas
    
    Args:
        product_name: Nombre del producto a buscar
        
    Returns:
        Dict con datos de competencia en Mercado Libre
    """
    logger.info(f"🛒 [SATURATION] Analizando Mercado Libre Chile: '{product_name}'...")
    await asyncio.sleep(1.0)
    
    # Simulación basada en tipo de producto
    # En producción, hacer scraping real
    
    # Productos tech/gadgets suelen tener más competencia
    if any(keyword in product_name.lower() for keyword in ['led', 'bluetooth', 'smart', 'wireless']):
        sellers = 45
        avg_price = 35000  # CLP
        top_sales = 850
    # Productos de nicho tienen menos competencia
    elif any(keyword in product_name.lower() for keyword in ['galaxy', 'proyector', 'difusor']):
        sellers = 18
        avg_price = 42000
        top_sales = 320
    # Productos comunes muy saturados
    elif any(keyword in product_name.lower() for keyword in ['cargador', 'cable', 'funda']):
        sellers = 120
        avg_price = 8000
        top_sales = 2500
    else:
        sellers = 25
        avg_price = 28000
        top_sales = 450
    
    result = {
        "sellers_count": sellers,
        "avg_price_clp": avg_price,
        "top_seller_sales": top_sales,
        "url": f"https://listado.mercadolibre.cl/{product_name.replace(' ', '-')}"
    }
    
    logger.info(
        f"  ✅ Mercado Libre: {sellers} vendedores | "
        f"Precio promedio: ${avg_price:,} CLP | "
        f"Top seller: {top_sales} ventas"
    )
    
    return result


async def scrape_retail_stores_chile(product_name: str) -> Dict:
    """
    Verifica presencia en tiendas retail chilenas.
    
    Tiendas a verificar:
    - Falabella.com
    - Paris.cl
    - Ripley.cl
    - Lider.cl
    - Hites.com
    
    Args:
        product_name: Nombre del producto
        
    Returns:
        Dict con presencia en retail
    """
    logger.info(f"🏬 [SATURATION] Analizando tiendas retail Chile: '{product_name}'...")
    await asyncio.sleep(0.8)
    
    # Simulación de presencia en retail
    # Productos tech/populares suelen estar en retail
    stores_with_product = []
    
    if any(keyword in product_name.lower() for keyword in ['proyector', 'led', 'bluetooth']):
        stores_with_product = ["Falabella", "Paris"]
        avg_price = 55000
    elif any(keyword in product_name.lower() for keyword in ['cargador', 'cable']):
        stores_with_product = ["Falabella", "Paris", "Ripley", "Lider", "Hites"]
        avg_price = 12000
    else:
        stores_with_product = []
        avg_price = 0
    
    result = {
        "stores_count": len(stores_with_product),
        "stores_list": stores_with_product,
        "avg_price_clp": avg_price
    }
    
    if stores_with_product:
        logger.info(
            f"  ⚠️  Retail: Presente en {len(stores_with_product)} tiendas "
            f"({', '.join(stores_with_product)})"
        )
    else:
        logger.info(f"  ✅ Retail: No encontrado en tiendas grandes (buena señal)")
    
    return result


async def scrape_google_shopping_chile(product_name: str) -> Dict:
    """
    Analiza resultados en Google Shopping Chile.
    
    En producción usar:
    - Google Custom Search API
    - URL: https://www.google.cl/search?tbm=shop&q=PRODUCT
    - Contar número de resultados
    
    Args:
        product_name: Nombre del producto
        
    Returns:
        Dict con resultados de Google Shopping
    """
    logger.info(f"🔍 [SATURATION] Analizando Google Shopping Chile: '{product_name}'...")
    await asyncio.sleep(0.6)
    
    # Simulación de resultados
    # Productos populares tienen más resultados
    if any(keyword in product_name.lower() for keyword in ['cargador', 'cable', 'funda']):
        results_count = 250
    elif any(keyword in product_name.lower() for keyword in ['led', 'bluetooth', 'smart']):
        results_count = 85
    else:
        results_count = 35
    
    result = {
        "results_count": results_count,
        "url": f"https://www.google.cl/search?tbm=shop&q={product_name.replace(' ', '+')}"
    }
    
    logger.info(f"  📊 Google Shopping: {results_count} resultados")
    
    return result


# ============================================================================
# ANÁLISIS Y SCORING
# ============================================================================

def calculate_saturation_score(
    mercadolibre_sellers: int,
    retail_stores: int,
    google_results: int
) -> float:
    """
    Calcula score de saturación 0-100.
    
    0 = Sin competencia (ideal)
    100 = Completamente saturado (evitar)
    
    Args:
        mercadolibre_sellers: Número de vendedores en ML
        retail_stores: Número de tiendas retail
        google_results: Resultados en Google Shopping
        
    Returns:
        Score de saturación 0-100
    """
    score = 0.0
    
    # Peso: Mercado Libre (50%)
    if mercadolibre_sellers > 100:
        score += 50
    elif mercadolibre_sellers > 50:
        score += 40
    elif mercadolibre_sellers > 30:
        score += 30
    elif mercadolibre_sellers > 10:
        score += 15
    else:
        score += 5
    
    # Peso: Retail (30%)
    if retail_stores >= 5:
        score += 30
    elif retail_stores >= 3:
        score += 20
    elif retail_stores >= 1:
        score += 10
    else:
        score += 0
    
    # Peso: Google Shopping (20%)
    if google_results > 200:
        score += 20
    elif google_results > 100:
        score += 15
    elif google_results > 50:
        score += 10
    elif google_results > 20:
        score += 5
    else:
        score += 0
    
    return round(score, 2)


def determine_saturation_level(score: float) -> str:
    """
    Determina nivel de saturación basado en score.
    
    Args:
        score: Score de saturación 0-100
        
    Returns:
        Nivel: "low", "medium", "high", "very_high"
    """
    if score < 20:
        return "low"
    elif score < 40:
        return "medium"
    elif score < 60:
        return "high"
    else:
        return "very_high"


def generate_recommendation(saturation_result: MarketSaturationResult) -> str:
    """
    Genera recomendación basada en análisis de saturación.
    
    Args:
        saturation_result: Resultado del análisis
        
    Returns:
        Recomendación de acción
    """
    level = saturation_result.saturation_level
    score = saturation_result.saturation_score
    
    if level == "low":
        return (
            f"✅ EXCELENTE OPORTUNIDAD (Score: {score}/100)\n"
            f"   Baja competencia en Chile. Producto ideal para lanzar.\n"
            f"   Puedes ser de los primeros en el mercado."
        )
    elif level == "medium":
        return (
            f"⚠️  COMPETENCIA MODERADA (Score: {score}/100)\n"
            f"   Hay competencia pero aún hay espacio.\n"
            f"   Diferénciate con mejor copy, envío rápido o precio."
        )
    elif level == "high":
        return (
            f"🟠 ALTA COMPETENCIA (Score: {score}/100)\n"
            f"   Mercado competitivo. Solo lanzar si tienes ventaja clara.\n"
            f"   Considera buscar variaciones del producto."
        )
    else:  # very_high
        return (
            f"🔴 MERCADO SATURADO (Score: {score}/100)\n"
            f"   Demasiada competencia. EVITAR este producto.\n"
            f"   Busca alternativas o nichos menos saturados."
        )


def identify_competitive_advantages(saturation_result: MarketSaturationResult) -> List[str]:
    """
    Identifica posibles ventajas competitivas.
    
    Args:
        saturation_result: Resultado del análisis
        
    Returns:
        Lista de ventajas competitivas posibles
    """
    advantages = []
    
    # Si no está en retail, ventaja de precio
    if saturation_result.retail_stores_count == 0:
        advantages.append("Precio más bajo que retail (no tienen el producto)")
    
    # Si hay pocos vendedores en ML
    if saturation_result.mercadolibre_sellers < 20:
        advantages.append("Poca competencia en marketplaces")
    
    # Si el top seller no tiene muchas ventas
    if saturation_result.mercadolibre_top_seller_sales < 500:
        advantages.append("Mercado no dominado por un líder claro")
    
    # Siempre puedes competir con estos
    advantages.extend([
        "Envío más rápido (eCommerce vs Marketplace)",
        "Mejor experiencia de compra (landing page profesional)",
        "Marketing en redes sociales (TikTok/Instagram)",
        "Garantía y soporte post-venta"
    ])
    
    return advantages


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

async def analyze_market_saturation(
    product_name: str,
    target_country: str = "CL"
) -> MarketSaturationResult:
    """
    Analiza la saturación del mercado para un producto.
    
    Proceso:
    1. Scraping de Mercado Libre (competencia marketplace)
    2. Scraping de tiendas retail (competencia establecida)
    3. Análisis de Google Shopping (competencia total)
    4. Cálculo de score de saturación
    5. Generación de recomendación
    
    Args:
        product_name: Nombre del producto a analizar
        target_country: País objetivo (default: Chile)
        
    Returns:
        MarketSaturationResult con análisis completo
    """
    logger.info("\n" + "="*70)
    logger.info("🔍 ANÁLISIS DE SATURACIÓN DE MERCADO")
    logger.info("="*70)
    logger.info(f"Producto: {product_name}")
    logger.info(f"País: {target_country}")
    logger.info("")
    
    # Scraping paralelo de todas las fuentes
    ml_data, retail_data, google_data = await asyncio.gather(
        scrape_mercadolibre_chile(product_name),
        scrape_retail_stores_chile(product_name),
        scrape_google_shopping_chile(product_name)
    )
    
    # Calcular score de saturación
    saturation_score = calculate_saturation_score(
        ml_data["sellers_count"],
        retail_data["stores_count"],
        google_data["results_count"]
    )
    
    saturation_level = determine_saturation_level(saturation_score)
    is_saturated = saturation_level in ["high", "very_high"]
    
    # Crear resultado
    result = MarketSaturationResult(
        product_name=product_name,
        target_country=target_country,
        mercadolibre_sellers=ml_data["sellers_count"],
        mercadolibre_avg_price=ml_data["avg_price_clp"],
        mercadolibre_top_seller_sales=ml_data["top_seller_sales"],
        retail_stores_count=retail_data["stores_count"],
        retail_avg_price=retail_data["avg_price_clp"],
        google_shopping_results=google_data["results_count"],
        saturation_level=saturation_level,
        saturation_score=saturation_score,
        is_saturated=is_saturated
    )
    
    # Generar recomendación y ventajas
    result.recommendation = generate_recommendation(result)
    result.competitive_advantage = identify_competitive_advantages(result)
    
    # Log de resultados
    logger.info("\n" + "-"*70)
    logger.info("📊 RESULTADOS DEL ANÁLISIS")
    logger.info("-"*70)
    logger.info(f"Score de Saturación: {saturation_score}/100")
    logger.info(f"Nivel: {saturation_level.upper()}")
    logger.info(f"¿Saturado?: {'SÍ ❌' if is_saturated else 'NO ✅'}")
    logger.info("")
    logger.info("Competencia:")
    logger.info(f"  • Mercado Libre: {ml_data['sellers_count']} vendedores")
    logger.info(f"  • Retail: {retail_data['stores_count']} tiendas")
    logger.info(f"  • Google Shopping: {google_data['results_count']} resultados")
    logger.info("")
    logger.info(result.recommendation)
    logger.info("")
    
    if not is_saturated:
        logger.info("💡 Ventajas Competitivas:")
        for advantage in result.competitive_advantage[:3]:
            logger.info(f"  ✓ {advantage}")
    
    logger.info("="*70 + "\n")
    
    return result


# ============================================================================
# FUNCIÓN DE FILTRADO
# ============================================================================

def should_reject_product_by_saturation(
    saturation_result: MarketSaturationResult,
    strict_mode: bool = True
) -> bool:
    """
    Determina si un producto debe ser rechazado por saturación.
    
    Args:
        saturation_result: Resultado del análisis
        strict_mode: Si True, rechaza "high" y "very_high"
                    Si False, solo rechaza "very_high"
        
    Returns:
        True si debe rechazarse, False si puede continuar
    """
    if strict_mode:
        return saturation_result.saturation_level in ["high", "very_high"]
    else:
        return saturation_result.saturation_level == "very_high"


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    async def test():
        # Ejemplo 1: Producto de nicho (baja saturación)
        result1 = await analyze_market_saturation("Proyector Galaxy LED 360")
        print(f"\nProducto 1 rechazado: {should_reject_product_by_saturation(result1)}")
        
        # Ejemplo 2: Producto común (alta saturación)
        result2 = await analyze_market_saturation("Cargador USB Tipo C")
        print(f"\nProducto 2 rechazado: {should_reject_product_by_saturation(result2)}")
    
    asyncio.run(test())
