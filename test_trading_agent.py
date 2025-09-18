"""
Tests for the Bitcoin trading agent
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import pandas as pd
import numpy as np

from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer, NewsItem
from ollama_client import OllamaClient
from trading_agent import BitcoinTradingAgent
from trading_strategies import RiskManager, TechnicalStrategy, SentimentStrategy, PortfolioManager, TradingSignal, SignalType, RiskLevel

class TestBybitClient:
    """Test Bybit client functionality"""
    
    @pytest.fixture
    def bybit_client(self):
        return BybitClient()
    
    @pytest.mark.asyncio
    async def test_get_market_data(self, bybit_client):
        """Test market data retrieval"""
        with patch.object(bybit_client.exchange, 'fetch_ohlcv') as mock_fetch:
            # Mock OHLCV data
            mock_data = [
                [1640995200000, 47000, 48000, 46000, 47500, 1000],
                [1640998800000, 47500, 48500, 47000, 48000, 1200]
            ]
            mock_fetch.return_value = mock_data
            
            df = await bybit_client.get_market_data(limit=2)
            
            assert len(df) == 2
            assert 'open' in df.columns
            assert 'high' in df.columns
            assert 'low' in df.columns
            assert 'close' in df.columns
            assert 'volume' in df.columns
    
    @pytest.mark.asyncio
    async def test_get_ticker(self, bybit_client):
        """Test ticker data retrieval"""
        with patch.object(bybit_client.exchange, 'fetch_ticker') as mock_fetch:
            mock_ticker = {
                'symbol': 'BTCUSDT',
                'last': 47500,
                'bid': 47450,
                'ask': 47550,
                'volume': 1000
            }
            mock_fetch.return_value = mock_ticker
            
            ticker = await bybit_client.get_ticker()
            
            assert ticker['symbol'] == 'BTCUSDT'
            assert ticker['last'] == 47500

class TestMarketAnalyzer:
    """Test market analyzer functionality"""
    
    @pytest.fixture
    def market_analyzer(self):
        bybit_client = Mock(spec=BybitClient)
        return MarketAnalyzer(bybit_client)
    
    def test_calculate_indicators(self, market_analyzer):
        """Test technical indicator calculations"""
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(100, 1000, 100)
        }, index=dates)
        
        indicators = market_analyzer._calculate_indicators(df)
        
        assert 'sma_20' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'bb_upper' in indicators
        assert 0 <= indicators['rsi'] <= 100
    
    def test_analyze_sentiment(self, market_analyzer):
        """Test sentiment analysis"""
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=50, freq='1H')
        prices = 50000 + np.cumsum(np.random.randn(50) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(100, 1000, 50)
        }, index=dates)
        
        indicators = {
            'rsi': 25,  # Oversold
            'macd': 100,
            'macd_signal': 50,
            'bb_position': 0.1,
            'volume_ratio': 2.0
        }
        
        sentiment = market_analyzer._analyze_sentiment(df, indicators)
        
        assert 'score' in sentiment
        assert 'overall' in sentiment
        assert 'factors' in sentiment
        assert sentiment['score'] > 0  # Should be positive due to oversold RSI

class TestNewsAnalyzer:
    """Test news analyzer functionality"""
    
    @pytest.fixture
    def news_analyzer(self):
        return NewsAnalyzer()
    
    def test_calculate_relevance(self, news_analyzer):
        """Test news relevance calculation"""
        news_item = NewsItem(
            title="Bitcoin price surges to new all-time high",
            url="https://example.com",
            snippet="Bitcoin reaches $100,000 as institutional adoption grows",
            published_date=datetime.now(),
            source="CryptoNews"
        )
        
        relevance = news_analyzer._calculate_relevance(news_item)
        
        assert 0 <= relevance <= 1
        assert relevance > 0.5  # Should be high relevance for Bitcoin news
    
    def test_remove_duplicates(self, news_analyzer):
        """Test duplicate news removal"""
        news_items = [
            NewsItem("Bitcoin price up", "url1", "snippet1", datetime.now(), "source1"),
            NewsItem("Bitcoin price rises", "url2", "snippet2", datetime.now(), "source2"),  # Similar
            NewsItem("Ethereum price down", "url3", "snippet3", datetime.now(), "source3")  # Different
        ]
        
        unique_items = news_analyzer._remove_duplicates(news_items)
        
        assert len(unique_items) == 2  # Should remove one duplicate

class TestTradingStrategies:
    """Test trading strategies"""
    
    @pytest.fixture
    def risk_manager(self):
        return RiskManager(max_position_size=0.1, risk_percentage=2.0)
    
    @pytest.fixture
    def technical_strategy(self, risk_manager):
        return TechnicalStrategy(risk_manager)
    
    def test_calculate_position_size(self, risk_manager):
        """Test position size calculation"""
        account_balance = 10000
        entry_price = 50000
        stop_loss = 48000
        
        position_size = risk_manager.calculate_position_size(
            account_balance, entry_price, stop_loss
        )
        
        assert position_size > 0
        assert position_size <= account_balance * 0.1  # Max position size
    
    def test_validate_trade(self, risk_manager):
        """Test trade validation"""
        signal = TradingSignal(
            signal_type=SignalType.BUY,
            confidence=80,
            entry_price=50000,
            stop_loss=48000,
            take_profit=52000,
            position_size=0.01,
            risk_level=RiskLevel.MEDIUM,
            reasoning="Test signal",
            timestamp=datetime.now()
        )
        
        is_valid, reason = risk_manager.validate_trade(signal, [], 10000)
        
        assert is_valid
        assert reason == "Trade validated"
    
    def test_rsi_strategy(self, technical_strategy):
        """Test RSI-based strategy"""
        indicators = {'rsi': 25}  # Oversold
        current_price = 50000
        
        signal = technical_strategy._rsi_strategy(indicators, current_price)
        
        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.confidence > 0
    
    def test_macd_strategy(self, technical_strategy):
        """Test MACD-based strategy"""
        indicators = {
            'macd': 100,
            'macd_signal': 50,
            'macd_histogram': 50
        }
        current_price = 50000
        
        signal = technical_strategy._macd_strategy(indicators, current_price)
        
        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.confidence > 0

class TestPortfolioManager:
    """Test portfolio management"""
    
    @pytest.fixture
    def portfolio_manager(self):
        risk_manager = RiskManager()
        return PortfolioManager(risk_manager)
    
    def test_add_position(self, portfolio_manager):
        """Test adding position"""
        from trading_strategies import Position
        
        position = Position(
            symbol="BTCUSDT",
            side="long",
            size=0.1,
            entry_price=50000,
            current_price=51000,
            unrealized_pnl=100,
            stop_loss=48000,
            take_profit=52000,
            timestamp=datetime.now()
        )
        
        portfolio_manager.add_position(position)
        
        assert len(portfolio_manager.positions) == 1
        assert portfolio_manager.positions[0].symbol == "BTCUSDT"
    
    def test_update_position(self, portfolio_manager):
        """Test position update"""
        from trading_strategies import Position
        
        position = Position(
            symbol="BTCUSDT",
            side="long",
            size=0.1,
            entry_price=50000,
            current_price=50000,
            unrealized_pnl=0,
            stop_loss=48000,
            take_profit=52000,
            timestamp=datetime.now()
        )
        
        portfolio_manager.add_position(position)
        portfolio_manager.update_position("BTCUSDT", 51000)
        
        updated_position = portfolio_manager.positions[0]
        assert updated_position.current_price == 51000
        assert updated_position.unrealized_pnl == 100  # (51000 - 50000) * 0.1
    
    def test_check_stop_loss_take_profit(self, portfolio_manager):
        """Test stop loss and take profit triggers"""
        from trading_strategies import Position
        
        position = Position(
            symbol="BTCUSDT",
            side="long",
            size=0.1,
            entry_price=50000,
            current_price=50000,
            unrealized_pnl=0,
            stop_loss=48000,
            take_profit=52000,
            timestamp=datetime.now()
        )
        
        portfolio_manager.add_position(position)
        
        # Test stop loss trigger
        triggers = portfolio_manager.check_stop_loss_take_profit("BTCUSDT", 47000)
        assert len(triggers) > 0
        assert "Stop loss triggered" in triggers[0]
        
        # Test take profit trigger
        triggers = portfolio_manager.check_stop_loss_take_profit("BTCUSDT", 53000)
        assert len(triggers) > 0
        assert "Take profit triggered" in triggers[0]

@pytest.mark.asyncio
async def test_integration():
    """Integration test for the trading agent"""
    # Mock all external dependencies
    with patch('bybit_client.BybitClient') as mock_bybit, \
         patch('news_analyzer.NewsAnalyzer') as mock_news, \
         patch('ollama_client.OllamaClient') as mock_ollama:
        
        # Setup mocks
        mock_bybit_instance = AsyncMock()
        mock_bybit.return_value = mock_bybit_instance
        
        mock_news_instance = AsyncMock()
        mock_news.return_value = mock_news_instance
        
        mock_ollama_instance = AsyncMock()
        mock_ollama.return_value = mock_ollama_instance
        
        # Create trading agent
        agent = BitcoinTradingAgent()
        
        # Test single analysis cycle
        result = await agent.run_analysis_cycle()
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'timestamp' in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])