"""
Tests for Risk Manager
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from risk_manager import RiskManager
from models import MarketData, Position, TradingDecision, TradeSignal

class TestRiskManager:
    """Test cases for RiskManager"""
    
    @pytest.fixture
    def mock_bybit_client(self):
        """Mock Bybit client"""
        client = Mock()
        client.get_account_info.return_value = {
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
        return client
    
    @pytest.fixture
    def risk_manager(self, mock_bybit_client):
        """Create RiskManager instance with mocked client"""
        return RiskManager(mock_bybit_client)
    
    def test_extract_account_balance(self, risk_manager):
        """Test account balance extraction"""
        account_info = {
            "result": {
                "list": [{
                    "accountType": "UNIFIED",
                    "coin": [{
                        "coin": "USDT",
                        "walletBalance": "5000.0"
                    }]
                }]
            }
        }
        
        balance = risk_manager._extract_account_balance(account_info)
        assert balance == 5000.0
    
    def test_extract_account_balance_no_usdt(self, risk_manager):
        """Test account balance extraction when no USDT"""
        account_info = {
            "result": {
                "list": [{
                    "accountType": "UNIFIED",
                    "coin": [{
                        "coin": "BTC",
                        "walletBalance": "1.0"
                    }]
                }]
            }
        }
        
        balance = risk_manager._extract_account_balance(account_info)
        assert balance == 0.0
    
    def test_calculate_position_metrics(self, risk_manager):
        """Test position metrics calculation"""
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
        
        position = Position(
            symbol="BTCUSDT",
            side="Buy",
            size=0.1,
            entry_price=49000.0,
            mark_price=50000.0,
            unrealized_pnl=100.0,
            realized_pnl=0.0
        )
        
        metrics = risk_manager._calculate_position_metrics(position, market_data)
        
        assert metrics["position_value"] == 5000.0  # 0.1 * 50000
        assert metrics["unrealized_pnl"] == 100.0
        assert metrics["position_risk"] > 0
        assert metrics["position_size_percent"] > 0
    
    def test_calculate_position_metrics_no_position(self, risk_manager):
        """Test position metrics calculation with no position"""
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
        
        metrics = risk_manager._calculate_position_metrics(None, market_data)
        
        assert metrics["position_value"] == 0.0
        assert metrics["unrealized_pnl"] == 0.0
        assert metrics["position_risk"] == 0.0
        assert metrics["position_size_percent"] == 0.0
    
    def test_calculate_market_risk(self, risk_manager):
        """Test market risk calculation"""
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
        
        risk = risk_manager._calculate_market_risk(market_data)
        
        assert "volatility" in risk
        assert "trend_strength" in risk
        assert "volume_risk" in risk
        assert "price_change_risk" in risk
        assert 0 <= risk["volatility"] <= 1
        assert 0 <= risk["trend_strength"] <= 1
    
    def test_calculate_portfolio_risk(self, risk_manager):
        """Test portfolio risk calculation"""
        account_balance = 10000.0
        position = Position(
            symbol="BTCUSDT",
            side="Buy",
            size=0.1,
            entry_price=49000.0,
            mark_price=50000.0,
            unrealized_pnl=100.0,
            realized_pnl=0.0
        )
        
        risk = risk_manager._calculate_portfolio_risk(account_balance, position)
        
        assert "total_risk" in risk
        assert "leverage_risk" in risk
        assert "concentration_risk" in risk
        assert 0 <= risk["total_risk"] <= 1
        assert 0 <= risk["leverage_risk"] <= 1
        assert 0 <= risk["concentration_risk"] <= 1
    
    def test_calculate_max_position_size(self, risk_manager):
        """Test maximum position size calculation"""
        account_balance = 10000.0
        market_risk = {
            "volatility": 0.05,
            "trend_strength": 0.5,
            "volume_risk": 0.5,
            "price_change_risk": 0.5
        }
        portfolio_risk = {
            "total_risk": 0.2,
            "leverage_risk": 0.3,
            "concentration_risk": 0.4
        }
        
        max_size = risk_manager._calculate_max_position_size(account_balance, market_risk, portfolio_risk)
        
        assert 0 <= max_size <= 0.2  # Should be capped at 20%
        assert max_size > 0  # Should be positive
    
    def test_calculate_stop_take_levels(self, risk_manager):
        """Test stop loss and take profit level calculation"""
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
        
        market_risk = {
            "volatility": 0.05,
            "trend_strength": 0.5,
            "volume_risk": 0.5,
            "price_change_risk": 0.5
        }
        
        stop_loss, take_profit = risk_manager._calculate_stop_take_levels(market_data, market_risk)
        
        assert stop_loss is not None
        assert take_profit is not None
        assert stop_loss < market_data.price
        assert take_profit > market_data.price
    
    def test_perform_risk_checks(self, risk_manager):
        """Test risk checks performance"""
        risk_metrics = {
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
        
        market_analysis = Mock()
        market_analysis.confidence = 0.8
        
        checks = risk_manager._perform_risk_checks(risk_metrics, market_analysis)
        
        assert "daily_loss_ok" in checks
        assert "daily_trades_ok" in checks
        assert "position_size_ok" in checks
        assert "portfolio_risk_ok" in checks
        assert "volatility_ok" in checks
        assert "account_balance_ok" in checks
        assert "analysis_confidence_ok" in checks
        assert "can_trade" in checks
        assert isinstance(checks["can_trade"], bool)
    
    def test_determine_risk_level(self, risk_manager):
        """Test risk level determination"""
        # Low risk scenario
        low_risk_checks = {
            "can_trade": True,
            "daily_loss_ok": True,
            "daily_trades_ok": True,
            "position_size_ok": True,
            "portfolio_risk_ok": True,
            "volatility_ok": True,
            "account_balance_ok": True,
            "analysis_confidence_ok": True
        }
        low_risk_metrics = {"portfolio_risk": 0.2}
        
        risk_level = risk_manager._determine_risk_level(low_risk_checks, low_risk_metrics)
        assert risk_level == "LOW"
        
        # High risk scenario
        high_risk_checks = {
            "can_trade": False,
            "daily_loss_ok": False,
            "daily_trades_ok": False,
            "position_size_ok": False,
            "portfolio_risk_ok": False,
            "volatility_ok": False,
            "account_balance_ok": False,
            "analysis_confidence_ok": False
        }
        high_risk_metrics = {"portfolio_risk": 0.8}
        
        risk_level = risk_manager._determine_risk_level(high_risk_checks, high_risk_metrics)
        assert risk_level == "HIGH"
    
    def test_generate_risk_recommendations(self, risk_manager):
        """Test risk recommendations generation"""
        # All checks pass
        good_checks = {
            "daily_loss_ok": True,
            "daily_trades_ok": True,
            "position_size_ok": True,
            "portfolio_risk_ok": True,
            "volatility_ok": True,
            "account_balance_ok": True,
            "analysis_confidence_ok": True
        }
        
        recommendations = risk_manager._generate_risk_recommendations(good_checks, "LOW")
        assert len(recommendations) > 0
        assert "LOW RISK" in recommendations[0]
        
        # Some checks fail
        bad_checks = {
            "daily_loss_ok": False,
            "daily_trades_ok": True,
            "position_size_ok": False,
            "portfolio_risk_ok": True,
            "volatility_ok": True,
            "account_balance_ok": True,
            "analysis_confidence_ok": True
        }
        
        recommendations = risk_manager._generate_risk_recommendations(bad_checks, "HIGH")
        assert len(recommendations) > 1
        assert any("Daily loss limit exceeded" in rec for rec in recommendations)
        assert any("Position size too large" in rec for rec in recommendations)
    
    def test_create_order(self, risk_manager):
        """Test order creation"""
        trading_decision = TradingDecision(
            signal=TradeSignal.BUY,
            confidence=0.8,
            position_size=0.1,
            reasoning="Strong buy signal",
            market_analysis=Mock()
        )
        
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
        
        order = risk_manager._create_order(trading_decision, market_data, 0.1)
        
        assert order.symbol == "BTCUSDT"
        assert order.side.value == "Buy"
        assert order.quantity > 0
    
    def test_reset_daily_counters_if_needed(self, risk_manager):
        """Test daily counters reset"""
        # Set initial values
        risk_manager.daily_pnl = 100.0
        risk_manager.daily_trades = 5
        risk_manager.last_reset_date = datetime.now().date()
        
        # Should not reset on same day
        risk_manager._reset_daily_counters_if_needed()
        assert risk_manager.daily_pnl == 100.0
        assert risk_manager.daily_trades == 5
        
        # Should reset on new day
        risk_manager.last_reset_date = datetime.now().date() - timedelta(days=1)
        risk_manager._reset_daily_counters_if_needed()
        assert risk_manager.daily_pnl == 0.0
        assert risk_manager.daily_trades == 0
    
    @pytest.mark.asyncio
    async def test_assess_risk(self, risk_manager):
        """Test comprehensive risk assessment"""
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
        
        market_analysis = Mock()
        market_analysis.confidence = 0.8
        
        position = Position(
            symbol="BTCUSDT",
            side="Buy",
            size=0.1,
            entry_price=49000.0,
            mark_price=50000.0,
            unrealized_pnl=100.0,
            realized_pnl=0.0
        )
        
        result = await risk_manager.assess_risk(market_data, market_analysis, position)
        
        assert "risk_level" in result
        assert "risk_metrics" in result
        assert "risk_checks" in result
        assert "recommendations" in result
        assert "can_trade" in result
        assert "max_position_size" in result
        assert "stop_loss_level" in result
        assert "take_profit_level" in result
    
    @pytest.mark.asyncio
    async def test_execute_trade(self, risk_manager):
        """Test trade execution"""
        trading_decision = TradingDecision(
            signal=TradeSignal.BUY,
            confidence=0.8,
            position_size=0.1,
            reasoning="Strong buy signal",
            market_analysis=Mock()
        )
        
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
        
        # Mock successful order placement
        risk_manager.bybit_client.place_order.return_value = {
            "retCode": 0,
            "result": {"orderId": "12345"}
        }
        
        result = await risk_manager.execute_trade(trading_decision, market_data, None)
        
        assert "success" in result
        assert "order_id" in result
        assert "order" in result
        assert "risk_assessment" in result
    
    def test_error_handling(self, risk_manager):
        """Test error handling in various methods"""
        # Test with invalid data
        result = risk_manager._extract_account_balance({})
        assert result == 0.0
        
        # Test with None values
        result = risk_manager._calculate_position_metrics(None, None)
        assert result["position_value"] == 0.0
        
        # Test with invalid market data
        invalid_market_data = MarketData(
            symbol="BTCUSDT",
            price=0.0,  # Invalid price
            volume=0.0,
            timestamp=datetime.now(),
            high_24h=0.0,
            low_24h=0.0,
            change_24h=0.0,
            change_percent_24h=0.0
        )
        
        risk = risk_manager._calculate_market_risk(invalid_market_data)
        assert "volatility" in risk
        assert risk["volatility"] >= 0