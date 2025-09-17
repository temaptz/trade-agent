"""
Data models for Bitcoin Trading Agent
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class TradeSignal(str, Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class OrderSide(str, Enum):
    """Order side types"""
    BUY = "Buy"
    SELL = "Sell"

class OrderType(str, Enum):
    """Order type types"""
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"

class MarketData(BaseModel):
    """Market data structure"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    high_24h: float
    low_24h: float
    change_24h: float
    change_percent_24h: float

class TechnicalIndicators(BaseModel):
    """Technical indicators"""
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    volume_sma: Optional[float] = None

class NewsItem(BaseModel):
    """News item structure"""
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None

class MarketAnalysis(BaseModel):
    """Market analysis result"""
    technical_score: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=0, le=1)
    news_score: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    risk_level: str

class TradingDecision(BaseModel):
    """Trading decision structure"""
    signal: TradeSignal
    confidence: float = Field(ge=0, le=1)
    position_size: float = Field(ge=0, le=1)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str
    market_analysis: MarketAnalysis
    timestamp: datetime = Field(default_factory=datetime.now)

class Order(BaseModel):
    """Order structure"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"
    reduce_only: bool = False

class Position(BaseModel):
    """Position structure"""
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime = Field(default_factory=datetime.now)

class TradingState(BaseModel):
    """Trading state for LangGraph"""
    market_data: Optional[MarketData] = None
    technical_indicators: Optional[TechnicalIndicators] = None
    news_items: List[NewsItem] = Field(default_factory=list)
    market_analysis: Optional[MarketAnalysis] = None
    trading_decision: Optional[TradingDecision] = None
    current_position: Optional[Position] = None
    orders: List[Order] = Field(default_factory=list)
    error: Optional[str] = None
    step: str = "initialize"