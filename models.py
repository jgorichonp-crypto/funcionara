"""
Modelos de datos del sistema usando Pydantic v2.
Define el contrato de datos que fluye entre agentes.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime


class ProductState(BaseModel):
    """
    Estado global del producto que muta a través del pipeline.
    Representa el contrato de datos entre todos los agentes.
    """
    
    # Información básica del producto (Scout Agent)
    product_name: str = Field(default="", description="Nombre del producto ganador")
    supplier_url: str = Field(default="", description="URL del proveedor (AliExpress, CJ, etc.)")
    target_cost: float = Field(default=0.0, ge=0, description="Costo de adquisición en USD")
    suggested_price: float = Field(default=0.0, ge=0, description="Precio de venta sugerido en USD")
    profit_margin: float = Field(default=0.0, ge=0, description="Margen de ganancia calculado")
    
    # Marketing y creatividad (Creative Agent)
    marketing_angles: List[str] = Field(default_factory=list, description="Ángulos de marketing identificados")
    generated_copy: Dict[str, str] = Field(
        default_factory=dict,
        description="Copy generado con keys: headline, body, cta"
    )
    image_assets: List[str] = Field(default_factory=list, description="URLs de imágenes generadas")
    
    # Deployment (DevOps Agent)
    deployed_url: str = Field(default="", description="URL de la tienda desplegada")
    deployment_timestamp: Optional[datetime] = Field(default=None, description="Timestamp del deployment")
    
    # Publicidad (Media Buyer Agent)
    instagram_ad_draft_id: str = Field(default="", description="ID de la campaña en Meta Ads")
    campaign_status: str = Field(default="pending", description="Estado de la campaña publicitaria")
    
    # Metadata del flujo
    pipeline_stage: str = Field(default="initialized", description="Etapa actual del pipeline")
    errors: List[str] = Field(default_factory=list, description="Errores acumulados durante el flujo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Smart LED Strip 15m RGB",
                "supplier_url": "https://aliexpress.com/item/123456",
                "target_cost": 8.50,
                "suggested_price": 29.99,
                "profit_margin": 3.52,
                "marketing_angles": [
                    "Transform any room instantly",
                    "Perfect for gamers and streamers"
                ],
                "generated_copy": {
                    "headline": "Transform Your Space in 60 Seconds",
                    "body": "Professional RGB lighting that syncs with your music",
                    "cta": "Get 40% OFF Today Only"
                },
                "image_assets": [
                    "https://s3.amazonaws.com/assets/product-1.jpg"
                ],
                "deployed_url": "https://smart-led-store.vercel.app",
                "instagram_ad_draft_id": "120210000000000",
                "campaign_status": "draft"
            }
        }
