"""
Tests for Market Analyzer
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

from market_analyzer import MarketAnalyzer
from models import MarketData

class TestMarketAnalyzer:
    """Test cases for MarketAnalyzer"""
    
    @pytest.fixture
    def mock_bybit_client(self):
        """Mock Bybit client"""
        client = Mock()
        client.get_market_data.return_value = MarketData(
            symbol="BTCUSDT",
            price=50000.0,
            volume=1000000.0,
            timestamp=datetime.now(),
            high_24h=51000.0,
            low_24h=49000.0,
            change_24h=1000.0,
            change_percent_24h=2.0
        )
        
        # Mock klines data
        klines_data = []
        base_price = 50000.0
        for i in range(200):
            price = base_price + np.random.normal(0, 100)
            klines_data.append({
                'timestamp': str(int((datetime.now().timestamp() - (200-i)*3600) * 1000)),
                'open': str(price),
                'high': str(price + 50),
                'low': str(price - 50),
                'close': str(price + 10),
                'volume': str(1000000 + np.random.normal(0, 100000)),
                'turnover': str(price * 1000000)
            })
        
        client.get_klines.return_value = klines_data
        return client
    
    @pytest.fixture
    def market_analyzer(self, mock_bybit_client):
        """Create MarketAnalyzer instance with mocked client"""
        return MarketAnalyzer(mock_bybit_client)
    
    def test_analyze_market_data(self, market_analyzer):
        """Test market data analysis"""
        result = market_analyzer.analyze_market_data("BTCUSDT")
        
        assert result is not None
        assert hasattr(result, 'technical_score')
        assert hasattr(result, 'sentiment_score')
        assert hasattr(result, 'news_score')
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'reasoning')
        assert hasattr(result, 'risk_level')
        
        # Check score ranges
        assert 0 <= result.technical_score <= 1
        assert 0 <= result.sentiment_score <= 1
        assert 0 <= result.news_score <= 1
        assert 0 <= result.overall_score <= 1
        assert 0 <= result.confidence <= 1
        assert result.risk_level in ['LOW', 'MEDIUM', 'HIGH']
    
    def test_klines_to_dataframe(self, market_analyzer):
        """Test klines to DataFrame conversion"""
        klines = [
            {
                'timestamp': '1640995200000',
                'open': '50000',
                'high': '51000',
                'low': '49000',
                'close': '50500',
                'volume': '1000000',
                'turnover': '50500000000'
            }
        ]
        
        df = market_analyzer._klines_to_dataframe(klines)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert df['open'].dtype == 'float64'
    
    def test_calculate_technical_indicators(self, market_analyzer):
        """Test technical indicators calculation"""
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 50,
            'low': prices - 50,
            'close': prices + 10,
            'volume': np.random.randint(100000, 2000000, 100)
        }, index=dates)
        
        indicators = market_analyzer._calculate_technical_indicators(df)
        
        assert indicators is not None
        assert hasattr(indicators, 'rsi_14')
        assert hasattr(indicators, 'macd')
        assert hasattr(indicators, 'macd_signal')
        assert hasattr(indicators, 'bollinger_upper')
        assert hasattr(indicators, 'sma_20')
        assert hasattr(indicators, 'sma_50')
    
    def test_analyze_technical_patterns(self, market_analyzer):
        """Test technical patterns analysis"""
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 50,
            'low': prices - 50,
            'close': prices + 10,
            'volume': np.random.randint(100000, 2000000, 100)
        }, index=dates)
        
        indicators = market_analyzer._calculate_technical_indicators(df)
        score = market_analyzer._analyze_technical_patterns(df, indicators)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_analyze_market_structure(self, market_analyzer):
        """Test market structure analysis"""
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 50,
            'low': prices - 50,
            'close': prices + 10,
            'volume': np.random.randint(100000, 2000000, 100)
        }, index=dates)
        
        market_data = MarketData(
            symbol="BTCUSDT",
            price=50000.0,
            volume=1000000.0,
            timestamp=datetime.now(),
            high_24h=51000.0,
            low_24h=49000.0,
            change_24h=1000.0,
            change_percent_24h=2.0
        )
        
        score = market_analyzer._analyze_market_structure(df, market_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_calculate_confidence(self, market_analyzer):
        """Test confidence calculation"""
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 50,
            'low': prices - 50,
            'close': prices + 10,
            'volume': np.random.randint(100000, 2000000, 100)
        }, index=dates)
        
        indicators = market_analyzer._calculate_technical_indicators(df)
        confidence = market_analyzer._calculate_confidence(df, indicators)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    def test_assess_risk_level(self, market_analyzer):
        """Test risk level assessment"""
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 50,
            'low': prices - 50,
            'close': prices + 10,
            'volume': np.random.randint(100000, 2000000, 100)
        }, index=dates)
        
        market_data = MarketData(
            symbol="BTCUSDT",
            price=50000.0,
            volume=1000000.0,
            timestamp=datetime.now(),
            high_24h=51000.0,
            low_24h=49000.0,
            change_24h=1000.0,
            change_percent_24h=2.0
        )
        
        risk_level = market_analyzer._assess_risk_level(df, market_data)
        
        assert risk_level in ['LOW', 'MEDIUM', 'HIGH']
    
    def test_generate_technical_reasoning(self, market_analyzer):
        """Test technical reasoning generation"""
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 50,
            'low': prices - 50,
            'close': prices + 10,
            'volume': np.random.randint(100000, 2000000, 100)
        }, index=dates)
        
        indicators = market_analyzer._calculate_technical_indicators(df)
        reasoning = market_analyzer._generate_technical_reasoning(df, indicators)
        
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
    
    def test_error_handling(self, market_analyzer):
        """Test error handling in analysis"""
        # Test with invalid data
        with patch.object(market_analyzer.bybit_client, 'get_market_data', side_effect=Exception("API Error")):
            result = market_analyzer.analyze_market_data("INVALID")
            # Should handle error gracefully
            assert result is not None