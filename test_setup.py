"""
Скрипт для тестирования настройки торгового робота
"""
import sys
import os
from loguru import logger

def test_imports():
    """Тестировать импорты всех модулей"""
    logger.info("Тестируем импорты...")
    
    try:
        import langchain
        import langgraph
        import langchain_ollama
        import ollama
        import pybit
        import requests
        import pandas
        import numpy
        import ta
        import schedule
        from dotenv import load_dotenv
        logger.success("Все основные зависимости импортированы успешно")
        return True
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return False

def test_config():
    """Тестировать конфигурацию"""
    logger.info("Тестируем конфигурацию...")
    
    try:
        from config import settings
        logger.success(f"Конфигурация загружена: {settings.trading_pair}")
        return True
    except Exception as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return False

def test_ollama_connection():
    """Тестировать подключение к Ollama"""
    logger.info("Тестируем подключение к Ollama...")
    
    try:
        import ollama
        models = ollama.list()
        if models and 'models' in models:
            logger.success(f"Ollama подключен. Модели: {[m['name'] for m in models['models']]}")
            return True
        else:
            logger.warning("Ollama подключен, но модели не найдены")
            return False
    except Exception as e:
        logger.error(f"Ошибка подключения к Ollama: {e}")
        return False

def test_bybit_client():
    """Тестировать клиент Bybit"""
    logger.info("Тестируем клиент Bybit...")
    
    try:
        from bybit_client import BybitClient
        client = BybitClient()
        
        # Тестируем получение цены
        price = client.get_current_price()
        if price:
            logger.success(f"Bybit клиент работает. Текущая цена: {price}")
            return True
        else:
            logger.warning("Bybit клиент создан, но не удалось получить цену")
            return False
    except Exception as e:
        logger.error(f"Ошибка Bybit клиента: {e}")
        return False

def test_market_analyzer():
    """Тестировать анализатор рынка"""
    logger.info("Тестируем анализатор рынка...")
    
    try:
        from market_analyzer import MarketAnalyzer
        analyzer = MarketAnalyzer()
        
        # Тестируем получение данных
        data = analyzer.get_historical_data()
        if data is not None and not data.empty:
            logger.success(f"Анализатор рынка работает. Получено {len(data)} записей")
            return True
        else:
            logger.warning("Анализатор рынка создан, но данные не получены")
            return False
    except Exception as e:
        logger.error(f"Ошибка анализатора рынка: {e}")
        return False

def test_news_analyzer():
    """Тестировать анализатор новостей"""
    logger.info("Тестируем анализатор новостей...")
    
    try:
        from news_analyzer import NewsAnalyzer
        analyzer = NewsAnalyzer()
        
        # Тестируем поиск новостей
        news = analyzer.search_crypto_news("bitcoin", max_results=3)
        if news:
            logger.success(f"Анализатор новостей работает. Найдено {len(news)} новостей")
            return True
        else:
            logger.warning("Анализатор новостей создан, но новости не найдены")
            return False
    except Exception as e:
        logger.error(f"Ошибка анализатора новостей: {e}")
        return False

def test_trading_agent():
    """Тестировать торгового агента"""
    logger.info("Тестируем торгового агента...")
    
    try:
        from trading_agent import TradingAgent
        agent = TradingAgent()
        logger.success("Торговый агент создан успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка торгового агента: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("Начинаем тестирование настройки торгового робота...")
    logger.info("=" * 50)
    
    tests = [
        ("Импорты", test_imports),
        ("Конфигурация", test_config),
        ("Ollama", test_ollama_connection),
        ("Bybit клиент", test_bybit_client),
        ("Анализатор рынка", test_market_analyzer),
        ("Анализатор новостей", test_news_analyzer),
        ("Торговый агент", test_trading_agent),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Тест: {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.success(f"✅ {test_name}: ПРОЙДЕН")
            else:
                logger.warning(f"⚠️  {test_name}: ЧАСТИЧНО ПРОЙДЕН")
        except Exception as e:
            logger.error(f"❌ {test_name}: ПРОВАЛЕН - {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.success("🎉 Все тесты пройдены! Торговый робот готов к работе.")
        return True
    elif passed >= total * 0.7:
        logger.warning("⚠️  Большинство тестов пройдено. Робот может работать с ограничениями.")
        return True
    else:
        logger.error("❌ Много тестов провалено. Необходимо исправить проблемы перед запуском.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)