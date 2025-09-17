"""
Конфигурация торгового робота
"""
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Bybit API
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY", "")
    BYBIT_SECRET_KEY: str = os.getenv("BYBIT_SECRET_KEY", "")
    BYBIT_TESTNET: bool = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma2:9b")
    
    # Trading
    TRADING_SYMBOL: str = os.getenv("TRADING_SYMBOL", "BTCUSDT")
    TRADE_AMOUNT: float = float(os.getenv("TRADE_AMOUNT", "0.001"))
    MAX_POSITION_SIZE: float = float(os.getenv("MAX_POSITION_SIZE", "0.01"))
    RISK_PERCENTAGE: float = float(os.getenv("RISK_PERCENTAGE", "2.0"))
    
    # News API
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка обязательных параметров конфигурации"""
        required_fields = [
            cls.BYBIT_API_KEY,
            cls.BYBIT_SECRET_KEY
        ]
        
        if not all(required_fields):
            raise ValueError("Отсутствуют обязательные параметры конфигурации")
        
        return True