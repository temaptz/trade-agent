"""
Конфигурация торгового робота
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Bybit API
    bybit_api_key: str = Field(..., env="BYBIT_API_KEY")
    bybit_secret_key: str = Field(..., env="BYBIT_SECRET_KEY")
    bybit_testnet: bool = Field(True, env="BYBIT_TESTNET")
    
    # Alpha Vantage API
    alpha_vantage_api_key: str = Field(..., env="ALPHA_VANTAGE_API_KEY")
    
    # Trading parameters
    trading_pair: str = Field("BTCUSDT", env="TRADING_PAIR")
    position_size: float = Field(0.001, env="POSITION_SIZE")
    max_position_size: float = Field(0.01, env="MAX_POSITION_SIZE")
    stop_loss_percent: float = Field(2.0, env="STOP_LOSS_PERCENT")
    take_profit_percent: float = Field(3.0, env="TAKE_PROFIT_PERCENT")
    
    # Risk management
    max_daily_trades: int = Field(5, env="MAX_DAILY_TRADES")
    min_confidence_threshold: float = Field(0.7, env="MIN_CONFIDENCE_THRESHOLD")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Глобальный экземпляр настроек
settings = Settings()