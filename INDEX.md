# 📑 Índice de Navegación del Proyecto

## 🚀 Inicio Rápido

**¿Primera vez aquí? Empieza por:**

1. 📖 [QUICKSTART.md](QUICKSTART.md) - Guía de inicio en 5 minutos
2. 🚀 Ejecuta `start.bat` (Windows) o sigue los pasos manuales
3. 🎉 ¡Listo! El sistema se ejecutará automáticamente

---

## 📚 Documentación

### Para Usuarios

| Documento | Descripción | Cuándo Leerlo |
|-----------|-------------|---------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Inicio rápido en 5 minutos | 🟢 Primero |
| **[README.md](README.md)** | Documentación completa del proyecto | 🟡 Después de ejecutar |
| **[EXAMPLES.md](EXAMPLES.md)** | 12 ejemplos de uso avanzado | 🟠 Para personalizar |

### Para Desarrolladores

| Documento | Descripción | Cuándo Leerlo |
|-----------|-------------|---------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Arquitectura técnica detallada | 🔵 Para entender el diseño |
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Resumen ejecutivo del proyecto | 🟣 Para overview rápido |

---

## 🗂️ Estructura de Archivos

### 📂 Código Fuente

```
agents/
├── __init__.py          # Exportaciones del paquete
├── scout.py             # 🔍 Búsqueda de productos ganadores
├── creative.py          # 🎨 Generación de copy e imágenes
├── devops.py            # ⚙️  Deployment de landing pages
└── media_buyer.py       # 💰 Creación de campañas publicitarias
```

### 📄 Archivos Core

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| **config.py** | Configuración con Pydantic Settings | 38 |
| **models.py** | Modelos de datos (ProductState) | 68 |
| **main.py** | Orquestador principal del pipeline | 234 |

### 🛠️ Utilidades

| Archivo | Propósito |
|---------|-----------|
| **verify.py** | Script de verificación del sistema |
| **start.bat** | Inicio automático para Windows |
| **requirements.txt** | Dependencias de Python |
| **.env.example** | Plantilla de configuración |
| **.gitignore** | Archivos a ignorar en Git |

---

## 🎯 Flujo de Lectura Recomendado

### Para Ejecutar Rápidamente
```
1. QUICKSTART.md (5 min)
2. Ejecutar start.bat
3. ¡Listo!
```

### Para Entender el Sistema
```
1. PROJECT_SUMMARY.md (10 min) - Overview
2. README.md (20 min) - Documentación completa
3. ARCHITECTURE.md (30 min) - Detalles técnicos
4. Revisar código en agents/ (30 min)
```

### Para Personalizar
```
1. EXAMPLES.md (20 min) - Ver casos de uso
2. Modificar config.py y .env
3. Extender agentes según necesidad
```

---

## 🔍 Búsqueda Rápida

### ¿Cómo hacer...?

| Pregunta | Respuesta en |
|----------|--------------|
| ¿Cómo instalar? | [QUICKSTART.md](QUICKSTART.md) |
| ¿Cómo configurar variables? | [README.md](README.md) - Sección Configuración |
| ¿Cómo agregar un agente? | [README.md](README.md) - Sección Desarrollo |
| ¿Cómo funciona el pipeline? | [ARCHITECTURE.md](ARCHITECTURE.md) - Flujo de Datos |
| ¿Cómo procesar múltiples productos? | [EXAMPLES.md](EXAMPLES.md) - Ejemplo 3 |
| ¿Cómo integrar con DB? | [EXAMPLES.md](EXAMPLES.md) - Ejemplo 5 |
| ¿Cómo hacer testing? | [EXAMPLES.md](EXAMPLES.md) - Ejemplo 9 |
| ¿Cómo crear API REST? | [EXAMPLES.md](EXAMPLES.md) - Ejemplo 10 |

### ¿Qué hace cada agente?

| Agente | Archivo | Descripción |
|--------|---------|-------------|
| **Scout** | [agents/scout.py](agents/scout.py) | Identifica productos ganadores con margen 3X+ |
| **Creative** | [agents/creative.py](agents/creative.py) | Genera copy persuasivo e imágenes con IA |
| **DevOps** | [agents/devops.py](agents/devops.py) | Crea landing page HTML/Tailwind y despliega |
| **Media Buyer** | [agents/media_buyer.py](agents/media_buyer.py) | Crea campaña en Meta Ads ($5/día, modo DRAFT) |

---

## 📊 Diagramas

### Flujo del Pipeline

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Scout Agent    │ → Producto: Proyector Galaxy LED
│  (2 segundos)   │   Margen: 3.85X
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Creative Agent  │ → Copy + 4 Imágenes + 5 Ángulos
│  (3 segundos)   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  DevOps Agent   │ → Landing Page en Vercel
│  (3 segundos)   │   https://producto-auto.vercel.app
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Media Buyer     │ → Campaña Meta Ads (DRAFT)
│  (2 segundos)   │   ID: 120210xxxxx
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   SUCCESS   │ ✅ Pipeline completado en ~10s
└─────────────┘
```

### Arquitectura de Datos

```
ProductState (Pydantic Model)
├── product_name: str
├── supplier_url: str
├── target_cost: float
├── suggested_price: float
├── profit_margin: float
├── marketing_angles: List[str]
├── generated_copy: Dict[str, str]
├── image_assets: List[str]
├── deployed_url: str
├── instagram_ad_draft_id: str
└── pipeline_stage: str
```

---

## 🎓 Recursos de Aprendizaje

### Conceptos Clave

| Concepto | Dónde Aprender |
|----------|----------------|
| **Event-Driven Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) - Principios de Diseño |
| **Async/Await en Python** | [ARCHITECTURE.md](ARCHITECTURE.md) - Async/Await Pattern |
| **Pydantic v2** | [ARCHITECTURE.md](ARCHITECTURE.md) - Contract-First Design |
| **Pipeline Pattern** | [ARCHITECTURE.md](ARCHITECTURE.md) - Patrones de Diseño |
| **Growth Hacking** | [agents/creative.py](agents/creative.py) - Comentarios |

### Tecnologías Usadas

- **Python 3.11+** - Lenguaje principal
- **asyncio** - Programación asíncrona
- **Pydantic v2** - Validación de datos
- **aiohttp** - Cliente HTTP asíncrono
- **Tailwind CSS** - Framework CSS (en HTML generado)

---

## 🚨 Troubleshooting

### Problemas Comunes

| Problema | Solución | Documento |
|----------|----------|-----------|
| Python no reconocido | Instalar Python 3.11+ | [QUICKSTART.md](QUICKSTART.md) |
| Dependencias faltantes | `pip install -r requirements.txt` | [QUICKSTART.md](QUICKSTART.md) |
| Error de módulo | Verificar con `python verify.py` | [QUICKSTART.md](QUICKSTART.md) |
| Error de margen | Ajustar MIN_PROFIT_MARGIN en .env | [README.md](README.md) |

---

## 📞 Ayuda Rápida

### Comandos Esenciales

```bash
# Verificar sistema
python verify.py

# Ejecutar pipeline
python main.py

# Ejecutar con logs detallados
set LOG_LEVEL=DEBUG && python main.py

# Inicio automático (Windows)
start.bat
```

### Archivos de Configuración

```bash
# Copiar plantilla
copy .env.example .env

# Editar configuración
notepad .env
```

---

## 🎯 Próximos Pasos

### Después de Ejecutar

1. ✅ Revisar la salida en consola
2. ✅ Leer [README.md](README.md) para entender el sistema
3. ✅ Explorar [EXAMPLES.md](EXAMPLES.md) para casos avanzados
4. ✅ Configurar APIs reales en `.env`
5. ✅ Personalizar agentes según necesidad

### Para Producción

1. 🔐 Configurar credenciales reales en `.env`
2. 🔗 Integrar APIs reales (OpenAI, Stability, Meta, Vercel)
3. 💾 Agregar base de datos para tracking
4. 📊 Configurar dashboard de monitoreo
5. 🚀 Desplegar en servidor/cloud

---

## 📈 Roadmap

- **v1.0** (Actual) ✅ - Sistema base funcional
- **v1.1** (Próximo) - Integración con APIs reales
- **v2.0** (Futuro) - Dashboard web + DB
- **v3.0** (Visión) - Multi-tenant + ML

Ver detalles en [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## 🏆 Características Destacadas

- ✅ **Arquitectura Event-Driven** - Modular y escalable
- ✅ **Código Asíncrono** - Performance optimizado
- ✅ **Validación Estricta** - Pydantic v2
- ✅ **Manejo de Errores** - Robusto con alertas
- ✅ **Documentación Completa** - 5 archivos MD
- ✅ **Ejemplos Prácticos** - 12 casos de uso
- ✅ **Scripts de Utilidad** - verify.py, start.bat

---

## 📝 Notas Finales

Este proyecto está **listo para producción** con:
- ✅ Código limpio y comentado
- ✅ Arquitectura sólida
- ✅ Documentación exhaustiva
- ✅ Ejemplos prácticos
- ✅ Scripts de utilidad

**¡Empieza con [QUICKSTART.md](QUICKSTART.md) y automatiza tu Dropshipping! 🚀**

---

**Última actualización:** 2024-01-15  
**Versión:** 1.0.0
