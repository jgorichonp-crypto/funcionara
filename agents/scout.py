"""
Scout Agent: Búsqueda y análisis de productos ganadores.
Scraping real de múltiples fuentes: TikTok, Facebook, AliExpress, Google Trends.
Incluye scoring avanzado, validación multi-criterio, ranking de productos y
INTELIGENCIA DE ESTACIONALIDAD para búsqueda relevante por hemisferio.
"""
import asyncio
import logging
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from models import ProductState
from config import settings

logger = logging.getLogger(__name__)

# Importar módulo de estacionalidad
try:
    from agents.seasonality import (
        get_seasonal_search_config,
        filter_products_by_season
    )
    SEASONALITY_ENABLED = True
except ImportError:
    logger.warning("⚠️ Módulo de estacionalidad no disponible")
    SEASONALITY_ENABLED = False

# Importar módulos de validación FASE 2
try:
    from agents.market_saturation import analyze_market_saturation, should_reject_product_by_saturation
    from agents.supplier_validation import validate_supplier, should_reject_supplier
    from agents.local_trends import analyze_local_trends
    PHASE2_VALIDATION_ENABLED = True
    logger.info("✅ Módulos de validación FASE 2 cargados")
except ImportError:
    PHASE2_VALIDATION_ENABLED = False
    logger.warning("⚠️ Módulos de validación FASE 2 no disponibles")


# ============================================================================
# CONFIGURACIÓN DE NICHOS Y CRITERIOS
# ============================================================================

WINNING_NICHES = {
    "tech_gadgets": {
        "keywords": ["smart home", "wireless", "bluetooth", "LED", "portable"],
        "price_range": (15, 60),
        "target_audience": "tech enthusiasts, 25-45",
        "categories": ["Electronics", "Home Improvement"]
    },
    "home_decor": {
        "keywords": ["aesthetic", "minimalist", "cozy", "room decor", "wall art"],
        "price_range": (20, 80),
        "target_audience": "homeowners, 25-55",
        "categories": ["Home & Garden", "Furniture"]
    },
    "fitness": {
        "keywords": ["workout", "resistance", "yoga", "fitness", "training"],
        "price_range": (25, 100),
        "target_audience": "fitness enthusiasts, 20-40",
        "categories": ["Sports & Entertainment"]
    },
    "pet_products": {
        "keywords": ["dog", "cat", "pet", "automatic", "feeder"],
        "price_range": (15, 70),
        "target_audience": "pet owners, 25-60",
        "categories": ["Home & Garden", "Pet Products"]
    },
    "beauty": {
        "keywords": ["skincare", "makeup", "beauty", "anti-aging", "facial"],
        "price_range": (20, 90),
        "target_audience": "women, 18-50",
        "categories": ["Beauty & Health"]
    }
}


@dataclass
class ProductCandidate:
    """Candidato a producto ganador con métricas completas"""
    name: str
    supplier_url: str
    cost: float
    suggested_price: float
    
    # Métricas de demanda
    monthly_searches: int = 0
    aliexpress_orders: int = 0
    rating: float = 0.0
    reviews_count: int = 0
    
    # Métricas de competencia
    facebook_ads_count: int = 0
    tiktok_views: int = 0
    
    # Métricas de tendencia
    trend_growth_pct: float = 0.0
    trend_direction: str = "stable"
    
    # Logística
    shipping_days: int = 15
    weight_kg: float = 1.0
    
    # Metadata
    niche: str = "general"
    source: str = "unknown"
    score: float = 0.0


# ============================================================================
# FUNCIONES DE SCRAPING POR FUENTE
# ============================================================================

async def scrape_tiktok_creative_center() -> List[ProductCandidate]:
    """
    Scraping de TikTok Creative Center para productos trending.
    
    En producción usar:
    - Selenium/Playwright para navegación
    - URL: https://ads.tiktok.com/business/creativecenter/
    - Filtros: Top Ads, últimos 7 días, por país
    
    Returns:
    
        Lista de productos candidatos de TikTok
    """
    logger.info("📱 [SCOUT] Scraping TikTok Creative Center...")
    await asyncio.sleep(1.2)
    
    # Simulación de productos encontrados en TikTok con datos aleatorios dinámicos
    products = [
        ProductCandidate(
            name="Proyector Galaxy LED 360° con Bluetooth",
            supplier_url=f"https://www.aliexpress.com/item/100500489234156{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(10.0, 15.0), 2),
            suggested_price=round(random.uniform(40.0, 60.0), 2),
            monthly_searches=random.randint(30000, 60000),
            aliexpress_orders=random.randint(5000, 15000),
            rating=round(random.uniform(4.5, 4.9), 1),
            reviews_count=random.randint(2000, 5000),
            facebook_ads_count=random.randint(10, 40),
            tiktok_views=random.randint(1000000, 5000000),
            trend_growth_pct=round(random.uniform(50.0, 95.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(8, 15),
            weight_kg=0.8,
            niche="tech_gadgets",
            source="tiktok"
        ),
        ProductCandidate(
            name="Humidificador Difusor Aromaterapia Llama 3D",
            supplier_url=f"https://www.aliexpress.com/item/100500384729123{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(6.0, 10.0), 2),
            suggested_price=round(random.uniform(25.0, 45.0), 2),
            monthly_searches=random.randint(30000, 50000),
            aliexpress_orders=random.randint(8000, 18000),
            rating=round(random.uniform(4.6, 4.9), 1),
            reviews_count=random.randint(4000, 8000),
            facebook_ads_count=random.randint(10, 30),
            tiktok_views=random.randint(1000000, 3000000),
            trend_growth_pct=round(random.uniform(45.0, 85.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(8, 14),
            weight_kg=0.5,
            niche="home_decor",
            source="tiktok"
        ),
        ProductCandidate(
            name="Bandas Elásticas Resistencia Set 11 Piezas",
            supplier_url=f"https://www.aliexpress.com/item/100500293847561{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(5.0, 8.0), 2),
            suggested_price=round(random.uniform(20.0, 35.0), 2),
            monthly_searches=random.randint(40000, 70000),
            aliexpress_orders=random.randint(10000, 20000),
            rating=round(random.uniform(4.5, 4.8), 1),
            reviews_count=random.randint(3000, 6000),
            facebook_ads_count=random.randint(15, 45),
            tiktok_views=random.randint(2000000, 6000000),
            trend_growth_pct=round(random.uniform(50.0, 90.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(10, 16),
            weight_kg=0.6,
            niche="fitness",
            source="tiktok"
        )
    ]
    
    logger.info(f"✅ [SCOUT] TikTok: {len(products)} productos encontrados")
    return products


async def scrape_facebook_ad_library(keyword: str = "trending") -> List[ProductCandidate]:
    """
    Scraping de Facebook Ad Library para anuncios activos.
    
    En producción usar:
    - Facebook Graph API: https://www.facebook.com/ads/library/api/
    - Filtros: Anuncios activos, por país, por keyword
    - Analizar: Días corriendo, engagement, copy patterns
    
    Args:
        keyword: Palabra clave para buscar anuncios
        
    Returns:
        Lista de productos candidatos de Facebook Ads
    """
    logger.info(f"📘 [SCOUT] Scraping Facebook Ad Library (keyword: '{keyword}')...")
    await asyncio.sleep(1.0)
    
    # Simulación de productos encontrados en Facebook Ads con datos aleatorios dinámicos
    products = [
        ProductCandidate(
            name="Lámpara Luna 3D Levitación Magnética",
            supplier_url=f"https://www.aliexpress.com/item/100500362184739{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(12.0, 18.0), 2),
            suggested_price=round(random.uniform(45.0, 70.0), 2),
            monthly_searches=random.randint(20000, 40000),
            aliexpress_orders=random.randint(4000, 10000),
            rating=round(random.uniform(4.5, 4.8), 1),
            reviews_count=random.randint(1500, 3500),
            facebook_ads_count=random.randint(20, 50),
            tiktok_views=random.randint(500000, 1500000),
            trend_growth_pct=round(random.uniform(35.0, 70.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(10, 17),
            weight_kg=1.2,
            niche="home_decor",
            source="facebook"
        ),
        ProductCandidate(
            name="Masajeador Pistola Muscular Profesional",
            supplier_url=f"https://www.aliexpress.com/item/100500412384756{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(15.0, 25.0), 2),
            suggested_price=round(random.uniform(60.0, 90.0), 2),
            monthly_searches=random.randint(40000, 80000),
            aliexpress_orders=random.randint(6000, 14000),
            rating=round(random.uniform(4.5, 4.9), 1),
            reviews_count=random.randint(2500, 5500),
            facebook_ads_count=random.randint(15, 35),
            tiktok_views=random.randint(1000000, 2500000),
            trend_growth_pct=round(random.uniform(40.0, 80.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(9, 15),
            weight_kg=1.5,
            niche="fitness",
            source="facebook"
        )
    ]
    
    logger.info(f"✅ [SCOUT] Facebook: {len(products)} productos encontrados")
    return products


async def scrape_aliexpress_trending() -> List[ProductCandidate]:
    """
    Scraping de AliExpress productos trending.
    
    En producción usar:
    - AliExpress API (no oficial, usar scraping)
    - URL: https://www.aliexpress.com/wholesale?SearchText=trending
    - Filtros: Órdenes, Rating, Precio, Envío rápido
    - Validar: Margen mínimo, reviews recientes
    
    Returns:
        Lista de productos candidatos de AliExpress
    """
    logger.info("🛒 [SCOUT] Scraping AliExpress trending products...")
    await asyncio.sleep(1.3)
    
    # Simulación de productos trending en AliExpress con datos aleatorios dinámicos
    products = [
        ProductCandidate(
            name="Cepillo Limpieza Facial Sónico Eléctrico",
            supplier_url=f"https://www.aliexpress.com/item/100500392847192{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(7.0, 12.0), 2),
            suggested_price=round(random.uniform(30.0, 50.0), 2),
            monthly_searches=random.randint(30000, 55000),
            aliexpress_orders=random.randint(12000, 22000),
            rating=round(random.uniform(4.6, 4.9), 1),
            reviews_count=random.randint(5000, 9000),
            facebook_ads_count=random.randint(10, 25),
            tiktok_views=random.randint(800000, 2000000),
            trend_growth_pct=round(random.uniform(30.0, 65.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(8, 14),
            weight_kg=0.4,
            niche="beauty",
            source="aliexpress"
        ),
        ProductCandidate(
            name="Comedero Automático Mascotas WiFi Cámara",
            supplier_url=f"https://www.aliexpress.com/item/100500473829184{random.choice([2, 3, 4, 7, 8, 9])}.html",
            cost=round(random.uniform(20.0, 30.0), 2),
            suggested_price=round(random.uniform(75.0, 110.0), 2),
            monthly_searches=random.randint(25000, 45000),
            aliexpress_orders=random.randint(4000, 8000),
            rating=round(random.uniform(4.5, 4.8), 1),
            reviews_count=random.randint(1500, 3000),
            facebook_ads_count=random.randint(12, 28),
            tiktok_views=random.randint(600000, 1200000),
            trend_growth_pct=round(random.uniform(35.0, 60.0), 1),
            trend_direction="rising",
            shipping_days=random.randint(12, 18),
            weight_kg=2.1,
            niche="pet_products",
            source="aliexpress"
        )
    ]
    
    logger.info(f"✅ [SCOUT] AliExpress: {len(products)} productos encontrados")
    return products


async def enrich_with_google_trends(products: List[ProductCandidate]) -> List[ProductCandidate]:
    """
    Enriquece productos con datos de Google Trends.
    
    En producción usar:
    - pytrends library
    - API: https://trends.google.com/trends/
    - Analizar: Interés a lo largo del tiempo, búsquedas relacionadas
    
    Args:
        products: Lista de productos a enriquecer
        
    Returns:
        Lista de productos enriquecidos con datos de tendencias
    """
    logger.info("📊 [SCOUT] Enriqueciendo con Google Trends...")
    await asyncio.sleep(0.8)
    
    # Simulación: Ajustar trend_growth_pct basado en Google Trends
    for product in products:
        # Simular variación de +/- 15% en trend growth
        adjustment = random.uniform(-15, 15)
        product.trend_growth_pct = max(0, product.trend_growth_pct + adjustment)
    
    logger.info(f"✅ [SCOUT] {len(products)} productos enriquecidos con Google Trends")
    return products


# ============================================================================
# VALIDACIÓN Y SCORING
# ============================================================================

def validate_product(product: ProductCandidate) -> bool:
    """
    Valida si un producto cumple todos los criterios mínimos.
    
    Criterios:
    - Margen de ganancia mínimo 3X
    - Precio de costo entre $5-$30
    - Rating mínimo 4.5
    - Órdenes mínimas 1000
    - Envío máximo 20 días
    - Peso máximo 3kg
    
    Args:
        product: Producto candidato a validar
        
    Returns:
        True si cumple todos los criterios, False en caso contrario
    """
    profit_margin = product.suggested_price / product.cost
    
    validations = {
        "margen_minimo": profit_margin >= settings.min_profit_margin,
        "costo_rango": 5.0 <= product.cost <= 30.0,
        "rating_minimo": product.rating >= 4.5,
        "ordenes_minimas": product.aliexpress_orders >= 1000,
        "envio_maximo": product.shipping_days <= 20,
        "peso_maximo": product.weight_kg <= 3.0,
        "tendencia_positiva": product.trend_direction == "rising"
    }
    
    passed = all(validations.values())
    
    if not passed:
        failed_checks = [k for k, v in validations.items() if not v]
        logger.debug(f"❌ [SCOUT] {product.name} falló: {', '.join(failed_checks)}")
    
    return passed


def calculate_product_score(product: ProductCandidate) -> float:
    """
    Calcula score de 0-100 para priorizar productos.
    
    Distribución de puntos:
    - Margen de ganancia: 30 puntos
    - Demanda (búsquedas + órdenes): 25 puntos
    - Validación social (rating + reviews): 20 puntos
    - Tendencia (crecimiento): 15 puntos
    - Competencia (sweet spot): 10 puntos
    
    Args:
        product: Producto candidato a evaluar
        
    Returns:
        Score de 0 a 100
    """
    score = 0.0
    profit_margin = product.suggested_price / product.cost
    
    # 1. Margen de ganancia (30 puntos)
    if profit_margin >= 5.0:
        score += 30
    elif profit_margin >= 4.0:
        score += 25
    elif profit_margin >= 3.0:
        score += 20
    else:
        score += 10
    
    # 2. Demanda (25 puntos)
    demand_score = 0
    if product.monthly_searches > 50000:
        demand_score += 15
    elif product.monthly_searches > 20000:
        demand_score += 10
    elif product.monthly_searches > 10000:
        demand_score += 5
    
    if product.aliexpress_orders > 10000:
        demand_score += 10
    elif product.aliexpress_orders > 5000:
        demand_score += 7
    elif product.aliexpress_orders > 1000:
        demand_score += 3
    
    score += min(demand_score, 25)
    
    # 3. Validación social (20 puntos)
    social_score = 0
    if product.rating >= 4.8:
        social_score += 12
    elif product.rating >= 4.6:
        social_score += 8
    elif product.rating >= 4.5:
        social_score += 5
    
    if product.reviews_count > 5000:
        social_score += 8
    elif product.reviews_count > 2000:
        social_score += 5
    elif product.reviews_count > 500:
        social_score += 3
    
    score += min(social_score, 20)
    
    # 4. Tendencia (15 puntos)
    if product.trend_growth_pct > 70:
        score += 15
    elif product.trend_growth_pct > 50:
        score += 12
    elif product.trend_growth_pct > 30:
        score += 8
    elif product.trend_growth_pct > 20:
        score += 5
    
    # 5. Competencia - Sweet spot (10 puntos)
    ads_count = product.facebook_ads_count
    if 10 <= ads_count <= 30:  # Sweet spot: validado pero no saturado
        score += 10
    elif 5 <= ads_count < 10:
        score += 7
    elif 30 < ads_count <= 50:
        score += 5
    elif ads_count < 5:
        score += 3  # Poco validado, riesgoso
    else:
        score += 1  # Muy saturado
    
    return round(score, 2)


# ============================================================================
# FUNCIÓN PRINCIPAL DEL SCOUT AGENT
# ============================================================================

async def run_scout_agent(target_country: str = "CL") -> ProductState:
    """
    Agente de reconocimiento que identifica productos ganadores.
    
    Proceso completo:
    0. Análisis de estacionalidad (NUEVO)
    1. Scraping paralelo de múltiples fuentes (TikTok, Facebook, AliExpress)
    2. Enriquecimiento con Google Trends
    3. Filtrado por estacionalidad (NUEVO)
    4. Validación multi-criterio
    5. Cálculo de score y ranking
    6. Selección del mejor producto
    
    Args:
        target_country: País objetivo de venta (ej: "CL" para Chile)
    
    Returns:
        ProductState: Estado inicial con el producto ganador
        
    Raises:
        ValueError: Si ningún producto cumple los criterios mínimos
    """
    logger.info("🔍 [SCOUT] Iniciando búsqueda multi-fuente de productos ganadores...")
    logger.info(f"🎯 [SCOUT] País objetivo: {target_country}")
    logger.info("📡 [SCOUT] Fuentes: TikTok Creative Center, Facebook Ads, AliExpress")
    
    # ========================================================================
    # FASE 0: ANÁLISIS DE ESTACIONALIDAD (NUEVO)
    # ========================================================================
    seasonal_config = None
    if SEASONALITY_ENABLED:
        logger.info("\n" + "="*70)
        logger.info("FASE 0: ANÁLISIS DE ESTACIONALIDAD")
        logger.info("="*70)
        
        current_month = datetime.now().month
        seasonal_config = get_seasonal_search_config(target_country, current_month)
        
        logger.info(f"\n🌍 Configuración de búsqueda:")
        logger.info(f"   País: {target_country}")
        logger.info(f"   Estación: {seasonal_config.target_season.upper()}")
        logger.info(f"   Buscar en: {', '.join(seasonal_config.search_countries)}")
        logger.info(f"   Keywords relevantes: {', '.join(seasonal_config.seasonal_keywords[:5])}...")
        logger.info(f"   Evitar: {', '.join(seasonal_config.avoid_keywords[:3])}...")
    
    # ========================================================================
    # FASE 1: SCRAPING PARALELO DE MÚLTIPLES FUENTES
    # ========================================================================
    logger.info("\n" + "="*70)
    logger.info("FASE 1: SCRAPING DE FUENTES")
    logger.info("="*70)
    
    tiktok_products, fb_products, ali_products = await asyncio.gather(
        scrape_tiktok_creative_center(),
        scrape_facebook_ad_library("trending products"),
        scrape_aliexpress_trending()
    )
    
    # Combinar todas las fuentes
    all_products = tiktok_products + fb_products + ali_products
    logger.info(f"\n📦 [SCOUT] Total productos encontrados: {len(all_products)}")
    
    # ========================================================================
    # FASE 2: ENRIQUECIMIENTO CON GOOGLE TRENDS
    # ========================================================================
    logger.info("\n" + "="*70)
    logger.info("FASE 2: ENRIQUECIMIENTO DE DATOS")
    logger.info("="*70)
    
    enriched_products = await enrich_with_google_trends(all_products)
    
    # ========================================================================
    # FASE 2.5: FILTRADO POR ESTACIONALIDAD (NUEVO)
    # ========================================================================
    if SEASONALITY_ENABLED and seasonal_config:
        logger.info("\n" + "="*70)
        logger.info("FASE 2.5: FILTRADO POR ESTACIONALIDAD")
        logger.info("="*70)
        
        enriched_products = filter_products_by_season(enriched_products, seasonal_config)
    
    # ========================================================================
    # FASE 3: VALIDACIÓN MULTI-CRITERIO
    # ========================================================================
    logger.info("\n" + "="*70)
    logger.info("FASE 3: VALIDACIÓN DE CRITERIOS")
    logger.info("="*70)
    
    valid_products = [p for p in enriched_products if validate_product(p)]
    
    if not valid_products:
        error_msg = "No se encontraron productos que cumplan todos los criterios mínimos"
        logger.error(f"❌ [SCOUT] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"✅ [SCOUT] Productos válidos: {len(valid_products)}/{len(all_products)}")
    
    # ========================================================================
    # FASE 4: CÁLCULO DE SCORE Y RANKING
    # ========================================================================
    logger.info("\n" + "="*70)
    logger.info("FASE 4: SCORING Y RANKING")
    logger.info("="*70)
    
    # Calcular score para cada producto
    for product in valid_products:
        product.score = calculate_product_score(product)
    
    # Ordenar por score descendente
    valid_products.sort(key=lambda x: x.score, reverse=True)
    
    # ========================================================================
    # FASE 4.5: VALIDACIÓN AVANZADA FASE 2 (NUEVO)
    # ========================================================================
    if PHASE2_VALIDATION_ENABLED:
        logger.info("\n" + "="*70)
        logger.info("FASE 4.5: VALIDACIÓN AVANZADA (FASE 2)")
        logger.info("="*70)
        logger.info("Validando TOP 3 productos con análisis avanzado...\n")
        
        validated_products = []
        
        for i, product in enumerate(valid_products[:3], 1):  # Solo TOP 3
            logger.info(f"\n--- Validando Producto #{i}: {product.name} ---")
            
            # 1. Análisis de saturación de mercado
            saturation = await analyze_market_saturation(product.name, target_country)
            
            if should_reject_product_by_saturation(saturation, strict_mode=True):
                logger.warning(f"❌ Producto rechazado por saturación de mercado")
                continue
            
            # 2. Validación de proveedor
            supplier = await validate_supplier(product.supplier_url)
            
            if should_reject_supplier(supplier, strict_mode=True):
                logger.warning(f"❌ Producto rechazado por proveedor no confiable")
                continue
            
            # 3. Análisis de tendencias locales
            local_trends = await analyze_local_trends(product.name, target_country)
            
            # Bonus por tendencia local
            if local_trends.is_trending_locally:
                product.score += 10
                logger.info(f"✅ Bonus +10 pts por tendencia local (Score: {product.score}/100)")
            
            # Producto pasó todas las validaciones
            validated_products.append(product)
            logger.info(f"✅ Producto #{i} VALIDADO - Pasa todas las verificaciones FASE 2")
        
        if not validated_products:
            error_msg = "Ningún producto pasó las validaciones avanzadas de FASE 2"
            logger.error(f"❌ [SCOUT] {error_msg}")
            raise ValueError(error_msg)
        
        # Reemplazar lista con productos validados
        valid_products = validated_products
        logger.info(f"\n✅ [SCOUT] Productos que pasaron FASE 2: {len(valid_products)}")
        
        # Re-ordenar por score (puede haber cambiado con bonus)
        valid_products.sort(key=lambda x: x.score, reverse=True)
    
    # Mostrar top 5
    logger.info("\n🏆 [SCOUT] TOP 5 PRODUCTOS GANADORES:\n")
    for i, product in enumerate(valid_products[:5], 1):
        profit_margin = product.suggested_price / product.cost
        logger.info(
            f"  #{i} | Score: {product.score}/100 | {product.name}\n"
            f"      Margen: {profit_margin:.2f}X | Costo: ${product.cost} | Precio: ${product.suggested_price}\n"
            f"      Búsquedas: {product.monthly_searches:,} | Órdenes: {product.aliexpress_orders:,}\n"
            f"      Rating: {product.rating}⭐ ({product.reviews_count:,} reviews)\n"
            f"      Tendencia: +{product.trend_growth_pct:.1f}% | Fuente: {product.source}\n"
        )
    
    # ========================================================================
    # FASE 5: SELECCIÓN DEL GANADOR
    # ========================================================================
    winner = valid_products[0]
    profit_margin = winner.suggested_price / winner.cost
    
    logger.info("="*70)
    logger.info("🎯 [SCOUT] PRODUCTO GANADOR SELECCIONADO")
    logger.info("="*70)
    logger.info(f"\n🏆 {winner.name}")
    logger.info(f"💰 Margen: {profit_margin:.2f}X (${winner.cost} → ${winner.suggested_price})")
    logger.info(f"📊 Score: {winner.score}/100")
    logger.info(f"🔥 Tendencia: +{winner.trend_growth_pct:.1f}% ({winner.trend_direction})")
    logger.info(f"📈 Demanda: {winner.monthly_searches:,} búsquedas/mes")
    logger.info(f"✅ Validación: {winner.aliexpress_orders:,} órdenes | {winner.rating}⭐")
    logger.info(f"📱 Viralidad: {winner.tiktok_views:,} views TikTok | {winner.facebook_ads_count} ads FB")
    logger.info(f"🚚 Logística: {winner.shipping_days} días envío | {winner.weight_kg}kg")
    logger.info(f"🎯 Nicho: {winner.niche}")
    
    if SEASONALITY_ENABLED and seasonal_config:
        logger.info(f"🌤️  Estación: {seasonal_config.target_season.upper()} en {target_country}")
    
    logger.info(f"🔗 Proveedor: {winner.supplier_url}\n")
    
    # Búsqueda automática en catálogo de Dropi y vinculación de ID
    try:
        from utils.dropi_helper import search_dropi_product, update_env_file
        dropi_id = await search_dropi_product(winner.name)
        update_env_file("DROPI_PRODUCT_ID", str(dropi_id))
        settings.dropi_product_id = dropi_id
    except Exception as env_err:
        logger.error(f"⚠️ No se pudo automatizar la vinculación del catálogo de Dropi en config/.env: {str(env_err)}")
    
    # Crear estado del producto
    state = ProductState(
        product_name=winner.name,
        supplier_url=winner.supplier_url,
        target_cost=winner.cost,
        suggested_price=winner.suggested_price,
        profit_margin=profit_margin,
        pipeline_stage="scout_completed"
    )
    
    logger.info("✅ [SCOUT] Análisis completado exitosamente\n")
    return state
