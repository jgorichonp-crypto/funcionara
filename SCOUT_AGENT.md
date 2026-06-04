# 🔍 Scout Agent - Documentación Completa

## Descripción General

El **Scout Agent** es el primer agente del pipeline y el más crítico. Su función es identificar productos ganadores con alto potencial de rentabilidad mediante scraping de múltiples fuentes, validación multi-criterio y scoring avanzado.

---

## 🎯 Fuentes de Datos

### 1. TikTok Creative Center
- **URL:** https://ads.tiktok.com/business/creativecenter/
- **Qué extrae:**
  - Top Ads con mejor rendimiento
  - Productos trending en últimos 7 días
  - Métricas de engagement y views
- **Implementación actual:** Simulado con productos reales
- **Implementación producción:** Selenium/Playwright

### 2. Facebook Ad Library
- **URL:** https://www.facebook.com/ads/library/
- **Qué extrae:**
  - Anuncios activos de competidores
  - Días corriendo (indicador de rentabilidad)
  - Copy y creativos que funcionan
- **Implementación actual:** Simulado
- **Implementación producción:** Facebook Graph API

### 3. AliExpress Trending
- **URL:** https://www.aliexpress.com/wholesale?SearchText=trending
- **Qué extrae:**
  - Productos con más órdenes
  - Rating y reviews
  - Precio de proveedor
- **Implementación actual:** Simulado con productos reales
- **Implementación producción:** Web scraping con BeautifulSoup/Scrapy

### 4. Google Trends (Enriquecimiento)
- **URL:** https://trends.google.com/trends/
- **Qué extrae:**
  - Interés a lo largo del tiempo
  - Crecimiento de búsquedas
  - Tendencia (rising/falling)
- **Implementación actual:** Simulado
- **Implementación producción:** pytrends library

---

## 📊 Criterios de Validación

Cada producto debe cumplir **TODOS** estos criterios:

| Criterio | Valor Mínimo | Razón |
|----------|--------------|-------|
| **Margen de ganancia** | 3.0X | Rentabilidad después de ads y costos |
| **Costo de producto** | $5 - $30 | Sweet spot para dropshipping |
| **Rating** | 4.5⭐ | Calidad del producto |
| **Órdenes en AliExpress** | 1,000+ | Validación social |
| **Días de envío** | ≤ 20 días | Satisfacción del cliente |
| **Peso** | ≤ 3kg | Costos de envío razonables |
| **Tendencia** | Rising | Demanda creciente |

---

## 🏆 Sistema de Scoring (0-100 puntos)

### Distribución de Puntos

#### 1. Margen de Ganancia (30 puntos)
```
≥ 5.0X  → 30 puntos
≥ 4.0X  → 25 puntos
≥ 3.0X  → 20 puntos
< 3.0X  → 10 puntos
```

#### 2. Demanda (25 puntos)
**Búsquedas mensuales:**
```
> 50,000  → 15 puntos
> 20,000  → 10 puntos
> 10,000  → 5 puntos
```

**Órdenes en AliExpress:**
```
> 10,000  → 10 puntos
> 5,000   → 7 puntos
> 1,000   → 3 puntos
```

#### 3. Validación Social (20 puntos)
**Rating:**
```
≥ 4.8⭐  → 12 puntos
≥ 4.6⭐  → 8 puntos
≥ 4.5⭐  → 5 puntos
```

**Reviews:**
```
> 5,000  → 8 puntos
> 2,000  → 5 puntos
> 500    → 3 puntos
```

#### 4. Tendencia (15 puntos)
```
> 70% crecimiento  → 15 puntos
> 50% crecimiento  → 12 puntos
> 30% crecimiento  → 8 puntos
> 20% crecimiento  → 5 puntos
```

#### 5. Competencia - Sweet Spot (10 puntos)
```
10-30 ads activos  → 10 puntos (ideal: validado pero no saturado)
5-10 ads activos   → 7 puntos
30-50 ads activos  → 5 puntos
< 5 ads activos    → 3 puntos (poco validado)
> 50 ads activos   → 1 punto (muy saturado)
```

---

## 🎯 Nichos Configurados

### Tech Gadgets
- **Keywords:** smart home, wireless, bluetooth, LED, portable
- **Precio:** $15 - $60
- **Audiencia:** Tech enthusiasts, 25-45 años
- **Ejemplos:** Proyectores LED, gadgets inteligentes

### Home Decor
- **Keywords:** aesthetic, minimalist, cozy, room decor, wall art
- **Precio:** $20 - $80
- **Audiencia:** Homeowners, 25-55 años
- **Ejemplos:** Lámparas decorativas, difusores

### Fitness
- **Keywords:** workout, resistance, yoga, fitness, training
- **Precio:** $25 - $100
- **Audiencia:** Fitness enthusiasts, 20-40 años
- **Ejemplos:** Bandas de resistencia, masajeadores

### Pet Products
- **Keywords:** dog, cat, pet, automatic, feeder
- **Precio:** $15 - $70
- **Audiencia:** Pet owners, 25-60 años
- **Ejemplos:** Comederos automáticos, juguetes

### Beauty
- **Keywords:** skincare, makeup, beauty, anti-aging, facial
- **Precio:** $20 - $90
- **Audiencia:** Women, 18-50 años
- **Ejemplos:** Cepillos faciales, dispositivos de belleza

---

## 🔄 Flujo del Scout Agent

```
┌─────────────────────────────────────────────────────────┐
│ FASE 1: SCRAPING PARALELO                              │
├─────────────────────────────────────────────────────────┤
│ • TikTok Creative Center (3 productos)                 │
│ • Facebook Ad Library (2 productos)                    │
│ • AliExpress Trending (2 productos)                    │
│ Total: 7 productos candidatos                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 2: ENRIQUECIMIENTO                                │
├─────────────────────────────────────────────────────────┤
│ • Google Trends (ajuste de trend_growth_pct)           │
│ • Validación de datos                                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 3: VALIDACIÓN MULTI-CRITERIO                      │
├─────────────────────────────────────────────────────────┤
│ • Margen ≥ 3X                                          │
│ • Costo $5-$30                                         │
│ • Rating ≥ 4.5⭐                                        │
│ • Órdenes ≥ 1,000                                      │
│ • Envío ≤ 20 días                                      │
│ • Peso ≤ 3kg                                           │
│ • Tendencia rising                                     │
│ Resultado: 5-7 productos válidos                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 4: SCORING Y RANKING                              │
├─────────────────────────────────────────────────────────┤
│ • Calcular score 0-100 para cada producto              │
│ • Ordenar por score descendente                        │
│ • Mostrar TOP 5                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 5: SELECCIÓN DEL GANADOR                          │
├─────────────────────────────────────────────────────────┤
│ • Producto con mayor score                             │
│ • Crear ProductState                                   │
│ • Retornar al pipeline                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 Ejemplo de Salida

```
🔍 [SCOUT] Iniciando búsqueda multi-fuente de productos ganadores...
📡 [SCOUT] Fuentes: TikTok Creative Center, Facebook Ads, AliExpress

======================================================================
FASE 1: SCRAPING DE FUENTES
======================================================================
📱 [SCOUT] Scraping TikTok Creative Center...
✅ [SCOUT] TikTok: 3 productos encontrados
📘 [SCOUT] Scraping Facebook Ad Library (keyword: 'trending products')...
✅ [SCOUT] Facebook: 2 productos encontrados
🛒 [SCOUT] Scraping AliExpress trending products...
✅ [SCOUT] AliExpress: 2 productos encontrados

📦 [SCOUT] Total productos encontrados: 7

======================================================================
FASE 2: ENRIQUECIMIENTO DE DATOS
======================================================================
📊 [SCOUT] Enriqueciendo con Google Trends...
✅ [SCOUT] 7 productos enriquecidos con Google Trends

======================================================================
FASE 3: VALIDACIÓN DE CRITERIOS
======================================================================
✅ [SCOUT] Productos válidos: 7/7

======================================================================
FASE 4: SCORING Y RANKING
======================================================================

🏆 [SCOUT] TOP 5 PRODUCTOS GANADORES:

  #1 | Score: 87.5/100 | Proyector Galaxy LED 360° con Bluetooth
      Margen: 3.85X | Costo: $12.99 | Precio: $49.99
      Búsquedas: 45,000 | Órdenes: 8,500
      Rating: 4.7⭐ (3,200 reviews)
      Tendencia: +85.0% | Fuente: tiktok

  #2 | Score: 82.0/100 | Bandas Elásticas Resistencia Set 11 Piezas
      Margen: 4.41X | Costo: $6.80 | Precio: $29.99
      Búsquedas: 52,000 | Órdenes: 15,000
      Rating: 4.6⭐ (4,100 reviews)
      Tendencia: +72.0% | Fuente: tiktok

  #3 | Score: 78.5/100 | Humidificador Difusor Aromaterapia Llama 3D
      Margen: 4.12X | Costo: $8.50 | Precio: $34.99
      Búsquedas: 38,000 | Órdenes: 12,000
      Rating: 4.8⭐ (5,600 reviews)
      Tendencia: +65.0% | Fuente: tiktok

======================================================================
🎯 [SCOUT] PRODUCTO GANADOR SELECCIONADO
======================================================================

🏆 Proyector Galaxy LED 360° con Bluetooth
💰 Margen: 3.85X ($12.99 → $49.99)
📊 Score: 87.5/100
🔥 Tendencia: +85.0% (rising)
📈 Demanda: 45,000 búsquedas/mes
✅ Validación: 8,500 órdenes | 4.7⭐
📱 Viralidad: 2,500,000 views TikTok | 23 ads FB
🚚 Logística: 12 días envío | 0.8kg
🎯 Nicho: tech_gadgets
🔗 Proveedor: https://www.aliexpress.com/item/1005004892341567.html

✅ [SCOUT] Análisis completado exitosamente
```

---

## 🚀 Integración con APIs Reales

### Para TikTok Creative Center

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

async def scrape_tiktok_real():
    driver = webdriver.Chrome()
    driver.get("https://ads.tiktok.com/business/creativecenter/")
    
    # Login si es necesario
    # Navegar a Top Ads
    # Extraer productos con Selenium
    
    products = []
    # ... lógica de scraping
    
    driver.quit()
    return products
```

### Para Facebook Ad Library

```python
import requests

async def scrape_facebook_real(access_token: str):
    url = "https://graph.facebook.com/v19.0/ads_archive"
    params = {
        "access_token": access_token,
        "ad_reached_countries": "US",
        "search_terms": "trending products",
        "ad_active_status": "ACTIVE",
        "limit": 100
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Procesar y convertir a ProductCandidate
    return products
```

### Para AliExpress

```python
from bs4 import BeautifulSoup
import aiohttp

async def scrape_aliexpress_real():
    url = "https://www.aliexpress.com/wholesale?SearchText=trending"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraer productos
            products = []
            # ... lógica de scraping
            
            return products
```

### Para Google Trends

```python
from pytrends.request import TrendReq

async def enrich_with_google_trends_real(products):
    pytrends = TrendReq(hl='en-US', tz=360)
    
    for product in products:
        # Buscar tendencia del producto
        pytrends.build_payload([product.name], timeframe='today 3-m')
        interest = pytrends.interest_over_time()
        
        # Calcular crecimiento
        if not interest.empty:
            recent = interest.tail(30).mean()
            previous = interest.head(30).mean()
            growth = ((recent - previous) / previous) * 100
            product.trend_growth_pct = growth
    
    return products
```

---

## 🔧 Configuración

### Variables de Entorno Adicionales

Agregar a `.env`:

```env
# Scout Agent Configuration
TIKTOK_SESSION_ID=your_session_id_here
FACEBOOK_ACCESS_TOKEN=your_fb_token_here
ALIEXPRESS_API_KEY=your_ali_key_here

# Scraping Configuration
SCRAPING_TIMEOUT=30
MAX_PRODUCTS_PER_SOURCE=10
USER_AGENT=Mozilla/5.0...

# Scoring Weights (opcional)
SCORE_WEIGHT_MARGIN=30
SCORE_WEIGHT_DEMAND=25
SCORE_WEIGHT_SOCIAL=20
SCORE_WEIGHT_TREND=15
SCORE_WEIGHT_COMPETITION=10
```

---

## 📊 Métricas de Performance

- **Tiempo de ejecución:** ~4-5 segundos (simulado)
- **Productos analizados:** 7 candidatos
- **Productos válidos:** 5-7 (depende de criterios)
- **Tasa de éxito:** 70-100%
- **Precisión del scoring:** Alta (basado en múltiples métricas)

---

## 🎓 Mejoras Futuras

1. **Machine Learning:**
   - Predecir éxito de productos con ML
   - Análisis de sentimiento de reviews
   - Detección de productos virales antes del pico

2. **Más Fuentes:**
   - Amazon Best Sellers
   - Shopify Exchange
   - Instagram hashtags
   - YouTube trending

3. **Automatización:**
   - Ejecución programada cada 24h
   - Alertas de nuevos productos ganadores
   - Dashboard web con productos rankeados

4. **Análisis Avanzado:**
   - Análisis de competencia profundo
   - Predicción de saturación de mercado
   - Optimización de pricing dinámico

---

## 🐛 Troubleshooting

### Error: "No se encontraron productos válidos"

**Causa:** Criterios de validación muy estrictos

**Solución:**
```python
# En config.py, ajustar:
MIN_PROFIT_MARGIN=2.5  # Reducir de 3.0 a 2.5
```

### Error: "Timeout en scraping"

**Causa:** Fuentes externas lentas o bloqueadas

**Solución:**
- Aumentar timeout en configuración
- Usar proxies rotativos
- Implementar retry logic

### Productos con score bajo

**Causa:** Métricas insuficientes

**Solución:**
- Revisar pesos de scoring
- Agregar más fuentes de datos
- Ajustar criterios de validación

---

**Última actualización:** 2024-01-15  
**Versión:** 2.0.0 (Mejorado con multi-source scraping)
