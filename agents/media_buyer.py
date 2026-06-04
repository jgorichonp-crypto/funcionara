"""
Media Buyer Agent: Creación automática de campañas publicitarias.
Integra con Meta Graph API para crear ads en modo DRAFT.
"""
import asyncio
import logging
import aiohttp
from models import ProductState
from config import settings

logger = logging.getLogger(__name__)


async def _create_meta_campaign(state: ProductState) -> str:
    """
    Crea una campaña publicitaria en Meta Ads (Facebook/Instagram) en modo DRAFT.
    
    En producción, esto haría:
    POST https://graph.facebook.com/v19.0/{ad_account_id}/campaigns
    """
    logger.info("📱 [MEDIA BUYER] Creando campaña en Meta Ads...")
    
    # Simular latencia de API
    await asyncio.sleep(1.8)
    
    # Payload para Meta Graph API
    campaign_data = {
        "name": f"AUTO - {state.product_name} - Test Campaign",
        "objective": "OUTCOME_SALES",  # Optimizar para ventas
        "status": "PAUSED",  # Crear en modo DRAFT/PAUSED
        "special_ad_categories": [],
        "daily_budget": int(settings.daily_ad_budget * 100),  # En centavos
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP"
    }
    
    ad_creative = {
        "name": f"Creative - {state.product_name}",
        "object_story_spec": {
            "page_id": "YOUR_PAGE_ID",
            "link_data": {
                "link": state.deployed_url,
                "message": state.generated_copy.get("body", ""),
                "name": state.generated_copy.get("headline", ""),
                "call_to_action": {
                    "type": "SHOP_NOW",
                    "value": {
                        "link": state.deployed_url
                    }
                }
            }
        }
    }
    
    logger.info(
        f"📊 [MEDIA BUYER] Configuración de campaña:\n"
        f"  - Objetivo: Ventas (OUTCOME_SALES)\n"
        f"  - Presupuesto diario: ${settings.daily_ad_budget}\n"
        f"  - Estado: DRAFT (requiere aprobación manual)\n"
        f"  - URL destino: {state.deployed_url}"
    )
    
    # En producción, aquí iría la llamada real a Meta Graph API
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {settings.meta_access_token}",
            "Content-Type": "application/json"
        }
        
        # Crear campaña
        async with session.post(
            f"https://graph.facebook.com/v19.0/{settings.meta_ad_account_id}/campaigns",
            headers=headers,
            json=campaign_data
        ) as response:
            campaign_response = await response.json()
            campaign_id = campaign_response["id"]
            
        # Crear ad creative
        async with session.post(
            f"https://graph.facebook.com/v19.0/{settings.meta_ad_account_id}/adcreatives",
            headers=headers,
            json=ad_creative
        ) as response:
            creative_response = await response.json()
            
        return campaign_id
    """
    
    # ID simulado de campaña creada
    campaign_id = f"120210{asyncio.get_event_loop().time():.0f}"
    
    logger.info(f"✅ [MEDIA BUYER] Campaña creada exitosamente: {campaign_id}")
    return campaign_id


async def _validate_campaign_budget(daily_budget: float) -> bool:
    """
    Valida que el presupuesto esté dentro de límites seguros para testing.
    """
    if daily_budget > 10.0:
        logger.warning(
            f"⚠️  [MEDIA BUYER] Presupuesto alto detectado: ${daily_budget}. "
            f"Recomendado: $5-10 para testing inicial"
        )
    return True


async def run_media_buyer_agent(state: ProductState) -> ProductState:
    """
    Agente Media Buyer que crea campañas publicitarias automáticas.
    
    Proceso:
    1. Valida presupuesto y configuración
    2. Crea campaña en Meta Ads en modo DRAFT
    3. Configura targeting y creativos
    4. Retorna ID de campaña para aprobación manual
    
    Args:
        state: Estado actual con URL de landing page
        
    Returns:
        ProductState: Estado actualizado con ID de campaña
    """
    logger.info("💰 [MEDIA BUYER] Iniciando creación de campaña publicitaria...")
    
    # Validar que tengamos URL de destino
    if not state.deployed_url:
        raise ValueError("No se puede crear campaña sin URL de landing page")
    
    # Validar presupuesto
    await _validate_campaign_budget(settings.daily_ad_budget)
    
    # Crear campaña en Meta Ads
    campaign_id = await _create_meta_campaign(state)
    
    # Actualizar estado
    state.instagram_ad_draft_id = campaign_id
    state.campaign_status = "draft"
    state.pipeline_stage = "media_buyer_completed"
    
    logger.info(
        f"🎯 [MEDIA BUYER] Campaña lista para revisión:\n"
        f"  - ID: {campaign_id}\n"
        f"  - Estado: DRAFT (requiere aprobación)\n"
        f"  - Presupuesto: ${settings.daily_ad_budget}/día\n"
        f"  - Próximo paso: Revisar en Meta Ads Manager"
    )
    
    return state
