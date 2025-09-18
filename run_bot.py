#!/usr/bin/env python3
"""
Скрипт запуска ИИ агента торговли биткойном
"""
import asyncio
import sys
import signal
import argparse
from pathlib import Path
from loguru import logger

# Добавление текущей директории в путь
sys.path.insert(0, str(Path(__file__).parent))

from main import BitcoinTradingBot

def setup_logging(debug: bool = False):
    """Настройка логирования"""
    logger.remove()
    
    # Консольный вывод
    logger.add(
        sys.stdout,
        level="DEBUG" if debug else "INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True
    )
    
    # Файловое логирование
    logger.add(
        "logs/trading_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG" if debug else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
    
    # Логи ошибок
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )

def check_requirements():
    """Проверка требований"""
    try:
        # Проверка Python версии
        if sys.version_info < (3, 8):
            logger.error("Требуется Python 3.8 или выше")
            return False
        
        # Проверка файла конфигурации
        if not Path(".env").exists():
            logger.error("Файл .env не найден. Скопируйте .env.example в .env и настройте")
            return False
        
        # Проверка зависимостей
        try:
            import pandas
            import numpy
            import aiohttp
            import sqlite3
        except ImportError as e:
            logger.error(f"Отсутствует зависимость: {e}")
            logger.error("Установите зависимости: pip install -r requirements.txt")
            return False
        
        logger.info("Все требования выполнены")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки требований: {e}")
        return False

def check_ollama():
    """Проверка Ollama"""
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            if "gemma2:9b" in result.stdout:
                logger.info("Ollama и модель gemma2:9b готовы")
                return True
            else:
                logger.warning("Модель gemma2:9b не найдена. Установите: ollama pull gemma2:9b")
                return False
        else:
            logger.error("Ollama не запущен. Запустите: ollama serve")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.error("Ollama не найден. Установите Ollama: https://ollama.ai/")
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки Ollama: {e}")
        return False

async def run_bot(debug: bool = False, test_mode: bool = False):
    """Запуск бота"""
    try:
        logger.info("🚀 Запуск ИИ агента торговли биткойном")
        
        # Проверки
        if not check_requirements():
            return False
        
        if not test_mode:
            if not check_ollama():
                logger.warning("Продолжение без Ollama (ограниченная функциональность)")
        
        # Создание бота
        bot = BitcoinTradingBot()
        
        if test_mode:
            logger.info("🧪 Тестовый режим - один цикл")
            result = await bot.run_cycle()
            logger.info(f"Результат цикла: {result.get('final_decision', {}).get('action', 'HOLD')}")
        else:
            logger.info("🔄 Запуск основного цикла торговли")
            await bot.start_trading()
        
        return True
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
        return True
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False

def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"Получен сигнал {signum}, остановка...")
    sys.exit(0)

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="ИИ агент торговли биткойном")
    parser.add_argument("--debug", action="store_true", help="Режим отладки")
    parser.add_argument("--test", action="store_true", help="Тестовый режим (один цикл)")
    parser.add_argument("--setup", action="store_true", help="Запуск настройки")
    parser.add_argument("--status", action="store_true", help="Проверка статуса")
    
    args = parser.parse_args()
    
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Настройка логирования
    setup_logging(debug=args.debug)
    
    if args.setup:
        logger.info("🔧 Запуск настройки...")
        import subprocess
        subprocess.run([sys.executable, "setup.py"])
        return
    
    if args.status:
        logger.info("📊 Проверка статуса...")
        try:
            import sqlite3
            if Path("trading_data.db").exists():
                conn = sqlite3.connect("trading_data.db")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM trading_events")
                events_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM market_data")
                market_count = cursor.fetchone()[0]
                conn.close()
                
                logger.info(f"📈 События торговли: {events_count}")
                logger.info(f"📊 Рыночные данные: {market_count}")
            else:
                logger.info("📊 База данных не найдена")
        except Exception as e:
            logger.error(f"Ошибка проверки статуса: {e}")
        return
    
    # Запуск бота
    try:
        success = asyncio.run(run_bot(debug=args.debug, test_mode=args.test))
        if success:
            logger.info("✅ Бот завершил работу успешно")
        else:
            logger.error("❌ Бот завершил работу с ошибками")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()