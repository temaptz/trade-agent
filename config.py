"""
Configuration module for Bitcoin Trading Agent
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class TradingConfig(BaseSettings):
    """Trading configuration settings"""
    
    # Bybit API
    bybit_api_key: str = Field(..., env="BYBIT_API_KEY")
    bybit_secret_key: str = Field(..., env="BYBIT_SECRET_KEY")
    bybit_testnet: bool = Field(True, env="BYBIT_TESTNET")
    
    # Ollama
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field("llama3.1:8b", env="OLLAMA_MODEL")
    
    # Trading parameters
    trading_pair: str = Field("BTCUSDT", env="TRADING_PAIR")
    max_position_size: float = Field(0.1, env="MAX_POSITION_SIZE")
    risk_percentage: float = Field(2.0, env="RISK_PERCENTAGE")
    stop_loss_percentage: float = Field(3.0, env="STOP_LOSS_PERCENTAGE")
    take_profit_percentage: float = Field(6.0, env="TAKE_PROFIT_PERCENTAGE")
    
    # News analysis
    news_update_interval: int = Field(300, env="NEWS_UPDATE_INTERVAL")
    sentiment_threshold: float = Field(0.6, env="SENTIMENT_THRESHOLD")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/trading_agent.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global config instance
config = TradingConfig()

# Bybit API endpoints
BYBIT_BASE_URL = "https://api-testnet.bybit.com" if config.bybit_testnet else "https://api.bybit.com"
BYBIT_WS_URL = "wss://stream-testnet.bybit.com/v5/public/spot" if config.bybit_testnet else "wss://stream.bybit.com/v5/public/spot"