"""Configuration settings for the trading bot."""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Bybit API Configuration
    bybit_api_key: str = Field(..., env="BYBIT_API_KEY")
    bybit_secret_key: str = Field(..., env="BYBIT_SECRET_KEY")
    bybit_testnet: bool = Field(True, env="BYBIT_TESTNET")
    
    # Ollama Configuration
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field("gemma2:9b", env="OLLAMA_MODEL")
    
    # Trading Configuration
    trading_pair: str = Field("BTCUSDT", env="TRADING_PAIR")
    max_position_size: float = Field(0.1, env="MAX_POSITION_SIZE")
    stop_loss_percent: float = Field(2.0, env="STOP_LOSS_PERCENT")
    take_profit_percent: float = Field(3.0, env="TAKE_PROFIT_PERCENT")
    risk_per_trade: float = Field(0.02, env="RISK_PER_TRADE")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/trading_bot.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()