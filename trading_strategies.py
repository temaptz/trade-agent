"""
Trading strategies and risk management for Bitcoin trading
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from loguru import logger
from config import config

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"

class RiskLevel(Enum):
    """Risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    signal_type: SignalType
    confidence: float
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: float
    risk_level: RiskLevel
    reasoning: str
    timestamp: datetime

@dataclass
class Position:
    """Position data structure"""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    timestamp: datetime

class RiskManager:
    """Risk management system"""
    
    def __init__(self, max_position_size: float = None, risk_percentage: float = None):
        self.max_position_size = max_position_size or config.max_position_size
        self.risk_percentage = risk_percentage or config.risk_percentage
        self.max_daily_loss = 5.0  # Maximum daily loss percentage
        self.max_drawdown = 10.0   # Maximum drawdown percentage
        
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                              stop_loss: float, risk_amount: float = None) -> float:
        """Calculate position size based on risk management rules"""
        try:
            if risk_amount is None:
                risk_amount = account_balance * (self.risk_percentage / 100)
            
            # Calculate position size based on stop loss distance
            price_diff = abs(entry_price - stop_loss)
            if price_diff == 0:
                return 0.0
            
            position_size = risk_amount / price_diff
            
            # Apply maximum position size limit
            max_size = account_balance * self.max_position_size
            position_size = min(position_size, max_size)
            
            return round(position_size, 6)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def validate_trade(self, signal: TradingSignal, current_positions: List[Position], 
                      account_balance: float) -> Tuple[bool, str]:
        """Validate if a trade should be executed based on risk rules"""
        try:
            # Check if we already have a position in this symbol
            existing_position = next(
                (p for p in current_positions if p.symbol == signal.symbol), 
                None
            )
            
            if existing_position:
                return False, "Position already exists for this symbol"
            
            # Check daily loss limit
            daily_pnl = sum(p.unrealized_pnl for p in current_positions)
            if daily_pnl < -(account_balance * self.max_daily_loss / 100):
                return False, "Daily loss limit reached"
            
            # Check maximum position size
            if signal.position_size > account_balance * self.max_position_size:
                return False, "Position size exceeds maximum allowed"
            
            # Check risk level
            if signal.risk_level == RiskLevel.VERY_HIGH:
                return False, "Risk level too high"
            
            return True, "Trade validated"
            
        except Exception as e:
            logger.error(f"Error validating trade: {e}")
            return False, f"Validation error: {e}"

class TechnicalStrategy:
    """Technical analysis based trading strategy"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
    
    def analyze_signals(self, market_data: Dict, indicators: Dict) -> List[TradingSignal]:
        """Analyze technical indicators and generate trading signals"""
        try:
            signals = []
            current_price = market_data['price_data']['current_price']
            
            # RSI Strategy
            rsi_signal = self._rsi_strategy(indicators, current_price)
            if rsi_signal:
                signals.append(rsi_signal)
            
            # MACD Strategy
            macd_signal = self._macd_strategy(indicators, current_price)
            if macd_signal:
                signals.append(macd_signal)
            
            # Bollinger Bands Strategy
            bb_signal = self._bollinger_bands_strategy(indicators, current_price)
            if bb_signal:
                signals.append(bb_signal)
            
            # Moving Average Crossover Strategy
            ma_signal = self._moving_average_strategy(indicators, current_price)
            if ma_signal:
                signals.append(ma_signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error analyzing technical signals: {e}")
            return []
    
    def _rsi_strategy(self, indicators: Dict, current_price: float) -> Optional[TradingSignal]:
        """RSI-based trading strategy"""
        try:
            rsi = indicators.get('rsi', 50)
            
            if rsi < 30:  # Oversold
                return TradingSignal(
                    signal_type=SignalType.BUY,
                    confidence=min((30 - rsi) / 30 * 100, 90),
                    entry_price=current_price,
                    stop_loss=current_price * 0.95,  # 5% stop loss
                    take_profit=current_price * 1.10,  # 10% take profit
                    position_size=0.0,  # Will be calculated by risk manager
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=f"RSI oversold at {rsi:.2f}",
                    timestamp=datetime.now()
                )
            elif rsi > 70:  # Overbought
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    confidence=min((rsi - 70) / 30 * 100, 90),
                    entry_price=current_price,
                    stop_loss=current_price * 1.05,  # 5% stop loss
                    take_profit=current_price * 0.90,  # 10% take profit
                    position_size=0.0,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=f"RSI overbought at {rsi:.2f}",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in RSI strategy: {e}")
            return None
    
    def _macd_strategy(self, indicators: Dict, current_price: float) -> Optional[TradingSignal]:
        """MACD-based trading strategy"""
        try:
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            macd_histogram = indicators.get('macd_histogram', 0)
            
            # MACD bullish crossover
            if macd > macd_signal and macd_histogram > 0:
                confidence = min(abs(macd_histogram) * 100, 85)
                return TradingSignal(
                    signal_type=SignalType.BUY,
                    confidence=confidence,
                    entry_price=current_price,
                    stop_loss=current_price * 0.97,
                    take_profit=current_price * 1.08,
                    position_size=0.0,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=f"MACD bullish crossover (histogram: {macd_histogram:.4f})",
                    timestamp=datetime.now()
                )
            # MACD bearish crossover
            elif macd < macd_signal and macd_histogram < 0:
                confidence = min(abs(macd_histogram) * 100, 85)
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    confidence=confidence,
                    entry_price=current_price,
                    stop_loss=current_price * 1.03,
                    take_profit=current_price * 0.92,
                    position_size=0.0,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=f"MACD bearish crossover (histogram: {macd_histogram:.4f})",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in MACD strategy: {e}")
            return None
    
    def _bollinger_bands_strategy(self, indicators: Dict, current_price: float) -> Optional[TradingSignal]:
        """Bollinger Bands-based trading strategy"""
        try:
            bb_upper = indicators.get('bb_upper', current_price)
            bb_lower = indicators.get('bb_lower', current_price)
            bb_position = indicators.get('bb_position', 0.5)
            
            # Price near lower band - potential bounce
            if bb_position < 0.2:
                return TradingSignal(
                    signal_type=SignalType.BUY,
                    confidence=min((0.2 - bb_position) * 500, 80),
                    entry_price=current_price,
                    stop_loss=bb_lower * 0.98,
                    take_profit=bb_upper * 0.98,
                    position_size=0.0,
                    risk_level=RiskLevel.LOW,
                    reasoning=f"Price near lower Bollinger Band (position: {bb_position:.2f})",
                    timestamp=datetime.now()
                )
            # Price near upper band - potential pullback
            elif bb_position > 0.8:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    confidence=min((bb_position - 0.8) * 500, 80),
                    entry_price=current_price,
                    stop_loss=bb_upper * 1.02,
                    take_profit=bb_lower * 1.02,
                    position_size=0.0,
                    risk_level=RiskLevel.LOW,
                    reasoning=f"Price near upper Bollinger Band (position: {bb_position:.2f})",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Bollinger Bands strategy: {e}")
            return None
    
    def _moving_average_strategy(self, indicators: Dict, current_price: float) -> Optional[TradingSignal]:
        """Moving Average crossover strategy"""
        try:
            sma_20 = indicators.get('sma_20', current_price)
            sma_50 = indicators.get('sma_50', current_price)
            sma_200 = indicators.get('sma_200', current_price)
            
            # Golden cross (20 SMA crosses above 50 SMA)
            if current_price > sma_20 > sma_50 and sma_20 > sma_50:
                return TradingSignal(
                    signal_type=SignalType.BUY,
                    confidence=75,
                    entry_price=current_price,
                    stop_loss=sma_50 * 0.95,
                    take_profit=current_price * 1.15,
                    position_size=0.0,
                    risk_level=RiskLevel.LOW,
                    reasoning="Golden cross: 20 SMA above 50 SMA",
                    timestamp=datetime.now()
                )
            # Death cross (20 SMA crosses below 50 SMA)
            elif current_price < sma_20 < sma_50 and sma_20 < sma_50:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    confidence=75,
                    entry_price=current_price,
                    stop_loss=sma_50 * 1.05,
                    take_profit=current_price * 0.85,
                    position_size=0.0,
                    risk_level=RiskLevel.LOW,
                    reasoning="Death cross: 20 SMA below 50 SMA",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Moving Average strategy: {e}")
            return None

class SentimentStrategy:
    """News and sentiment-based trading strategy"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
    
    def analyze_sentiment_signals(self, news_analysis: Dict, market_sentiment: Dict) -> List[TradingSignal]:
        """Analyze sentiment and generate trading signals"""
        try:
            signals = []
            
            # News sentiment analysis
            news_sentiment_score = news_analysis.get('sentiment', {}).get('sentiment_score', 0)
            news_sentiment = news_analysis.get('sentiment', {}).get('overall_sentiment', 'neutral')
            
            # Market sentiment analysis
            market_sentiment_score = market_sentiment.get('score', 0)
            market_sentiment_overall = market_sentiment.get('overall', 'neutral')
            
            # Combined sentiment score
            combined_score = (news_sentiment_score + market_sentiment_score) / 2
            
            # Generate signals based on sentiment
            if combined_score > 0.5:  # Positive sentiment
                signal = TradingSignal(
                    signal_type=SignalType.BUY,
                    confidence=min(abs(combined_score) * 100, 85),
                    entry_price=0.0,  # Will be set by caller
                    stop_loss=None,
                    take_profit=None,
                    position_size=0.0,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=f"Positive sentiment: news={news_sentiment}, market={market_sentiment_overall}",
                    timestamp=datetime.now()
                )
                signals.append(signal)
            elif combined_score < -0.5:  # Negative sentiment
                signal = TradingSignal(
                    signal_type=SignalType.SELL,
                    confidence=min(abs(combined_score) * 100, 85),
                    entry_price=0.0,
                    stop_loss=None,
                    take_profit=None,
                    position_size=0.0,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=f"Negative sentiment: news={news_sentiment}, market={market_sentiment_overall}",
                    timestamp=datetime.now()
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment signals: {e}")
            return []

class PortfolioManager:
    """Portfolio and position management"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.positions: List[Position] = []
        self.trade_history: List[Dict] = []
    
    def add_position(self, position: Position):
        """Add a new position"""
        self.positions.append(position)
        logger.info(f"Added position: {position.symbol} {position.side} {position.size}")
    
    def update_position(self, symbol: str, current_price: float):
        """Update position with current price"""
        for position in self.positions:
            if position.symbol == symbol:
                position.current_price = current_price
                # Calculate unrealized PnL
                if position.side == 'long':
                    position.unrealized_pnl = (current_price - position.entry_price) * position.size
                else:  # short
                    position.unrealized_pnl = (position.entry_price - current_price) * position.size
                break
    
    def remove_position(self, symbol: str):
        """Remove a position"""
        self.positions = [p for p in self.positions if p.symbol != symbol]
        logger.info(f"Removed position: {symbol}")
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        try:
            total_pnl = sum(p.unrealized_pnl for p in self.positions)
            total_value = sum(p.current_price * p.size for p in self.positions)
            
            return {
                'total_positions': len(self.positions),
                'total_pnl': total_pnl,
                'total_value': total_value,
                'positions': [
                    {
                        'symbol': p.symbol,
                        'side': p.side,
                        'size': p.size,
                        'entry_price': p.entry_price,
                        'current_price': p.current_price,
                        'unrealized_pnl': p.unrealized_pnl
                    }
                    for p in self.positions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> List[str]:
        """Check if any positions hit stop loss or take profit"""
        actions = []
        
        for position in self.positions:
            if position.symbol == symbol:
                # Check stop loss
                if position.stop_loss:
                    if position.side == 'long' and current_price <= position.stop_loss:
                        actions.append(f"Stop loss triggered for {symbol} at {current_price}")
                    elif position.side == 'short' and current_price >= position.stop_loss:
                        actions.append(f"Stop loss triggered for {symbol} at {current_price}")
                
                # Check take profit
                if position.take_profit:
                    if position.side == 'long' and current_price >= position.take_profit:
                        actions.append(f"Take profit triggered for {symbol} at {current_price}")
                    elif position.side == 'short' and current_price <= position.take_profit:
                        actions.append(f"Take profit triggered for {symbol} at {current_price}")
        
        return actions