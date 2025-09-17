"""
Модуль для обработки ошибок и логирования
"""
import traceback
import functools
import time
from typing import Any, Callable, Optional
from loguru import logger
from config import settings

class TradingError(Exception):
    """Базовое исключение для торговых операций"""
    pass

class APIError(TradingError):
    """Ошибка API"""
    pass

class AnalysisError(TradingError):
    """Ошибка анализа"""
    pass

class TradingLimitError(TradingError):
    """Ошибка превышения лимитов торговли"""
    pass

class InsufficientFundsError(TradingError):
    """Ошибка недостаточных средств"""
    pass

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Декоратор для повторных попыток при ошибках"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(
                            f"Попытка {attempt + 1}/{max_retries + 1} не удалась для {func.__name__}: {e}. "
                            f"Повтор через {wait_time:.1f}с"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Все попытки исчерпаны для {func.__name__}: {e}")
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator

def log_execution_time(func: Callable) -> Callable:
    """Декоратор для логирования времени выполнения"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} выполнен за {execution_time:.2f}с")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} завершился с ошибкой за {execution_time:.2f}с: {e}")
            raise
    return wrapper

def safe_execute(func: Callable, *args, **kwargs) -> tuple[Any, Optional[Exception]]:
    """Безопасное выполнение функции с возвратом результата и ошибки"""
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        logger.error(f"Ошибка в {func.__name__}: {e}")
        logger.debug(f"Трассировка: {traceback.format_exc()}")
        return None, e

class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    def __init__(self):
        self.error_count = 0
        self.last_error_time = None
        self.error_threshold = 10  # Максимальное количество ошибок за период
        self.error_reset_time = 3600  # Время сброса счетчика ошибок (1 час)
    
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """
        Обработать ошибку
        Возвращает True, если обработка прошла успешно, False если нужно остановить выполнение
        """
        current_time = time.time()
        
        # Сбрасываем счетчик ошибок, если прошло достаточно времени
        if (self.last_error_time and 
            current_time - self.last_error_time > self.error_reset_time):
            self.error_count = 0
        
        self.error_count += 1
        self.last_error_time = current_time
        
        # Логируем ошибку
        logger.error(f"Ошибка в {context}: {error}")
        logger.debug(f"Трассировка: {traceback.format_exc()}")
        
        # Проверяем, не превышен ли лимит ошибок
        if self.error_count > self.error_threshold:
            logger.critical(f"Превышен лимит ошибок ({self.error_threshold}). Остановка выполнения.")
            return False
        
        # Определяем тип ошибки и принимаем решение
        if isinstance(error, InsufficientFundsError):
            logger.critical("Недостаточно средств для торговли. Остановка.")
            return False
        elif isinstance(error, TradingLimitError):
            logger.warning("Превышен лимит торговли. Пропускаем операцию.")
            return True
        elif isinstance(error, APIError):
            logger.warning("Ошибка API. Повторяем попытку позже.")
            return True
        elif isinstance(error, AnalysisError):
            logger.warning("Ошибка анализа. Пропускаем текущий цикл.")
            return True
        else:
            logger.warning("Неизвестная ошибка. Продолжаем выполнение.")
            return True
    
    def reset_error_count(self):
        """Сбросить счетчик ошибок"""
        self.error_count = 0
        self.last_error_time = None
        logger.info("Счетчик ошибок сброшен")
    
    def get_error_stats(self) -> dict:
        """Получить статистику ошибок"""
        return {
            "error_count": self.error_count,
            "last_error_time": self.last_error_time,
            "error_threshold": self.error_threshold,
            "time_since_last_error": time.time() - self.last_error_time if self.last_error_time else None
        }

class TradingLogger:
    """Специализированный логгер для торговых операций"""
    
    def __init__(self):
        self.trade_log = []
        self.max_log_size = 1000
    
    def log_trade_decision(self, decision: dict, market_data: dict, news_data: dict):
        """Логировать торговое решение"""
        log_entry = {
            "timestamp": time.time(),
            "decision": decision,
            "market_summary": {
                "current_price": market_data.get("current_price"),
                "trend": market_data.get("trend_analysis", {}).get("trend"),
                "confidence": market_data.get("trend_analysis", {}).get("confidence")
            },
            "news_summary": {
                "sentiment": news_data.get("market_sentiment"),
                "article_count": news_data.get("total_news", 0)
            }
        }
        
        self.trade_log.append(log_entry)
        
        # Ограничиваем размер лога
        if len(self.trade_log) > self.max_log_size:
            self.trade_log = self.trade_log[-self.max_log_size:]
        
        logger.info(f"Торговое решение залогировано: {decision.get('action', 'UNKNOWN')}")
    
    def log_trade_execution(self, action: str, quantity: float, price: float, result: dict):
        """Логировать выполнение торговой операции"""
        log_entry = {
            "timestamp": time.time(),
            "action": action,
            "quantity": quantity,
            "price": price,
            "result": result,
            "success": "orderId" in result
        }
        
        self.trade_log.append(log_entry)
        
        if log_entry["success"]:
            logger.success(f"Торговая операция выполнена: {action} {quantity} @ {price}")
        else:
            logger.error(f"Ошибка выполнения торговой операции: {result}")
    
    def get_trade_history(self, limit: int = 50) -> list:
        """Получить историю торговых операций"""
        return self.trade_log[-limit:] if limit else self.trade_log
    
    def get_trade_stats(self) -> dict:
        """Получить статистику торговли"""
        if not self.trade_log:
            return {"total_trades": 0, "successful_trades": 0, "success_rate": 0}
        
        total_trades = len([log for log in self.trade_log if "action" in log])
        successful_trades = len([log for log in self.trade_log if log.get("success", False)])
        
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "success_rate": successful_trades / total_trades if total_trades > 0 else 0,
            "last_trade_time": self.trade_log[-1]["timestamp"] if self.trade_log else None
        }

# Глобальные экземпляры
error_handler = ErrorHandler()
trading_logger = TradingLogger()

def setup_logging():
    """Настройка системы логирования"""
    import os
    
    # Создаем директорию для логов
    os.makedirs("logs", exist_ok=True)
    
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Консольный вывод
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # Файл для всех логов
    logger.add(
        "logs/trading_robot_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # Файл только для торговых операций
    logger.add(
        "logs/trades_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="1 day",
        retention="90 days",
        filter=lambda record: "Торговая операция" in record["message"] or "Торговое решение" in record["message"]
    )
    
    # Файл для ошибок
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{traceback}",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        backtrace=True,
        diagnose=True
    )
    
    logger.info("Система логирования настроена")

if __name__ == "__main__":
    # Тестируем систему логирования
    setup_logging()
    
    logger.info("Тест информационного сообщения")
    logger.warning("Тест предупреждения")
    logger.error("Тест ошибки")
    
    # Тестируем обработку ошибок
    try:
        raise TradingError("Тестовая торговая ошибка")
    except Exception as e:
        error_handler.handle_error(e, "тест")
    
    print("Тест системы логирования завершен")