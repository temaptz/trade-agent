"""
Тесты для торгового бота
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from models import TradingState, TradingSignal, TradeAction, MarketAnalysis, MarketCondition
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from trading_agent import TradingAgent
from monitoring import TradingMonitor

class TestBybitClient:
    """Тесты для BybitClient"""
    
    def test_initialization(self):
        """Тест инициализации клиента"""
        client = BybitClient()
        assert client.http_client is not None
        assert client.ws_client is None
        assert client.is_connected is False
    
    @patch('pybit.unified_trading.HTTP')
    def test_get_current_price(self, mock_http):
        """Тест получения текущей цены"""
        # Настраиваем мок
        mock_response = {
            'retCode': 0,
            'result': {
                'list': [{'lastPrice': '50000.0'}]
            }
        }
        mock_http.return_value.get_tickers.return_value = mock_response
        
        client = BybitClient()
        client.http_client = mock_http.return_value
        
        price = client.get_current_price()
        assert price == 50000.0
    
    def test_calculate_position_size(self):
        """Тест расчета размера позиции"""
        client = BybitClient()
        
        # Тест с нормальными параметрами
        size = client.calculate_position_size(1000, 2, 50000, 47500)
        assert size > 0
        
        # Тест с нулевой разницей цен
        size = client.calculate_position_size(1000, 2, 50000, 50000)
        assert size == 0

class TestMarketAnalyzer:
    """Тесты для MarketAnalyzer"""
    
    def test_initialization(self):
        """Тест инициализации анализатора"""
        mock_client = Mock()
        analyzer = MarketAnalyzer(mock_client)
        assert analyzer.bybit_client == mock_client
    
    def test_calculate_volatility(self):
        """Тест расчета волатильности"""
        import pandas as pd
        
        mock_client = Mock()
        analyzer = MarketAnalyzer(mock_client)
        
        # Создаем тестовые данные
        data = pd.DataFrame({
            'close': [100, 102, 98, 105, 103, 107, 101, 99, 104, 106]
        })
        
        volatility = analyzer.calculate_volatility(data, window=5)
        assert volatility >= 0
    
    def test_analyze_market_condition(self):
        """Тест анализа состояния рынка"""
        import pandas as pd
        
        mock_client = Mock()
        analyzer = MarketAnalyzer(mock_client)
        
        # Создаем тестовые данные
        data = pd.DataFrame({
            'close': [100, 105, 110, 115, 120, 125, 130, 135, 140, 145]
        })
        
        from models import TechnicalIndicators
        indicators = TechnicalIndicators(rsi=45, macd=0.1, macd_signal=0.05)
        
        condition = analyzer.analyze_market_condition(data, indicators)
        assert condition in [MarketCondition.BULLISH, MarketCondition.BEARISH, 
                           MarketCondition.SIDEWAYS, MarketCondition.VOLATILE]

class TestNewsAnalyzer:
    """Тесты для NewsAnalyzer"""
    
    def test_initialization(self):
        """Тест инициализации анализатора новостей"""
        analyzer = NewsAnalyzer()
        assert analyzer.ddgs is not None
        assert len(analyzer.crypto_keywords) > 0
    
    def test_calculate_relevance_score(self):
        """Тест расчета релевантности"""
        analyzer = NewsAnalyzer()
        
        # Тест с релевантным текстом
        relevant_text = "bitcoin price analysis trading cryptocurrency"
        score = analyzer._calculate_relevance_score(relevant_text)
        assert 0 <= score <= 1
        assert score > 0.5
        
        # Тест с нерелевантным текстом
        irrelevant_text = "weather forecast today sunny"
        score = analyzer._calculate_relevance_score(irrelevant_text)
        assert 0 <= score <= 1
        assert score < 0.5

class TestTradingAgent:
    """Тесты для TradingAgent"""
    
    def test_initialization(self):
        """Тест инициализации агента"""
        agent = TradingAgent()
        assert agent.bybit_client is not None
        assert agent.market_analyzer is not None
        assert agent.news_analyzer is not None
        assert agent.llm is not None
        assert agent.graph is not None
    
    def test_prepare_llm_context(self):
        """Тест подготовки контекста для LLM"""
        agent = TradingAgent()
        state = TradingState()
        state.account_balance = 1000.0
        state.available_balance = 500.0
        
        context = agent._prepare_llm_context(state)
        assert 'current_time' in context
        assert context['account_balance'] == 1000.0
        assert context['available_balance'] == 500.0
    
    def test_parse_llm_response(self):
        """Тест парсинга ответа LLM"""
        agent = TradingAgent()
        state = TradingState()
        
        # Тест с валидным JSON
        valid_response = '{"action": "BUY", "confidence": 0.8, "reason": "Test"}'
        signal = agent._parse_llm_response(valid_response, state)
        assert signal.action == TradeAction.BUY
        assert signal.confidence == 0.8
        assert signal.reason == "Test"
        
        # Тест с невалидным JSON
        invalid_response = "Just some text with BUY in it"
        signal = agent._parse_llm_response(invalid_response, state)
        assert signal.action == TradeAction.BUY  # Должен найти BUY в тексте
        assert signal.confidence == 0.5  # Значение по умолчанию

class TestTradingMonitor:
    """Тесты для TradingMonitor"""
    
    def test_initialization(self):
        """Тест инициализации монитора"""
        monitor = TradingMonitor()
        assert monitor.log_file is not None
        assert isinstance(monitor.trading_history, list)
    
    def test_log_trading_decision(self):
        """Тест логирования торгового решения"""
        monitor = TradingMonitor()
        signal = TradingSignal(
            action=TradeAction.BUY,
            confidence=0.8,
            reason="Test signal"
        )
        state = TradingState()
        state.account_balance = 1000.0
        
        monitor.log_trading_decision(signal, state)
        assert len(monitor.trading_history) == 1
        assert monitor.trading_history[0]['action'] == 'BUY'
    
    def test_calculate_performance_metrics(self):
        """Тест расчета метрик производительности"""
        monitor = TradingMonitor()
        
        # Добавляем тестовые данные
        monitor.trading_history = [
            {
                'timestamp': '2024-01-01T10:00:00',
                'action': 'BUY',
                'confidence': 0.8,
                'reason': 'Test 1'
            },
            {
                'timestamp': '2024-01-01T11:00:00',
                'action': 'SELL',
                'confidence': 0.7,
                'reason': 'Test 2'
            }
        ]
        
        metrics = monitor.calculate_performance_metrics()
        assert metrics['total_decisions'] == 2
        assert metrics['buy_decisions'] == 1
        assert metrics['sell_decisions'] == 1
        assert metrics['avg_confidence'] == 0.75

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_market_analysis_integration(self):
        """Тест интеграции анализа рынка"""
        # Создаем мок клиента
        mock_client = Mock()
        mock_client.get_historical_klines.return_value = [
            ['1640995200000', '50000', '51000', '49000', '50500', '1000', '50000000'],
            ['1640995260000', '50500', '51500', '49500', '51000', '1100', '55000000'],
        ]
        
        analyzer = MarketAnalyzer(mock_client)
        
        # Тестируем получение исторических данных
        df = analyzer.get_historical_data_bybit()
        assert df is not None
        assert len(df) == 2
    
    @pytest.mark.asyncio
    async def test_news_analysis_integration(self):
        """Тест интеграции анализа новостей"""
        analyzer = NewsAnalyzer()
        
        # Тестируем расчет релевантности
        score = analyzer._calculate_relevance_score("bitcoin price analysis")
        assert 0 <= score <= 1

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов торгового бота...")
    
    # Создаем тестовые классы
    test_classes = [
        TestBybitClient,
        TestMarketAnalyzer,
        TestNewsAnalyzer,
        TestTradingAgent,
        TestTradingMonitor,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Тестирование {test_class.__name__}...")
        
        # Создаем экземпляр класса
        test_instance = test_class()
        
        # Получаем все методы тестирования
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                
                # Проверяем, является ли метод асинхронным
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                
                print(f"  ✅ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
    
    print(f"\n📊 Результаты тестирования:")
    print(f"Всего тестов: {total_tests}")
    print(f"Пройдено: {passed_tests}")
    print(f"Провалено: {total_tests - passed_tests}")
    print(f"Процент успеха: {passed_tests/total_tests*100:.1f}%")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n⚠️  Некоторые тесты не прошли")