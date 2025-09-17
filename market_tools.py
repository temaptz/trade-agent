"""Market analysis tools for the trading bot."""
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from duckduckgo_search import DDGS
import ccxt
from loguru import logger
import ta

class MarketDataProvider:
    """Provides market data from various sources."""
    
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': '',
            'secret': '',
            'sandbox': True,  # Use testnet
            'enableRateLimit': True,
        })
    
    def get_historical_data(self, symbol: str = "BTCUSDT", timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        """Get historical price data."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """Get current price of the symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            return None
    
    def get_market_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators."""
        if df.empty:
            return {}
        
        try:
            indicators = {
                'sma_20': ta.trend.sma_indicator(df['close'], window=20).iloc[-1],
                'sma_50': ta.trend.sma_indicator(df['close'], window=50).iloc[-1],
                'ema_12': ta.trend.ema_indicator(df['close'], window=12).iloc[-1],
                'ema_26': ta.trend.ema_indicator(df['close'], window=26).iloc[-1],
                'rsi': ta.momentum.rsi(df['close'], window=14).iloc[-1],
                'macd': ta.trend.macd(df['close']).iloc[-1],
                'macd_signal': ta.trend.macd_signal(df['close']).iloc[-1],
                'bb_upper': ta.volatility.bollinger_hband(df['close']).iloc[-1],
                'bb_lower': ta.volatility.bollinger_lband(df['close']).iloc[-1],
                'bb_middle': ta.volatility.bollinger_mavg(df['close']).iloc[-1],
                'volume_sma': ta.volume.volume_sma(df['close'], df['volume']).iloc[-1],
                'atr': ta.volatility.average_true_range(df['high'], df['low'], df['close']).iloc[-1],
            }
            
            # Calculate additional indicators
            indicators['price_change_1h'] = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            indicators['price_change_24h'] = ((df['close'].iloc[-1] - df['close'].iloc[-25]) / df['close'].iloc[-25]) * 100
            indicators['volume_ratio'] = df['volume'].iloc[-1] / df['volume'].mean()
            
            return indicators
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

class NewsAnalyzer:
    """Analyzes market news and sentiment."""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    def search_crypto_news(self, query: str = "bitcoin", max_results: int = 10) -> List[Dict[str, str]]:
        """Search for cryptocurrency news."""
        try:
            results = self.ddgs.news(
                keywords=f"{query} cryptocurrency bitcoin",
                region="wt-wt",
                safesearch="moderate",
                timelimit="d",
                max_results=max_results
            )
            return list(results)
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    def search_market_analysis(self, query: str = "bitcoin technical analysis", max_results: int = 5) -> List[Dict[str, str]]:
        """Search for market analysis articles."""
        try:
            results = self.ddgs.news(
                keywords=f"{query} bitcoin analysis prediction",
                region="wt-wt",
                safesearch="moderate",
                timelimit="d",
                max_results=max_results
            )
            return list(results)
        except Exception as e:
            logger.error(f"Error searching market analysis: {e}")
            return []
    
    def analyze_sentiment(self, news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simple sentiment analysis based on keywords."""
        positive_keywords = ['bullish', 'rise', 'surge', 'gain', 'positive', 'up', 'growth', 'breakout']
        negative_keywords = ['bearish', 'fall', 'drop', 'decline', 'negative', 'down', 'crash', 'correction']
        
        positive_count = 0
        negative_count = 0
        total_text = ""
        
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('body', '')}".lower()
            total_text += text + " "
            
            for keyword in positive_keywords:
                if keyword in text:
                    positive_count += 1
            
            for keyword in negative_keywords:
                if keyword in text:
                    negative_count += 1
        
        total_sentiment = positive_count + negative_count
        if total_sentiment == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / total_sentiment
        
        return {
            'sentiment_score': sentiment_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'total_articles': len(news_items),
            'sentiment_text': 'positive' if sentiment_score > 0.1 else 'negative' if sentiment_score < -0.1 else 'neutral'
        }

class MarketAnalyzer:
    """Main market analysis class."""
    
    def __init__(self):
        self.data_provider = MarketDataProvider()
        self.news_analyzer = NewsAnalyzer()
    
    def get_comprehensive_analysis(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get comprehensive market analysis."""
        logger.info(f"Starting comprehensive analysis for {symbol}")
        
        # Get historical data
        df = self.data_provider.get_historical_data(symbol, "1h", 100)
        current_price = self.data_provider.get_current_price(symbol)
        
        # Calculate technical indicators
        indicators = self.data_provider.get_market_indicators(df)
        
        # Get news and sentiment
        news = self.news_analyzer.search_crypto_news("bitcoin", 10)
        analysis_news = self.news_analyzer.search_market_analysis("bitcoin technical analysis", 5)
        sentiment = self.news_analyzer.analyze_sentiment(news + analysis_news)
        
        # Compile analysis
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'technical_indicators': indicators,
            'sentiment_analysis': sentiment,
            'news_summary': {
                'total_news': len(news),
                'analysis_articles': len(analysis_news),
                'recent_news': news[:3] if news else []
            },
            'market_trend': self._determine_trend(indicators),
            'volatility': self._calculate_volatility(df),
            'support_resistance': self._find_support_resistance(df)
        }
        
        logger.info(f"Analysis completed for {symbol}")
        return analysis
    
    def _determine_trend(self, indicators: Dict[str, Any]) -> str:
        """Determine market trend based on indicators."""
        if not indicators:
            return "unknown"
        
        trend_score = 0
        
        # SMA trend
        if indicators.get('sma_20', 0) > indicators.get('sma_50', 0):
            trend_score += 1
        else:
            trend_score -= 1
        
        # MACD trend
        if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
            trend_score += 1
        else:
            trend_score -= 1
        
        # RSI trend
        rsi = indicators.get('rsi', 50)
        if rsi > 50:
            trend_score += 0.5
        else:
            trend_score -= 0.5
        
        if trend_score > 1:
            return "bullish"
        elif trend_score < -1:
            return "bearish"
        else:
            return "sideways"
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate market volatility."""
        if df.empty or len(df) < 20:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        return returns.std() * np.sqrt(24)  # Annualized volatility
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Find support and resistance levels."""
        if df.empty:
            return {}
        
        # Simple support/resistance calculation
        recent_highs = df['high'].rolling(window=20).max()
        recent_lows = df['low'].rolling(window=20).min()
        
        return {
            'resistance': recent_highs.iloc[-1],
            'support': recent_lows.iloc[-1],
            'current': df['close'].iloc[-1]
        }