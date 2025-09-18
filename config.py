"""
Конфигурация для ИИ агента торговли биткойном
"""
import os
from typing import Optional
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Bybit API
    bybit_api_key: str = os.getenv("BYBIT_API_KEY", "")
    bybit_secret_key: str = os.getenv("BYBIT_SECRET_KEY", "")
    bybit_testnet: bool = os.getenv("BYBIT_TESTNET", "True").lower() == "true"
    
    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma2:9b")
    
    # Trading
    trading_pair: str = os.getenv("TRADING_PAIR", "BTCUSDT")
    trade_amount: float = float(os.getenv("TRADE_AMOUNT", "0.001"))
    max_risk_percent: float = float(os.getenv("MAX_RISK_PERCENT", "2.0"))
    stop_loss_percent: float = float(os.getenv("STOP_LOSS_PERCENT", "2.0"))
    take_profit_percent: float = float(os.getenv("TAKE_PROFIT_PERCENT", "4.0"))
    
    # Intervals
    news_update_interval: int = int(os.getenv("NEWS_UPDATE_INTERVAL", "300"))
    market_analysis_interval: int = int(os.getenv("MARKET_ANALYSIS_INTERVAL", "60"))
    
    class Config:
        env_file = ".env"

settings = Settings()