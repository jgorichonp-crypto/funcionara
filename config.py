"""
Configuración centralizada del sistema usando Pydantic Settings.
Maneja variables de entorno y configuraciones críticas.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configuración global del sistema de automatización de Dropshipping."""
    
    # APIs de terceros
    gemini_api_key: str = "AIzaSy-placeholder"
    meta_access_token: str = "EAAtest-placeholder"
    meta_ad_account_id: str = "act_123456789"
    
    # Dropi Integration
    dropi_api_key: str = "your-dropi-api-key-here"
    dropi_product_id: int = 123456
    dropi_email: Optional[str] = None
    dropi_password: Optional[str] = None
    dropi_product_name: str = "Producto de Tienda"
    dropi_product_price: float = 0.0
    dropi_supplier_id: Optional[int] = None
    
    # WhatsApp Integration
    whatsapp_provider: str = "mock"  # "mock", "evolution", o "twilio"
    whatsapp_api_url: str = "https://api.whatsapp-gateway.com"
    whatsapp_api_token: str = "whatsapp-token-placeholder"
    whatsapp_instance: str = "my-instance"
    whatsapp_phone_number_id: str = "twilio-phone-number-id-placeholder"
    
    # Database Integration (PostgreSQL / Supabase)
    database_url: Optional[str] = None
    
    # Deployment
    vercel_token: str = "vercel-test-token-placeholder"
    vercel_team_id: Optional[str] = None
    
    # Configuración de negocio
    min_profit_margin: float = 3.0  # Margen mínimo 3X
    daily_ad_budget: float = 5.0  # Budget diario en USD
    
    # Webhooks y alertas
    emergency_webhook_url: str = "https://hooks.slack.com/services/TEST/WEBHOOK"
    
    # Configuración de logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Instancia global de configuración
settings = Settings()
