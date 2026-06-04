# 🏗️ Arquitectura Técnica del Sistema

## Visión General

Sistema autónomo de automatización de Dropshipping construido con arquitectura event-driven y programación asíncrona en Python 3.11+.

## Principios de Diseño

### 1. Event-Driven Architecture
- Cada agente es un nodo independiente que recibe y emite eventos
- El estado fluye de forma inmutable entre agentes
- Desacoplamiento total entre componentes

### 2. Async/Await Pattern
- Todas las operaciones I/O son asíncronas
- Uso de `asyncio` para concurrencia
- Optimización de tiempo de ejecución mediante `asyncio.gather()`

### 3. Contract-First Design
- Pydantic v2 como contrato de datos
- Validación estricta en tiempo de ejecución
- Type hints completos para IDE support

### 4. Fail-Fast Philosophy
- Validaciones tempranas (margen de ganancia, URLs, etc.)
- Manejo explícito de errores en cada capa
- Alertas automáticas en caso de fallo crítico

## Componentes del Sistema

### Core Layer

#### `models.py` - Capa de Datos
```python
ProductState (BaseModel)
├── Información del producto (Scout)
├── Assets de marketing (Creative)
├── Deployment info (DevOps)
├── Campaign info (Media Buyer)
└── Metadata del pipeline
```

**Responsabilidades:**
- Definir el contrato de datos entre agentes
- Validar tipos y restricciones (Pydantic)
- Proveer ejemplos para documentación

**Patrones aplicados:**
- Data Transfer Object (DTO)
- Immutable State (cada agente retorna nuevo estado)

#### `config.py` - Configuración
```python
Settings (BaseSettings)
├── API Keys (OpenAI, Stability, Meta, Vercel)
├── Business Rules (margen mínimo, budget)
└── Operational Config (webhooks, logging)
```

**Responsabilidades:**
- Centralizar configuración del sistema
- Cargar variables de entorno de forma segura
- Proveer defaults sensatos

**Patrones aplicados:**
- Singleton (instancia global `settings`)
- Environment Variable Pattern

### Agent Layer

Cada agente sigue el mismo contrato:

```python
async def run_agent(state: ProductState) -> ProductState:
    """
    Args:
        state: Estado actual del producto
    
    Returns:
        ProductState: Estado actualizado con nuevos datos
    
    Raises:
        ValueError: Error de validación de negocio
        aiohttp.ClientError: Error de conexión con APIs
    """
```

#### `agents/scout.py` - Reconocimiento
**Responsabilidades:**
- Simular scraping de TikTok Creative Center
- Identificar productos con alto potencial
- Validar margen de ganancia mínimo
- Calcular pricing óptimo

**Integraciones futuras:**
- TikTok Creative Center API
- AliExpress API
- CJ Dropshipping API

**Métricas clave:**
- Margen de ganancia (target: 3X+)
- Volumen de búsquedas
- Tendencia de crecimiento

#### `agents/creative.py` - Generación de Contenido
**Responsabilidades:**
- Generar copy persuasivo con LLM
- Crear imágenes con IA generativa
- Identificar ángulos de marketing
- Optimizar para conversión

**Integraciones:**
- OpenAI GPT-4 (copy generation)
- Stability AI / DALL-E (image generation)
- S3 (almacenamiento de assets)

**Técnicas de Growth Hacking:**
- Escasez artificial ("Limited stock")
- Prueba social ("10,000+ reviews")
- Ancla de valor (precio tachado)
- Urgencia temporal ("50% OFF Today Only")

**Ejecución paralela:**
```python
copy, images, angles = await asyncio.gather(
    _generate_marketing_copy(),
    _generate_image_assets(),
    _identify_marketing_angles()
)
```

#### `agents/devops.py` - Deployment
**Responsabilidades:**
- Generar HTML estático con Tailwind CSS
- Inyectar datos dinámicamente en template
- Desplegar a Vercel/Netlify
- Retornar URL en vivo

**Stack tecnológico:**
- HTML5 + Tailwind CSS (vía CDN)
- Vercel API para deployment
- Responsive design (mobile-first)

**Optimizaciones:**
- CSS inline crítico
- Lazy loading de imágenes
- Meta tags para SEO
- Open Graph para social sharing

#### `agents/media_buyer.py` - Publicidad
**Responsabilidades:**
- Crear campaña en Meta Ads
- Configurar targeting y presupuesto
- Estructurar ad creative
- Retornar ID de campaña en modo DRAFT

**Configuración de campaña:**
- Objetivo: `OUTCOME_SALES`
- Presupuesto: $5/día (testing)
- Estado: `PAUSED` (requiere aprobación)
- Placement: Automático (Facebook + Instagram)

**Integraciones:**
- Meta Graph API v19.0
- Facebook Business Manager
- Instagram Ads

### Orchestration Layer

#### `main.py` - Orquestador Principal
**Responsabilidades:**
- Coordinar ejecución secuencial de agentes
- Manejar errores y excepciones
- Logging detallado de cada fase
- Enviar alertas en caso de fallo
- Generar resumen ejecutivo

**Flujo de ejecución:**
```
main()
├── try:
│   ├── run_scout_agent()
│   ├── run_creative_agent()
│   ├── run_devops_agent()
│   └── run_media_buyer_agent()
├── except ValueError: (validación de negocio)
├── except ClientError: (error de API)
└── except Exception: (error inesperado)
    └── send_emergency_alert()
```

**Manejo de errores:**
- Captura específica por tipo de error
- Logging de stack trace completo
- Webhook de alerta automática
- Exit codes apropiados

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────┐
│                    ProductState                         │
│  (Contrato de datos inmutable entre agentes)            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ SCOUT AGENT                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Input:  None                                        │ │
│ │ Output: ProductState {                              │ │
│ │   product_name: str                                 │ │
│ │   supplier_url: str                                 │ │
│ │   target_cost: float                                │ │
│ │   suggested_price: float                            │ │
│ │   profit_margin: float                              │ │
│ │ }                                                    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ CREATIVE AGENT                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Input:  ProductState (from Scout)                   │ │
│ │ Output: ProductState + {                            │ │
│ │   marketing_angles: List[str]                       │ │
│ │   generated_copy: Dict[str, str]                    │ │
│ │   image_assets: List[str]                           │ │
│ │ }                                                    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ DEVOPS AGENT                                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Input:  ProductState (from Creative)                │ │
│ │ Output: ProductState + {                            │ │
│ │   deployed_url: str                                 │ │
│ │   deployment_timestamp: datetime                    │ │
│ │ }                                                    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ MEDIA BUYER AGENT                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Input:  ProductState (from DevOps)                  │ │
│ │ Output: ProductState + {                            │ │
│ │   instagram_ad_draft_id: str                        │ │
│ │   campaign_status: str                              │ │
│ │ }                                                    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ FINAL STATE   │
                  │ (Complete)    │
                  └───────────────┘
```

## Patrones de Diseño Aplicados

### 1. Pipeline Pattern
Cada agente es una etapa del pipeline que transforma el estado.

### 2. Chain of Responsibility
El estado fluye secuencialmente a través de los agentes.

### 3. Strategy Pattern
Cada agente implementa una estrategia específica (scout, creative, etc.).

### 4. Observer Pattern (futuro)
Sistema de eventos para notificar cambios de estado.

### 5. Factory Pattern (futuro)
Para crear diferentes tipos de agentes dinámicamente.

## Consideraciones de Seguridad

### 1. Secrets Management
- Variables sensibles en `.env` (nunca en código)
- `.env` en `.gitignore`
- Uso de `pydantic-settings` para validación

### 2. API Rate Limiting
- Implementar retry logic con backoff exponencial
- Respetar límites de APIs externas
- Cachear respuestas cuando sea posible

### 3. Budget Control
- Presupuesto bajo por defecto ($5/día)
- Campañas en modo DRAFT (requieren aprobación)
- Validación de margen mínimo

### 4. Error Handling
- No exponer stack traces a usuarios finales
- Sanitizar datos en logs
- Alertas automáticas para errores críticos

## Escalabilidad

### Horizontal Scaling
- Cada agente puede ejecutarse en contenedor separado
- Comunicación vía message queue (RabbitMQ, SQS)
- Estado persistido en base de datos

### Vertical Scaling
- Optimización de queries a APIs
- Caching de resultados frecuentes
- Compresión de imágenes

### Future Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API GW    │────▶│   Lambda    │────▶│     SQS     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
              ┌──────────┐            ┌──────────┐            ┌──────────┐
              │  Scout   │            │ Creative │            │  DevOps  │
              │  Worker  │            │  Worker  │            │  Worker  │
              └──────────┘            └──────────┘            └──────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                        ┌──────────┐
                                        │ DynamoDB │
                                        └──────────┘
```

## Métricas y Monitoreo

### KPIs del Sistema
- Tiempo de ejecución por pipeline
- Tasa de éxito por agente
- Margen promedio de productos identificados
- ROI de campañas publicitarias

### Logging
- Nivel INFO: Progreso normal del pipeline
- Nivel WARNING: Situaciones anómalas no críticas
- Nivel ERROR: Errores recuperables
- Nivel CRITICAL: Errores que detienen el pipeline

### Alertas
- Webhook a Slack/Discord en errores críticos
- Email para reportes diarios
- SMS para alertas de presupuesto excedido

## Testing Strategy

### Unit Tests
```python
# tests/test_scout.py
async def test_scout_agent_validates_margin():
    state = await run_scout_agent()
    assert state.profit_margin >= 3.0
```

### Integration Tests
```python
# tests/test_pipeline.py
async def test_full_pipeline():
    state = await main()
    assert state.pipeline_stage == "media_buyer_completed"
    assert state.deployed_url.startswith("https://")
```

### Load Tests
- Simular 100 productos simultáneos
- Validar límites de APIs
- Medir tiempo de respuesta

## Deployment

### Local Development
```bash
python main.py
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### AWS Lambda (futuro)
- Cada agente como función Lambda separada
- Step Functions para orquestación
- S3 para almacenamiento de estado

## Roadmap Técnico

### v1.0 (Actual)
- ✅ Arquitectura base event-driven
- ✅ 4 agentes funcionales (simulados)
- ✅ Manejo robusto de errores
- ✅ Logging detallado

### v1.1 (Próximo)
- [ ] Integración real con OpenAI
- [ ] Integración real con Stability AI
- [ ] Integración real con Vercel API
- [ ] Integración real con Meta Graph API

### v2.0 (Futuro)
- [ ] Base de datos para tracking
- [ ] Dashboard web (FastAPI + React)
- [ ] A/B testing automático
- [ ] Optimización de presupuesto con ML

### v3.0 (Visión)
- [ ] Multi-tenant support
- [ ] Marketplace de productos
- [ ] Análisis predictivo de tendencias
- [ ] Auto-scaling basado en demanda

---

**Última actualización:** 2024-01-15
**Versión:** 1.0.0
**Arquitecto:** Sistema Autónomo de Dropshipping
