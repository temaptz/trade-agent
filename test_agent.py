"""
Тесты для ИИ агента торговли биткойном
"""
import asyncio
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from trading_agent import TradingAgent, AgentState
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer, NewsItem
from ollama_client import OllamaClient
from risk_manager import RiskManager, TradingStrategy, PortfolioManager
from monitor import SystemMonitor, TradingEvent, MarketAlert
from utils import PerformanceAnalyzer, DataExporter

class TestMarketAnalyzer:
    """Тесты анализатора рынка"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.analyzer = MarketAnalyzer()
        
        # Создание тестовых данных
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + np.random.rand(100) * 50,
            'low': prices - np.random.rand(100) * 50,
            'close': prices,
            'volume': np.random.rand(100) * 1000
        })
    
    def test_calculate_technical_indicators(self):
        """Тест расчета технических индикаторов"""
        indicators = self.analyzer.calculate_technical_indicators(self.test_data)
        
        assert isinstance(indicators, dict)
        assert 'sma_20' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
        
        # Проверка, что индикаторы не пустые
        assert not indicators['sma_20'].empty
        assert not indicators['rsi'].empty
    
    def test_analyze_trend(self):
        """Тест анализа тренда"""
        indicators = self.analyzer.calculate_technical_indicators(self.test_data)
        trend_analysis = self.analyzer.analyze_trend(self.test_data, indicators)
        
        assert 'trend' in trend_analysis
        assert 'strength' in trend_analysis
        assert trend_analysis['trend'] in ['bullish', 'bearish', 'sideways']
    
    def test_analyze_volatility(self):
        """Тест анализа волатильности"""
        indicators = self.analyzer.calculate_technical_indicators(self.test_data)
        volatility_analysis = self.analyzer.analyze_volatility(self.test_data, indicators)
        
        assert 'volatility' in volatility_analysis
        assert 'level' in volatility_analysis
        assert volatility_analysis['volatility'] in ['high', 'medium', 'low']
    
    def test_find_support_resistance(self):
        """Тест поиска уровней поддержки и сопротивления"""
        levels = self.analyzer.find_support_resistance(self.test_data)
        
        assert 'support' in levels
        assert 'resistance' in levels
    
    def test_calculate_risk_metrics(self):
        """Тест расчета метрик риска"""
        risk_metrics = self.analyzer.calculate_risk_metrics(self.test_data)
        
        assert 'volatility' in risk_metrics
        assert 'max_drawdown' in risk_metrics
        assert 'sharpe_ratio' in risk_metrics

class TestNewsAnalyzer:
    """Тесты анализатора новостей"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.analyzer = NewsAnalyzer()
    
    def test_analyze_sentiment(self):
        """Тест анализа тональности"""
        positive_text = "Bitcoin price surges to new highs with strong bullish momentum"
        negative_text = "Bitcoin crashes as market panic spreads across exchanges"
        neutral_text = "Bitcoin price remains stable with moderate trading volume"
        
        assert self.analyzer.analyze_sentiment(positive_text) == "positive"
        assert self.analyzer.analyze_sentiment(negative_text) == "negative"
        assert self.analyzer.analyze_sentiment(neutral_text) == "neutral"
    
    def test_calculate_relevance_score(self):
        """Тест расчета релевантности"""
        news_item = NewsItem(
            title="Bitcoin price analysis",
            url="https://example.com",
            snippet="Bitcoin trading volume increases",
            timestamp=datetime.now(),
            source="Test"
        )
        
        keywords = ["bitcoin", "price", "trading"]
        score = self.analyzer.calculate_relevance_score(news_item, keywords)
        
        assert 0 <= score <= 1
        assert score > 0  # Должен быть релевантным

class TestRiskManager:
    """Тесты менеджера рисков"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.risk_manager = RiskManager()
    
    def test_calculate_position_size(self):
        """Тест расчета размера позиции"""
        balance = 10000.0
        position_size = self.risk_manager.calculate_position_size(balance)
        
        assert position_size > 0
        assert position_size <= self.risk_manager.risk_limits.max_position_size
    
    def test_calculate_stop_loss(self):
        """Тест расчета стоп-лосса"""
        entry_price = 50000.0
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, "Buy")
        
        assert stop_loss < entry_price
        assert stop_loss > 0
    
    def test_calculate_take_profit(self):
        """Тест расчета тейк-профита"""
        entry_price = 50000.0
        take_profit = self.risk_manager.calculate_take_profit(entry_price, "Buy")
        
        assert take_profit > entry_price
        assert take_profit > 0
    
    def test_check_risk_limits(self):
        """Тест проверки лимитов риска"""
        positions = [
            {"size": 0.001, "side": "Buy", "avgPrice": 50000.0, "unrealisedPnl": 10.0}
        ]
        balance = 10000.0
        
        risk_ok, message = self.risk_manager.check_risk_limits(positions, balance)
        
        assert isinstance(risk_ok, bool)
        assert isinstance(message, str)
    
    def test_should_close_position(self):
        """Тест проверки закрытия позиции"""
        position = {
            "side": "Buy",
            "avgPrice": 50000.0,
            "size": 0.001
        }
        current_price = 49000.0  # Убыток
        
        should_close, reason = self.risk_manager.should_close_position(position, current_price)
        
        assert isinstance(should_close, bool)
        assert isinstance(reason, str)

class TestTradingStrategy:
    """Тесты торговой стратегии"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.risk_manager = RiskManager()
        self.strategy = TradingStrategy(self.risk_manager)
    
    def test_should_trade(self):
        """Тест определения возможности торговли"""
        market_analysis = {
            "trend": {"trend": "bullish", "strength": 0.8}
        }
        news_sentiment = {
            "sentiment": "positive",
            "confidence": 0.7
        }
        ai_analysis = {
            "ai_analysis": {"recommendation": "BUY", "confidence": 0.8}
        }
        
        should_trade, reason = self.strategy.should_trade(
            market_analysis, news_sentiment, ai_analysis
        )
        
        assert isinstance(should_trade, bool)
        assert isinstance(reason, str)
    
    def test_calculate_entry_price(self):
        """Тест расчета цены входа"""
        current_price = 50000.0
        market_analysis = {"current_price": current_price}
        
        entry_price = self.strategy.calculate_entry_price(current_price, market_analysis)
        
        assert entry_price > 0
        assert abs(entry_price - current_price) < current_price * 0.1  # В пределах 10%

class TestPortfolioManager:
    """Тесты менеджера портфеля"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.risk_manager = RiskManager()
        self.portfolio_manager = PortfolioManager(self.risk_manager)
    
    def test_get_portfolio_summary(self):
        """Тест получения сводки портфеля"""
        # Сначала обновляем позиции
        positions = [
            {"side": "Buy", "size": 0.001, "unrealisedPnl": 10.0},
            {"side": "Sell", "size": 0.0005, "unrealisedPnl": -5.0}
        ]
        
        asyncio.run(self.portfolio_manager.update_positions(positions))
        summary = self.portfolio_manager.get_portfolio_summary()
        
        assert "total_positions" in summary
        assert "total_pnl" in summary
        assert summary["total_positions"] == 2
    
    def test_get_performance_metrics(self):
        """Тест получения метрик производительности"""
        # Добавляем тестовые данные
        for i in range(10):
            asyncio.run(self.portfolio_manager.update_positions([
                {"side": "Buy", "size": 0.001, "unrealisedPnl": i * 10}
            ]))
        
        metrics = self.portfolio_manager.get_performance_metrics()
        
        assert "total_return" in metrics
        assert "max_drawdown" in metrics
        assert "volatility" in metrics

class TestPerformanceAnalyzer:
    """Тесты анализатора производительности"""
    
    def test_calculate_sharpe_ratio(self):
        """Тест расчета коэффициента Шарпа"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01]
        sharpe = PerformanceAnalyzer.calculate_sharpe_ratio(returns)
        
        assert isinstance(sharpe, float)
    
    def test_calculate_max_drawdown(self):
        """Тест расчета максимальной просадки"""
        equity_curve = [1000, 1100, 1050, 1200, 1000]
        max_dd = PerformanceAnalyzer.calculate_max_drawdown(equity_curve)
        
        assert 0 <= max_dd <= 1
        assert max_dd > 0  # Должна быть просадка
    
    def test_calculate_win_rate(self):
        """Тест расчета процента выигрышных сделок"""
        trades = [
            {"pnl": 100.0},
            {"pnl": -50.0},
            {"pnl": 200.0},
            {"pnl": -25.0},
            {"pnl": 150.0}
        ]
        
        win_rate = PerformanceAnalyzer.calculate_win_rate(trades)
        
        assert 0 <= win_rate <= 1
        assert win_rate == 0.6  # 3 из 5 сделок прибыльные

class TestTradingAgent:
    """Тесты торгового агента"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.agent = TradingAgent()
    
    @patch('trading_agent.BybitClient')
    @patch('trading_agent.MarketAnalyzer')
    @patch('trading_agent.NewsAnalyzer')
    @patch('trading_agent.OllamaClient')
    async def test_agent_cycle(self, mock_ollama, mock_news, mock_market, mock_bybit):
        """Тест цикла агента"""
        # Мокирование
        mock_bybit.return_value.get_klines = AsyncMock(return_value=pd.DataFrame())
        mock_bybit.return_value.get_current_price = AsyncMock(return_value=50000.0)
        mock_bybit.return_value.get_account_balance = AsyncMock(return_value={"totalWalletBalance": 10000.0})
        mock_bybit.return_value.get_positions = AsyncMock(return_value=[])
        mock_bybit.return_value.get_open_orders = AsyncMock(return_value=[])
        
        mock_market.return_value.comprehensive_analysis = AsyncMock(return_value={"trend": "bullish"})
        
        mock_news.return_value.__aenter__ = AsyncMock()
        mock_news.return_value.__aexit__ = AsyncMock()
        mock_news.return_value.get_market_sentiment = AsyncMock(return_value={"sentiment": "positive"})
        
        mock_ollama.return_value.__aenter__ = AsyncMock()
        mock_ollama.return_value.__aexit__ = AsyncMock()
        mock_ollama.return_value.analyze_market_data = AsyncMock(return_value={"recommendation": "BUY"})
        
        # Запуск цикла
        result = await self.agent.run_cycle()
        
        assert isinstance(result, dict)

class TestSystemMonitor:
    """Тесты системного мониторинга"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.monitor = SystemMonitor()
    
    def test_trading_event_creation(self):
        """Тест создания торгового события"""
        event = TradingEvent(
            timestamp=datetime.now().isoformat(),
            event_type="buy",
            symbol="BTCUSDT",
            side="Buy",
            size=0.001,
            price=50000.0,
            pnl=10.0,
            reason="AI recommendation",
            confidence=0.8
        )
        
        assert event.symbol == "BTCUSDT"
        assert event.event_type == "buy"
        assert event.pnl == 10.0
    
    def test_market_alert_creation(self):
        """Тест создания рыночного оповещения"""
        alert = MarketAlert(
            timestamp=datetime.now().isoformat(),
            alert_type="price_change",
            symbol="BTCUSDT",
            message="Price increased by 5%",
            severity="medium",
            data={"change_percent": 0.05}
        )
        
        assert alert.alert_type == "price_change"
        assert alert.severity == "medium"
        assert alert.data["change_percent"] == 0.05

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """Тест полного рабочего процесса с моками"""
        with patch('trading_agent.BybitClient') as mock_bybit, \
             patch('trading_agent.MarketAnalyzer') as mock_market, \
             patch('trading_agent.NewsAnalyzer') as mock_news, \
             patch('trading_agent.OllamaClient') as mock_ollama:
            
            # Настройка моков
            mock_bybit.return_value.get_klines = AsyncMock(return_value=pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
                'open': np.random.rand(100) * 1000 + 50000,
                'high': np.random.rand(100) * 1000 + 50000,
                'low': np.random.rand(100) * 1000 + 50000,
                'close': np.random.rand(100) * 1000 + 50000,
                'volume': np.random.rand(100) * 1000
            }))
            mock_bybit.return_value.get_current_price = AsyncMock(return_value=50000.0)
            mock_bybit.return_value.get_account_balance = AsyncMock(return_value={"totalWalletBalance": 10000.0})
            mock_bybit.return_value.get_positions = AsyncMock(return_value=[])
            mock_bybit.return_value.get_open_orders = AsyncMock(return_value=[])
            
            mock_market.return_value.comprehensive_analysis = AsyncMock(return_value={
                "current_price": 50000.0,
                "trend": {"trend": "bullish", "strength": 0.8},
                "volatility": {"volatility": "medium", "level": 2},
                "volume": {"volume_trend": "normal", "anomaly": False}
            })
            
            mock_news.return_value.__aenter__ = AsyncMock()
            mock_news.return_value.__aexit__ = AsyncMock()
            mock_news.return_value.get_market_sentiment = AsyncMock(return_value={
                "sentiment": "positive",
                "confidence": 0.7
            })
            
            mock_ollama.return_value.__aenter__ = AsyncMock()
            mock_ollama.return_value.__aexit__ = AsyncMock()
            mock_ollama.return_value.analyze_market_data = AsyncMock(return_value={
                "ai_analysis": {
                    "recommendation": "BUY",
                    "confidence": 0.8
                }
            })
            mock_ollama.return_value.analyze_risk = AsyncMock(return_value={
                "risk_analysis": "Low risk detected"
            })
            mock_ollama.return_value.generate_trading_plan = AsyncMock(return_value={
                "trading_plan": "Buy 0.001 BTC at market price"
            })
            
            # Создание и запуск агента
            agent = TradingAgent()
            result = await agent.run_cycle()
            
            # Проверки
            assert isinstance(result, dict)
            assert "market_analysis" in result
            assert "news_sentiment" in result
            assert "ai_analysis" in result

def run_tests():
    """Запуск всех тестов"""
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    run_tests()