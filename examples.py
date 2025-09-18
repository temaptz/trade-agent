"""
Примеры использования ИИ агента торговли биткойном
"""
import asyncio
from datetime import datetime
from loguru import logger

from trading_agent import TradingAgent
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from ollama_client import OllamaClient
from risk_manager import RiskManager, TradingStrategy
from monitor import SystemMonitor
from utils import DataExporter, PerformanceAnalyzer

async def example_market_analysis():
    """Пример анализа рынка"""
    logger.info("=== Пример анализа рынка ===")
    
    # Создание клиента Bybit
    bybit_client = BybitClient()
    
    # Получение исторических данных
    klines = await bybit_client.get_klines(limit=100)
    
    if not klines.empty:
        # Анализ данных
        analyzer = MarketAnalyzer()
        analysis = await analyzer.comprehensive_analysis(klines)
        
        logger.info(f"Текущая цена: ${analysis.get('current_price', 0):.2f}")
        logger.info(f"Тренд: {analysis.get('trend', {}).get('trend', 'unknown')}")
        logger.info(f"Волатильность: {analysis.get('volatility', {}).get('volatility', 'unknown')}")
        
        return analysis
    else:
        logger.error("Не удалось получить рыночные данные")
        return None

async def example_news_analysis():
    """Пример анализа новостей"""
    logger.info("=== Пример анализа новостей ===")
    
    async with NewsAnalyzer() as news_analyzer:
        # Получение новостей
        news_items = await news_analyzer.get_crypto_news(max_results=10)
        
        logger.info(f"Найдено новостей: {len(news_items)}")
        
        for i, news in enumerate(news_items[:3], 1):
            logger.info(f"Новость {i}: {news.title}")
            logger.info(f"Тональность: {news.sentiment}")
            logger.info(f"Релевантность: {news.relevance_score:.2f}")
        
        # Анализ настроения рынка
        sentiment = await news_analyzer.get_market_sentiment()
        logger.info(f"Настроение рынка: {sentiment.get('sentiment', 'unknown')}")
        logger.info(f"Уверенность: {sentiment.get('confidence', 0):.2f}")
        
        return sentiment

async def example_ai_analysis():
    """Пример ИИ анализа"""
    logger.info("=== Пример ИИ анализа ===")
    
    # Получение данных
    market_analysis = await example_market_analysis()
    news_sentiment = await example_news_analysis()
    
    if market_analysis and news_sentiment:
        async with OllamaClient() as ollama_client:
            # ИИ анализ
            ai_analysis = await ollama_client.analyze_market_data(
                market_analysis, news_sentiment
            )
            
            logger.info("ИИ анализ завершен")
            logger.info(f"Рекомендация: {ai_analysis.get('ai_analysis', {}).get('recommendation', 'HOLD')}")
            logger.info(f"Уверенность: {ai_analysis.get('ai_analysis', {}).get('confidence', 5)}")
            
            return ai_analysis
    else:
        logger.error("Недостаточно данных для ИИ анализа")
        return None

async def example_risk_management():
    """Пример управления рисками"""
    logger.info("=== Пример управления рисками ===")
    
    risk_manager = RiskManager()
    
    # Пример расчета размера позиции
    account_balance = 10000.0
    position_size = risk_manager.calculate_position_size(account_balance)
    logger.info(f"Размер позиции для баланса ${account_balance}: ${position_size:.2f}")
    
    # Пример расчета стоп-лосса
    entry_price = 50000.0
    stop_loss = risk_manager.calculate_stop_loss(entry_price, "Buy")
    take_profit = risk_manager.calculate_take_profit(entry_price, "Buy")
    
    logger.info(f"Цена входа: ${entry_price:.2f}")
    logger.info(f"Стоп-лосс: ${stop_loss:.2f}")
    logger.info(f"Тейк-профит: ${take_profit:.2f}")
    
    # Пример проверки лимитов риска
    positions = [
        {"size": 0.001, "side": "Buy", "avgPrice": 50000.0, "unrealisedPnl": 10.0}
    ]
    
    risk_ok, message = risk_manager.check_risk_limits(positions, account_balance)
    logger.info(f"Проверка рисков: {'OK' if risk_ok else 'FAILED'}")
    logger.info(f"Сообщение: {message}")

async def example_trading_agent():
    """Пример работы торгового агента"""
    logger.info("=== Пример торгового агента ===")
    
    agent = TradingAgent()
    
    # Запуск одного цикла
    result = await agent.run_cycle()
    
    if result.get("final_decision"):
        decision = result["final_decision"]
        logger.info(f"Решение агента: {decision.get('action', 'HOLD')}")
        logger.info(f"Причина: {decision.get('reason', '')}")
        logger.info(f"Уверенность: {decision.get('confidence', 0):.2f}")
    
    return result

async def example_monitoring():
    """Пример мониторинга"""
    logger.info("=== Пример мониторинга ===")
    
    monitor = SystemMonitor()
    
    # Получение статуса системы
    status = monitor.get_system_status()
    logger.info(f"Статус системы: {status.get('status', 'unknown')}")
    logger.info(f"Время работы: {status.get('uptime', 'unknown')}")
    
    # Пример создания оповещения
    from monitor import MarketAlert
    
    alert = MarketAlert(
        timestamp=datetime.now().isoformat(),
        alert_type="price_change",
        symbol="BTCUSDT",
        message="Цена изменилась на 5%",
        severity="medium",
        data={"change_percent": 0.05}
    )
    
    monitor.db_manager.save_alert(alert)
    logger.info("Оповещение сохранено")

async def example_data_export():
    """Пример экспорта данных"""
    logger.info("=== Пример экспорта данных ===")
    
    # Экспорт торговых данных
    await DataExporter.export_trading_data("trading_data.db")
    
    # Генерация отчета
    report_path = await DataExporter.generate_report()
    if report_path:
        logger.info(f"Отчет сгенерирован: {report_path}")

async def example_performance_analysis():
    """Пример анализа производительности"""
    logger.info("=== Пример анализа производительности ===")
    
    # Пример данных о сделках
    trades = [
        {"pnl": 100.0, "timestamp": "2024-01-01T10:00:00"},
        {"pnl": -50.0, "timestamp": "2024-01-01T11:00:00"},
        {"pnl": 200.0, "timestamp": "2024-01-01T12:00:00"},
    ]
    
    # Расчет метрик
    win_rate = PerformanceAnalyzer.calculate_win_rate(trades)
    logger.info(f"Процент выигрышных сделок: {win_rate:.2%}")
    
    # Пример кривой капитала
    equity_curve = [1000, 1100, 1050, 1250]
    max_drawdown = PerformanceAnalyzer.calculate_max_drawdown(equity_curve)
    logger.info(f"Максимальная просадка: {max_drawdown:.2%}")

async def example_full_workflow():
    """Пример полного рабочего процесса"""
    logger.info("=== Полный рабочий процесс ===")
    
    try:
        # 1. Анализ рынка
        market_analysis = await example_market_analysis()
        
        # 2. Анализ новостей
        news_sentiment = await example_news_analysis()
        
        # 3. ИИ анализ
        ai_analysis = await example_ai_analysis()
        
        # 4. Управление рисками
        await example_risk_management()
        
        # 5. Мониторинг
        await example_monitoring()
        
        # 6. Экспорт данных
        await example_data_export()
        
        logger.info("Полный рабочий процесс завершен успешно")
        
    except Exception as e:
        logger.error(f"Ошибка в рабочем процессе: {e}")

async def main():
    """Главная функция с примерами"""
    logger.info("Запуск примеров использования ИИ агента торговли биткойном")
    
    examples = [
        ("Анализ рынка", example_market_analysis),
        ("Анализ новостей", example_news_analysis),
        ("ИИ анализ", example_ai_analysis),
        ("Управление рисками", example_risk_management),
        ("Торговый агент", example_trading_agent),
        ("Мониторинг", example_monitoring),
        ("Экспорт данных", example_data_export),
        ("Анализ производительности", example_performance_analysis),
        ("Полный процесс", example_full_workflow),
    ]
    
    for name, example_func in examples:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Запуск примера: {name}")
            logger.info(f"{'='*50}")
            
            await example_func()
            
        except Exception as e:
            logger.error(f"Ошибка в примере '{name}': {e}")
        
        # Пауза между примерами
        await asyncio.sleep(1)
    
    logger.info("\nВсе примеры завершены!")

if __name__ == "__main__":
    # Настройка логирования
    logger.remove()
    logger.add(
        "examples_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        level="INFO"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO"
    )
    
    # Запуск примеров
    asyncio.run(main())