# ⚡ Inicio Rápido - 5 Minutos

## Opción 1: Inicio Automático (Windows)

```bash
# Doble clic en:
start.bat
```

El script automáticamente:
1. ✅ Crea entorno virtual
2. ✅ Instala dependencias
3. ✅ Verifica configuración
4. ✅ Ejecuta el sistema

---

## Opción 2: Inicio Manual

### Paso 1: Instalar Dependencias (1 min)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar Variables (2 min)

```bash
# Copiar plantilla
copy .env.example .env

# Editar con tus credenciales
notepad .env
```

**Mínimo requerido para testing:**
```env
# Dejar valores por defecto para simulación
MIN_PROFIT_MARGIN=3.0
DAILY_AD_BUDGET=5.0
LOG_LEVEL=INFO
```

### Paso 3: Verificar Sistema (30 seg)

```bash
python verify.py
```

Deberías ver:
```
✅ Python 3.11.x - OK
✅ pydantic - Instalado
✅ aiohttp - Instalado
✅ config - OK
✅ models - OK
✅ agents.scout - OK
✅ SISTEMA LISTO PARA EJECUTAR
```

### Paso 4: Ejecutar (1 min)

```bash
python main.py
```

---

## ¿Qué Esperar?

El sistema ejecutará automáticamente:

1. **Scout Agent** (2s) - Identifica producto ganador
2. **Creative Agent** (3s) - Genera copy e imágenes
3. **DevOps Agent** (3s) - Crea y despliega landing page
4. **Media Buyer Agent** (2s) - Crea campaña publicitaria

**Tiempo total:** ~10-12 segundos

---

## Salida Esperada

```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
🤖 INICIANDO SISTEMA DE AUTOMATIZACIÓN DE DROPSHIPPING
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

================================================================================
FASE 1/4: SCOUT AGENT
================================================================================
✅ [SCOUT] Producto identificado: Proyector Galaxy LED 360° con Bluetooth
   Margen: 3.85X | Costo: $12.99 | Precio: $49.99

================================================================================
FASE 2/4: CREATIVE AGENT
================================================================================
✅ [CREATIVE] Contenido generado: 4 imágenes, 5 ángulos, copy completo

================================================================================
FASE 3/4: DEVOPS AGENT
================================================================================
✅ [DEVOPS] Landing page en vivo: https://proyector-galaxy-led-auto.vercel.app

================================================================================
FASE 4/4: MEDIA BUYER AGENT
================================================================================
✅ [MEDIA BUYER] Campaña creada: 1202101705318257 (Estado: DRAFT)

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
✅ PIPELINE COMPLETADO EXITOSAMENTE
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉

📊 RESUMEN EJECUTIVO DEL PIPELINE
================================================================================
✅ Estado Final: media_buyer_completed
⏱️  Tiempo Total: 10.45 segundos

📦 Producto: Proyector Galaxy LED 360° con Bluetooth
💰 Costo: $12.99 | Precio: $49.99 | Margen: 3.85X
🎨 Assets Generados: 4 imágenes
📝 Copy: Transform Any Room Into a Cosmic Paradise in 60 Seconds...
🌐 Landing Page: https://proyector-galaxy-led-auto.vercel.app
📱 Campaña Meta Ads: 1202101705318257 (Estado: draft)

🎯 Próximos Pasos:
  1. Revisar landing page en el navegador
  2. Aprobar campaña en Meta Ads Manager
  3. Monitorear métricas de conversión
  4. Escalar presupuesto si ROI > 2.5X
================================================================================
```

---

## Troubleshooting Rápido

### Error: "Python no reconocido"
```bash
# Instalar Python 3.11+ desde python.org
# Asegurarse de marcar "Add to PATH" durante instalación
```

### Error: "pip no reconocido"
```bash
# Reinstalar Python con opción "Add to PATH"
# O usar: python -m pip install -r requirements.txt
```

### Error: "ModuleNotFoundError"
```bash
# Asegurarse de estar en el entorno virtual
venv\Scripts\activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "No module named 'dotenv'"
```bash
# Instalar python-dotenv
pip install python-dotenv
```

---

## Próximos Pasos

### 1. Explorar el Código
```bash
# Ver estructura
tree /F  # Windows
# tree    # Linux/Mac

# Leer documentación
notepad README.md
notepad ARCHITECTURE.md
notepad EXAMPLES.md
```

### 2. Personalizar Configuración
```bash
# Editar configuración
notepad .env

# Cambiar margen mínimo, budget, etc.
```

### 3. Integrar APIs Reales
```bash
# Obtener API keys:
# - OpenAI: https://platform.openai.com/api-keys
# - Stability AI: https://platform.stability.ai/
# - Meta Ads: https://developers.facebook.com/
# - Vercel: https://vercel.com/account/tokens

# Agregar a .env
```

### 4. Ejecutar en Producción
```bash
# Ver ejemplos avanzados
notepad EXAMPLES.md

# Configurar base de datos
# Configurar webhooks
# Configurar monitoreo
```

---

## Comandos Útiles

```bash
# Verificar sistema
python verify.py

# Ejecutar pipeline
python main.py

# Ejecutar con logs detallados
set LOG_LEVEL=DEBUG && python main.py

# Ejecutar tests (si existen)
pytest

# Limpiar cache
rmdir /s /q __pycache__
rmdir /s /q agents\__pycache__
```

---

## Recursos

- 📖 **README.md** - Documentación completa
- 🏗️ **ARCHITECTURE.md** - Arquitectura técnica
- 📚 **EXAMPLES.md** - Ejemplos avanzados
- 🔧 **verify.py** - Script de verificación
- 🚀 **start.bat** - Inicio automático

---

## Soporte

¿Problemas? Revisa:
1. ✅ Python 3.11+ instalado
2. ✅ Dependencias instaladas (`pip list`)
3. ✅ Entorno virtual activado
4. ✅ Archivo `.env` configurado

---

**¡Listo para automatizar tu Dropshipping! 🚀**
