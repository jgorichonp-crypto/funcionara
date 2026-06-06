"""
Paquete de agentes autónomos para el sistema de Dropshipping.
Cada agente es responsable de una fase específica del pipeline.

Módulos de validación FASE 2:
- market_saturation: Análisis de saturación de mercado
- supplier_validation: Validación de confiabilidad de proveedores
- local_trends: Análisis de tendencias locales Chile
- seasonality: Inteligencia de estacionalidad
"""
from .scout import run_scout_agent
from .creative import run_creative_agent
from .devops import run_devops_agent
from .media_buyer import run_media_buyer_agent
from .crm import send_order_confirmation_request, process_incoming_reply

# Módulos de validación FASE 2
try:
    from .market_saturation import analyze_market_saturation, should_reject_product_by_saturation
    from .supplier_validation import validate_supplier, should_reject_supplier
    from .local_trends import analyze_local_trends
    from .seasonality import get_seasonal_search_config, filter_products_by_season
    PHASE2_MODULES_AVAILABLE = True
except ImportError:
    PHASE2_MODULES_AVAILABLE = False

__all__ = [
    "run_scout_agent",
    "run_creative_agent",
    "run_devops_agent",
    "run_media_buyer_agent",
    "send_order_confirmation_request",
    "process_incoming_reply",
    # FASE 2
    "analyze_market_saturation",
    "should_reject_product_by_saturation",
    "validate_supplier",
    "should_reject_supplier",
    "analyze_local_trends",
    "get_seasonal_search_config",
    "filter_products_by_season",
    "PHASE2_MODULES_AVAILABLE"
]
