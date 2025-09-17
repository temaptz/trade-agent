"""
Примеры использования торгового бота
"""
import asyncio
from trading_agent import TradingAgent
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from bybit_client import BybitClient
from monitoring import TradingMonitor

async def example_market_analysis():
    """Пример анализа рынка"""
    print("=== ПРИМЕР АНАЛИЗА РЫНКА ===")
    
    # Создаем клиент Bybit
    bybit_client = BybitClient()
    
    # Создаем анализатор рынка
    market_analyzer = MarketAnalyzer(bybit_client)
    
    # Получаем анализ рынка
    analysis = await market_analyzer.analyze_market()
    
    print(f"Состояние рынка: {analysis.market_condition}")
    print(f"Тренд: {analysis.price_trend}")
    print(f"Волатильность: {analysis.volatility:.2f}%")
    print(f"Рекомендация: {analysis.recommendation}")
    print(f"Уверенность: {analysis.confidence:.2f}")
    
    if analysis.technical_indicators.rsi:
        print(f"RSI: {analysis.technical_indicators.rsi:.2f}")
    
    if analysis.technical_indicators.macd:
        print(f"MACD: {analysis.technical_indicators.macd:.4f}")

async def example_news_analysis():
    """Пример анализа новостей"""
    print("\n=== ПРИМЕР АНАЛИЗА НОВОСТЕЙ ===")
    
    # Создаем анализатор новостей
    news_analyzer = NewsAnalyzer()
    
    # Получаем анализ новостей
    news_analysis = await news_analyzer.get_comprehensive_news_analysis()
    
    print(f"Всего новостей: {news_analysis['total_news']}")
    print(f"Релевантных: {news_analysis['relevant_news']}")
    print(f"Тональность: {news_analysis['sentiment_analysis']['sentiment']}")
    print(f"Уверенность: {news_analysis['sentiment_analysis']['confidence']:.2f}")
    
    print("\nТоп новости:")
    for i, news in enumerate(news_analysis['top_news'][:3], 1):
        print(f"{i}. {news.title}")
        print(f"   Релевантность: {news.relevance_score:.2f}")

async def example_trading_decision():
    """Пример принятия торгового решения"""
    print("\n=== ПРИМЕР ТОРГОВОГО РЕШЕНИЯ ===")
    
    # Создаем торгового агента
    agent = TradingAgent()
    
    # Запускаем один цикл торговли
    result = await agent.run_trading_cycle()
    
    if agent.current_state.last_signal:
        signal = agent.current_state.last_signal
        print(f"Решение: {signal.action}")
        print(f"Уверенность: {signal.confidence:.2f}")
        print(f"Причина: {signal.reason}")
        
        if signal.price_target:
            print(f"Целевая цена: {signal.price_target}")
        if signal.stop_loss:
            print(f"Стоп-лосс: {signal.stop_loss}")
        if signal.take_profit:
            print(f"Тейк-профит: {signal.take_profit}")

async def example_bybit_operations():
    """Пример операций с Bybit"""
    print("\n=== ПРИМЕР ОПЕРАЦИЙ С BYBIT ===")
    
    # Создаем клиент Bybit
    bybit_client = BybitClient()
    
    # Получаем текущую цену
    price = bybit_client.get_current_price()
    if price:
        print(f"Текущая цена BTC: ${price:,.2f}")
    
    # Получаем рыночные данные
    market_data = bybit_client.get_market_data()
    if market_data:
        print(f"Объем за 24ч: {market_data.volume:,.2f}")
        print(f"Изменение за 24ч: {market_data.change_percent_24h:.2f}%")
    
    # Получаем баланс
    balance = bybit_client.get_account_balance()
    if balance and "list" in balance:
        for account in balance["list"]:
            if "coin" in account and account["coin"]:
                for coin in account["coin"]:
                    if coin["coin"] == "USDT":
                        print(f"Баланс USDT: {coin['walletBalance']}")
                        break
    
    # Получаем позиции
    positions = bybit_client.get_positions()
    if positions:
        print(f"Открытых позиций: {len(positions)}")
        for pos in positions:
            print(f"  {pos.side} {pos.size} @ {pos.entry_price}")
    else:
        print("Нет открытых позиций")

def example_monitoring():
    """Пример мониторинга"""
    print("\n=== ПРИМЕР МОНИТОРИНГА ===")
    
    # Создаем монитор
    monitor = TradingMonitor()
    
    # Загружаем историю
    history = monitor.load_trading_history()
    print(f"Записей в истории: {len(history)}")
    
    # Рассчитываем метрики
    metrics = monitor.calculate_performance_metrics()
    if metrics:
        print(f"Всего решений: {metrics['total_decisions']}")
        print(f"Покупки: {metrics['buy_decisions']}")
        print(f"Продажи: {metrics['sell_decisions']}")
        print(f"Удержания: {metrics['hold_decisions']}")
        print(f"Средняя уверенность: {metrics['avg_confidence']:.2f}")
    
    # Получаем статус системы
    status = monitor.get_system_status()
    print(f"Статус системы: {status}")

async def example_full_cycle():
    """Пример полного цикла работы"""
    print("\n=== ПРИМЕР ПОЛНОГО ЦИКЛА ===")
    
    # Создаем все компоненты
    bybit_client = BybitClient()
    market_analyzer = MarketAnalyzer(bybit_client)
    news_analyzer = NewsAnalyzer()
    monitor = TradingMonitor()
    
    print("1. Анализ рынка...")
    market_analysis = await market_analyzer.analyze_market()
    print(f"   Состояние: {market_analysis.market_condition}")
    print(f"   Рекомендация: {market_analysis.recommendation}")
    
    print("2. Анализ новостей...")
    news_analysis = await news_analyzer.get_comprehensive_news_analysis()
    print(f"   Тональность: {news_analysis['sentiment_analysis']['sentiment']}")
    print(f"   Новостей: {news_analysis['total_news']}")
    
    print("3. Принятие решения...")
    # Здесь бы использовался LLM для принятия решения
    print("   (Требуется настройка Ollama)")
    
    print("4. Мониторинг...")
    monitor.log_market_analysis({
        "market_condition": market_analysis.market_condition.value,
        "price_trend": market_analysis.price_trend,
        "volatility": market_analysis.volatility,
        "recommendation": market_analysis.recommendation,
        "confidence": market_analysis.confidence
    })
    
    print("Цикл завершен!")

async def main():
    """Запуск всех примеров"""
    print("🤖 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ТОРГОВОГО БОТА")
    print("=" * 60)
    
    try:
        # Примеры анализа
        await example_market_analysis()
        await example_news_analysis()
        
        # Примеры операций
        await example_bybit_operations()
        
        # Примеры мониторинга
        example_monitoring()
        
        # Полный цикл
        await example_full_cycle()
        
        # Пример принятия решения (требует настройки)
        # await example_trading_decision()
        
    except Exception as e:
        print(f"❌ Ошибка в примерах: {e}")
        print("Убедитесь, что все зависимости установлены и API ключи настроены")

if __name__ == "__main__":
    asyncio.run(main())