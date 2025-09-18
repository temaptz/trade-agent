"""
Market analysis module with technical indicators and market sentiment
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import asyncio
from loguru import logger
from bybit_client import BybitClient

class MarketAnalyzer:
    """Comprehensive market analysis with technical indicators"""
    
    def __init__(self, bybit_client: BybitClient):
        self.client = bybit_client
        self.symbol = bybit_client.symbol
        
    async def analyze_market(self, timeframe: str = None, limit: int = 200) -> Dict:
        """Comprehensive market analysis"""
        try:
            # Get market data
            df = await self.client.get_market_data(limit=limit)
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Market sentiment analysis
            sentiment = self._analyze_sentiment(df, indicators)
            
            # Trend analysis
            trend = self._analyze_trend(df, indicators)
            
            # Volatility analysis
            volatility = self._analyze_volatility(df)
            
            # Support and resistance levels
            levels = self._find_support_resistance(df)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'symbol': self.symbol,
                'price_data': {
                    'current_price': df['close'].iloc[-1],
                    'price_change_24h': self._calculate_price_change(df),
                    'volume_24h': df['volume'].iloc[-1],
                    'high_24h': df['high'].max(),
                    'low_24h': df['low'].min()
                },
                'indicators': indicators,
                'sentiment': sentiment,
                'trend': trend,
                'volatility': volatility,
                'support_resistance': levels,
                'recommendation': self._generate_recommendation(indicators, sentiment, trend)
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            raise
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        try:
            indicators = {}
            
            # Moving averages
            indicators['sma_20'] = ta.trend.sma_indicator(df['close'], window=20).iloc[-1]
            indicators['sma_50'] = ta.trend.sma_indicator(df['close'], window=50).iloc[-1]
            indicators['sma_200'] = ta.trend.sma_indicator(df['close'], window=200).iloc[-1]
            indicators['ema_12'] = ta.trend.ema_indicator(df['close'], window=12).iloc[-1]
            indicators['ema_26'] = ta.trend.ema_indicator(df['close'], window=26).iloc[-1]
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd.macd_diff().iloc[-1]
            
            # RSI
            indicators['rsi'] = ta.momentum.rsi(df['close'], window=14).iloc[-1]
            indicators['rsi_oversold'] = indicators['rsi'] < 30
            indicators['rsi_overbought'] = indicators['rsi'] > 70
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'])
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            indicators['bb_position'] = (df['close'].iloc[-1] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
            
            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            indicators['stoch_k'] = stoch.stoch().iloc[-1]
            indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
            
            # Williams %R
            indicators['williams_r'] = ta.momentum.williams_r(df['high'], df['low'], df['close']).iloc[-1]
            
            # ADX (Average Directional Index)
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            indicators['adx'] = adx.adx().iloc[-1]
            indicators['adx_pos'] = adx.adx_pos().iloc[-1]
            indicators['adx_neg'] = adx.adx_neg().iloc[-1]
            
            # Volume indicators
            indicators['volume_sma'] = ta.volume.volume_sma(df['close'], df['volume']).iloc[-1]
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
            
            # Ichimoku Cloud
            ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'], df['close'])
            indicators['ichimoku_a'] = ichimoku.ichimoku_a().iloc[-1]
            indicators['ichimoku_b'] = ichimoku.ichimoku_b().iloc[-1]
            indicators['ichimoku_base'] = ichimoku.ichimoku_base_line().iloc[-1]
            indicators['ichimoku_conversion'] = ichimoku.ichimoku_conversion_line().iloc[-1]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _analyze_sentiment(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Analyze market sentiment based on multiple factors"""
        try:
            sentiment_score = 0
            factors = []
            
            current_price = df['close'].iloc[-1]
            
            # RSI sentiment
            if indicators.get('rsi', 50) < 30:
                sentiment_score += 2
                factors.append("RSI oversold - bullish signal")
            elif indicators.get('rsi', 50) > 70:
                sentiment_score -= 2
                factors.append("RSI overbought - bearish signal")
            
            # MACD sentiment
            if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
                sentiment_score += 1
                factors.append("MACD bullish crossover")
            else:
                sentiment_score -= 1
                factors.append("MACD bearish crossover")
            
            # Bollinger Bands sentiment
            bb_position = indicators.get('bb_position', 0.5)
            if bb_position < 0.2:
                sentiment_score += 1
                factors.append("Price near lower Bollinger Band - potential bounce")
            elif bb_position > 0.8:
                sentiment_score -= 1
                factors.append("Price near upper Bollinger Band - potential pullback")
            
            # Moving average sentiment
            if current_price > indicators.get('sma_20', current_price):
                sentiment_score += 1
                factors.append("Price above 20 SMA - bullish")
            else:
                sentiment_score -= 1
                factors.append("Price below 20 SMA - bearish")
            
            # Volume sentiment
            volume_ratio = indicators.get('volume_ratio', 1)
            if volume_ratio > 1.5:
                sentiment_score += 1
                factors.append("High volume - strong momentum")
            elif volume_ratio < 0.5:
                sentiment_score -= 1
                factors.append("Low volume - weak momentum")
            
            # Determine overall sentiment
            if sentiment_score >= 3:
                overall_sentiment = "Very Bullish"
            elif sentiment_score >= 1:
                overall_sentiment = "Bullish"
            elif sentiment_score <= -3:
                overall_sentiment = "Very Bearish"
            elif sentiment_score <= -1:
                overall_sentiment = "Bearish"
            else:
                overall_sentiment = "Neutral"
            
            return {
                'score': sentiment_score,
                'overall': overall_sentiment,
                'factors': factors
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'score': 0, 'overall': 'Neutral', 'factors': []}
    
    def _analyze_trend(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Analyze market trend"""
        try:
            current_price = df['close'].iloc[-1]
            sma_20 = indicators.get('sma_20', current_price)
            sma_50 = indicators.get('sma_50', current_price)
            sma_200 = indicators.get('sma_200', current_price)
            
            trend_signals = []
            trend_strength = 0
            
            # Short-term trend (20 SMA)
            if current_price > sma_20:
                trend_signals.append("Price above 20 SMA - short-term bullish")
                trend_strength += 1
            else:
                trend_signals.append("Price below 20 SMA - short-term bearish")
                trend_strength -= 1
            
            # Medium-term trend (50 SMA)
            if current_price > sma_50:
                trend_signals.append("Price above 50 SMA - medium-term bullish")
                trend_strength += 1
            else:
                trend_signals.append("Price below 50 SMA - medium-term bearish")
                trend_strength -= 1
            
            # Long-term trend (200 SMA)
            if current_price > sma_200:
                trend_signals.append("Price above 200 SMA - long-term bullish")
                trend_strength += 1
            else:
                trend_signals.append("Price below 200 SMA - long-term bearish")
                trend_strength -= 1
            
            # MACD trend
            if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
                trend_signals.append("MACD bullish - trend continuation")
                trend_strength += 1
            else:
                trend_signals.append("MACD bearish - trend reversal")
                trend_strength -= 1
            
            # ADX trend strength
            adx = indicators.get('adx', 0)
            if adx > 25:
                trend_signals.append(f"Strong trend (ADX: {adx:.2f})")
            elif adx > 15:
                trend_signals.append(f"Moderate trend (ADX: {adx:.2f})")
            else:
                trend_signals.append(f"Weak trend (ADX: {adx:.2f})")
            
            # Determine overall trend
            if trend_strength >= 3:
                overall_trend = "Strong Uptrend"
            elif trend_strength >= 1:
                overall_trend = "Uptrend"
            elif trend_strength <= -3:
                overall_trend = "Strong Downtrend"
            elif trend_strength <= -1:
                overall_trend = "Downtrend"
            else:
                overall_trend = "Sideways"
            
            return {
                'overall': overall_trend,
                'strength': trend_strength,
                'signals': trend_signals,
                'adx': adx
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return {'overall': 'Unknown', 'strength': 0, 'signals': [], 'adx': 0}
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """Analyze market volatility"""
        try:
            # Calculate ATR (Average True Range)
            atr = ta.volatility.average_true_range(df['high'], df['low'], df['close']).iloc[-1]
            
            # Calculate volatility percentage
            volatility_pct = (atr / df['close'].iloc[-1]) * 100
            
            # Volatility classification
            if volatility_pct > 5:
                volatility_level = "High"
            elif volatility_pct > 2:
                volatility_level = "Medium"
            else:
                volatility_level = "Low"
            
            return {
                'atr': atr,
                'volatility_percentage': volatility_pct,
                'level': volatility_level
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volatility: {e}")
            return {'atr': 0, 'volatility_percentage': 0, 'level': 'Unknown'}
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Find support and resistance levels"""
        try:
            # Simple pivot points
            high = df['high'].iloc[-20:].max()
            low = df['low'].iloc[-20:].min()
            close = df['close'].iloc[-1]
            
            # Pivot point calculation
            pivot = (high + low + close) / 3
            resistance1 = 2 * pivot - low
            support1 = 2 * pivot - high
            resistance2 = pivot + (high - low)
            support2 = pivot - (high - low)
            
            return {
                'pivot': pivot,
                'resistance': [resistance1, resistance2],
                'support': [support1, support2],
                'current_level': close
            }
            
        except Exception as e:
            logger.error(f"Error finding support/resistance: {e}")
            return {'pivot': 0, 'resistance': [], 'support': [], 'current_level': 0}
    
    def _calculate_price_change(self, df: pd.DataFrame) -> float:
        """Calculate 24h price change percentage"""
        try:
            if len(df) < 2:
                return 0.0
            
            current_price = df['close'].iloc[-1]
            previous_price = df['close'].iloc[-2]
            
            return ((current_price - previous_price) / previous_price) * 100
            
        except Exception as e:
            logger.error(f"Error calculating price change: {e}")
            return 0.0
    
    def _generate_recommendation(self, indicators: Dict, sentiment: Dict, trend: Dict) -> Dict:
        """Generate trading recommendation based on analysis"""
        try:
            recommendation_score = 0
            reasons = []
            
            # Sentiment-based recommendation
            sentiment_score = sentiment.get('score', 0)
            if sentiment_score >= 2:
                recommendation_score += 2
                reasons.append("Strong bullish sentiment")
            elif sentiment_score <= -2:
                recommendation_score -= 2
                reasons.append("Strong bearish sentiment")
            
            # Trend-based recommendation
            trend_strength = trend.get('strength', 0)
            if trend_strength >= 2:
                recommendation_score += 1
                reasons.append("Strong uptrend")
            elif trend_strength <= -2:
                recommendation_score -= 1
                reasons.append("Strong downtrend")
            
            # RSI-based recommendation
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                recommendation_score += 1
                reasons.append("RSI oversold - potential bounce")
            elif rsi > 70:
                recommendation_score -= 1
                reasons.append("RSI overbought - potential pullback")
            
            # MACD-based recommendation
            if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
                recommendation_score += 1
                reasons.append("MACD bullish signal")
            else:
                recommendation_score -= 1
                reasons.append("MACD bearish signal")
            
            # Generate recommendation
            if recommendation_score >= 3:
                action = "STRONG_BUY"
            elif recommendation_score >= 1:
                action = "BUY"
            elif recommendation_score <= -3:
                action = "STRONG_SELL"
            elif recommendation_score <= -1:
                action = "SELL"
            else:
                action = "HOLD"
            
            return {
                'action': action,
                'score': recommendation_score,
                'reasons': reasons,
                'confidence': min(abs(recommendation_score) / 4, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {'action': 'HOLD', 'score': 0, 'reasons': [], 'confidence': 0.0}