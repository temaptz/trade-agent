#!/usr/bin/env python3
"""
Примеры использования торгового робота
"""
import time
import json
from datetime import datetime
from config import Config
from trading_agent import TradingAgent
from bybit_client import BybitClient
from monitor import TradingMonitor

def example_single_analysis():
    """Пример одноразового анализа"""
    print("🔍 Пример одноразового анализа")
    print("-" * 40)
    
    try:
        # Инициализация
        config = Config()
        agent = TradingAgent(config)
        
        # Запуск анализа
        print("Запуск анализа...")
        result = agent.run_analysis()
        
        # Вывод результата
        print(f"Решение: {result.get('decision', 'N/A')}")
        print(f"Обоснование: {result.get('reasoning', 'N/A')}")
        
        if result.get('action'):
            action = result['action']
            print(f"Действие: {action.get('type', 'N/A')}")
            print(f"Статус: {action.get('status', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def example_continuous_monitoring():
    """Пример непрерывного мониторинга"""
    print("🔄 Пример непрерывного мониторинга")
    print("-" * 40)
    
    try:
        config = Config()
        monitor = TradingMonitor(config)
        
        if not monitor.initialize():
            print("Ошибка инициализации")
            return
        
        # Запуск мониторинга на 10 минут
        print("Запуск мониторинга на 10 минут...")
        start_time = time.time()
        
        while time.time() - start_time < 600:  # 10 минут
            try:
                # Запуск анализа
                result = monitor.run_analysis_and_monitor()
                
                # Вывод статуса
                status = monitor.get_system_status()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Решение: {result.get('decision', 'N/A')}, "
                      f"Баланс BTC: {status.get('balance', {}).get('btc', 0):.8f}")
                
                # Ждем 2 минуты
                time.sleep(120)
                
            except KeyboardInterrupt:
                print("\nМониторинг прерван")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(30)
        
        # Генерация отчета
        report = monitor.generate_report()
        print("\n" + report)
        
    except Exception as e:
        print(f"Ошибка: {e}")

def example_market_analysis():
    """Пример анализа рынка"""
    print("📊 Пример анализа рынка")
    print("-" * 40)
    
    try:
        from market_tools import MarketDataTool, NewsSearchTool, TechnicalAnalysisTool
        
        # Инициализация инструментов
        market_tool = MarketDataTool()
        news_tool = NewsSearchTool()
        tech_tool = TechnicalAnalysisTool()
        
        # Анализ рыночных данных
        print("Получение рыночных данных...")
        market_data = market_tool._run("BTCUSDT", "1h", 100)
        print(f"Рыночные данные: {market_data[:200]}...")
        
        # Поиск новостей
        print("\nПоиск новостей...")
        news_data = news_tool._run("Bitcoin BTC cryptocurrency news", 3)
        print(f"Новости: {news_data[:200]}...")
        
        # Технический анализ
        print("\nТехнический анализ...")
        tech_analysis = tech_tool._run("BTCUSDT", "1h")
        print(f"Технический анализ: {tech_analysis[:200]}...")
        
    except Exception as e:
        print(f"Ошибка: {e}")

def example_bybit_operations():
    """Пример операций с Bybit"""
    print("🏦 Пример операций с Bybit")
    print("-" * 40)
    
    try:
        config = Config()
        client = BybitClient(config)
        
        # Получение баланса
        print("Получение баланса...")
        balance = client.get_account_balance()
        print(f"Баланс BTC: {balance.get('btc_balance', 0):.8f}")
        print(f"Баланс USDT: {balance.get('usdt_balance', 0):.2f}")
        
        # Получение текущей цены
        print("\nПолучение текущей цены...")
        price = client.get_current_price()
        print(f"Текущая цена BTC: ${price:.2f}")
        
        # Получение рыночных данных
        print("\nПолучение рыночных данных...")
        market_data = client.get_market_data("BTCUSDT", "1h", 10)
        print(f"Получено {len(market_data)} свечей")
        
        if market_data:
            latest = market_data[-1]
            print(f"Последняя свеча: {latest}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

def example_error_handling():
    """Пример обработки ошибок"""
    print("🛡️ Пример обработки ошибок")
    print("-" * 40)
    
    try:
        from error_handler import safe_execute, ErrorLogger
        import logging
        
        logger = logging.getLogger(__name__)
        error_logger = ErrorLogger(logger)
        
        # Безопасное выполнение функции
        def risky_function():
            import random
            if random.random() < 0.5:
                raise Exception("Случайная ошибка")
            return "Успех"
        
        print("Тестирование безопасного выполнения...")
        for i in range(5):
            result, error = safe_execute(risky_function)
            if error:
                print(f"Попытка {i+1}: Ошибка - {error}")
                error_logger.log_trading_error("test_operation", error)
            else:
                print(f"Попытка {i+1}: {result}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

def example_configuration():
    """Пример работы с конфигурацией"""
    print("⚙️ Пример работы с конфигурацией")
    print("-" * 40)
    
    try:
        config = Config()
        
        print("Текущая конфигурация:")
        print(f"Символ торговли: {config.TRADING_SYMBOL}")
        print(f"Размер торговли: {config.TRADE_AMOUNT}")
        print(f"Максимальная позиция: {config.MAX_POSITION_SIZE}")
        print(f"Процент риска: {config.RISK_PERCENTAGE}%")
        print(f"Ollama URL: {config.OLLAMA_BASE_URL}")
        print(f"Ollama модель: {config.OLLAMA_MODEL}")
        print(f"Тестовая сеть: {config.BYBIT_TESTNET}")
        
        # Валидация конфигурации
        from error_handler import validate_config
        try:
            validate_config(config)
            print("\n✅ Конфигурация корректна")
        except Exception as e:
            print(f"\n❌ Ошибка конфигурации: {e}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

def main():
    """Главная функция с примерами"""
    print("🤖 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ТОРГОВОГО РОБОТА")
    print("=" * 50)
    
    examples = [
        ("Конфигурация", example_configuration),
        ("Анализ рынка", example_market_analysis),
        ("Операции Bybit", example_bybit_operations),
        ("Обработка ошибок", example_error_handling),
        ("Одноразовый анализ", example_single_analysis),
        ("Непрерывный мониторинг", example_continuous_monitoring),
    ]
    
    print("Доступные примеры:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    try:
        choice = input("\nВыберите пример (1-6) или Enter для всех: ").strip()
        
        if choice:
            try:
                index = int(choice) - 1
                if 0 <= index < len(examples):
                    name, func = examples[index]
                    print(f"\n{'='*20} {name} {'='*20}")
                    func()
                else:
                    print("Неверный выбор")
            except ValueError:
                print("Неверный формат")
        else:
            # Запуск всех примеров
            for name, func in examples:
                print(f"\n{'='*20} {name} {'='*20}")
                try:
                    func()
                except Exception as e:
                    print(f"Ошибка в примере {name}: {e}")
                print()
    
    except KeyboardInterrupt:
        print("\n👋 Примеры прерваны")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()