"""
Модели данных для торгового бота
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MarketCondition(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"

class TradingSignal(BaseModel):
    action: TradeAction
    confidence: float  # 0.0 to 1.0
    reason: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = datetime.now()

class MarketData(BaseModel):
    symbol: str
    price: float
    volume: float
    change_24h: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime

class NewsItem(BaseModel):
    title: str
    content: str
    source: str
    sentiment: Optional[str] = None
    relevance_score: float = 0.0
    timestamp: datetime

class TechnicalIndicators(BaseModel):
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

class MarketAnalysis(BaseModel):
    market_condition: MarketCondition
    technical_indicators: TechnicalIndicators
    news_sentiment: Optional[str] = None
    price_trend: str
    volatility: float
    support_levels: List[float] = []
    resistance_levels: List[float] = []
    recommendation: str
    confidence: float

class Position(BaseModel):
    symbol: str
    side: str  # "Buy" or "Sell"
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime

class TradingState(BaseModel):
    current_position: Optional[Position] = None
    account_balance: float = 0.0
    available_balance: float = 0.0
    total_pnl: float = 0.0
    last_analysis: Optional[MarketAnalysis] = None
    last_signal: Optional[TradingSignal] = None
    consecutive_losses: int = 0
    last_trade_time: Optional[datetime] = None