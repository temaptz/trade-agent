"""
Модуль управления рисками и торговой логики
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import numpy as np
from config import settings

@dataclass
class RiskLimits:
    """Лимиты риска"""
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    max_leverage: float
    stop_loss_percent: float
    take_profit_percent: float

@dataclass
class Position:
    """Позиция"""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    timestamp: datetime

class RiskManager:
    def __init__(self):
        self.risk_limits = RiskLimits(
            max_position_size=settings.trade_amount * 10,  # Максимум 10 позиций
            max_daily_loss=1000.0,  # Максимальная дневная потеря
            max_drawdown=0.05,  # 5% максимальная просадка
            max_leverage=1.0,  # Без плеча
            stop_loss_percent=settings.stop_loss_percent,
            take_profit_percent=settings.take_profit_percent
        )
        
        self.daily_pnl = 0.0
        self.max_equity = 0.0
        self.positions_history = []
        
    def calculate_position_size(self, account_balance: float, 
                              risk_percent: float = None) -> float:
        """Расчет размера позиции"""
        try:
            if risk_percent is None:
                risk_percent = settings.max_risk_percent / 100.0
            
            # Размер позиции на основе риска
            risk_amount = account_balance * risk_percent
            
            # Ограничение максимальным размером
            max_size = min(risk_amount, self.risk_limits.max_position_size)
            
            # Минимальный размер
            min_size = settings.trade_amount
            
            return max(min_size, max_size)
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return settings.trade_amount
    
    def check_risk_limits(self, positions: List[Dict], 
                         account_balance: float) -> Tuple[bool, str]:
        """Проверка лимитов риска"""
        try:
            # Проверка общего размера позиций
            total_exposure = sum(float(pos.get('size', 0)) for pos in positions)
            if total_exposure > self.risk_limits.max_position_size:
                return False, f"Превышен лимит размера позиций: {total_exposure}"
            
            # Проверка дневной потери
            if self.daily_pnl < -self.risk_limits.max_daily_loss:
                return False, f"Превышен лимит дневной потери: {self.daily_pnl}"
            
            # Проверка просадки
            current_equity = account_balance + sum(
                float(pos.get('unrealisedPnl', 0)) for pos in positions
            )
            
            if current_equity > self.max_equity:
                self.max_equity = current_equity
            
            drawdown = (self.max_equity - current_equity) / self.max_equity
            if drawdown > self.risk_limits.max_drawdown:
                return False, f"Превышена максимальная просадка: {drawdown:.2%}"
            
            return True, "Лимиты соблюдены"
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов: {e}")
            return False, f"Ошибка проверки: {e}"
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Расчет уровня стоп-лосса"""
        try:
            stop_loss_percent = self.risk_limits.stop_loss_percent / 100.0
            
            if side == "Buy":
                return entry_price * (1 - stop_loss_percent)
            else:
                return entry_price * (1 + stop_loss_percent)
                
        except Exception as e:
            logger.error(f"Ошибка расчета стоп-лосса: {e}")
            return entry_price
    
    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Расчет уровня тейк-профита"""
        try:
            take_profit_percent = self.risk_limits.take_profit_percent / 100.0
            
            if side == "Buy":
                return entry_price * (1 + take_profit_percent)
            else:
                return entry_price * (1 - take_profit_percent)
                
        except Exception as e:
            logger.error(f"Ошибка расчета тейк-профита: {e}")
            return entry_price
    
    def should_close_position(self, position: Dict, current_price: float) -> Tuple[bool, str]:
        """Проверка необходимости закрытия позиции"""
        try:
            side = position.get('side', '')
            entry_price = float(position.get('avgPrice', 0))
            size = float(position.get('size', 0))
            
            if not entry_price or not size:
                return False, "Некорректные данные позиции"
            
            # Расчет PnL
            if side == "Buy":
                pnl_percent = (current_price - entry_price) / entry_price
            else:
                pnl_percent = (entry_price - current_price) / entry_price
            
            # Проверка стоп-лосса
            stop_loss_percent = -self.risk_limits.stop_loss_percent / 100.0
            if pnl_percent <= stop_loss_percent:
                return True, f"Стоп-лосс: {pnl_percent:.2%}"
            
            # Проверка тейк-профита
            take_profit_percent = self.risk_limits.take_profit_percent / 100.0
            if pnl_percent >= take_profit_percent:
                return True, f"Тейк-профит: {pnl_percent:.2%}"
            
            return False, "Позиция в пределах лимитов"
            
        except Exception as e:
            logger.error(f"Ошибка проверки закрытия позиции: {e}")
            return False, f"Ошибка: {e}"
    
    def update_daily_pnl(self, pnl: float):
        """Обновление дневной прибыли/убытка"""
        self.daily_pnl += pnl
        
        # Сброс в начале нового дня
        if datetime.now().hour == 0 and datetime.now().minute == 0:
            self.daily_pnl = 0.0
    
    def get_risk_metrics(self, positions: List[Dict], 
                        account_balance: float) -> Dict:
        """Получение метрик риска"""
        try:
            total_exposure = sum(float(pos.get('size', 0)) for pos in positions)
            total_pnl = sum(float(pos.get('unrealisedPnl', 0)) for pos in positions)
            
            current_equity = account_balance + total_pnl
            
            # Расчет просадки
            drawdown = 0.0
            if self.max_equity > 0:
                drawdown = (self.max_equity - current_equity) / self.max_equity
            
            # Расчет риска на позицию
            risk_per_position = 0.0
            if positions:
                avg_position_size = total_exposure / len(positions)
                risk_per_position = avg_position_size / account_balance if account_balance > 0 else 0
            
            return {
                "total_exposure": total_exposure,
                "total_pnl": total_pnl,
                "current_equity": current_equity,
                "daily_pnl": self.daily_pnl,
                "max_equity": self.max_equity,
                "drawdown": drawdown,
                "risk_per_position": risk_per_position,
                "position_count": len(positions),
                "risk_utilization": total_exposure / self.risk_limits.max_position_size
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик риска: {e}")
            return {}

class TradingStrategy:
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.last_signal_time = None
        self.signal_cooldown = 300  # 5 минут между сигналами
        
    def should_trade(self, market_analysis: Dict, news_sentiment: Dict, 
                    ai_analysis: Dict) -> Tuple[bool, str]:
        """Определение возможности торговли"""
        try:
            # Проверка кулдауна
            if self.last_signal_time:
                time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
                if time_since_last < self.signal_cooldown:
                    return False, f"Кулдаун: {self.signal_cooldown - time_since_last:.0f}с"
            
            # Проверка качества сигналов
            confidence_score = 0.0
            
            # Анализ тренда
            trend = market_analysis.get('trend', {})
            if trend.get('trend') == 'bullish':
                confidence_score += 0.3
            elif trend.get('trend') == 'bearish':
                confidence_score -= 0.3
            
            # Анализ новостей
            sentiment = news_sentiment.get('sentiment', 'neutral')
            if sentiment == 'positive':
                confidence_score += 0.2
            elif sentiment == 'negative':
                confidence_score -= 0.2
            
            # ИИ анализ
            ai_data = ai_analysis.get('ai_analysis', {})
            ai_confidence = ai_data.get('confidence', 0.5)
            confidence_score += (ai_confidence - 0.5) * 0.5
            
            # Минимальный порог уверенности
            min_confidence = 0.6
            if abs(confidence_score) < min_confidence:
                return False, f"Низкая уверенность: {abs(confidence_score):.2f}"
            
            # Определение направления
            if confidence_score > 0:
                action = "BUY"
            else:
                action = "SELL"
            
            self.last_signal_time = datetime.now()
            
            return True, f"{action} с уверенностью {abs(confidence_score):.2f}"
            
        except Exception as e:
            logger.error(f"Ошибка определения торговли: {e}")
            return False, f"Ошибка: {e}"
    
    def calculate_entry_price(self, current_price: float, 
                            market_analysis: Dict) -> float:
        """Расчет цены входа"""
        try:
            # Простая логика - можно расширить
            return current_price
            
        except Exception as e:
            logger.error(f"Ошибка расчета цены входа: {e}")
            return current_price
    
    def should_exit_position(self, position: Dict, market_analysis: Dict, 
                           current_price: float) -> Tuple[bool, str]:
        """Определение необходимости выхода из позиции"""
        try:
            # Проверка стоп-лосса и тейк-профита
            should_close, reason = self.risk_manager.should_close_position(
                position, current_price
            )
            
            if should_close:
                return True, reason
            
            # Анализ изменения тренда
            trend = market_analysis.get('trend', {})
            current_trend = trend.get('trend', 'neutral')
            position_side = position.get('side', '')
            
            # Если тренд изменился против позиции
            if (position_side == 'Buy' and current_trend == 'bearish') or \
               (position_side == 'Sell' and current_trend == 'bullish'):
                return True, f"Изменение тренда: {current_trend}"
            
            return False, "Позиция в порядке"
            
        except Exception as e:
            logger.error(f"Ошибка определения выхода: {e}")
            return False, f"Ошибка: {e}"
    
    def get_position_sizing(self, account_balance: float, 
                          confidence: float) -> float:
        """Расчет размера позиции на основе уверенности"""
        try:
            # Базовый размер
            base_size = self.risk_manager.calculate_position_size(account_balance)
            
            # Корректировка на уверенность
            confidence_multiplier = min(confidence * 2, 1.0)  # Максимум 1.0
            
            return base_size * confidence_multiplier
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return settings.trade_amount

class PortfolioManager:
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.positions = []
        self.performance_history = []
        
    async def update_positions(self, positions: List[Dict]):
        """Обновление позиций"""
        try:
            self.positions = positions
            
            # Расчет производительности
            total_pnl = sum(float(pos.get('unrealisedPnl', 0)) for pos in positions)
            
            performance_record = {
                "timestamp": datetime.now().isoformat(),
                "total_pnl": total_pnl,
                "position_count": len(positions),
                "positions": positions
            }
            
            self.performance_history.append(performance_record)
            
            # Ограничение истории
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-500:]
            
            logger.info(f"Портфель обновлен: {len(positions)} позиций, PnL: {total_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления портфеля: {e}")
    
    def get_portfolio_summary(self) -> Dict:
        """Получение сводки портфеля"""
        try:
            if not self.positions:
                return {"error": "Нет позиций"}
            
            total_pnl = sum(float(pos.get('unrealisedPnl', 0)) for pos in self.positions)
            total_exposure = sum(float(pos.get('size', 0)) for pos in self.positions)
            
            # Группировка по сторонам
            buy_positions = [pos for pos in self.positions if pos.get('side') == 'Buy']
            sell_positions = [pos for pos in self.positions if pos.get('side') == 'Sell']
            
            return {
                "total_positions": len(self.positions),
                "buy_positions": len(buy_positions),
                "sell_positions": len(sell_positions),
                "total_pnl": total_pnl,
                "total_exposure": total_exposure,
                "avg_pnl_per_position": total_pnl / len(self.positions) if self.positions else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки портфеля: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict:
        """Получение метрик производительности"""
        try:
            if len(self.performance_history) < 2:
                return {"error": "Недостаточно данных"}
            
            # Расчет доходности
            pnl_values = [record["total_pnl"] for record in self.performance_history]
            
            # Статистика
            total_return = pnl_values[-1] - pnl_values[0]
            max_pnl = max(pnl_values)
            min_pnl = min(pnl_values)
            max_drawdown = max_pnl - min_pnl
            
            # Волатильность
            returns = np.diff(pnl_values)
            volatility = np.std(returns) if len(returns) > 1 else 0
            
            return {
                "total_return": total_return,
                "max_pnl": max_pnl,
                "min_pnl": min_pnl,
                "max_drawdown": max_drawdown,
                "volatility": volatility,
                "data_points": len(self.performance_history)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик производительности: {e}")
            return {"error": str(e)}