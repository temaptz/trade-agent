"""
Market data analysis module with technical indicators
"""
import pandas as pd
import numpy as np
import ta
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from models import MarketData, TechnicalIndicators, MarketAnalysis
from bybit_client import BybitClient

class MarketAnalyzer:
    """Advanced market data analyzer with technical indicators"""
    
    def __init__(self, bybit_client: BybitClient):
        self.bybit_client = bybit_client
        self.symbol = None
        
    def analyze_market_data(self, symbol: str = None) -> MarketAnalysis:
        """Comprehensive market analysis"""
        try:
            if symbol is None:
                symbol = config.trading_pair
            self.symbol = symbol
            
            # Get market data
            market_data = self.bybit_client.get_market_data(symbol)
            
            # Get historical data for technical analysis
            klines = self.bybit_client.get_klines(symbol, "1h", 200)
            
            # Convert to DataFrame
            df = self._klines_to_dataframe(klines)
            
            # Calculate technical indicators
            technical_indicators = self._calculate_technical_indicators(df)
            
            # Analyze technical patterns
            technical_score = self._analyze_technical_patterns(df, technical_indicators)
            
            # Analyze market structure
            structure_score = self._analyze_market_structure(df, market_data)
            
            # Calculate overall technical score
            overall_technical = (technical_score + structure_score) / 2
            
            # Create market analysis
            analysis = MarketAnalysis(
                technical_score=overall_technical,
                sentiment_score=0.5,  # Will be updated by news analyzer
                news_score=0.5,       # Will be updated by news analyzer
                overall_score=overall_technical,
                confidence=self._calculate_confidence(df, technical_indicators),
                reasoning=self._generate_technical_reasoning(df, technical_indicators),
                risk_level=self._assess_risk_level(df, market_data)
            )
            
            logger.info(f"Market analysis completed for {symbol}: Technical={overall_technical:.3f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            raise
    
    def _klines_to_dataframe(self, klines: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert klines data to pandas DataFrame"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Convert to numeric
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'turnover']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        return df
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate comprehensive technical indicators"""
        try:
            # RSI
            rsi_14 = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            
            # MACD
            macd_indicator = ta.trend.MACD(df['close'])
            macd = macd_indicator.macd()
            macd_signal = macd_indicator.macd_signal()
            macd_histogram = macd_indicator.macd_diff()
            
            # Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            bb_upper = bb_indicator.bollinger_hband()
            bb_middle = bb_indicator.bollinger_mavg()
            bb_lower = bb_indicator.bollinger_lband()
            
            # Moving Averages
            sma_20 = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            sma_50 = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            ema_12 = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            ema_26 = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            
            # Volume indicators
            volume_sma = ta.volume.VolumeSMAIndicator(df['close'], df['volume'], window=20).volume_sma()
            
            return TechnicalIndicators(
                rsi_14=rsi_14.iloc[-1] if not rsi_14.empty else None,
                macd=macd.iloc[-1] if not macd.empty else None,
                macd_signal=macd_signal.iloc[-1] if not macd_signal.empty else None,
                macd_histogram=macd_histogram.iloc[-1] if not macd_histogram.empty else None,
                bollinger_upper=bb_upper.iloc[-1] if not bb_upper.empty else None,
                bollinger_middle=bb_middle.iloc[-1] if not bb_middle.empty else None,
                bollinger_lower=bb_lower.iloc[-1] if not bb_lower.empty else None,
                sma_20=sma_20.iloc[-1] if not sma_20.empty else None,
                sma_50=sma_50.iloc[-1] if not sma_50.empty else None,
                ema_12=ema_12.iloc[-1] if not ema_12.empty else None,
                ema_26=ema_26.iloc[-1] if not ema_26.empty else None,
                volume_sma=volume_sma.iloc[-1] if not volume_sma.empty else None
            )
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return TechnicalIndicators()
    
    def _analyze_technical_patterns(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> float:
        """Analyze technical patterns and return score (0-1)"""
        try:
            score = 0.0
            factors = 0
            
            current_price = df['close'].iloc[-1]
            
            # RSI Analysis
            if indicators.rsi_14 is not None:
                if indicators.rsi_14 < 30:  # Oversold
                    score += 0.8
                elif indicators.rsi_14 > 70:  # Overbought
                    score += 0.2
                elif 40 <= indicators.rsi_14 <= 60:  # Neutral
                    score += 0.5
                else:
                    score += 0.3
                factors += 1
            
            # MACD Analysis
            if indicators.macd is not None and indicators.macd_signal is not None:
                if indicators.macd > indicators.macd_signal:
                    score += 0.7  # Bullish crossover
                else:
                    score += 0.3  # Bearish crossover
                factors += 1
            
            # Bollinger Bands Analysis
            if all([indicators.bollinger_upper, indicators.bollinger_lower, indicators.bollinger_middle]):
                if current_price <= indicators.bollinger_lower:
                    score += 0.8  # Near lower band - potential bounce
                elif current_price >= indicators.bollinger_upper:
                    score += 0.2  # Near upper band - potential pullback
                elif indicators.bollinger_lower < current_price < indicators.bollinger_upper:
                    score += 0.5  # Within bands
                factors += 1
            
            # Moving Average Analysis
            if indicators.sma_20 is not None and indicators.sma_50 is not None:
                if current_price > indicators.sma_20 > indicators.sma_50:
                    score += 0.8  # Strong uptrend
                elif current_price < indicators.sma_20 < indicators.sma_50:
                    score += 0.2  # Strong downtrend
                elif indicators.sma_20 > current_price > indicators.sma_50:
                    score += 0.6  # Weak uptrend
                elif indicators.sma_50 > current_price > indicators.sma_20:
                    score += 0.4  # Weak downtrend
                else:
                    score += 0.5  # Sideways
                factors += 1
            
            # EMA Analysis
            if indicators.ema_12 is not None and indicators.ema_26 is not None:
                if indicators.ema_12 > indicators.ema_26:
                    score += 0.6  # Bullish EMA trend
                else:
                    score += 0.4  # Bearish EMA trend
                factors += 1
            
            # Volume Analysis
            if indicators.volume_sma is not None:
                current_volume = df['volume'].iloc[-1]
                if current_volume > indicators.volume_sma * 1.5:
                    score += 0.1  # High volume confirmation
                factors += 1
            
            return score / factors if factors > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing technical patterns: {e}")
            return 0.5
    
    def _analyze_market_structure(self, df: pd.DataFrame, market_data: MarketData) -> float:
        """Analyze market structure and momentum"""
        try:
            score = 0.0
            factors = 0
            
            # Price momentum
            price_change = market_data.change_percent_24h
            if price_change > 5:
                score += 0.8  # Strong positive momentum
            elif price_change < -5:
                score += 0.2  # Strong negative momentum
            elif price_change > 0:
                score += 0.6  # Positive momentum
            elif price_change < 0:
                score += 0.4  # Negative momentum
            else:
                score += 0.5  # No momentum
            factors += 1
            
            # Volume analysis
            if len(df) >= 20:
                recent_volume = df['volume'].tail(5).mean()
                historical_volume = df['volume'].tail(20).mean()
                volume_ratio = recent_volume / historical_volume if historical_volume > 0 else 1
                
                if volume_ratio > 1.5:
                    score += 0.1  # High volume
                elif volume_ratio < 0.5:
                    score -= 0.1  # Low volume
                factors += 1
            
            # Volatility analysis
            if len(df) >= 20:
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(24)  # Hourly to daily
                
                if volatility < 0.02:  # Low volatility
                    score += 0.1
                elif volatility > 0.08:  # High volatility
                    score -= 0.1
                factors += 1
            
            # Support/Resistance levels
            support_resistance_score = self._analyze_support_resistance(df)
            score += support_resistance_score
            factors += 1
            
            return max(0, min(1, score / factors)) if factors > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing market structure: {e}")
            return 0.5
    
    def _analyze_support_resistance(self, df: pd.DataFrame) -> float:
        """Analyze support and resistance levels"""
        try:
            if len(df) < 50:
                return 0.5
            
            # Find local highs and lows
            highs = df['high'].rolling(window=10, center=True).max()
            lows = df['low'].rolling(window=10, center=True).min()
            
            # Identify resistance levels (local highs)
            resistance_levels = df[df['high'] == highs]['high'].dropna().tail(5)
            
            # Identify support levels (local lows)
            support_levels = df[df['low'] == lows]['low'].dropna().tail(5)
            
            current_price = df['close'].iloc[-1]
            
            # Check proximity to support/resistance
            if not resistance_levels.empty:
                nearest_resistance = resistance_levels.iloc[-1]
                if current_price >= nearest_resistance * 0.98:  # Near resistance
                    return 0.3
            
            if not support_levels.empty:
                nearest_support = support_levels.iloc[-1]
                if current_price <= nearest_support * 1.02:  # Near support
                    return 0.7
            
            return 0.5  # Neutral
            
        except Exception as e:
            logger.error(f"Error analyzing support/resistance: {e}")
            return 0.5
    
    def _calculate_confidence(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> float:
        """Calculate confidence level based on indicator convergence"""
        try:
            confidence_factors = []
            
            # RSI confidence
            if indicators.rsi_14 is not None:
                if indicators.rsi_14 < 20 or indicators.rsi_14 > 80:
                    confidence_factors.append(0.9)  # Extreme levels
                elif indicators.rsi_14 < 30 or indicators.rsi_14 > 70:
                    confidence_factors.append(0.7)  # Strong signals
                else:
                    confidence_factors.append(0.5)  # Weak signals
            
            # MACD confidence
            if indicators.macd is not None and indicators.macd_signal is not None:
                macd_diff = abs(indicators.macd - indicators.macd_signal)
                if macd_diff > 0.01:  # Strong divergence
                    confidence_factors.append(0.8)
                else:
                    confidence_factors.append(0.5)
            
            # Volume confidence
            if indicators.volume_sma is not None and len(df) > 0:
                current_volume = df['volume'].iloc[-1]
                volume_ratio = current_volume / indicators.volume_sma
                if volume_ratio > 2:
                    confidence_factors.append(0.8)  # High volume
                elif volume_ratio > 1.2:
                    confidence_factors.append(0.6)  # Above average
                else:
                    confidence_factors.append(0.4)  # Low volume
            
            return np.mean(confidence_factors) if confidence_factors else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _assess_risk_level(self, df: pd.DataFrame, market_data: MarketData) -> str:
        """Assess market risk level"""
        try:
            risk_factors = 0
            
            # Volatility risk
            if len(df) >= 20:
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(24)
                if volatility > 0.1:
                    risk_factors += 2
                elif volatility > 0.05:
                    risk_factors += 1
            
            # Price change risk
            if abs(market_data.change_percent_24h) > 10:
                risk_factors += 2
            elif abs(market_data.change_percent_24h) > 5:
                risk_factors += 1
            
            # Volume risk
            if len(df) >= 20:
                recent_volume = df['volume'].tail(5).mean()
                historical_volume = df['volume'].tail(20).mean()
                if recent_volume > historical_volume * 3:
                    risk_factors += 1
            
            if risk_factors >= 4:
                return "HIGH"
            elif risk_factors >= 2:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "MEDIUM"
    
    def _generate_technical_reasoning(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> str:
        """Generate human-readable technical analysis reasoning"""
        try:
            reasoning_parts = []
            current_price = df['close'].iloc[-1]
            
            # RSI reasoning
            if indicators.rsi_14 is not None:
                if indicators.rsi_14 < 30:
                    reasoning_parts.append(f"RSI oversold at {indicators.rsi_14:.1f}")
                elif indicators.rsi_14 > 70:
                    reasoning_parts.append(f"RSI overbought at {indicators.rsi_14:.1f}")
                else:
                    reasoning_parts.append(f"RSI neutral at {indicators.rsi_14:.1f}")
            
            # MACD reasoning
            if indicators.macd is not None and indicators.macd_signal is not None:
                if indicators.macd > indicators.macd_signal:
                    reasoning_parts.append("MACD bullish crossover")
                else:
                    reasoning_parts.append("MACD bearish crossover")
            
            # Moving average reasoning
            if indicators.sma_20 is not None and indicators.sma_50 is not None:
                if current_price > indicators.sma_20 > indicators.sma_50:
                    reasoning_parts.append("Price above both SMAs - uptrend")
                elif current_price < indicators.sma_20 < indicators.sma_50:
                    reasoning_parts.append("Price below both SMAs - downtrend")
                else:
                    reasoning_parts.append("Mixed MA signals")
            
            # Bollinger Bands reasoning
            if all([indicators.bollinger_upper, indicators.bollinger_lower]):
                if current_price <= indicators.bollinger_lower:
                    reasoning_parts.append("Price near lower Bollinger Band")
                elif current_price >= indicators.bollinger_upper:
                    reasoning_parts.append("Price near upper Bollinger Band")
                else:
                    reasoning_parts.append("Price within Bollinger Bands")
            
            return "; ".join(reasoning_parts) if reasoning_parts else "No clear technical signals"
            
        except Exception as e:
            logger.error(f"Error generating technical reasoning: {e}")
            return "Technical analysis error"