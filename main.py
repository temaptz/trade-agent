"""
Главный файл для запуска торгового бота
"""
import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import settings
from trading_agent import TradingAgent
from monitoring import TradingMonitor

class TradingBot:
    def __init__(self):
        self.agent = TradingAgent()
        self.monitor = TradingMonitor()
        self.running = False
        
    async def initialize(self):
        """Инициализация бота"""
        try:
            logger.info("Инициализация торгового бота...")
            
            # Проверяем конфигурацию
            if not self._check_configuration():
                logger.error("Ошибка конфигурации. Проверьте настройки в .env файле")
                return False
            
            # Подключаемся к Bybit
            await self.agent.bybit_client.connect_websocket()
            
            # Загружаем историю торговли
            self.monitor.load_trading_history()
            
            logger.info("Торговый бот инициализирован успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            return False
    
    def _check_configuration(self) -> bool:
        """Проверка конфигурации"""
        try:
            # Проверяем обязательные параметры
            if not settings.bybit_api_key or not settings.bybit_secret_key:
                logger.error("Не настроены API ключи Bybit")
                return False
            
            if not settings.ollama_model:
                logger.error("Не настроена модель Ollama")
                return False
            
            # Проверяем файл .env
            env_file = Path(".env")
            if not env_file.exists():
                logger.warning("Файл .env не найден. Создайте его на основе .env.example")
                return False
            
            logger.info("Конфигурация проверена успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки конфигурации: {e}")
            return False
    
    async def run_single_cycle(self):
        """Запуск одного цикла торговли"""
        try:
            logger.info("=== ЗАПУСК ТОРГОВОГО ЦИКЛА ===")
            
            # Запускаем торговый цикл
            result = await self.agent.run_trading_cycle()
            
            # Логируем результат
            if self.agent.current_state.last_signal:
                self.monitor.log_trading_decision(
                    self.agent.current_state.last_signal,
                    self.agent.current_state
                )
            
            if self.agent.current_state.last_analysis:
                analysis_data = {
                    "market_condition": self.agent.current_state.last_analysis.market_condition.value,
                    "price_trend": self.agent.current_state.last_analysis.price_trend,
                    "volatility": self.agent.current_state.last_analysis.volatility,
                    "recommendation": self.agent.current_state.last_analysis.recommendation,
                    "confidence": self.agent.current_state.last_analysis.confidence,
                    "news_sentiment": self.agent.current_state.last_analysis.news_sentiment,
                    "technical_indicators": {
                        "rsi": self.agent.current_state.last_analysis.technical_indicators.rsi,
                        "macd": self.agent.current_state.last_analysis.technical_indicators.macd,
                        "macd_signal": self.agent.current_state.last_analysis.technical_indicators.macd_signal,
                        "sma_20": self.agent.current_state.last_analysis.technical_indicators.sma_20,
                        "sma_50": self.agent.current_state.last_analysis.technical_indicators.sma_50
                    }
                }
                self.monitor.log_market_analysis(analysis_data)
            
            # Проверяем здоровье системы
            health_status = await self.monitor.monitor_trading_health(self.agent.current_state)
            if health_status.get("overall_health") != "healthy":
                logger.warning(f"Статус системы: {health_status['overall_health']}")
            
            logger.info("=== ЦИКЛ ЗАВЕРШЕН ===")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка торгового цикла: {e}")
            return None
    
    async def run_continuous(self, interval_minutes: int = 30):
        """Запуск непрерывной торговли"""
        try:
            self.running = True
            logger.info(f"Запуск непрерывной торговли с интервалом {interval_minutes} минут")
            
            while self.running:
                try:
                    await self.run_single_cycle()
                    
                    if self.running:
                        logger.info(f"Ожидание {interval_minutes} минут до следующего цикла...")
                        await asyncio.sleep(interval_minutes * 60)
                        
                except KeyboardInterrupt:
                    logger.info("Получен сигнал остановки")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в торговом цикле: {e}")
                    if self.running:
                        await asyncio.sleep(60)  # Ждем минуту перед повтором
                        
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            await self.shutdown()
    
    async def run_interactive(self):
        """Интерактивный режим"""
        try:
            logger.info("Запуск в интерактивном режиме")
            
            while True:
                print("\n=== ТОРГОВЫЙ БОТ - ИНТЕРАКТИВНЫЙ РЕЖИМ ===")
                print("1. Запустить один торговый цикл")
                print("2. Показать статус системы")
                print("3. Показать отчет о производительности")
                print("4. Создать график производительности")
                print("5. Запустить непрерывную торговлю")
                print("0. Выход")
                
                choice = input("\nВыберите опцию: ").strip()
                
                if choice == "1":
                    await self.run_single_cycle()
                elif choice == "2":
                    status = self.monitor.get_system_status()
                    print(f"\nСтатус системы: {status}")
                elif choice == "3":
                    report = self.monitor.generate_performance_report()
                    print(f"\n{report}")
                elif choice == "4":
                    self.monitor.create_performance_chart()
                    print("График создан: performance_chart.html")
                elif choice == "5":
                    interval = input("Введите интервал в минутах (по умолчанию 30): ").strip()
                    interval = int(interval) if interval.isdigit() else 30
                    await self.run_continuous(interval)
                elif choice == "0":
                    break
                else:
                    print("Неверный выбор")
                    
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        except Exception as e:
            logger.error(f"Ошибка в интерактивном режиме: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            logger.info("Завершение работы торгового бота...")
            self.running = False
            
            # Отключаемся от WebSocket
            await self.agent.bybit_client.disconnect_websocket()
            
            # Сохраняем историю
            self.monitor._save_trading_history()
            
            logger.info("Торговый бот остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка при завершении работы: {e}")

def setup_signal_handlers(bot: TradingBot):
    """Настройка обработчиков сигналов"""
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        asyncio.create_task(bot.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Главная функция"""
    try:
        # Создаем экземпляр бота
        bot = TradingBot()
        
        # Настраиваем обработчики сигналов
        setup_signal_handlers(bot)
        
        # Инициализируем бота
        if not await bot.initialize():
            logger.error("Не удалось инициализировать бота")
            return
        
        # Проверяем аргументы командной строки
        if len(sys.argv) > 1:
            if sys.argv[1] == "continuous":
                interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
                await bot.run_continuous(interval)
            elif sys.argv[1] == "single":
                await bot.run_single_cycle()
            else:
                print("Использование: python main.py [continuous|single] [interval_minutes]")
        else:
            # Запускаем в интерактивном режиме
            await bot.run_interactive()
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Программа завершена")

if __name__ == "__main__":
    # Запускаем главную функцию
    asyncio.run(main())