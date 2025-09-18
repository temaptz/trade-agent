"""
Утилиты и вспомогательные функции
"""
import asyncio
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import aiofiles
from pathlib import Path

class DataExporter:
    """Экспорт данных"""
    
    @staticmethod
    async def export_trading_data(db_path: str, output_dir: str = "exports"):
        """Экспорт торговых данных"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            
            # Экспорт событий торговли
            events_df = pd.read_sql_query("SELECT * FROM trading_events", conn)
            events_df.to_csv(output_path / "trading_events.csv", index=False)
            
            # Экспорт рыночных данных
            market_df = pd.read_sql_query("SELECT * FROM market_data", conn)
            market_df.to_csv(output_path / "market_data.csv", index=False)
            
            # Экспорт производительности
            performance_df = pd.read_sql_query("SELECT * FROM performance", conn)
            performance_df.to_csv(output_path / "performance.csv", index=False)
            
            conn.close()
            
            logger.info(f"Данные экспортированы в {output_path}")
            
        except Exception as e:
            logger.error(f"Ошибка экспорта данных: {e}")
    
    @staticmethod
    async def generate_report(data_dir: str = "exports") -> str:
        """Генерация отчета"""
        try:
            data_path = Path(data_dir)
            
            # Загрузка данных
            events_df = pd.read_csv(data_path / "trading_events.csv")
            performance_df = pd.read_csv(data_path / "performance.csv")
            
            # Анализ торговли
            total_trades = len(events_df)
            profitable_trades = len(events_df[events_df['pnl'] > 0])
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            
            # Анализ производительности
            if not performance_df.empty:
                total_return = performance_df['total_pnl'].iloc[-1] - performance_df['total_pnl'].iloc[0]
                max_drawdown = performance_df['total_pnl'].max() - performance_df['total_pnl'].min()
            else:
                total_return = 0
                max_drawdown = 0
            
            # Генерация отчета
            report = f"""
# ОТЧЕТ О ТОРГОВЛЕ БИТКОЙНОМ
## Период: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Торговые метрики:
- Общее количество сделок: {total_trades}
- Прибыльных сделок: {profitable_trades}
- Процент выигрышных: {win_rate:.2%}
- Общая доходность: {total_return:.2f}
- Максимальная просадка: {max_drawdown:.2f}

### Рекомендации:
- {'Увеличить размер позиций' if win_rate > 0.6 else 'Снизить размер позиций'}
- {'Продолжить текущую стратегию' if total_return > 0 else 'Пересмотреть стратегию'}
"""
            
            # Сохранение отчета
            report_path = data_path / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(report)
            
            logger.info(f"Отчет сохранен: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return ""

class MarketDataProcessor:
    """Обработка рыночных данных"""
    
    @staticmethod
    def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Расчет технических индикаторов"""
        try:
            if df.empty:
                return df
            
            # Простые скользящие средние
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # Экспоненциальные скользящие средние
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            return df
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return df
    
    @staticmethod
    def detect_patterns(df: pd.DataFrame) -> List[Dict]:
        """Обнаружение паттернов"""
        try:
            patterns = []
            
            if df.empty or len(df) < 10:
                return patterns
            
            # Простые паттерны
            recent_data = df.tail(10)
            
            # Двойная вершина
            if len(recent_data) >= 5:
                highs = recent_data['high'].tail(5)
                if len(highs) >= 3:
                    max_high = highs.max()
                    if highs.iloc[-1] < max_high * 0.98 and highs.iloc[-3] < max_high * 0.98:
                        patterns.append({
                            "type": "double_top",
                            "confidence": 0.7,
                            "description": "Двойная вершина"
                        })
            
            # Двойное дно
            if len(recent_data) >= 5:
                lows = recent_data['low'].tail(5)
                if len(lows) >= 3:
                    min_low = lows.min()
                    if lows.iloc[-1] > min_low * 1.02 and lows.iloc[-3] > min_low * 1.02:
                        patterns.append({
                            "type": "double_bottom",
                            "confidence": 0.7,
                            "description": "Двойное дно"
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Ошибка обнаружения паттернов: {e}")
            return []
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> float:
        """Расчет волатильности"""
        try:
            if df.empty or len(df) < window:
                return 0.0
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.rolling(window=window).std().iloc[-1]
            
            return float(volatility) if not np.isnan(volatility) else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета волатильности: {e}")
            return 0.0

class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self):
        self.notifications = []
    
    async def send_notification(self, message: str, level: str = "info"):
        """Отправка уведомления"""
        try:
            notification = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "level": level
            }
            
            self.notifications.append(notification)
            
            # Логирование
            if level == "error":
                logger.error(f"УВЕДОМЛЕНИЕ: {message}")
            elif level == "warning":
                logger.warning(f"УВЕДОМЛЕНИЕ: {message}")
            else:
                logger.info(f"УВЕДОМЛЕНИЕ: {message}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def get_notifications(self, limit: int = 50) -> List[Dict]:
        """Получение уведомлений"""
        return self.notifications[-limit:]

class ConfigValidator:
    """Валидатор конфигурации"""
    
    @staticmethod
    def validate_config(config: Dict) -> Tuple[bool, List[str]]:
        """Валидация конфигурации"""
        errors = []
        
        try:
            # Проверка API ключей
            if not config.get("bybit_api_key"):
                errors.append("Отсутствует BYBIT_API_KEY")
            
            if not config.get("bybit_secret_key"):
                errors.append("Отсутствует BYBIT_SECRET_KEY")
            
            # Проверка торговых параметров
            trade_amount = config.get("trade_amount", 0)
            if trade_amount <= 0:
                errors.append("TRADE_AMOUNT должен быть больше 0")
            
            max_risk = config.get("max_risk_percent", 0)
            if max_risk <= 0 or max_risk > 100:
                errors.append("MAX_RISK_PERCENT должен быть от 1 до 100")
            
            # Проверка интервалов
            news_interval = config.get("news_update_interval", 0)
            if news_interval < 60:
                errors.append("NEWS_UPDATE_INTERVAL должен быть не менее 60 секунд")
            
            market_interval = config.get("market_analysis_interval", 0)
            if market_interval < 30:
                errors.append("MARKET_ANALYSIS_INTERVAL должен быть не менее 30 секунд")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Ошибка валидации: {e}"]

class PerformanceAnalyzer:
    """Анализатор производительности"""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Расчет коэффициента Шарпа"""
        try:
            if not returns:
                return 0.0
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            
            sharpe = (mean_return - risk_free_rate / 252) / std_return
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"Ошибка расчета коэффициента Шарпа: {e}")
            return 0.0
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> float:
        """Расчет максимальной просадки"""
        try:
            if not equity_curve:
                return 0.0
            
            peak = equity_curve[0]
            max_dd = 0.0
            
            for value in equity_curve:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            
            return float(max_dd)
            
        except Exception as e:
            logger.error(f"Ошибка расчета максимальной просадки: {e}")
            return 0.0
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict]) -> float:
        """Расчет процента выигрышных сделок"""
        try:
            if not trades:
                return 0.0
            
            profitable = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
            total = len(trades)
            
            return profitable / total if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета процента выигрышных: {e}")
            return 0.0

class DataBackup:
    """Резервное копирование данных"""
    
    @staticmethod
    async def backup_database(db_path: str, backup_dir: str = "backups"):
        """Создание резервной копии базы данных"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"trading_data_backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(db_path, backup_file)
            
            logger.info(f"Резервная копия создана: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return ""
    
    @staticmethod
    async def cleanup_old_backups(backup_dir: str = "backups", days: int = 7):
        """Очистка старых резервных копий"""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for backup_file in backup_path.glob("*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.info(f"Удален старый бэкап: {backup_file}")
            
        except Exception as e:
            logger.error(f"Ошибка очистки бэкапов: {e}")

# Глобальные утилиты
def format_currency(amount: float, currency: str = "USD") -> str:
    """Форматирование валюты"""
    return f"{amount:,.2f} {currency}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Форматирование процентов"""
    return f"{value:.{decimals}%}"

def format_timestamp(timestamp: str) -> str:
    """Форматирование временной метки"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def safe_float(value: Any, default: float = 0.0) -> float:
    """Безопасное преобразование в float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование в int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default