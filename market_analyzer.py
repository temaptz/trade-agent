"""
Анализатор рынка для технического анализа и получения исторических данных
"""
import pandas as pd
import numpy as np
import requests
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import ta
from loguru import logger
from config import settings
from models import TechnicalIndicators, MarketAnalysis, MarketCondition, NewsItem
from bybit_client import BybitClient

class MarketAnalyzer:
    def __init__(self, bybit_client: BybitClient):
        self.bybit_client = bybit_client
        self.alpha_vantage_api_key = settings.alpha_vantage_api_key
        
    def get_historical_data_alpha_vantage(self, symbol: str = "BTC", 
                                        function: str = "DIGITAL_CURRENCY_DAILY",
                                        market: str = "USD") -> Optional[pd.DataFrame]:
        """Получение исторических данных от Alpha Vantage"""
        try:
            if not self.alpha_vantage_api_key:
                logger.warning("Alpha Vantage API ключ не настроен")
                return None
                
            url = "https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol,
                "market": market,
                "apikey": self.alpha_vantage_api_key,
                "outputsize": "full"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                logger.error(f"Alpha Vantage API ошибка: {data['Error Message']}")
                return None
                
            if "Note" in data:
                logger.warning(f"Alpha Vantage API лимит: {data['Note']}")
                return None
            
            # Извлекаем данные о ценах
            time_series_key = "Time Series (Digital Currency Daily)"
            if time_series_key not in data:
                logger.error("Неожиданная структура данных от Alpha Vantage")
                return None
                
            df = pd.DataFrame(data[time_series_key]).T
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            
            # Переименовываем колонки для совместимости
            df.columns = ['open', 'high', 'low', 'close', 'volume', 'market_cap']
            
            logger.info(f"Получено {len(df)} записей исторических данных от Alpha Vantage")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка получения данных от Alpha Vantage: {e}")
            return None
    
    def get_historical_data_bybit(self, symbol: str = None, interval: str = "1", 
                                 limit: int = 200) -> Optional[pd.DataFrame]:
        """Получение исторических данных от Bybit"""
        try:
            symbol = symbol or settings.trading_symbol
            klines = self.bybit_client.get_historical_klines(symbol, interval, limit)
            
            if not klines:
                return None
                
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Конвертируем типы данных
            for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Получено {len(df)} записей исторических данных от Bybit")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка получения данных от Bybit: {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Расчет технических индикаторов"""
        try:
            if df.empty or len(df) < 50:
                logger.warning("Недостаточно данных для расчета технических индикаторов")
                return TechnicalIndicators()
            
            # RSI
            rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            
            # MACD
            macd_indicator = ta.trend.MACD(df['close'])
            macd = macd_indicator.macd()
            macd_signal = macd_indicator.macd_signal()
            
            # Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(df['close'], window=20)
            bb_upper = bb_indicator.bollinger_hband()
            bb_lower = bb_indicator.bollinger_lband()
            
            # Moving Averages
            sma_20 = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            sma_50 = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            ema_12 = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            ema_26 = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            
            # Получаем последние значения
            latest_idx = -1
            
            return TechnicalIndicators(
                rsi=rsi.iloc[latest_idx] if not pd.isna(rsi.iloc[latest_idx]) else None,
                macd=macd.iloc[latest_idx] if not pd.isna(macd.iloc[latest_idx]) else None,
                macd_signal=macd_signal.iloc[latest_idx] if not pd.isna(macd_signal.iloc[latest_idx]) else None,
                bollinger_upper=bb_upper.iloc[latest_idx] if not pd.isna(bb_upper.iloc[latest_idx]) else None,
                bollinger_lower=bb_lower.iloc[latest_idx] if not pd.isna(bb_lower.iloc[latest_idx]) else None,
                sma_20=sma_20.iloc[latest_idx] if not pd.isna(sma_20.iloc[latest_idx]) else None,
                sma_50=sma_50.iloc[latest_idx] if not pd.isna(sma_50.iloc[latest_idx]) else None,
                ema_12=ema_12.iloc[latest_idx] if not pd.isna(ema_12.iloc[latest_idx]) else None,
                ema_26=ema_26.iloc[latest_idx] if not pd.isna(ema_26.iloc[latest_idx]) else None
            )
            
        except Exception as e:
            logger.error(f"Ошибка расчета технических индикаторов: {e}")
            return TechnicalIndicators()
    
    def analyze_market_condition(self, df: pd.DataFrame, 
                               technical_indicators: TechnicalIndicators) -> MarketCondition:
        """Анализ состояния рынка"""
        try:
            if df.empty or len(df) < 20:
                return MarketCondition.SIDEWAYS
            
            # Анализ тренда
            recent_prices = df['close'].tail(20)
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            
            # Анализ волатильности
            volatility = recent_prices.pct_change().std() * 100
            
            # Анализ RSI
            rsi = technical_indicators.rsi
            if rsi is not None:
                if rsi > 70:
                    rsi_signal = "overbought"
                elif rsi < 30:
                    rsi_signal = "oversold"
                else:
                    rsi_signal = "neutral"
            else:
                rsi_signal = "neutral"
            
            # Анализ MACD
            macd = technical_indicators.macd
            macd_signal = technical_indicators.macd_signal
            macd_bullish = (macd is not None and macd_signal is not None and 
                           macd > macd_signal) if macd and macd_signal else False
            
            # Определение состояния рынка
            if volatility > 5.0:
                return MarketCondition.VOLATILE
            elif price_change > 0.05 and macd_bullish and rsi_signal != "overbought":
                return MarketCondition.BULLISH
            elif price_change < -0.05 and not macd_bullish and rsi_signal != "oversold":
                return MarketCondition.BEARISH
            else:
                return MarketCondition.SIDEWAYS
                
        except Exception as e:
            logger.error(f"Ошибка анализа состояния рынка: {e}")
            return MarketCondition.SIDEWAYS
    
    def find_support_resistance_levels(self, df: pd.DataFrame, 
                                     window: int = 20) -> tuple[List[float], List[float]]:
        """Поиск уровней поддержки и сопротивления"""
        try:
            if df.empty or len(df) < window:
                return [], []
            
            highs = df['high'].rolling(window=window).max()
            lows = df['low'].rolling(window=window).min()
            
            # Находим локальные максимумы и минимумы
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(df) - window):
                if df['high'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(df['high'].iloc[i])
                if df['low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(df['low'].iloc[i])
            
            # Убираем дубликаты и сортируем
            resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:5]
            support_levels = sorted(list(set(support_levels)))[:5]
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Ошибка поиска уровней поддержки/сопротивления: {e}")
            return [], []
    
    def calculate_volatility(self, df: pd.DataFrame, window: int = 20) -> float:
        """Расчет волатильности"""
        try:
            if df.empty or len(df) < window:
                return 0.0
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.rolling(window=window).std().iloc[-1] * 100
            return float(volatility) if not pd.isna(volatility) else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета волатильности: {e}")
            return 0.0
    
    async def analyze_market(self, symbol: str = None) -> MarketAnalysis:
        """Полный анализ рынка"""
        try:
            symbol = symbol or settings.trading_symbol
            
            # Получаем исторические данные
            df = self.get_historical_data_bybit(symbol)
            if df is None or df.empty:
                logger.error("Не удалось получить исторические данные")
                return MarketAnalysis(
                    market_condition=MarketCondition.SIDEWAYS,
                    technical_indicators=TechnicalIndicators(),
                    price_trend="unknown",
                    volatility=0.0,
                    recommendation="HOLD",
                    confidence=0.0
                )
            
            # Рассчитываем технические индикаторы
            technical_indicators = self.calculate_technical_indicators(df)
            
            # Анализируем состояние рынка
            market_condition = self.analyze_market_condition(df, technical_indicators)
            
            # Находим уровни поддержки и сопротивления
            support_levels, resistance_levels = self.find_support_resistance_levels(df)
            
            # Рассчитываем волатильность
            volatility = self.calculate_volatility(df)
            
            # Анализируем тренд
            recent_prices = df['close'].tail(10)
            price_trend = "bullish" if recent_prices.iloc[-1] > recent_prices.iloc[0] else "bearish"
            
            # Генерируем рекомендацию
            recommendation = self._generate_recommendation(
                market_condition, technical_indicators, volatility
            )
            
            # Рассчитываем уверенность
            confidence = self._calculate_confidence(
                technical_indicators, market_condition, volatility
            )
            
            return MarketAnalysis(
                market_condition=market_condition,
                technical_indicators=technical_indicators,
                price_trend=price_trend,
                volatility=volatility,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                recommendation=recommendation,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа рынка: {e}")
            return MarketAnalysis(
                market_condition=MarketCondition.SIDEWAYS,
                technical_indicators=TechnicalIndicators(),
                price_trend="unknown",
                volatility=0.0,
                recommendation="HOLD",
                confidence=0.0
            )
    
    def _generate_recommendation(self, market_condition: MarketCondition,
                               technical_indicators: TechnicalIndicators,
                               volatility: float) -> str:
        """Генерация торговой рекомендации"""
        try:
            rsi = technical_indicators.rsi
            macd = technical_indicators.macd
            macd_signal = technical_indicators.macd_signal
            
            # Базовые условия
            rsi_oversold = rsi is not None and rsi < 30
            rsi_overbought = rsi is not None and rsi > 70
            macd_bullish = (macd is not None and macd_signal is not None and 
                           macd > macd_signal)
            
            if market_condition == MarketCondition.BULLISH and not rsi_overbought and macd_bullish:
                return "BUY"
            elif market_condition == MarketCondition.BEARISH and not rsi_oversold and not macd_bullish:
                return "SELL"
            elif rsi_oversold and macd_bullish:
                return "BUY"
            elif rsi_overbought and not macd_bullish:
                return "SELL"
            elif volatility > 8.0:
                return "HOLD"  # Высокая волатильность - держим позицию
            else:
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендации: {e}")
            return "HOLD"
    
    def _calculate_confidence(self, technical_indicators: TechnicalIndicators,
                            market_condition: MarketCondition, volatility: float) -> float:
        """Расчет уверенности в анализе"""
        try:
            confidence = 0.5  # Базовая уверенность
            
            # RSI вносит вклад
            rsi = technical_indicators.rsi
            if rsi is not None:
                if 30 <= rsi <= 70:
                    confidence += 0.1  # Нейтральная зона RSI
                elif rsi < 30 or rsi > 70:
                    confidence += 0.2  # Экстремальные значения RSI
            
            # MACD вносит вклад
            macd = technical_indicators.macd
            macd_signal = technical_indicators.macd_signal
            if macd is not None and macd_signal is not None:
                if abs(macd - macd_signal) > 0.1:  # Сильный сигнал MACD
                    confidence += 0.2
            
            # Состояние рынка
            if market_condition in [MarketCondition.BULLISH, MarketCondition.BEARISH]:
                confidence += 0.1
            
            # Волатильность снижает уверенность
            if volatility > 5.0:
                confidence -= 0.1
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Ошибка расчета уверенности: {e}")
            return 0.5