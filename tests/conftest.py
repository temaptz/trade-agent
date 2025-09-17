"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from unittest.mock import Mock
from datetime import datetime

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_market_data():
    """Mock market data for testing"""
    return {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "volume": 1000000.0,
        "timestamp": datetime.now(),
        "high_24h": 51000.0,
        "low_24h": 49000.0,
        "change_24h": 1000.0,
        "change_percent_24h": 2.0
    }

@pytest.fixture
def mock_news_item():
    """Mock news item for testing"""
    return {
        "title": "Bitcoin price analysis shows bullish trends",
        "content": "Bitcoin cryptocurrency market analysis indicates positive momentum",
        "url": "https://example.com/news",
        "source": "CryptoNews",
        "published_at": datetime.now(),
        "sentiment_score": 0.8,
        "relevance_score": 0.7
    }

@pytest.fixture
def mock_trading_decision():
    """Mock trading decision for testing"""
    return {
        "signal": "BUY",
        "confidence": 0.8,
        "position_size": 0.1,
        "reasoning": "Strong technical and sentiment signals",
        "stop_loss": 48500.0,
        "take_profit": 53000.0
    }

@pytest.fixture
def mock_position():
    """Mock position for testing"""
    return {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "size": 0.1,
        "entry_price": 49000.0,
        "mark_price": 50000.0,
        "unrealized_pnl": 100.0,
        "realized_pnl": 0.0
    }

@pytest.fixture
def mock_account_info():
    """Mock account info for testing"""
    return {
        "result": {
            "list": [{
                "accountType": "UNIFIED",
                "coin": [{
                    "coin": "USDT",
                    "walletBalance": "10000.0"
                }]
            }]
        }
    }

@pytest.fixture
def mock_klines_data():
    """Mock klines data for testing"""
    klines = []
    base_price = 50000.0
    for i in range(200):
        price = base_price + (i - 100) * 10  # Simple trend
        klines.append({
            'timestamp': str(int((datetime.now().timestamp() - (200-i)*3600) * 1000)),
            'open': str(price),
            'high': str(price + 50),
            'low': str(price - 50),
            'close': str(price + 10),
            'volume': str(1000000 + i * 1000),
            'turnover': str(price * (1000000 + i * 1000))
        })
    return klines

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        'message': {
            'content': '''
            {
                "overall_sentiment": "bullish",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "key_factors": ["Strong technical indicators", "Positive news sentiment"],
                "market_outlook": "Bullish trend expected to continue",
                "risk_assessment": "medium",
                "trading_recommendation": "buy",
                "reasoning": "Multiple positive factors align for upward movement"
            }
            '''
        }
    }

@pytest.fixture
def mock_risk_metrics():
    """Mock risk metrics for testing"""
    return {
        "account_balance": 10000.0,
        "current_position_value": 1000.0,
        "unrealized_pnl": 100.0,
        "position_risk": 0.1,
        "market_volatility": 0.05,
        "market_trend": 0.5,
        "portfolio_risk": 0.2,
        "max_allowed_position_size": 0.1,
        "suggested_stop_loss": 48500.0,
        "suggested_take_profit": 53000.0,
        "daily_pnl": 50.0,
        "daily_trades": 3
    }

@pytest.fixture
def mock_risk_checks():
    """Mock risk checks for testing"""
    return {
        "daily_loss_ok": True,
        "daily_trades_ok": True,
        "position_size_ok": True,
        "portfolio_risk_ok": True,
        "volatility_ok": True,
        "account_balance_ok": True,
        "analysis_confidence_ok": True,
        "can_trade": True
    }

@pytest.fixture
def mock_market_analysis():
    """Mock market analysis for testing"""
    analysis = Mock()
    analysis.technical_score = 0.8
    analysis.sentiment_score = 0.7
    analysis.news_score = 0.6
    analysis.overall_score = 0.7
    analysis.confidence = 0.8
    analysis.reasoning = "Strong technical signals"
    analysis.risk_level = "LOW"
    return analysis

@pytest.fixture
def mock_sentiment_analysis():
    """Mock sentiment analysis for testing"""
    return {
        "overall_sentiment": "bullish",
        "sentiment_score": 0.8,
        "confidence": 0.9,
        "key_factors": ["Strong technical indicators", "Positive news"],
        "market_outlook": "Bullish trend expected",
        "risk_assessment": "medium",
        "trading_recommendation": "buy",
        "reasoning": "Multiple positive factors"
    }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Mark tests based on their location
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "test_analyze_news" in item.nodeid or "test_analyze_sentiment_advanced" in item.nodeid:
            item.add_marker(pytest.mark.slow)