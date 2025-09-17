"""
Модуль для анализа рынка и исторических данных
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from alpha_vantage.timeseries import TimeSeries
import ta
from loguru import logger
from config import settings

class MarketAnalyzer:
    """Анализатор рынка с использованием Alpha Vantage API"""
    
    def __init__(self):
        """Инициализация анализатора"""
        self.crypto_api = CryptoCurrencies(key=settings.alpha_vantage_api_key)
        self.ts_api = TimeSeries(key=settings.alpha_vantage_api_key)
        logger.info("MarketAnalyzer инициализирован")
    
    def get_historical_data(self, symbol: str = "BTC", market: str = "USD", 
                          outputsize: str = "compact") -> Optional[pd.DataFrame]:
        """Получить исторические данные криптовалюты"""
        try:
            data, meta_data = self.crypto_api.get_digital_currency_daily(
                symbol=symbol, 
                market=market
            )
            
            if data is not None:
                df = pd.DataFrame(data).T
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Конвертируем в числовые типы
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.info(f"Получено {len(df)} дней исторических данных для {symbol}")
                return df
            else:
                logger.error("Не удалось получить исторические данные")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении исторических данных: {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Рассчитать технические индикаторы"""
        try:
            if df.empty:
                return df
            
            # RSI (Relative Strength Index)
            df['rsi'] = ta.momentum.RSIIndicator(df['4b. close (USD)']).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['4b. close (USD)'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['4b. close (USD)'])
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # SMA (Simple Moving Average)
            df['sma_20'] = ta.trend.SMAIndicator(df['4b. close (USD)'], window=20).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['4b. close (USD)'], window=50).sma_indicator()
            df['sma_200'] = ta.trend.SMAIndicator(df['4b. close (USD)'], window=200).sma_indicator()
            
            # EMA (Exponential Moving Average)
            df['ema_12'] = ta.trend.EMAIndicator(df['4b. close (USD)'], window=12).ema_indicator()
            df['ema_26'] = ta.trend.EMAIndicator(df['4b. close (USD)'], window=26).ema_indicator()
            
            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(
                df['2b. high (USD)'], 
                df['3b. low (USD)'], 
                df['4b. close (USD)']
            )
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(
                df['2b. high (USD)'], 
                df['3b. low (USD)'], 
                df['4b. close (USD)']
            ).williams_r()
            
            # Average True Range (ATR)
            df['atr'] = ta.volatility.AverageTrueRange(
                df['2b. high (USD)'], 
                df['3b. low (USD)'], 
                df['4b. close (USD)']
            ).average_true_range()
            
            # Volume indicators
            df['volume_sma'] = ta.volume.VolumeSMAIndicator(
                df['4b. close (USD)'], 
                df['5. volume']
            ).volume_sma()
            
            logger.info("Технические индикаторы рассчитаны")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка при расчете технических индикаторов: {e}")
            return df
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict[str, any]:
        """Анализ тренда на основе технических индикаторов"""
        try:
            if df.empty or len(df) < 50:
                return {"trend": "unknown", "strength": 0, "confidence": 0}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Анализ тренда по скользящим средним
            sma_trend = 0
            if latest['sma_20'] > latest['sma_50'] > latest['sma_200']:
                sma_trend = 1  # Восходящий тренд
            elif latest['sma_20'] < latest['sma_50'] < latest['sma_200']:
                sma_trend = -1  # Нисходящий тренд
            
            # Анализ MACD
            macd_trend = 0
            if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                macd_trend = 1  # Бычий сигнал
            elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                macd_trend = -1  # Медвежий сигнал
            
            # Анализ RSI
            rsi_signal = 0
            if latest['rsi'] < 30:
                rsi_signal = 1  # Перепроданность - сигнал к покупке
            elif latest['rsi'] > 70:
                rsi_signal = -1  # Перекупленность - сигнал к продаже
            
            # Анализ Bollinger Bands
            bb_signal = 0
            if latest['4b. close (USD)'] < latest['bb_lower']:
                bb_signal = 1  # Цена ниже нижней полосы - сигнал к покупке
            elif latest['4b. close (USD)'] > latest['bb_upper']:
                bb_signal = -1  # Цена выше верхней полосы - сигнал к продаже
            
            # Общий анализ тренда
            trend_score = sma_trend + macd_trend + rsi_signal + bb_signal
            
            if trend_score > 1:
                trend = "bullish"
                strength = min(abs(trend_score) / 4, 1.0)
            elif trend_score < -1:
                trend = "bearish"
                strength = min(abs(trend_score) / 4, 1.0)
            else:
                trend = "sideways"
                strength = 0.3
            
            # Уровень уверенности
            confidence = min(strength + 0.3, 1.0)
            
            result = {
                "trend": trend,
                "strength": strength,
                "confidence": confidence,
                "indicators": {
                    "sma_trend": sma_trend,
                    "macd_trend": macd_trend,
                    "rsi_signal": rsi_signal,
                    "bb_signal": bb_signal,
                    "rsi_value": latest['rsi'],
                    "macd_value": latest['macd'],
                    "price_vs_sma20": (latest['4b. close (USD)'] - latest['sma_20']) / latest['sma_20'] * 100
                }
            }
            
            logger.info(f"Анализ тренда: {trend} (сила: {strength:.2f}, уверенность: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе тренда: {e}")
            return {"trend": "unknown", "strength": 0, "confidence": 0}
    
    def calculate_volatility(self, df: pd.DataFrame, window: int = 20) -> float:
        """Рассчитать волатильность"""
        try:
            if len(df) < window:
                return 0.0
            
            returns = df['4b. close (USD)'].pct_change().dropna()
            volatility = returns.rolling(window=window).std().iloc[-1] * np.sqrt(252)  # Годовая волатильность
            
            logger.info(f"Волатильность за {window} дней: {volatility:.4f}")
            return volatility
            
        except Exception as e:
            logger.error(f"Ошибка при расчете волатильности: {e}")
            return 0.0
    
    def get_support_resistance_levels(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Найти уровни поддержки и сопротивления"""
        try:
            if len(df) < window:
                return {"support": 0, "resistance": 0}
            
            recent_data = df.tail(window)
            
            # Находим локальные минимумы и максимумы
            highs = recent_data['2b. high (USD)'].rolling(window=3, center=True).max()
            lows = recent_data['3b. low (USD)'].rolling(window=3, center=True).min()
            
            resistance = highs.max()
            support = lows.min()
            
            logger.info(f"Уровни поддержки: {support:.2f}, сопротивления: {resistance:.2f}")
            return {"support": support, "resistance": resistance}
            
        except Exception as e:
            logger.error(f"Ошибка при поиске уровней поддержки/сопротивления: {e}")
            return {"support": 0, "resistance": 0}
    
    def get_market_summary(self) -> Dict[str, any]:
        """Получить общую сводку по рынку"""
        try:
            # Получаем исторические данные
            df = self.get_historical_data()
            if df is None or df.empty:
                return {"error": "Не удалось получить данные"}
            
            # Рассчитываем индикаторы
            df = self.calculate_technical_indicators(df)
            
            # Анализируем тренд
            trend_analysis = self.analyze_trend(df)
            
            # Рассчитываем волатильность
            volatility = self.calculate_volatility(df)
            
            # Находим уровни поддержки/сопротивления
            levels = self.get_support_resistance_levels(df)
            
            # Текущая цена
            current_price = df['4b. close (USD)'].iloc[-1]
            
            summary = {
                "current_price": current_price,
                "trend_analysis": trend_analysis,
                "volatility": volatility,
                "support_resistance": levels,
                "data_points": len(df),
                "last_update": df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info("Сводка по рынку подготовлена")
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка при создании сводки по рынку: {e}")
            return {"error": str(e)}