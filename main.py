"""
Orquestador Principal del Sistema de Automatización de Dropshipping.
Coordina la ejecución secuencial de todos los agentes con manejo robusto de errores.
"""
import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

import aiohttp

from config import settings
from models import ProductState
from agents import (
    run_scout_agent,
    run_creative_agent,
    run_devops_agent,
    run_media_buyer_agent
)


# Configuración de logging con formato colorido
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def send_emergency_alert(error_message: str, state: Optional[ProductState] = None):
    """
    Envía alerta crítica a webhook de emergencia (Slack, Discord, etc.).
    
    Args:
        error_message: Descripción del error crítico
        state: Estado actual del producto (si está disponible)
    """
    logger.critical(f"🚨 [EMERGENCY] Enviando alerta crítica: {error_message}")
    
    payload = {
        "text": f"🚨 DROPSHIPPING AUTOMATION FAILURE",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Sistema de Automatización Detenido"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:* {error_message}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{datetime.utcnow().isoformat()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Stage:*\n{state.pipeline_stage if state else 'Unknown'}"
                    }
                ]
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.emergency_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    logger.info("✅ [EMERGENCY] Alerta enviada exitosamente")
                else:
                    logger.error(f"❌ [EMERGENCY] Error al enviar alerta: {response.status}")
    except Exception as e:
        logger.error(f"❌ [EMERGENCY] Fallo al enviar webhook: {str(e)}")


def print_pipeline_summary(state: ProductState, execution_time: float):
    """
    Imprime resumen ejecutivo del pipeline completado.
    """
    logger.info("\n" + "="*80)
    logger.info("📊 RESUMEN EJECUTIVO DEL PIPELINE")
    logger.info("="*80)
    logger.info(f"✅ Estado Final: {state.pipeline_stage}")
    logger.info(f"⏱️  Tiempo Total: {execution_time:.2f} segundos")
    logger.info("")
    logger.info(f"📦 Producto: {state.product_name}")
    logger.info(f"💰 Costo: ${state.target_cost} | Precio: ${state.suggested_price} | Margen: {state.profit_margin}X")
    logger.info(f"🎨 Assets Generados: {len(state.image_assets)} imágenes")
    logger.info(f"📝 Copy: {state.generated_copy.get('headline', 'N/A')[:60]}...")
    logger.info(f"🌐 Landing Page: {state.deployed_url}")
    logger.info(f"📱 Campaña Meta Ads: {state.instagram_ad_draft_id} (Estado: {state.campaign_status})")
    logger.info("")
    logger.info("🎯 Próximos Pasos:")
    logger.info("  1. Revisar landing page en el navegador")
    logger.info("  2. Aprobar campaña en Meta Ads Manager")
    logger.info("  3. Monitorear métricas de conversión")
    logger.info("  4. Escalar presupuesto si ROI > 2.5X")
    logger.info("="*80 + "\n")


async def main():
    """
    Función principal que orquesta el flujo completo del pipeline.
    
    Flujo:
    1. Scout Agent: Identifica producto ganador
    2. Creative Agent: Genera copy y assets visuales
    3. DevOps Agent: Crea y despliega landing page
    4. Media Buyer Agent: Crea campaña publicitaria
    
    Manejo de errores:
    - Captura excepciones en cada fase
    - Envía alertas críticas en caso de fallo
    - Registra errores en el estado para debugging
    """
    start_time = asyncio.get_event_loop().time()
    state: Optional[ProductState] = None
    
    logger.info("\n" + "🚀"*40)
    logger.info("🤖 INICIANDO SISTEMA DE AUTOMATIZACIÓN DE DROPSHIPPING")
    logger.info("🚀"*40 + "\n")
    
    try:
        # ============================================================
        # FASE 1: SCOUT AGENT - Búsqueda de Producto Ganador
        # ============================================================
        logger.info("=" * 80)
        logger.info("FASE 1/4: SCOUT AGENT")
        logger.info("=" * 80)
        
        state = await run_scout_agent()
        
        # ============================================================
        # FASE 2: CREATIVE AGENT - Generación de Contenido
        # ============================================================
        logger.info("\n" + "=" * 80)
        logger.info("FASE 2/4: CREATIVE AGENT")
        logger.info("=" * 80)
        
        state = await run_creative_agent(state)
        
        # ============================================================
        # FASE 3: DEVOPS AGENT - Deployment de Landing Page
        # ============================================================
        logger.info("\n" + "=" * 80)
        logger.info("FASE 3/4: DEVOPS AGENT")
        logger.info("=" * 80)
        
        state = await run_devops_agent(state)
        
        # ============================================================
        # FASE 4: MEDIA BUYER AGENT - Creación de Campaña
        # ============================================================
        logger.info("\n" + "=" * 80)
        logger.info("FASE 4/4: MEDIA BUYER AGENT")
        logger.info("=" * 80)
        
        state = await run_media_buyer_agent(state)
        
        # ============================================================
        # PIPELINE COMPLETADO EXITOSAMENTE
        # ============================================================
        execution_time = asyncio.get_event_loop().time() - start_time
        
        logger.info("\n" + "🎉"*40)
        logger.info("✅ PIPELINE COMPLETADO EXITOSAMENTE")
        logger.info("🎉"*40 + "\n")
        
        print_pipeline_summary(state, execution_time)
        
        return state
        
    except ValueError as e:
        # Error de validación de negocio (ej: margen insuficiente)
        error_msg = f"Error de validación: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        if state:
            state.errors.append(error_msg)
        
        await send_emergency_alert(error_msg, state)
        sys.exit(1)
        
    except aiohttp.ClientError as e:
        # Error de conexión con APIs externas
        error_msg = f"Error de conexión con API externa: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        if state:
            state.errors.append(error_msg)
        
        await send_emergency_alert(error_msg, state)
        sys.exit(1)
        
    except Exception as e:
        # Error inesperado
        error_msg = f"Error crítico inesperado: {type(e).__name__} - {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.exception("Stack trace completo:")
        
        if state:
            state.errors.append(error_msg)
        
        await send_emergency_alert(error_msg, state)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrumpido por el usuario")
        sys.exit(0)
