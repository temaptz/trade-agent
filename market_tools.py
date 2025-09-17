"""
Инструменты для анализа рынка
"""
import ccxt
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MarketDataInput(BaseModel):
    """Входные данные для получения рыночных данных"""
    symbol: str = Field(description="Торговый символ (например, BTC/USDT)")
    timeframe: str = Field(description="Временной интервал (1m, 5m, 15m, 1h, 4h, 1d)")
    limit: int = Field(description="Количество свечей", default=100)

class NewsSearchInput(BaseModel):
    """Входные данные для поиска новостей"""
    query: str = Field(description="Поисковый запрос")
    days: int = Field(description="Количество дней для поиска", default=7)

class TechnicalAnalysisInput(BaseModel):
    """Входные данные для технического анализа"""
    symbol: str = Field(description="Торговый символ")
    timeframe: str = Field(description="Временной интервал")

class MarketDataTool(BaseTool):
    """Инструмент для получения рыночных данных"""
    name = "get_market_data"
    description = "Получает исторические данные о ценах с биржи"
    args_schema = MarketDataInput
    
    def __init__(self):
        super().__init__()
        self.exchange = ccxt.bybit({
            'apiKey': '',  # Будет установлено из конфигурации
            'secret': '',
            'sandbox': True,
            'enableRateLimit': True,
        })
    
    def _run(self, symbol: str, timeframe: str, limit: int = 100) -> str:
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Вычисляем технические индикаторы
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['rsi'] = self._calculate_rsi(df['close'])
            df['macd'], df['macd_signal'] = self._calculate_macd(df['close'])
            
            # Последние данные
            latest = df.iloc[-1]
            
            result = {
                'current_price': float(latest['close']),
                'sma_20': float(latest['sma_20']) if not pd.isna(latest['sma_20']) else None,
                'sma_50': float(latest['sma_50']) if not pd.isna(latest['sma_50']) else None,
                'rsi': float(latest['rsi']) if not pd.isna(latest['rsi']) else None,
                'macd': float(latest['macd']) if not pd.isna(latest['macd']) else None,
                'macd_signal': float(latest['macd_signal']) if not pd.isna(latest['macd_signal']) else None,
                'volume_24h': float(latest['volume']),
                'price_change_24h': float((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100) if len(df) > 1 else 0
            }
            
            return f"Рыночные данные для {symbol}:\n{result}"
            
        except Exception as e:
            logger.error(f"Ошибка получения рыночных данных: {e}")
            return f"Ошибка получения данных: {str(e)}"
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Вычисляет RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Вычисляет MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal

class NewsSearchTool(BaseTool):
    """Инструмент для поиска новостей"""
    name = "search_news"
    description = "Ищет новости в интернете по заданному запросу"
    args_schema = NewsSearchInput
    
    def _run(self, query: str, days: int = 7) -> str:
        try:
            # Используем DuckDuckGo для поиска новостей
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                # Поиск новостей за последние дни
                news_results = []
                for result in ddgs.news(query, max_results=10):
                    news_results.append({
                        'title': result.get('title', ''),
                        'body': result.get('body', ''),
                        'url': result.get('url', ''),
                        'date': result.get('date', '')
                    })
                
                if not news_results:
                    return "Новости не найдены"
                
                # Форматируем результаты
                formatted_news = []
                for i, news in enumerate(news_results[:5], 1):
                    formatted_news.append(f"{i}. {news['title']}\n   {news['body'][:200]}...\n   {news['url']}\n")
                
                return f"Найдено новостей по запросу '{query}':\n\n" + "\n".join(formatted_news)
                
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            return f"Ошибка поиска новостей: {str(e)}"

class TechnicalAnalysisTool(BaseTool):
    """Инструмент для технического анализа"""
    name = "technical_analysis"
    description = "Выполняет технический анализ рыночных данных"
    args_schema = TechnicalAnalysisInput
    
    def _run(self, symbol: str, timeframe: str) -> str:
        try:
            # Получаем данные
            exchange = ccxt.bybit({'sandbox': True, 'enableRateLimit': True})
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Технические индикаторы
            analysis = self._perform_technical_analysis(df)
            
            return f"Технический анализ для {symbol} ({timeframe}):\n{analysis}"
            
        except Exception as e:
            logger.error(f"Ошибка технического анализа: {e}")
            return f"Ошибка технического анализа: {str(e)}"
    
    def _perform_technical_analysis(self, df: pd.DataFrame) -> str:
        """Выполняет технический анализ"""
        current_price = df['close'].iloc[-1]
        
        # Скользящие средние
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1]
        
        # RSI
        rsi = self._calculate_rsi(df['close']).iloc[-1]
        
        # MACD
        macd, macd_signal = self._calculate_macd(df['close'])
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df['close'])
        
        # Анализ тренда
        trend = "Восходящий" if current_price > sma_20 > sma_50 else "Нисходящий" if current_price < sma_20 < sma_50 else "Боковой"
        
        # Сигналы
        signals = []
        if rsi < 30:
            signals.append("RSI указывает на перепроданность")
        elif rsi > 70:
            signals.append("RSI указывает на перекупленность")
        
        if macd.iloc[-1] > macd_signal.iloc[-1]:
            signals.append("MACD показывает бычий сигнал")
        else:
            signals.append("MACD показывает медвежий сигнал")
        
        if current_price > bb_upper.iloc[-1]:
            signals.append("Цена выше верхней полосы Боллинджера")
        elif current_price < bb_lower.iloc[-1]:
            signals.append("Цена ниже нижней полосы Боллинджера")
        
        analysis = f"""
Текущая цена: {current_price:.2f}
SMA 20: {sma_20:.2f}
SMA 50: {sma_50:.2f}
RSI: {rsi:.2f}
MACD: {macd.iloc[-1]:.2f}
MACD Signal: {macd_signal.iloc[-1]:.2f}
Тренд: {trend}

Сигналы:
{chr(10).join(f"- {signal}" for signal in signals)}
        """
        
        return analysis
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Вычисляет RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Вычисляет MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
        """Вычисляет полосы Боллинджера"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower