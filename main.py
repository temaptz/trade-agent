"""
Основной файл запуска торгового робота
"""
import time
import schedule
import signal
import sys
from datetime import datetime
from loguru import logger
from trading_agent import TradingAgent
from config import settings

class TradingRobot:
    """Основной класс торгового робота"""
    
    def __init__(self):
        """Инициализация робота"""
        self.agent = TradingAgent()
        self.running = True
        self.trade_count = 0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Настройка логирования
        self._setup_logging()
        
        # Обработка сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Торговый робот инициализирован")
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        logger.remove()  # Удаляем стандартный обработчик
        
        # Добавляем консольный вывод
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level
        )
        
        # Добавляем запись в файл
        logger.add(
            "logs/trading_robot_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days"
        )
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, завершаем работу...")
        self.running = False
    
    def _reset_daily_counters(self):
        """Сброс дневных счетчиков"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.last_reset_date = current_date
            logger.info("Дневные счетчики сброшены")
    
    def _check_trading_limits(self) -> bool:
        """Проверить лимиты торговли"""
        self._reset_daily_counters()
        
        if self.daily_trades >= settings.max_daily_trades:
            logger.warning(f"Достигнут дневной лимит торгов: {self.daily_trades}/{settings.max_daily_trades}")
            return False
        
        return True
    
    def run_trading_cycle(self):
        """Запустить один торговый цикл"""
        try:
            if not self._check_trading_limits():
                logger.info("Пропускаем торговый цикл из-за лимитов")
                return
            
            logger.info("=" * 50)
            logger.info(f"Запуск торгового цикла #{self.trade_count + 1}")
            logger.info(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 50)
            
            # Запускаем анализ и принятие решения
            result = self.agent.run_trading_cycle()
            
            if "error" in result:
                logger.error(f"Ошибка в торговом цикле: {result['error']}")
                return
            
            # Анализируем результат
            decision = result.get("trading_decision", {})
            action = decision.get("action", "WAIT")
            confidence = decision.get("confidence", 0)
            reasoning = decision.get("reasoning", "")
            
            logger.info(f"Торговое решение: {action}")
            logger.info(f"Уверенность: {confidence:.2f}")
            logger.info(f"Обоснование: {reasoning}")
            
            # Если была выполнена торговая операция
            if decision.get("executed", False):
                self.trade_count += 1
                self.daily_trades += 1
                logger.info(f"Торговая операция выполнена! Всего операций: {self.trade_count}")
            else:
                logger.info("Торговая операция не выполнена")
            
            # Получаем сводку
            summary = self.agent.get_trading_summary()
            logger.info(f"Текущая цена: {summary.get('current_price', 'N/A')}")
            logger.info(f"Открытых ордеров: {summary.get('open_orders', 0)}")
            logger.info(f"Позиций: {summary.get('positions', 0)}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка в торговом цикле: {e}")
    
    def run_continuous(self, interval_minutes: int = 30):
        """Запустить непрерывную торговлю"""
        logger.info(f"Запуск непрерывной торговли с интервалом {interval_minutes} минут")
        
        # Планируем выполнение
        schedule.every(interval_minutes).minutes.do(self.run_trading_cycle)
        
        # Выполняем первый цикл сразу
        self.run_trading_cycle()
        
        # Основной цикл
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(60)  # Пауза при ошибке
        
        logger.info("Торговый робот остановлен")
    
    def run_single_cycle(self):
        """Запустить один торговый цикл"""
        logger.info("Запуск одиночного торгового цикла")
        self.run_trading_cycle()
        logger.info("Одиночный цикл завершен")
    
    def get_status(self):
        """Получить статус робота"""
        summary = self.agent.get_trading_summary()
        
        status = {
            "running": self.running,
            "total_trades": self.trade_count,
            "daily_trades": self.daily_trades,
            "max_daily_trades": settings.max_daily_trades,
            "current_price": summary.get("current_price"),
            "open_orders": summary.get("open_orders", 0),
            "positions": summary.get("positions", 0),
            "last_update": summary.get("timestamp")
        }
        
        return status

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Торговый робот для биткойна")
    parser.add_argument(
        "--mode", 
        choices=["single", "continuous"], 
        default="single",
        help="Режим работы: single (один цикл) или continuous (непрерывно)"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=30,
        help="Интервал между циклами в минутах (только для continuous режима)"
    )
    
    args = parser.parse_args()
    
    # Создаем робота
    robot = TradingRobot()
    
    try:
        if args.mode == "single":
            robot.run_single_cycle()
        elif args.mode == "continuous":
            robot.run_continuous(args.interval)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()