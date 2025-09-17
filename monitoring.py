"""
Система мониторинга и логирования торгового бота
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from loguru import logger
from config import settings
from models import TradingState, TradingSignal, Position

class TradingMonitor:
    def __init__(self, log_file: str = None):
        self.log_file = log_file or settings.log_file
        self.setup_logging()
        self.trading_history = []
        self.performance_metrics = {}
        
    def setup_logging(self):
        """Настройка системы логирования"""
        # Удаляем стандартный обработчик
        logger.remove()
        
        # Добавляем консольный вывод
        logger.add(
            lambda msg: print(msg, end=""),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level
        )
        
        # Добавляем файловый вывод
        logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        logger.info("Система логирования настроена")
    
    def log_trading_decision(self, signal: TradingSignal, state: TradingState):
        """Логирование торгового решения"""
        try:
            decision_data = {
                "timestamp": datetime.now().isoformat(),
                "action": signal.action.value,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "price_target": signal.price_target,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "account_balance": state.account_balance,
                "available_balance": state.available_balance,
                "consecutive_losses": state.consecutive_losses,
                "current_position": None
            }
            
            if state.current_position:
                decision_data["current_position"] = {
                    "side": state.current_position.side,
                    "size": state.current_position.size,
                    "entry_price": state.current_position.entry_price,
                    "current_price": state.current_position.current_price,
                    "unrealized_pnl": state.current_position.unrealized_pnl
                }
            
            # Сохраняем в историю
            self.trading_history.append(decision_data)
            
            # Логируем
            logger.info(f"Торговое решение: {signal.action.value} (уверенность: {signal.confidence:.2f})")
            logger.info(f"Причина: {signal.reason}")
            
            # Сохраняем в файл
            self._save_trading_history()
            
        except Exception as e:
            logger.error(f"Ошибка логирования торгового решения: {e}")
    
    def log_market_analysis(self, analysis: Dict[str, Any]):
        """Логирование анализа рынка"""
        try:
            logger.info("=== АНАЛИЗ РЫНКА ===")
            logger.info(f"Состояние: {analysis.get('market_condition', 'N/A')}")
            logger.info(f"Тренд: {analysis.get('price_trend', 'N/A')}")
            logger.info(f"Волатильность: {analysis.get('volatility', 0):.2f}%")
            logger.info(f"Рекомендация: {analysis.get('recommendation', 'N/A')}")
            logger.info(f"Уверенность: {analysis.get('confidence', 0):.2f}")
            
            if 'technical_indicators' in analysis:
                ti = analysis['technical_indicators']
                logger.info("Технические индикаторы:")
                logger.info(f"  RSI: {ti.get('rsi', 'N/A')}")
                logger.info(f"  MACD: {ti.get('macd', 'N/A')}")
                logger.info(f"  SMA 20: {ti.get('sma_20', 'N/A')}")
                logger.info(f"  SMA 50: {ti.get('sma_50', 'N/A')}")
            
            if 'news_sentiment' in analysis:
                logger.info(f"Тональность новостей: {analysis['news_sentiment']}")
            
            logger.info("==================")
            
        except Exception as e:
            logger.error(f"Ошибка логирования анализа рынка: {e}")
    
    def log_trade_execution(self, trade_result: Dict[str, Any], success: bool):
        """Логирование выполнения сделки"""
        try:
            if success:
                logger.info("=== СДЕЛКА ВЫПОЛНЕНА ===")
                logger.info(f"Результат: {trade_result}")
            else:
                logger.error("=== ОШИБКА ВЫПОЛНЕНИЯ СДЕЛКИ ===")
                logger.error(f"Ошибка: {trade_result}")
            
        except Exception as e:
            logger.error(f"Ошибка логирования выполнения сделки: {e}")
    
    def _save_trading_history(self):
        """Сохранение истории торговли"""
        try:
            history_file = Path("trading_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.trading_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории торговли: {e}")
    
    def load_trading_history(self) -> List[Dict[str, Any]]:
        """Загрузка истории торговли"""
        try:
            history_file = Path("trading_history.json")
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.trading_history = json.load(f)
                logger.info(f"Загружена история торговли: {len(self.trading_history)} записей")
            return self.trading_history
        except Exception as e:
            logger.error(f"Ошибка загрузки истории торговли: {e}")
            return []
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Расчет метрик производительности"""
        try:
            if not self.trading_history:
                return {}
            
            # Конвертируем в DataFrame для анализа
            df = pd.DataFrame(self.trading_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Общие метрики
            total_decisions = len(df)
            buy_decisions = len(df[df['action'] == 'BUY'])
            sell_decisions = len(df[df['action'] == 'SELL'])
            hold_decisions = len(df[df['action'] == 'HOLD'])
            
            # Средняя уверенность
            avg_confidence = df['confidence'].mean()
            
            # Распределение по времени
            df['hour'] = df['timestamp'].dt.hour
            hourly_distribution = df['hour'].value_counts().sort_index()
            
            # Последние решения
            recent_decisions = df.tail(10)[['timestamp', 'action', 'confidence', 'reason']].to_dict('records')
            
            metrics = {
                "total_decisions": total_decisions,
                "buy_decisions": buy_decisions,
                "sell_decisions": sell_decisions,
                "hold_decisions": hold_decisions,
                "avg_confidence": avg_confidence,
                "hourly_distribution": hourly_distribution.to_dict(),
                "recent_decisions": recent_decisions,
                "last_updated": datetime.now().isoformat()
            }
            
            self.performance_metrics = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик производительности: {e}")
            return {}
    
    def generate_performance_report(self) -> str:
        """Генерация отчета о производительности"""
        try:
            metrics = self.calculate_performance_metrics()
            if not metrics:
                return "Нет данных для отчета"
            
            report = f"""
=== ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ ТОРГОВОГО БОТА ===
Время генерации: {metrics['last_updated']}

ОБЩАЯ СТАТИСТИКА:
- Всего решений: {metrics['total_decisions']}
- Покупки: {metrics['buy_decisions']} ({metrics['buy_decisions']/metrics['total_decisions']*100:.1f}%)
- Продажи: {metrics['sell_decisions']} ({metrics['sell_decisions']/metrics['total_decisions']*100:.1f}%)
- Удержание: {metrics['hold_decisions']} ({metrics['hold_decisions']/metrics['total_decisions']*100:.1f}%)

СРЕДНЯЯ УВЕРЕННОСТЬ: {metrics['avg_confidence']:.2f}

ПОСЛЕДНИЕ 10 РЕШЕНИЙ:
"""
            
            for decision in metrics['recent_decisions']:
                report += f"- {decision['timestamp']}: {decision['action']} (уверенность: {decision['confidence']:.2f})\n"
                report += f"  Причина: {decision['reason'][:100]}...\n\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return f"Ошибка генерации отчета: {e}"
    
    def create_performance_chart(self, output_file: str = "performance_chart.html"):
        """Создание графика производительности"""
        try:
            if not self.trading_history:
                logger.warning("Нет данных для создания графика")
                return
            
            df = pd.DataFrame(self.trading_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Создаем субплоты
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Распределение решений', 'Уверенность по времени', 
                              'Решения по часам', 'Тренд уверенности'),
                specs=[[{"type": "pie"}, {"type": "scatter"}],
                       [{"type": "bar"}, {"type": "scatter"}]]
            )
            
            # График 1: Распределение решений
            action_counts = df['action'].value_counts()
            fig.add_trace(
                go.Pie(labels=action_counts.index, values=action_counts.values, name="Решения"),
                row=1, col=1
            )
            
            # График 2: Уверенность по времени
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['confidence'], mode='lines+markers', 
                          name="Уверенность", line=dict(color='blue')),
                row=1, col=2
            )
            
            # График 3: Решения по часам
            hourly_counts = df['hour'] = df['timestamp'].dt.hour
            hourly_dist = hourly_counts.value_counts().sort_index()
            fig.add_trace(
                go.Bar(x=hourly_dist.index, y=hourly_dist.values, name="Решения по часам"),
                row=2, col=1
            )
            
            # График 4: Тренд уверенности (скользящее среднее)
            df_sorted = df.sort_values('timestamp')
            df_sorted['confidence_ma'] = df_sorted['confidence'].rolling(window=5).mean()
            fig.add_trace(
                go.Scatter(x=df_sorted['timestamp'], y=df_sorted['confidence_ma'], 
                          mode='lines', name="Скользящее среднее уверенности", 
                          line=dict(color='red')),
                row=2, col=2
            )
            
            # Настройка макета
            fig.update_layout(
                title="Анализ производительности торгового бота",
                showlegend=True,
                height=800
            )
            
            # Сохраняем график
            fig.write_html(output_file)
            logger.info(f"График производительности сохранен: {output_file}")
            
        except Exception as e:
            logger.error(f"Ошибка создания графика: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "trading_history_count": len(self.trading_history),
                "log_file": self.log_file,
                "log_file_exists": Path(self.log_file).exists(),
                "performance_metrics_updated": bool(self.performance_metrics),
                "system_uptime": "N/A"  # Можно добавить отслеживание времени запуска
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return {"error": str(e)}
    
    async def monitor_trading_health(self, state: TradingState) -> Dict[str, Any]:
        """Мониторинг здоровья торговой системы"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": "healthy",
                "warnings": [],
                "errors": []
            }
            
            # Проверка баланса
            if state.available_balance < 50:
                health_status["warnings"].append("Низкий баланс аккаунта")
            
            # Проверка серии убытков
            if state.consecutive_losses >= 3:
                health_status["warnings"].append("Серия убытков подряд")
                health_status["overall_health"] = "warning"
            
            # Проверка последнего анализа
            if not state.last_analysis:
                health_status["warnings"].append("Нет данных анализа рынка")
            
            # Проверка последнего сигнала
            if not state.last_signal:
                health_status["warnings"].append("Нет торгового сигнала")
            
            # Проверка уверенности
            if state.last_signal and state.last_signal.confidence < 0.5:
                health_status["warnings"].append("Низкая уверенность в решениях")
            
            # Логируем предупреждения
            for warning in health_status["warnings"]:
                logger.warning(f"Предупреждение системы: {warning}")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга здоровья системы: {e}")
            return {"error": str(e), "overall_health": "error"}