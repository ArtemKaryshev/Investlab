from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings with environment validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Telegram
    bot_token: str
    webapp_url: str
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # API
    api_secret_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Admin
    admin_user_ids: str = ""
    
    @property
    def admin_ids(self) -> List[int]:
        """Parse admin user IDs from comma-separated string."""
        if not self.admin_user_ids:
            return []
        return [int(uid.strip()) for uid in self.admin_user_ids.split(",") if uid.strip()]
    
    # Market Data
    moex_api_base: str = "https://iss.moex.com/iss"
    market_update_interval: int = 30
    
    # Environment
    environment: str = "production"
    debug: bool = False


settings = Settings()
