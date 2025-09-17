"""
Основной файл торгового робота
"""
import logging
import time
import signal
import sys
from datetime import datetime
from typing import Optional

from config import Config
from trading_agent import TradingAgent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TradingBot:
    """Основной класс торгового робота"""
    
    def __init__(self):
        self.config = Config()
        self.agent = None
        self.running = False
        
        # Обработчик сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.running = False
    
    def initialize(self) -> bool:
        """Инициализация робота"""
        try:
            logger.info("Инициализация торгового робота...")
            
            # Проверяем конфигурацию
            self.config.validate()
            logger.info("Конфигурация проверена")
            
            # Инициализируем агента
            self.agent = TradingAgent(self.config)
            logger.info("Торговый агент инициализирован")
            
            # Проверяем подключение к Bybit
            balance = self.agent.bybit_client.get_account_balance()
            logger.info(f"Подключение к Bybit успешно. Баланс: {balance}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            return False
    
    def run_single_analysis(self) -> Optional[dict]:
        """Выполняет один цикл анализа"""
        try:
            logger.info("=" * 50)
            logger.info(f"Начало анализа - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Запускаем анализ
            result = self.agent.run_analysis()
            
            # Логируем результат
            self._log_analysis_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка выполнения анализа: {e}")
            return None
    
    def run_continuous(self, interval_minutes: int = 60):
        """Запускает непрерывный режим работы"""
        try:
            logger.info(f"Запуск непрерывного режима (интервал: {interval_minutes} мин)")
            self.running = True
            
            while self.running:
                try:
                    # Выполняем анализ
                    result = self.run_single_analysis()
                    
                    if result and result.get("action"):
                        action = result["action"]
                        if action.get("status") == "executed":
                            logger.info(f"Торговая операция выполнена: {action}")
                    
                    # Ждем до следующего цикла
                    if self.running:
                        logger.info(f"Ожидание {interval_minutes} минут до следующего анализа...")
                        time.sleep(interval_minutes * 60)
                
                except KeyboardInterrupt:
                    logger.info("Получен сигнал прерывания")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в цикле анализа: {e}")
                    if self.running:
                        logger.info("Ожидание 5 минут перед повтором...")
                        time.sleep(5 * 60)
            
            logger.info("Непрерывный режим завершен")
            
        except Exception as e:
            logger.error(f"Критическая ошибка в непрерывном режиме: {e}")
    
    def _log_analysis_result(self, result: dict):
        """Логирует результат анализа"""
        if not result:
            logger.warning("Результат анализа пуст")
            return
        
        logger.info("Результат анализа:")
        logger.info(f"  Решение: {result.get('decision', 'N/A')}")
        logger.info(f"  Обоснование: {result.get('reasoning', 'N/A')}")
        
        if result.get('action'):
            action = result['action']
            logger.info(f"  Действие: {action.get('type', 'N/A')}")
            logger.info(f"  Статус: {action.get('status', 'N/A')}")
            if action.get('amount'):
                logger.info(f"  Количество: {action['amount']}")
        
        if result.get('error'):
            logger.error(f"  Ошибка: {result['error']}")
    
    def get_status(self) -> dict:
        """Возвращает статус робота"""
        try:
            if not self.agent:
                return {"status": "not_initialized"}
            
            balance = self.agent.bybit_client.get_account_balance()
            current_price = self.agent.bybit_client.get_current_price()
            
            return {
                "status": "running" if self.running else "stopped",
                "current_price": current_price,
                "balance": balance,
                "config": {
                    "symbol": self.config.TRADING_SYMBOL,
                    "trade_amount": self.config.TRADE_AMOUNT,
                    "risk_percentage": self.config.RISK_PERCENTAGE
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

def main():
    """Главная функция"""
    print("🤖 Торговый робот с ИИ-агентом")
    print("=" * 40)
    
    # Создаем экземпляр робота
    bot = TradingBot()
    
    # Инициализируем
    if not bot.initialize():
        print("❌ Ошибка инициализации робота")
        return 1
    
    print("✅ Робот успешно инициализирован")
    
    # Выбираем режим работы
    print("\nВыберите режим работы:")
    print("1. Одноразовый анализ")
    print("2. Непрерывный режим (каждый час)")
    print("3. Непрерывный режим (каждые 30 минут)")
    print("4. Непрерывный режим (каждые 15 минут)")
    print("5. Показать статус")
    
    try:
        choice = input("\nВведите номер (1-5): ").strip()
        
        if choice == "1":
            print("\n🔍 Выполнение одноразового анализа...")
            result = bot.run_single_analysis()
            if result:
                print("✅ Анализ завершен")
            else:
                print("❌ Ошибка выполнения анализа")
        
        elif choice == "2":
            print("\n🔄 Запуск непрерывного режима (каждый час)...")
            bot.run_continuous(60)
        
        elif choice == "3":
            print("\n🔄 Запуск непрерывного режима (каждые 30 минут)...")
            bot.run_continuous(30)
        
        elif choice == "4":
            print("\n🔄 Запуск непрерывного режима (каждые 15 минут)...")
            bot.run_continuous(15)
        
        elif choice == "5":
            print("\n📊 Статус робота:")
            status = bot.get_status()
            print(f"Статус: {status.get('status', 'N/A')}")
            if 'current_price' in status:
                print(f"Текущая цена BTC: ${status['current_price']:.2f}")
            if 'balance' in status:
                balance = status['balance']
                print(f"Баланс BTC: {balance.get('btc_balance', 0):.8f}")
                print(f"Баланс USDT: {balance.get('usdt_balance', 0):.2f}")
        
        else:
            print("❌ Неверный выбор")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
        return 0
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())