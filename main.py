"""
Главный файл для запуска ИИ агента торговли биткойном
"""
import asyncio
import signal
import sys
from datetime import datetime
from loguru import logger
from typing import Dict, Any

from trading_agent import TradingAgent
from risk_manager import RiskManager, TradingStrategy, PortfolioManager
from monitor import SystemMonitor
from config import settings

class BitcoinTradingBot:
    def __init__(self):
        self.agent = TradingAgent()
        self.risk_manager = RiskManager()
        self.trading_strategy = TradingStrategy(self.risk_manager)
        self.portfolio_manager = PortfolioManager(self.risk_manager)
        self.system_monitor = SystemMonitor()
        
        self.running = False
        self.setup_signal_handlers()
        
        logger.info("ИИ агент торговли биткойном инициализирован")
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, остановка агента...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """Инициализация агента"""
        try:
            logger.info("Инициализация агента...")
            
            # Проверка подключения к Bybit
            balance = await self.agent.bybit_client.get_account_balance()
            if not balance:
                logger.error("Не удалось подключиться к Bybit API")
                return False
            
            logger.info("Подключение к Bybit успешно")
            
            # Проверка Ollama
            async with self.agent.ollama_client:
                test_response = await self.agent.ollama_client.generate_response(
                    "Тест подключения", temperature=0.1
                )
                if not test_response:
                    logger.error("Не удалось подключиться к Ollama")
                    return False
            
            logger.info("Подключение к Ollama успешно")
            
            # Инициализация портфеля
            positions = await self.agent.bybit_client.get_positions()
            await self.portfolio_manager.update_positions(positions)
            
            logger.info("Инициализация завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            return False
    
    async def run_trading_cycle(self) -> Dict[str, Any]:
        """Выполнение одного торгового цикла"""
        try:
            logger.info("Запуск торгового цикла...")
            
            # Запуск агента
            agent_result = await self.agent.run_cycle()
            
            # Мониторинг
            if agent_result.get("market_analysis"):
                await self.system_monitor.monitor_market(
                    agent_result["market_analysis"],
                    agent_result.get("news_sentiment", {})
                )
            
            # Обновление портфеля
            if agent_result.get("positions"):
                await self.portfolio_manager.update_positions(agent_result["positions"])
            
            # Мониторинг производительности
            if agent_result.get("balance"):
                risk_metrics = self.risk_manager.get_risk_metrics(
                    agent_result.get("positions", []),
                    agent_result["balance"].get("totalWalletBalance", 0)
                )
                
                await self.system_monitor.monitor_performance(
                    sum(float(pos.get('unrealisedPnl', 0)) for pos in agent_result.get("positions", [])),
                    len(agent_result.get("positions", [])),
                    agent_result["balance"].get("totalWalletBalance", 0),
                    risk_metrics
                )
            
            logger.info("Торговый цикл завершен")
            return agent_result
            
        except Exception as e:
            logger.error(f"Ошибка торгового цикла: {e}")
            return {"error": str(e)}
    
    async def start_trading(self):
        """Запуск торговли"""
        try:
            logger.info("Запуск торгового агента...")
            
            # Инициализация
            if not await self.initialize():
                logger.error("Не удалось инициализировать агента")
                return
            
            self.running = True
            cycle_count = 0
            
            while self.running:
                try:
                    cycle_count += 1
                    logger.info(f"Торговый цикл #{cycle_count}")
                    
                    # Выполнение цикла
                    result = await self.run_trading_cycle()
                    
                    # Логирование результата
                    if result.get("final_decision"):
                        decision = result["final_decision"]
                        logger.info(f"Решение: {decision.get('action', 'HOLD')} - {decision.get('reason', '')}")
                    
                    # Пауза между циклами
                    await asyncio.sleep(settings.market_analysis_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Получен сигнал остановки")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в основном цикле: {e}")
                    await asyncio.sleep(60)  # Пауза при ошибке
            
            logger.info("Торговый агент остановлен")
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        try:
            # Статус агента
            agent_status = {
                "running": self.running,
                "last_update": self.agent.state.get("last_update"),
                "current_action": self.agent.state.get("current_action"),
                "trading_enabled": self.agent.state.get("trading_enabled", True)
            }
            
            # Статус системы
            system_status = self.system_monitor.get_system_status()
            
            # Сводка портфеля
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            
            # Метрики производительности
            performance_metrics = self.portfolio_manager.get_performance_metrics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_status,
                "system": system_status,
                "portfolio": portfolio_summary,
                "performance": performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {"error": str(e)}
    
    async def emergency_stop(self):
        """Экстренная остановка"""
        try:
            logger.warning("ЭКСТРЕННАЯ ОСТАНОВКА")
            
            # Закрытие всех позиций
            positions = await self.agent.bybit_client.get_positions()
            for position in positions:
                if position.get('size', 0) > 0:
                    await self.agent.bybit_client.close_position()
                    logger.info(f"Позиция закрыта: {position.get('symbol')}")
            
            # Отмена всех ордеров
            orders = await self.agent.bybit_client.get_open_orders()
            for order in orders:
                await self.agent.bybit_client.cancel_order(order.get('orderId'))
                logger.info(f"Ордер отменен: {order.get('orderId')}")
            
            self.running = False
            logger.info("Экстренная остановка завершена")
            
        except Exception as e:
            logger.error(f"Ошибка экстренной остановки: {e}")

async def main():
    """Главная функция"""
    try:
        logger.info("Запуск ИИ агента торговли биткойном")
        logger.info(f"Конфигурация: {settings.trading_pair}, тестнет: {settings.bybit_testnet}")
        
        # Создание бота
        bot = BitcoinTradingBot()
        
        # Запуск торговли
        await bot.start_trading()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Программа завершена")

if __name__ == "__main__":
    # Настройка логирования
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    logger.add(
        "trading_bot_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )
    
    # Запуск
    asyncio.run(main())