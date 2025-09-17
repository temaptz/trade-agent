"""
Обработка ошибок и логирование
"""
import logging
import traceback
import functools
from typing import Callable, Any, Optional
from datetime import datetime
import json

class TradingError(Exception):
    """Базовый класс для ошибок торгового робота"""
    pass

class APIError(TradingError):
    """Ошибка API"""
    pass

class ConfigurationError(TradingError):
    """Ошибка конфигурации"""
    pass

class TradingExecutionError(TradingError):
    """Ошибка выполнения торговой операции"""
    pass

class MarketDataError(TradingError):
    """Ошибка получения рыночных данных"""
    pass

def setup_logging(log_level: str = "INFO", log_file: str = "trading_bot.log") -> logging.Logger:
    """Настраивает систему логирования"""
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Файловый обработчик
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger

def error_handler(func: Callable) -> Callable:
    """Декоратор для обработки ошибок"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except TradingError as e:
            logging.error(f"Торговая ошибка в {func.__name__}: {e}")
            raise
        except Exception as e:
            logging.error(f"Неожиданная ошибка в {func.__name__}: {e}")
            logging.error(f"Трассировка: {traceback.format_exc()}")
            raise TradingError(f"Неожиданная ошибка в {func.__name__}: {e}") from e
    return wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Декоратор для повторных попыток при ошибках"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (APIError, MarketDataError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logging.warning(f"Попытка {attempt + 1} неудачна в {func.__name__}: {e}")
                        logging.info(f"Повтор через {wait_time:.1f} секунд...")
                        import time
                        time.sleep(wait_time)
                    else:
                        logging.error(f"Все {max_retries + 1} попыток неудачны в {func.__name__}")
                        raise
                except Exception as e:
                    # Для других ошибок не повторяем
                    raise
            
            # Этот код никогда не должен выполняться, но на всякий случай
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

class ErrorLogger:
    """Класс для логирования ошибок с контекстом"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_api_error(self, operation: str, error: Exception, context: dict = None):
        """Логирует ошибку API"""
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.logger.error(f"API ошибка: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
    
    def log_trading_error(self, operation: str, error: Exception, trade_data: dict = None):
        """Логирует торговую ошибку"""
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "trade_data": trade_data or {}
        }
        
        self.logger.error(f"Торговая ошибка: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
    
    def log_market_data_error(self, operation: str, error: Exception, symbol: str = None):
        """Логирует ошибку получения рыночных данных"""
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol
        }
        
        self.logger.error(f"Ошибка рыночных данных: {json.dumps(error_data, ensure_ascii=False, indent=2)}")

def validate_config(config) -> bool:
    """Валидирует конфигурацию"""
    required_fields = [
        'BYBIT_API_KEY',
        'BYBIT_SECRET_KEY',
        'OLLAMA_BASE_URL',
        'OLLAMA_MODEL',
        'TRADING_SYMBOL'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not hasattr(config, field) or not getattr(config, field):
            missing_fields.append(field)
    
    if missing_fields:
        raise ConfigurationError(f"Отсутствуют обязательные поля конфигурации: {', '.join(missing_fields)}")
    
    # Проверяем числовые значения
    numeric_fields = ['TRADE_AMOUNT', 'MAX_POSITION_SIZE', 'RISK_PERCENTAGE']
    for field in numeric_fields:
        value = getattr(config, field, 0)
        if not isinstance(value, (int, float)) or value <= 0:
            raise ConfigurationError(f"Поле {field} должно быть положительным числом")
    
    return True

def safe_execute(func: Callable, *args, **kwargs) -> tuple[Any, Optional[Exception]]:
    """Безопасно выполняет функцию и возвращает результат и ошибку"""
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        return None, e

def log_performance(func: Callable) -> Callable:
    """Декоратор для логирования производительности"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logging.info(f"{func.__name__} выполнен за {execution_time:.2f} секунд")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logging.error(f"{func.__name__} завершился с ошибкой за {execution_time:.2f} секунд: {e}")
            raise
    return wrapper