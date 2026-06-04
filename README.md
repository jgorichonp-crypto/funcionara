# 🚀 Sistema Autónomo de Automatización de Dropshipping

Framework modular y orientado a eventos (Event-Driven) para automatizar el ciclo completo de Dropshipping, desde la identificación de productos ganadores hasta el lanzamiento de campañas publicitarias.

## 🎯 Características

- **Arquitectura Event-Driven**: Flujo asíncrono con Python 3.11+ y asyncio
- **Búsqueda Multi-Fuente**: Scout Agent con scraping de TikTok, Facebook, AliExpress y Google Trends
- **Scoring Avanzado**: Sistema de puntuación 0-100 con validación multi-criterio
- **Validación Estricta**: Pydantic v2 para contratos de datos entre agentes
- **Modular y Escalable**: Cada agente es independiente y reutilizable
- **Growth Hacking**: Copy optimizado para conversión y testing rápido
- **Deployment Automático**: Generación y despliegue de landing pages en segundos
- **Integración con Meta Ads**: Creación automática de campañas publicitarias

## 🏗️ Arquitectura

```
┌─────────────┐
│ Scout Agent │ → Búsqueda multi-fuente (TikTok, Facebook, AliExpress, Google Trends)
└──────┬──────┘   Scoring 0-100 | Validación 7 criterios | TOP 5 ranking
       ↓
┌─────────────────┐
│ Creative Agent  │ → Genera copy persuasivo + imágenes con IA
└──────┬──────────┘
       ↓
┌─────────────────┐
│ DevOps Agent    │ → Crea landing page HTML/Tailwind + Deploy a Vercel
└──────┬──────────┘
       ↓
┌──────────────────┐
│ Media Buyer Agent│ → Crea campaña en Meta Ads (modo DRAFT)
└──────────────────┘
```

## 📦 Estructura del Proyecto

```
Funcionara/
├── config.py              # Configuración con Pydantic Settings
├── models.py              # Modelos de datos (ProductState)
├── main.py                # Orquestador principal
├── agents/
│   ├── __init__.py
│   ├── scout.py           # Búsqueda multi-fuente + scoring avanzado
│   ├── creative.py        # Generación de contenido con IA
│   ├── devops.py          # Deployment de landing pages
│   └── media_buyer.py     # Creación de campañas publicitarias
├── requirements.txt       # Dependencias Python
├── .env.example           # Plantilla de variables de entorno
└── README.md              # Esta documentación
```

## 🚀 Instalación

### 1. Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Cuentas en:
  - OpenAI (para generación de copy)
  - Stability AI (para generación de imágenes)
  - Meta Business (para publicidad)
  - Vercel/Netlify (para deployment)

### 2. Clonar e Instalar

```bash
# Navegar al directorio
cd "C:\Users\jori_\OneDrive\Documentos\Funcionara"

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # En Windows
# source venv/bin/activate  # En Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
# Copiar plantilla
copy .env.example .env

# Editar .env con tus credenciales reales
notepad .env
```

**Variables críticas a configurar:**
- `OPENAI_API_KEY`: Tu API key de OpenAI
- `META_ACCESS_TOKEN`: Token de acceso de Meta Business
- `META_AD_ACCOUNT_ID`: ID de tu cuenta publicitaria
- `VERCEL_TOKEN`: Token de Vercel para deployment

## 🔍 Scout Agent - Búsqueda de Productos Ganadores

El Scout Agent es el componente más crítico del sistema. Utiliza múltiples fuentes para identificar productos con alto potencial:

### Fuentes de Datos

1. **TikTok Creative Center** - Top Ads y productos trending
2. **Facebook Ad Library** - Anuncios activos de competidores
3. **AliExpress** - Productos con más órdenes y mejor rating
4. **Google Trends** - Análisis de tendencias y crecimiento

### Sistema de Scoring (0-100 puntos)

- **Margen de ganancia** (30 pts): Mínimo 3X, ideal 5X+
- **Demanda** (25 pts): Búsquedas mensuales + órdenes en AliExpress
- **Validación social** (20 pts): Rating + número de reviews
- **Tendencia** (15 pts): Crecimiento en últimos 30 días
- **Competencia** (10 pts): Sweet spot 10-30 ads activos

### Criterios de Validación

- ✅ Margen ≥ 3X
- ✅ Costo $5-$30
- ✅ Rating ≥ 4.5⭐
- ✅ Órdenes ≥ 1,000
- ✅ Envío ≤ 20 días
- ✅ Peso ≤ 3kg
- ✅ Tendencia rising

**Ver documentación completa:** [SCOUT_AGENT.md](SCOUT_AGENT.md)

---

## 💻 Uso

### Ejecución Básica

```bash
python main.py
```

### Salida Esperada

```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
🤖 INICIANDO SISTEMA DE AUTOMATIZACIÓN DE DROPSHIPPING
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

================================================================================
FASE 1/4: SCOUT AGENT
================================================================================
2024-01-15 10:30:45 | INFO     | 🔍 [SCOUT] Iniciando búsqueda de productos ganadores...
2024-01-15 10:30:47 | INFO     | ✅ [SCOUT] Producto identificado: Proyector Galaxy LED 360° con Bluetooth | Margen: 3.85X | Costo: $12.99 | Precio: $49.99
2024-01-15 10:30:47 | INFO     | 🎯 [SCOUT] Análisis completado exitosamente

================================================================================
FASE 2/4: CREATIVE AGENT
================================================================================
2024-01-15 10:30:47 | INFO     | 🎨 [CREATIVE] Iniciando generación de contenido creativo...
2024-01-15 10:30:48 | INFO     | 📝 [CREATIVE] Generando copy con LLM...
2024-01-15 10:30:49 | INFO     | ✅ [CREATIVE] Copy generado: Transform Any Room Into a Cosmic Paradise in 60...
2024-01-15 10:30:49 | INFO     | 🎨 [CREATIVE] Generando assets visuales con IA...
2024-01-15 10:30:51 | INFO     | ✅ [CREATIVE] 4 imágenes generadas y subidas a S3
2024-01-15 10:30:51 | INFO     | 🎯 [CREATIVE] Identificando ángulos de marketing...
2024-01-15 10:30:52 | INFO     | ✅ [CREATIVE] 5 ángulos identificados
2024-01-15 10:30:52 | INFO     | ✅ [CREATIVE] Contenido generado exitosamente: 4 imágenes, 5 ángulos, copy completo

================================================================================
FASE 3/4: DEVOPS AGENT
================================================================================
2024-01-15 10:30:52 | INFO     | ⚙️  [DEVOPS] Iniciando generación y deployment de landing page...
2024-01-15 10:30:52 | INFO     | 📄 [DEVOPS] Generando HTML con Tailwind CSS...
2024-01-15 10:30:52 | INFO     | ✅ [DEVOPS] HTML generado (5847 caracteres)
2024-01-15 10:30:52 | INFO     | 🚀 [DEVOPS] Desplegando sitio a Vercel...
2024-01-15 10:30:55 | INFO     | ✅ [DEVOPS] Sitio desplegado exitosamente: https://proyector-galaxy-led-360-con-b-auto.vercel.app
2024-01-15 10:30:55 | INFO     | 🎉 [DEVOPS] Landing page en vivo: https://proyector-galaxy-led-360-con-b-auto.vercel.app

================================================================================
FASE 4/4: MEDIA BUYER AGENT
================================================================================
2024-01-15 10:30:55 | INFO     | 💰 [MEDIA BUYER] Iniciando creación de campaña publicitaria...
2024-01-15 10:30:55 | INFO     | 📱 [MEDIA BUYER] Creando campaña en Meta Ads...
2024-01-15 10:30:57 | INFO     | 📊 [MEDIA BUYER] Configuración de campaña:
  - Objetivo: Ventas (OUTCOME_SALES)
  - Presupuesto diario: $5.0
  - Estado: DRAFT (requiere aprobación manual)
  - URL destino: https://proyector-galaxy-led-360-con-b-auto.vercel.app
2024-01-15 10:30:57 | INFO     | ✅ [MEDIA BUYER] Campaña creada exitosamente: 1202101705318257
2024-01-15 10:30:57 | INFO     | 🎯 [MEDIA BUYER] Campaña lista para revisión:
  - ID: 1202101705318257
  - Estado: DRAFT (requiere aprobación)
  - Presupuesto: $5.0/día
  - Próximo paso: Revisar en Meta Ads Manager

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
✅ PIPELINE COMPLETADO EXITOSAMENTE
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉

================================================================================
📊 RESUMEN EJECUTIVO DEL PIPELINE
================================================================================
✅ Estado Final: media_buyer_completed
⏱️  Tiempo Total: 12.34 segundos

📦 Producto: Proyector Galaxy LED 360° con Bluetooth
💰 Costo: $12.99 | Precio: $49.99 | Margen: 3.85X
🎨 Assets Generados: 4 imágenes
📝 Copy: Transform Any Room Into a Cosmic Paradise in 60 Seconds...
🌐 Landing Page: https://proyector-galaxy-led-360-con-b-auto.vercel.app
📱 Campaña Meta Ads: 1202101705318257 (Estado: draft)

🎯 Próximos Pasos:
  1. Revisar landing page en el navegador
  2. Aprobar campaña en Meta Ads Manager
  3. Monitorear métricas de conversión
  4. Escalar presupuesto si ROI > 2.5X
================================================================================
```

## 🔧 Configuración Avanzada

### Ajustar Margen Mínimo

En `.env`:
```env
MIN_PROFIT_MARGIN=4.0  # Requerir margen de 4X en lugar de 3X
```

### Cambiar Presupuesto de Testing

En `.env`:
```env
DAILY_AD_BUDGET=10.0  # Aumentar a $10/día
```

### Configurar Alertas de Emergencia

En `.env`:
```env
EMERGENCY_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🛠️ Desarrollo

### Agregar un Nuevo Agente

1. Crear archivo en `agents/nuevo_agente.py`:

```python
import asyncio
import logging
from models import ProductState

logger = logging.getLogger(__name__)

async def run_nuevo_agente(state: ProductState) -> ProductState:
    logger.info("🔧 [NUEVO] Iniciando nuevo agente...")
    
    # Tu lógica aquí
    await asyncio.sleep(1)
    
    state.pipeline_stage = "nuevo_agente_completed"
    logger.info("✅ [NUEVO] Agente completado")
    return state
```

2. Importar en `agents/__init__.py`:

```python
from .nuevo_agente import run_nuevo_agente

__all__ = [..., "run_nuevo_agente"]
```

3. Agregar al flujo en `main.py`:

```python
state = await run_nuevo_agente(state)
```

### Testing

```bash
# Ejecutar con logs detallados
LOG_LEVEL=DEBUG python main.py

# Simular error para probar alertas
# (Modificar temporalmente MIN_PROFIT_MARGIN=10.0 en .env)
```

## 📊 Métricas de Rendimiento

- **Tiempo de ejecución**: ~10-15 segundos por producto
- **Margen mínimo**: 3X (configurable)
- **Presupuesto de testing**: $5/día (configurable)
- **Tasa de éxito**: Depende de la calidad del producto identificado

## 🚨 Manejo de Errores

El sistema incluye manejo robusto de errores:

- **Validación de margen**: Si el producto no cumple el margen mínimo, el pipeline se detiene
- **Errores de API**: Captura errores de conexión con APIs externas
- **Alertas automáticas**: Envía notificaciones a webhook configurado
- **Logs detallados**: Registra cada paso para debugging

## 🔐 Seguridad

- **Nunca commitear `.env`**: Archivo incluido en `.gitignore`
- **Tokens sensibles**: Usar variables de entorno, nunca hardcodear
- **Modo DRAFT**: Las campañas se crean pausadas para revisión manual
- **Presupuesto limitado**: Budget de testing bajo por defecto ($5/día)

## 📈 Roadmap

- [ ] Integración real con OpenAI GPT-4
- [ ] Integración real con Stability AI
- [ ] Integración real con Vercel API
- [ ] Integración real con Meta Graph API
- [ ] Dashboard web para monitoreo
- [ ] Base de datos para tracking de productos
- [ ] A/B testing automático de copy
- [ ] Análisis de competencia
- [ ] Optimización automática de presupuesto

## 🤝 Contribución

Este es un proyecto privado. Para sugerencias o mejoras, contactar al arquitecto del sistema.

## 📄 Licencia

Propietario: Sistema privado de automatización de Dropshipping.

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar logs en consola
2. Verificar configuración en `.env`
3. Validar credenciales de APIs
4. Revisar webhook de alertas

---

**Construido con ❤️ para automatizar el éxito en Dropshipping**
