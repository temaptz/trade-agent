"""
Конфигурация торгового бота
"""
import os
from dotenv import load_dotenv
from pydantic import BaseSettings
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    # Bybit API
    bybit_api_key: str = os.getenv("BYBIT_API_KEY", "")
    bybit_secret_key: str = os.getenv("BYBIT_SECRET_KEY", "")
    bybit_testnet: bool = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    
    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma2:9b")
    
    # Alpha Vantage
    alpha_vantage_api_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    
    # Trading
    trading_symbol: str = os.getenv("TRADING_SYMBOL", "BTCUSDT")
    max_position_size: float = float(os.getenv("MAX_POSITION_SIZE", "0.1"))
    risk_percentage: float = float(os.getenv("RISK_PERCENTAGE", "2.0"))
    stop_loss_percentage: float = float(os.getenv("STOP_LOSS_PERCENTAGE", "5.0"))
    take_profit_percentage: float = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "10.0"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "trading_bot.log")
    
    class Config:
        env_file = ".env"

settings = Settings()