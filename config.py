"""
Configuration settings for Bitcoin trading agent
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class TradingConfig(BaseSettings):
    """Trading configuration"""
    
    # Bybit API
    bybit_api_key: str = Field(..., env="BYBIT_API_KEY")
    bybit_secret_key: str = Field(..., env="BYBIT_SECRET_KEY")
    bybit_testnet: bool = Field(True, env="BYBIT_TESTNET")
    
    # Trading parameters
    trading_symbol: str = Field("BTCUSDT", env="TRADING_SYMBOL")
    trading_interval: str = Field("1h", env="TRADING_INTERVAL")
    max_position_size: float = Field(0.1, env="MAX_POSITION_SIZE")
    risk_percentage: float = Field(2.0, env="RISK_PERCENTAGE")
    
    # Analysis intervals
    news_update_interval: int = Field(300, env="NEWS_UPDATE_INTERVAL")
    market_analysis_interval: int = Field(60, env="MARKET_ANALYSIS_INTERVAL")
    
    # Ollama
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field("gemma2:9b", env="OLLAMA_MODEL")
    
    # LangSmith (optional)
    langchain_tracing_v2: bool = Field(False, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    langchain_project: str = Field("bitcoin-trading-agent", env="LANGCHAIN_PROJECT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global config instance
config = TradingConfig()