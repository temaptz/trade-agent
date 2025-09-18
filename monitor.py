"""
Модуль мониторинга и логирования
"""
import asyncio
import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from loguru import logger
import aiofiles
from pathlib import Path

@dataclass
class TradingEvent:
    """Событие торговли"""
    timestamp: str
    event_type: str
    symbol: str
    side: str
    size: float
    price: float
    pnl: float
    reason: str
    confidence: float

@dataclass
class MarketAlert:
    """Рыночное оповещение"""
    timestamp: str
    alert_type: str
    symbol: str
    message: str
    severity: str
    data: Dict

class DatabaseManager:
    def __init__(self, db_path: str = "trading_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица событий торговли
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    symbol TEXT,
                    side TEXT,
                    size REAL,
                    price REAL,
                    pnl REAL,
                    reason TEXT,
                    confidence REAL
                )
            ''')
            
            # Таблица рыночных данных
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    price REAL,
                    volume REAL,
                    market_analysis TEXT,
                    news_sentiment TEXT
                )
            ''')
            
            # Таблица оповещений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    alert_type TEXT,
                    symbol TEXT,
                    message TEXT,
                    severity TEXT,
                    data TEXT
                )
            ''')
            
            # Таблица производительности
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    total_pnl REAL,
                    position_count INTEGER,
                    account_balance REAL,
                    risk_metrics TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
    
    def save_trading_event(self, event: TradingEvent):
        """Сохранение события торговли"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_events 
                (timestamp, event_type, symbol, side, size, price, pnl, reason, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.timestamp, event.event_type, event.symbol, event.side,
                event.size, event.price, event.pnl, event.reason, event.confidence
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения события: {e}")
    
    def save_market_data(self, symbol: str, price: float, volume: float,
                        market_analysis: Dict, news_sentiment: Dict):
        """Сохранение рыночных данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_data 
                (timestamp, symbol, price, volume, market_analysis, news_sentiment)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(), symbol, price, volume,
                json.dumps(market_analysis), json.dumps(news_sentiment)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения рыночных данных: {e}")
    
    def save_alert(self, alert: MarketAlert):
        """Сохранение оповещения"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts 
                (timestamp, alert_type, symbol, message, severity, data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert.timestamp, alert.alert_type, alert.symbol,
                alert.message, alert.severity, json.dumps(alert.data)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения оповещения: {e}")
    
    def get_trading_history(self, limit: int = 100) -> List[Dict]:
        """Получение истории торговли"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trading_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
            return []
    
    def get_performance_data(self, days: int = 7) -> List[Dict]:
        """Получение данных производительности"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT * FROM performance 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (cutoff_date,))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка получения данных производительности: {e}")
            return []

class AlertManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.alert_rules = self._init_alert_rules()
    
    def _init_alert_rules(self) -> Dict:
        """Инициализация правил оповещений"""
        return {
            "price_change": {
                "threshold": 0.05,  # 5% изменение цены
                "severity": "medium"
            },
            "volume_spike": {
                "threshold": 2.0,  # 2x средний объем
                "severity": "high"
            },
            "risk_limit": {
                "threshold": 0.8,  # 80% от лимита риска
                "severity": "high"
            },
            "news_impact": {
                "threshold": 0.7,  # Высокое влияние новостей
                "severity": "medium"
            }
        }
    
    def check_price_alert(self, current_price: float, previous_price: float) -> Optional[MarketAlert]:
        """Проверка оповещения об изменении цены"""
        try:
            if not previous_price:
                return None
            
            change_percent = abs(current_price - previous_price) / previous_price
            threshold = self.alert_rules["price_change"]["threshold"]
            
            if change_percent >= threshold:
                alert = MarketAlert(
                    timestamp=datetime.now().isoformat(),
                    alert_type="price_change",
                    symbol="BTCUSDT",
                    message=f"Цена изменилась на {change_percent:.2%}",
                    severity=self.alert_rules["price_change"]["severity"],
                    data={
                        "current_price": current_price,
                        "previous_price": previous_price,
                        "change_percent": change_percent
                    }
                )
                
                self.db_manager.save_alert(alert)
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка проверки оповещения цены: {e}")
            return None
    
    def check_volume_alert(self, current_volume: float, avg_volume: float) -> Optional[MarketAlert]:
        """Проверка оповещения об объеме"""
        try:
            if not avg_volume:
                return None
            
            volume_ratio = current_volume / avg_volume
            threshold = self.alert_rules["volume_spike"]["threshold"]
            
            if volume_ratio >= threshold:
                alert = MarketAlert(
                    timestamp=datetime.now().isoformat(),
                    alert_type="volume_spike",
                    symbol="BTCUSDT",
                    message=f"Объем превысил средний в {volume_ratio:.1f} раз",
                    severity=self.alert_rules["volume_spike"]["severity"],
                    data={
                        "current_volume": current_volume,
                        "avg_volume": avg_volume,
                        "volume_ratio": volume_ratio
                    }
                )
                
                self.db_manager.save_alert(alert)
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка проверки оповещения объема: {e}")
            return None
    
    def check_risk_alert(self, risk_metrics: Dict) -> Optional[MarketAlert]:
        """Проверка оповещения о рисках"""
        try:
            risk_utilization = risk_metrics.get("risk_utilization", 0)
            threshold = self.alert_rules["risk_limit"]["threshold"]
            
            if risk_utilization >= threshold:
                alert = MarketAlert(
                    timestamp=datetime.now().isoformat(),
                    alert_type="risk_limit",
                    symbol="BTCUSDT",
                    message=f"Использование риска: {risk_utilization:.1%}",
                    severity=self.alert_rules["risk_limit"]["severity"],
                    data=risk_metrics
                )
                
                self.db_manager.save_alert(alert)
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка проверки оповещения рисков: {e}")
            return None

class PerformanceMonitor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.start_time = datetime.now()
        self.initial_balance = 0.0
        self.peak_balance = 0.0
        
    def update_performance(self, total_pnl: float, position_count: int, 
                          account_balance: float, risk_metrics: Dict):
        """Обновление метрик производительности"""
        try:
            # Обновление пикового баланса
            if account_balance > self.peak_balance:
                self.peak_balance = account_balance
            
            # Сохранение в БД
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance 
                (timestamp, total_pnl, position_count, account_balance, risk_metrics)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(), total_pnl, position_count,
                account_balance, json.dumps(risk_metrics)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка обновления производительности: {e}")
    
    def get_performance_summary(self) -> Dict:
        """Получение сводки производительности"""
        try:
            performance_data = self.db_manager.get_performance_data(days=7)
            
            if not performance_data:
                return {"error": "Нет данных о производительности"}
            
            # Расчет метрик
            total_return = 0.0
            if self.initial_balance > 0:
                latest_balance = performance_data[-1].get('account_balance', 0)
                total_return = (latest_balance - self.initial_balance) / self.initial_balance
            
            # Максимальная просадка
            balances = [record.get('account_balance', 0) for record in performance_data]
            peak = max(balances) if balances else 0
            trough = min(balances) if balances else 0
            max_drawdown = (peak - trough) / peak if peak > 0 else 0
            
            # Волатильность
            pnl_values = [record.get('total_pnl', 0) for record in performance_data]
            volatility = 0.0
            if len(pnl_values) > 1:
                returns = [pnl_values[i] - pnl_values[i-1] for i in range(1, len(pnl_values))]
                volatility = np.std(returns) if returns else 0
            
            return {
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "volatility": volatility,
                "peak_balance": self.peak_balance,
                "current_balance": balances[-1] if balances else 0,
                "trading_days": len(performance_data),
                "avg_daily_pnl": sum(pnl_values) / len(pnl_values) if pnl_values else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки производительности: {e}")
            return {"error": str(e)}

class LogManager:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Настройка логирования
        logger.remove()
        logger.add(
            self.log_dir / "trading_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        # Отдельный лог для ошибок
        logger.add(
            self.log_dir / "errors_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def log_trading_event(self, event: TradingEvent):
        """Логирование торгового события"""
        try:
            logger.info(f"Торговое событие: {event.event_type} {event.symbol} "
                       f"{event.side} {event.size} @ {event.price} "
                       f"PnL: {event.pnl} Причина: {event.reason}")
            
        except Exception as e:
            logger.error(f"Ошибка логирования события: {e}")
    
    def log_market_analysis(self, analysis: Dict):
        """Логирование анализа рынка"""
        try:
            trend = analysis.get('trend', {}).get('trend', 'unknown')
            price = analysis.get('current_price', 0)
            
            logger.info(f"Анализ рынка: Тренд {trend}, Цена ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Ошибка логирования анализа: {e}")
    
    def log_alert(self, alert: MarketAlert):
        """Логирование оповещения"""
        try:
            logger.warning(f"ОПОВЕЩЕНИЕ [{alert.severity}]: {alert.message}")
            
        except Exception as e:
            logger.error(f"Ошибка логирования оповещения: {e}")

class SystemMonitor:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.alert_manager = AlertManager(self.db_manager)
        self.performance_monitor = PerformanceMonitor(self.db_manager)
        self.log_manager = LogManager()
        
        self.last_price = None
        self.last_volume = None
        
    async def monitor_market(self, market_analysis: Dict, news_sentiment: Dict):
        """Мониторинг рынка"""
        try:
            current_price = market_analysis.get('current_price', 0)
            current_volume = market_analysis.get('volume', {}).get('current_volume', 0)
            
            # Проверка оповещений
            if self.last_price:
                price_alert = self.alert_manager.check_price_alert(current_price, self.last_price)
                if price_alert:
                    self.log_manager.log_alert(price_alert)
            
            if self.last_volume:
                avg_volume = market_analysis.get('volume', {}).get('avg_volume', 0)
                if avg_volume:
                    volume_alert = self.alert_manager.check_volume_alert(current_volume, avg_volume)
                    if volume_alert:
                        self.log_manager.log_alert(volume_alert)
            
            # Сохранение данных
            self.db_manager.save_market_data(
                "BTCUSDT", current_price, current_volume,
                market_analysis, news_sentiment
            )
            
            # Обновление последних значений
            self.last_price = current_price
            self.last_volume = current_volume
            
            # Логирование
            self.log_manager.log_market_analysis(market_analysis)
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга рынка: {e}")
    
    async def monitor_trading(self, trading_event: TradingEvent):
        """Мониторинг торговли"""
        try:
            # Сохранение события
            self.db_manager.save_trading_event(trading_event)
            
            # Логирование
            self.log_manager.log_trading_event(trading_event)
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга торговли: {e}")
    
    async def monitor_performance(self, total_pnl: float, position_count: int,
                                account_balance: float, risk_metrics: Dict):
        """Мониторинг производительности"""
        try:
            # Обновление метрик
            self.performance_monitor.update_performance(
                total_pnl, position_count, account_balance, risk_metrics
            )
            
            # Проверка оповещений о рисках
            risk_alert = self.alert_manager.check_risk_alert(risk_metrics)
            if risk_alert:
                self.log_manager.log_alert(risk_alert)
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга производительности: {e}")
    
    def get_system_status(self) -> Dict:
        """Получение статуса системы"""
        try:
            performance_summary = self.performance_monitor.get_performance_summary()
            
            return {
                "status": "running",
                "uptime": str(datetime.now() - self.performance_monitor.start_time),
                "performance": performance_summary,
                "database_status": "connected",
                "log_files": len(list(self.log_manager.log_dir.glob("*.log")))
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return {"status": "error", "error": str(e)}