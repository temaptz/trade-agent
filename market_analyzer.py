"""
Анализатор рыночных данных и технических индикаторов
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger
import asyncio

class MarketAnalyzer:
    def __init__(self):
        self.indicators_cache = {}
        self.analysis_cache = {}
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет технических индикаторов"""
        try:
            if df.empty or len(df) < 50:
                return {}
            
            # Базовые индикаторы
            indicators = {}
            
            # Moving Averages
            indicators['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            indicators['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            indicators['sma_200'] = ta.trend.sma_indicator(df['close'], window=200)
            indicators['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
            indicators['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            indicators['macd'] = macd.macd()
            indicators['macd_signal'] = macd.macd_signal()
            indicators['macd_histogram'] = macd.macd_diff()
            
            # RSI
            indicators['rsi'] = ta.momentum.rsi(df['close'], window=14)
            indicators['rsi_30'] = ta.momentum.rsi(df['close'], window=30)
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'])
            indicators['bb_upper'] = bb.bollinger_hband()
            indicators['bb_middle'] = bb.bollinger_mavg()
            indicators['bb_lower'] = bb.bollinger_lband()
            indicators['bb_width'] = bb.bollinger_wband()
            indicators['bb_percent'] = bb.bollinger_pband()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            indicators['stoch_k'] = stoch.stoch()
            indicators['stoch_d'] = stoch.stoch_signal()
            
            # Williams %R
            indicators['williams_r'] = ta.momentum.williams_r(df['high'], df['low'], df['close'])
            
            # ATR
            indicators['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
            
            # ADX
            indicators['adx'] = ta.trend.adx(df['high'], df['low'], df['close'])
            indicators['adx_pos'] = ta.trend.adx_pos(df['high'], df['low'], df['close'])
            indicators['adx_neg'] = ta.trend.adx_neg(df['high'], df['low'], df['close'])
            
            # Volume indicators
            indicators['volume_sma'] = ta.volume.volume_sma(df['close'], df['volume'])
            indicators['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
            indicators['vwap'] = ta.volume.volume_weighted_average_price(df['high'], df['low'], df['close'], df['volume'])
            
            # Ichimoku
            ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'])
            indicators['ichimoku_a'] = ichimoku.ichimoku_a()
            indicators['ichimoku_b'] = ichimoku.ichimoku_b()
            indicators['ichimoku_base'] = ichimoku.ichimoku_base_line()
            indicators['ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
            
            # Parabolic SAR
            indicators['psar'] = ta.trend.psar_up(df['high'], df['low'], df['close'])
            
            # CCI
            indicators['cci'] = ta.trend.cci(df['high'], df['low'], df['close'])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return {}
    
    def analyze_trend(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Анализ тренда"""
        try:
            if df.empty or not indicators:
                return {"trend": "unknown", "strength": 0}
            
            current_price = df['close'].iloc[-1]
            trend_signals = []
            strength = 0
            
            # SMA анализ
            if 'sma_20' in indicators and 'sma_50' in indicators:
                sma_20 = indicators['sma_20'].iloc[-1]
                sma_50 = indicators['sma_50'].iloc[-1]
                
                if sma_20 > sma_50 and current_price > sma_20:
                    trend_signals.append("bullish_sma")
                    strength += 1
                elif sma_20 < sma_50 and current_price < sma_20:
                    trend_signals.append("bearish_sma")
                    strength -= 1
            
            # MACD анализ
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd'].iloc[-1]
                macd_signal = indicators['macd_signal'].iloc[-1]
                
                if macd > macd_signal:
                    trend_signals.append("bullish_macd")
                    strength += 1
                elif macd < macd_signal:
                    trend_signals.append("bearish_macd")
                    strength -= 1
            
            # RSI анализ
            if 'rsi' in indicators:
                rsi = indicators['rsi'].iloc[-1]
                if rsi > 70:
                    trend_signals.append("overbought")
                    strength -= 0.5
                elif rsi < 30:
                    trend_signals.append("oversold")
                    strength += 0.5
            
            # Bollinger Bands
            if 'bb_upper' in indicators and 'bb_lower' in indicators:
                bb_upper = indicators['bb_upper'].iloc[-1]
                bb_lower = indicators['bb_lower'].iloc[-1]
                
                if current_price > bb_upper:
                    trend_signals.append("above_bb_upper")
                    strength -= 0.3
                elif current_price < bb_lower:
                    trend_signals.append("below_bb_lower")
                    strength += 0.3
            
            # Определение тренда
            if strength > 1:
                trend = "bullish"
            elif strength < -1:
                trend = "bearish"
            else:
                trend = "sideways"
            
            return {
                "trend": trend,
                "strength": abs(strength),
                "signals": trend_signals
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа тренда: {e}")
            return {"trend": "unknown", "strength": 0}
    
    def analyze_volatility(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Анализ волатильности"""
        try:
            if df.empty or 'atr' not in indicators:
                return {"volatility": "unknown", "level": 0}
            
            atr = indicators['atr'].iloc[-1]
            current_price = df['close'].iloc[-1]
            atr_percent = (atr / current_price) * 100
            
            # Bollinger Bands width
            bb_width = 0
            if 'bb_width' in indicators:
                bb_width = indicators['bb_width'].iloc[-1]
            
            # Определение уровня волатильности
            if atr_percent > 3:
                volatility = "high"
                level = 3
            elif atr_percent > 1.5:
                volatility = "medium"
                level = 2
            else:
                volatility = "low"
                level = 1
            
            return {
                "volatility": volatility,
                "level": level,
                "atr_percent": atr_percent,
                "bb_width": bb_width
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа волатильности: {e}")
            return {"volatility": "unknown", "level": 0}
    
    def analyze_volume(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Анализ объема"""
        try:
            if df.empty:
                return {"volume_trend": "unknown", "anomaly": False}
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Объемный анализ
            volume_trend = "normal"
            if volume_ratio > 2:
                volume_trend = "high"
            elif volume_ratio < 0.5:
                volume_trend = "low"
            
            # Аномалии объема
            anomaly = volume_ratio > 3 or volume_ratio < 0.2
            
            return {
                "volume_trend": volume_trend,
                "anomaly": anomaly,
                "volume_ratio": volume_ratio,
                "current_volume": current_volume,
                "avg_volume": avg_volume
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа объема: {e}")
            return {"volume_trend": "unknown", "anomaly": False}
    
    def find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Поиск уровней поддержки и сопротивления"""
        try:
            if df.empty or len(df) < 20:
                return {"support": None, "resistance": None}
            
            # Простой алгоритм поиска локальных экстремумов
            highs = df['high'].rolling(window=5, center=True).max()
            lows = df['low'].rolling(window=5, center=True).min()
            
            # Находим пики и впадины
            peaks = df[df['high'] == highs]['high'].tail(5)
            troughs = df[df['low'] == lows]['low'].tail(5)
            
            # Берем ближайшие уровни
            current_price = df['close'].iloc[-1]
            
            support = troughs[troughs < current_price].max() if not troughs[troughs < current_price].empty else None
            resistance = peaks[peaks > current_price].min() if not peaks[peaks > current_price].empty else None
            
            return {
                "support": float(support) if support is not None else None,
                "resistance": float(resistance) if resistance is not None else None,
                "peaks": peaks.tolist(),
                "troughs": troughs.tolist()
            }
            
        except Exception as e:
            logger.error(f"Ошибка поиска уровней поддержки/сопротивления: {e}")
            return {"support": None, "resistance": None}
    
    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict:
        """Расчет метрик риска"""
        try:
            if df.empty or len(df) < 20:
                return {}
            
            # Расчет доходности
            returns = df['close'].pct_change().dropna()
            
            # Волатильность
            volatility = returns.std() * np.sqrt(252)  # Годовая волатильность
            
            # VaR (Value at Risk)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # Максимальная просадка
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Sharpe Ratio (упрощенный)
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            
            return {
                "volatility": volatility,
                "var_95": var_95,
                "var_99": var_99,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "current_return": returns.iloc[-1] if not returns.empty else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик риска: {e}")
            return {}
    
    async def comprehensive_analysis(self, df: pd.DataFrame) -> Dict:
        """Комплексный анализ рынка"""
        try:
            if df.empty:
                return {"error": "No data available"}
            
            # Расчет индикаторов
            indicators = self.calculate_technical_indicators(df)
            
            # Анализ тренда
            trend_analysis = self.analyze_trend(df, indicators)
            
            # Анализ волатильности
            volatility_analysis = self.analyze_volatility(df, indicators)
            
            # Анализ объема
            volume_analysis = self.analyze_volume(df, indicators)
            
            # Уровни поддержки/сопротивления
            support_resistance = self.find_support_resistance(df)
            
            # Метрики риска
            risk_metrics = self.calculate_risk_metrics(df)
            
            # Текущие значения
            current_price = df['close'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            
            # Последние значения индикаторов
            latest_indicators = {}
            for key, values in indicators.items():
                if not values.empty:
                    latest_indicators[key] = float(values.iloc[-1])
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "current_volume": current_volume,
                "trend": trend_analysis,
                "volatility": volatility_analysis,
                "volume": volume_analysis,
                "support_resistance": support_resistance,
                "risk_metrics": risk_metrics,
                "indicators": latest_indicators,
                "data_points": len(df)
            }
            
            # Кэширование
            self.analysis_cache[df['timestamp'].iloc[-1]] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка комплексного анализа: {e}")
            return {"error": str(e)}