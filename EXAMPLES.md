# 📚 Ejemplos de Uso Avanzado

## Ejemplo 1: Ejecutar con Configuración Personalizada

```python
# custom_run.py
import asyncio
from config import Settings
from main import main

# Sobrescribir configuración
custom_settings = Settings(
    min_profit_margin=4.0,  # Requerir 4X en lugar de 3X
    daily_ad_budget=10.0,   # Aumentar budget a $10/día
    log_level="DEBUG"       # Logs más detallados
)

# Reemplazar settings global
import config
config.settings = custom_settings

# Ejecutar
asyncio.run(main())
```

## Ejemplo 2: Ejecutar Solo un Agente Específico

```python
# test_scout.py
import asyncio
from agents import run_scout_agent

async def test_scout():
    state = await run_scout_agent()
    print(f"Producto: {state.product_name}")
    print(f"Margen: {state.profit_margin}X")
    print(f"Precio: ${state.suggested_price}")

asyncio.run(test_scout())
```

## Ejemplo 3: Procesar Múltiples Productos en Paralelo

```python
# batch_processing.py
import asyncio
from main import main

async def process_batch(num_products: int):
    """Procesa múltiples productos en paralelo"""
    tasks = [main() for _ in range(num_products)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    print(f"✅ Exitosos: {len(successful)}")
    print(f"❌ Fallidos: {len(failed)}")
    
    return successful, failed

# Procesar 5 productos simultáneamente
asyncio.run(process_batch(5))
```

## Ejemplo 4: Agregar Validación Personalizada

```python
# custom_validation.py
from models import ProductState
from pydantic import field_validator

class CustomProductState(ProductState):
    """Estado con validaciones adicionales"""
    
    @field_validator('suggested_price')
    @classmethod
    def validate_price_range(cls, v):
        if v < 20 or v > 200:
            raise ValueError('Precio debe estar entre $20 y $200')
        return v
    
    @field_validator('product_name')
    @classmethod
    def validate_name_length(cls, v):
        if len(v) < 10:
            raise ValueError('Nombre muy corto para SEO')
        return v
```

## Ejemplo 5: Integración con Base de Datos

```python
# db_integration.py
import asyncio
import aiosqlite
from main import main

async def save_to_database(state):
    """Guarda el resultado en SQLite"""
    async with aiosqlite.connect('dropshipping.db') as db:
        await db.execute('''
            INSERT INTO products (
                name, cost, price, margin, 
                deployed_url, campaign_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            state.product_name,
            state.target_cost,
            state.suggested_price,
            state.profit_margin,
            state.deployed_url,
            state.instagram_ad_draft_id
        ))
        await db.commit()

async def run_with_persistence():
    """Ejecuta pipeline y guarda en DB"""
    state = await main()
    await save_to_database(state)
    print(f"✅ Producto guardado en base de datos")

asyncio.run(run_with_persistence())
```

## Ejemplo 6: Webhook Personalizado

```python
# custom_webhook.py
import aiohttp
from main import send_emergency_alert

async def send_success_notification(state):
    """Envía notificación de éxito a Slack"""
    webhook_url = "https://hooks.slack.com/services/YOUR/SUCCESS/WEBHOOK"
    
    payload = {
        "text": f"🎉 Nuevo producto lanzado: {state.product_name}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{state.product_name}*\n"
                            f"💰 Margen: {state.profit_margin}X\n"
                            f"🌐 URL: {state.deployed_url}\n"
                            f"📱 Campaña: {state.instagram_ad_draft_id}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Ver Landing"},
                        "url": state.deployed_url
                    }
                ]
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)
```

## Ejemplo 7: Retry Logic con Backoff

```python
# retry_logic.py
import asyncio
from typing import Callable, TypeVar

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """Reintenta una función con backoff exponencial"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = initial_delay * (2 ** attempt)
            print(f"⚠️  Intento {attempt + 1} falló. Reintentando en {delay}s...")
            await asyncio.sleep(delay)

# Uso
from agents import run_creative_agent

async def run_creative_with_retry(state):
    return await retry_with_backoff(
        lambda: run_creative_agent(state),
        max_retries=3
    )
```

## Ejemplo 8: Monitoreo de Performance

```python
# performance_monitor.py
import asyncio
import time
from functools import wraps

def measure_time(func):
    """Decorator para medir tiempo de ejecución"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} completado en {elapsed:.2f}s")
        return result
    return wrapper

# Aplicar a agentes
from agents import scout, creative, devops, media_buyer

scout.run_scout_agent = measure_time(scout.run_scout_agent)
creative.run_creative_agent = measure_time(creative.run_creative_agent)
devops.run_devops_agent = measure_time(devops.run_devops_agent)
media_buyer.run_media_buyer_agent = measure_time(media_buyer.run_media_buyer_agent)
```

## Ejemplo 9: Testing con Pytest

```python
# test_agents.py
import pytest
from models import ProductState
from agents import run_scout_agent, run_creative_agent

@pytest.mark.asyncio
async def test_scout_returns_valid_state():
    state = await run_scout_agent()
    assert isinstance(state, ProductState)
    assert state.product_name != ""
    assert state.profit_margin >= 3.0

@pytest.mark.asyncio
async def test_creative_generates_copy():
    # Arrange
    initial_state = ProductState(
        product_name="Test Product",
        target_cost=10.0,
        suggested_price=30.0,
        profit_margin=3.0
    )
    
    # Act
    result = await run_creative_agent(initial_state)
    
    # Assert
    assert "headline" in result.generated_copy
    assert "body" in result.generated_copy
    assert "cta" in result.generated_copy
    assert len(result.image_assets) > 0

@pytest.mark.asyncio
async def test_pipeline_handles_low_margin():
    from config import settings
    settings.min_profit_margin = 10.0  # Margen imposible
    
    with pytest.raises(ValueError):
        await run_scout_agent()
```

## Ejemplo 10: Dashboard Web con FastAPI

```python
# api.py
from fastapi import FastAPI, BackgroundTasks
from models import ProductState
from main import main
import asyncio

app = FastAPI(title="Dropshipping Automation API")

# Almacenamiento en memoria (usar DB en producción)
products = []

@app.post("/products/launch")
async def launch_product(background_tasks: BackgroundTasks):
    """Lanza un nuevo producto en background"""
    background_tasks.add_task(run_pipeline)
    return {"status": "Pipeline iniciado"}

async def run_pipeline():
    state = await main()
    products.append(state.dict())

@app.get("/products")
async def list_products():
    """Lista todos los productos lanzados"""
    return {"products": products}

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Obtiene detalles de un producto"""
    if product_id < len(products):
        return products[product_id]
    return {"error": "Producto no encontrado"}

# Ejecutar con: uvicorn api:app --reload
```

## Ejemplo 11: Integración con Telegram Bot

```python
# telegram_bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from main import main

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot de Dropshipping Automático\n"
        "Usa /launch para lanzar un nuevo producto"
    )

async def launch_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Iniciando pipeline...")
    
    try:
        state = await main()
        await update.message.reply_text(
            f"✅ Producto lanzado exitosamente!\n\n"
            f"📦 {state.product_name}\n"
            f"💰 Margen: {state.profit_margin}X\n"
            f"🌐 URL: {state.deployed_url}\n"
            f"📱 Campaña: {state.instagram_ad_draft_id}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main_bot():
    app = Application.builder().token("YOUR_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("launch", launch_product))
    app.run_polling()

if __name__ == "__main__":
    main_bot()
```

## Ejemplo 12: Análisis de Competencia

```python
# competitor_analysis.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def analyze_competitor(url: str):
    """Analiza la landing page de un competidor"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraer información clave
            title = soup.find('title').text if soup.find('title') else ""
            price = soup.find(class_='price')
            cta = soup.find('button')
            
            return {
                "url": url,
                "title": title,
                "has_urgency": "limited" in html.lower() or "hurry" in html.lower(),
                "has_social_proof": "reviews" in html.lower() or "customers" in html.lower()
            }

async def compare_with_competitors(state, competitor_urls):
    """Compara tu producto con competidores"""
    analyses = await asyncio.gather(*[
        analyze_competitor(url) for url in competitor_urls
    ])
    
    print(f"📊 Análisis de {len(analyses)} competidores:")
    for analysis in analyses:
        print(f"  - {analysis['url']}: Urgencia={analysis['has_urgency']}")
```

---

## Tips de Producción

### 1. Rate Limiting
```python
from asyncio import Semaphore

semaphore = Semaphore(5)  # Máximo 5 requests concurrentes

async def rate_limited_request(url):
    async with semaphore:
        # Tu request aquí
        pass
```

### 2. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_config(key: str):
    # Cachea configuraciones frecuentes
    pass
```

### 3. Logging Estructurado
```python
import structlog

logger = structlog.get_logger()
logger.info("product_launched", 
    product_name=state.product_name,
    margin=state.profit_margin,
    url=state.deployed_url
)
```

### 4. Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

**Para más ejemplos, consulta la documentación oficial o abre un issue en el repositorio.**
