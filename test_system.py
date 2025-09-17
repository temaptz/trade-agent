#!/usr/bin/env python3
"""
Скрипт для тестирования системы торгового робота
"""
import sys
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Тестирует импорт всех модулей"""
    print("🧪 Тестирование импортов...")
    
    modules = [
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("langchain_ollama", "LangChain Ollama"),
        ("ccxt", "CCXT"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("requests", "Requests"),
        ("duckduckgo_search", "DuckDuckGo Search"),
        ("dotenv", "Python-dotenv"),
        ("pydantic", "Pydantic")
    ]
    
    success = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError as e:
            print(f"❌ {display_name}: {e}")
            success = False
    
    return success

def test_config():
    """Тестирует конфигурацию"""
    print("\n⚙️ Тестирование конфигурации...")
    
    try:
        from config import Config
        config = Config()
        
        # Проверяем обязательные поля
        required_fields = [
            'BYBIT_API_KEY',
            'BYBIT_SECRET_KEY',
            'OLLAMA_BASE_URL',
            'OLLAMA_MODEL',
            'TRADING_SYMBOL'
        ]
        
        missing_fields = []
        for field in required_fields:
            value = getattr(config, field, None)
            if not value:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️ Отсутствуют поля конфигурации: {', '.join(missing_fields)}")
            print("📝 Заполните файл .env")
            return False
        else:
            print("✅ Конфигурация корректна")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_ollama_connection():
    """Тестирует подключение к Ollama"""
    print("\n🤖 Тестирование подключения к Ollama...")
    
    try:
        import requests
        
        # Проверяем доступность Ollama
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if 'gemma2:9b' in model_names:
                print("✅ Ollama доступен, модель Gemma2:9b найдена")
                return True
            else:
                print(f"⚠️ Ollama доступен, но модель Gemma2:9b не найдена")
                print(f"📋 Доступные модели: {', '.join(model_names)}")
                print("💡 Загрузите модель: ollama pull gemma2:9b")
                return False
        else:
            print(f"❌ Ollama недоступен (статус: {response.status_code})")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к Ollama")
        print("💡 Запустите Ollama: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        return False

def test_bybit_connection():
    """Тестирует подключение к Bybit (только если API ключи настроены)"""
    print("\n🏦 Тестирование подключения к Bybit...")
    
    try:
        from config import Config
        from bybit_client import BybitClient
        
        config = Config()
        
        # Проверяем, настроены ли API ключи
        if not config.BYBIT_API_KEY or not config.BYBIT_SECRET_KEY:
            print("⚠️ API ключи Bybit не настроены")
            print("📝 Заполните BYBIT_API_KEY и BYBIT_SECRET_KEY в .env")
            return False
        
        # Тестируем подключение
        client = BybitClient(config)
        balance = client.get_account_balance()
        
        print("✅ Подключение к Bybit успешно")
        print(f"💰 Баланс BTC: {balance.get('btc_balance', 0):.8f}")
        print(f"💰 Баланс USDT: {balance.get('usdt_balance', 0):.2f}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Bybit: {e}")
        return False

def test_market_tools():
    """Тестирует инструменты анализа рынка"""
    print("\n📊 Тестирование инструментов анализа рынка...")
    
    try:
        from market_tools import MarketDataTool, NewsSearchTool, TechnicalAnalysisTool
        
        # Тестируем инструмент рыночных данных
        market_tool = MarketDataTool()
        print("✅ MarketDataTool инициализирован")
        
        # Тестируем инструмент новостей
        news_tool = NewsSearchTool()
        print("✅ NewsSearchTool инициализирован")
        
        # Тестируем инструмент технического анализа
        tech_tool = TechnicalAnalysisTool()
        print("✅ TechnicalAnalysisTool инициализирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации инструментов: {e}")
        return False

def test_trading_agent():
    """Тестирует торгового агента"""
    print("\n🤖 Тестирование торгового агента...")
    
    try:
        from config import Config
        from trading_agent import TradingAgent
        
        config = Config()
        
        # Проверяем, что API ключи настроены
        if not config.BYBIT_API_KEY or not config.BYBIT_SECRET_KEY:
            print("⚠️ API ключи не настроены, пропускаем тест агента")
            return True
        
        agent = TradingAgent(config)
        print("✅ Торговый агент инициализирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации торгового агента: {e}")
        return False

def run_quick_test():
    """Запускает быстрый тест системы"""
    print("\n🚀 Запуск быстрого теста системы...")
    
    try:
        from config import Config
        from trading_agent import TradingAgent
        
        config = Config()
        
        if not config.BYBIT_API_KEY or not config.BYBIT_SECRET_KEY:
            print("⚠️ API ключи не настроены, пропускаем быстрый тест")
            return True
        
        agent = TradingAgent(config)
        
        # Запускаем один цикл анализа
        print("🔄 Запуск одного цикла анализа...")
        result = agent.run_analysis()
        
        if result and not result.get('error'):
            print("✅ Быстрый тест успешен")
            print(f"📊 Решение: {result.get('decision', 'N/A')}")
            return True
        else:
            print(f"❌ Ошибка в быстром тесте: {result.get('error', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка быстрого теста: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование торгового робота")
    print("=" * 40)
    
    tests = [
        ("Импорты модулей", test_imports),
        ("Конфигурация", test_config),
        ("Подключение к Ollama", test_ollama_connection),
        ("Инструменты анализа", test_market_tools),
        ("Торговый агент", test_trading_agent),
        ("Подключение к Bybit", test_bybit_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Быстрый тест (только если все основные тесты прошли)
    if all(result for _, result in results):
        print(f"\n{'='*20} Быстрый тест {'='*20}")
        try:
            quick_result = run_quick_test()
            results.append(("Быстрый тест", quick_result))
        except Exception as e:
            print(f"❌ Ошибка быстрого теста: {e}")
            results.append(("Быстрый тест", False))
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Система готова к работе.")
        print("\n🚀 Запустите робота: python main.py")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте конфигурацию.")
        print("📖 Дополнительная помощь в README.md")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())