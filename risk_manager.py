"""
Advanced risk management and position management system
"""
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json

from models import (
    TradingDecision, MarketData, Position, Order, OrderSide, OrderType,
    TradeSignal
)
from bybit_client import BybitClient
from config import config

class RiskManager:
    """Advanced risk management system for Bitcoin trading"""
    
    def __init__(self, bybit_client: BybitClient):
        self.bybit_client = bybit_client
        self.max_daily_loss = config.risk_percentage / 100
        self.max_position_size = config.max_position_size
        self.stop_loss_percentage = config.stop_loss_percentage / 100
        self.take_profit_percentage = config.take_profit_percentage / 100
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 10
        self.last_reset_date = datetime.now().date()
        
    async def assess_risk(self, market_data: MarketData, market_analysis: Any, current_position: Optional[Position]) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        try:
            logger.info("Assessing trading risk...")
            
            # Reset daily counters if new day
            self._reset_daily_counters_if_needed()
            
            # Calculate current risk metrics
            risk_metrics = await self._calculate_risk_metrics(market_data, current_position)
            
            # Check risk limits
            risk_checks = self._perform_risk_checks(risk_metrics, market_analysis)
            
            # Determine overall risk level
            risk_level = self._determine_risk_level(risk_checks, risk_metrics)
            
            # Generate risk recommendations
            recommendations = self._generate_risk_recommendations(risk_checks, risk_level)
            
            risk_assessment = {
                "risk_level": risk_level,
                "risk_metrics": risk_metrics,
                "risk_checks": risk_checks,
                "recommendations": recommendations,
                "can_trade": risk_checks["can_trade"],
                "max_position_size": risk_metrics["max_allowed_position_size"],
                "stop_loss_level": risk_metrics["suggested_stop_loss"],
                "take_profit_level": risk_metrics["suggested_take_profit"]
            }
            
            logger.info(f"Risk assessment completed: {risk_level} risk level")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return self._get_default_risk_assessment()
    
    async def _calculate_risk_metrics(self, market_data: MarketData, current_position: Optional[Position]) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        try:
            # Get account balance
            account_info = self.bybit_client.get_account_info()
            account_balance = self._extract_account_balance(account_info)
            
            # Calculate position-based metrics
            position_metrics = self._calculate_position_metrics(current_position, market_data)
            
            # Calculate market risk metrics
            market_risk = self._calculate_market_risk(market_data)
            
            # Calculate portfolio risk
            portfolio_risk = self._calculate_portfolio_risk(account_balance, current_position)
            
            # Calculate maximum allowed position size
            max_position_size = self._calculate_max_position_size(
                account_balance, market_risk, portfolio_risk
            )
            
            # Calculate stop loss and take profit levels
            stop_loss, take_profit = self._calculate_stop_take_levels(
                market_data, market_risk
            )
            
            return {
                "account_balance": account_balance,
                "current_position_value": position_metrics["position_value"],
                "unrealized_pnl": position_metrics["unrealized_pnl"],
                "position_risk": position_metrics["position_risk"],
                "market_volatility": market_risk["volatility"],
                "market_trend": market_risk["trend_strength"],
                "portfolio_risk": portfolio_risk["total_risk"],
                "max_allowed_position_size": max_position_size,
                "suggested_stop_loss": stop_loss,
                "suggested_take_profit": take_profit,
                "daily_pnl": self.daily_pnl,
                "daily_trades": self.daily_trades
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return self._get_default_risk_metrics()
    
    def _extract_account_balance(self, account_info: Dict[str, Any]) -> float:
        """Extract account balance from Bybit API response"""
        try:
            if "result" in account_info and "list" in account_info["result"]:
                for account in account_info["result"]["list"]:
                    if account.get("accountType") == "UNIFIED":
                        for coin in account.get("coin", []):
                            if coin.get("coin") == "USDT":
                                return float(coin.get("walletBalance", 0))
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting account balance: {e}")
            return 0.0
    
    def _calculate_position_metrics(self, position: Optional[Position], market_data: MarketData) -> Dict[str, Any]:
        """Calculate position-specific risk metrics"""
        if not position:
            return {
                "position_value": 0.0,
                "unrealized_pnl": 0.0,
                "position_risk": 0.0,
                "position_size_percent": 0.0
            }
        
        try:
            position_value = position.size * position.mark_price
            unrealized_pnl = position.unrealized_pnl
            position_risk = abs(unrealized_pnl) / position_value if position_value > 0 else 0
            position_size_percent = position_value / (position_value + abs(unrealized_pnl)) if position_value > 0 else 0
            
            return {
                "position_value": position_value,
                "unrealized_pnl": unrealized_pnl,
                "position_risk": position_risk,
                "position_size_percent": position_size_percent
            }
        except Exception as e:
            logger.error(f"Error calculating position metrics: {e}")
            return {
                "position_value": 0.0,
                "unrealized_pnl": 0.0,
                "position_risk": 0.0,
                "position_size_percent": 0.0
            }
    
    def _calculate_market_risk(self, market_data: MarketData) -> Dict[str, Any]:
        """Calculate market-specific risk metrics"""
        try:
            # Calculate volatility based on 24h price range
            price_range = market_data.high_24h - market_data.low_24h
            volatility = price_range / market_data.price if market_data.price > 0 else 0
            
            # Calculate trend strength
            trend_strength = abs(market_data.change_percent_24h) / 100
            
            # Calculate volume risk
            volume_risk = 1.0 if market_data.volume > 0 else 0.5
            
            return {
                "volatility": volatility,
                "trend_strength": trend_strength,
                "volume_risk": volume_risk,
                "price_change_risk": abs(market_data.change_percent_24h) / 100
            }
        except Exception as e:
            logger.error(f"Error calculating market risk: {e}")
            return {
                "volatility": 0.05,
                "trend_strength": 0.5,
                "volume_risk": 0.5,
                "price_change_risk": 0.5
            }
    
    def _calculate_portfolio_risk(self, account_balance: float, current_position: Optional[Position]) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics"""
        try:
            if account_balance <= 0:
                return {"total_risk": 1.0, "leverage_risk": 1.0, "concentration_risk": 1.0}
            
            # Calculate current portfolio risk
            position_value = 0.0
            if current_position:
                position_value = current_position.size * current_position.mark_price
            
            portfolio_risk = position_value / account_balance if account_balance > 0 else 0
            
            # Calculate leverage risk
            leverage_risk = min(1.0, portfolio_risk * 2)  # Simplified leverage calculation
            
            # Calculate concentration risk
            concentration_risk = min(1.0, portfolio_risk * 1.5)
            
            return {
                "total_risk": portfolio_risk,
                "leverage_risk": leverage_risk,
                "concentration_risk": concentration_risk
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return {"total_risk": 0.5, "leverage_risk": 0.5, "concentration_risk": 0.5}
    
    def _calculate_max_position_size(self, account_balance: float, market_risk: Dict[str, Any], portfolio_risk: Dict[str, Any]) -> float:
        """Calculate maximum allowed position size"""
        try:
            if account_balance <= 0:
                return 0.0
            
            # Base position size
            base_size = min(self.max_position_size, 0.1)  # Max 10% of account
            
            # Adjust for market volatility
            volatility_adjustment = max(0.1, 1.0 - market_risk["volatility"] * 2)
            
            # Adjust for portfolio risk
            portfolio_adjustment = max(0.1, 1.0 - portfolio_risk["total_risk"] * 2)
            
            # Adjust for daily loss
            daily_loss_adjustment = max(0.1, 1.0 - abs(self.daily_pnl) / account_balance * 5)
            
            # Calculate final position size
            max_size = base_size * volatility_adjustment * portfolio_adjustment * daily_loss_adjustment
            
            return max(0.0, min(max_size, 0.2))  # Cap at 20% of account
            
        except Exception as e:
            logger.error(f"Error calculating max position size: {e}")
            return 0.05  # Default 5%
    
    def _calculate_stop_take_levels(self, market_data: MarketData, market_risk: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        try:
            current_price = market_data.price
            
            # Adjust stop loss based on volatility
            volatility_multiplier = 1.0 + market_risk["volatility"] * 2
            stop_loss_pct = self.stop_loss_percentage * volatility_multiplier
            take_profit_pct = self.take_profit_percentage * (1.0 + market_risk["trend_strength"])
            
            # Calculate levels
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + take_profit_pct)
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating stop/take levels: {e}")
            return market_data.price * 0.97, market_data.price * 1.06  # Default 3% stop, 6% take
    
    def _perform_risk_checks(self, risk_metrics: Dict[str, Any], market_analysis: Any) -> Dict[str, bool]:
        """Perform comprehensive risk checks"""
        try:
            checks = {}
            
            # Daily loss check
            checks["daily_loss_ok"] = abs(self.daily_pnl) < (risk_metrics["account_balance"] * self.max_daily_loss)
            
            # Daily trades check
            checks["daily_trades_ok"] = self.daily_trades < self.max_daily_trades
            
            # Position size check
            max_allowed = risk_metrics["max_allowed_position_size"]
            checks["position_size_ok"] = max_allowed > 0.01  # At least 1% minimum
            
            # Portfolio risk check
            checks["portfolio_risk_ok"] = risk_metrics["portfolio_risk"] < 0.8  # Max 80% portfolio risk
            
            # Market volatility check
            checks["volatility_ok"] = risk_metrics["market_volatility"] < 0.15  # Max 15% volatility
            
            # Account balance check
            checks["account_balance_ok"] = risk_metrics["account_balance"] > 100  # Min $100 balance
            
            # Market analysis confidence check
            if market_analysis:
                checks["analysis_confidence_ok"] = market_analysis.confidence > 0.3
            else:
                checks["analysis_confidence_ok"] = False
            
            # Overall can trade check
            checks["can_trade"] = all([
                checks["daily_loss_ok"],
                checks["daily_trades_ok"],
                checks["position_size_ok"],
                checks["portfolio_risk_ok"],
                checks["volatility_ok"],
                checks["account_balance_ok"],
                checks["analysis_confidence_ok"]
            ])
            
            return checks
            
        except Exception as e:
            logger.error(f"Error performing risk checks: {e}")
            return {"can_trade": False}
    
    def _determine_risk_level(self, risk_checks: Dict[str, bool], risk_metrics: Dict[str, Any]) -> str:
        """Determine overall risk level"""
        try:
            if not risk_checks.get("can_trade", False):
                return "HIGH"
            
            # Count failed checks
            failed_checks = sum(1 for check, passed in risk_checks.items() if not passed and check != "can_trade")
            
            # Determine risk level based on failed checks and metrics
            if failed_checks >= 3 or risk_metrics["portfolio_risk"] > 0.6:
                return "HIGH"
            elif failed_checks >= 1 or risk_metrics["portfolio_risk"] > 0.3:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return "HIGH"
    
    def _generate_risk_recommendations(self, risk_checks: Dict[str, bool], risk_level: str) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if not risk_checks.get("daily_loss_ok", True):
            recommendations.append("Daily loss limit exceeded - reduce position size or stop trading")
        
        if not risk_checks.get("daily_trades_ok", True):
            recommendations.append("Daily trade limit reached - wait for next day")
        
        if not risk_checks.get("position_size_ok", True):
            recommendations.append("Position size too large - reduce size or wait for better conditions")
        
        if not risk_checks.get("portfolio_risk_ok", True):
            recommendations.append("Portfolio risk too high - reduce exposure")
        
        if not risk_checks.get("volatility_ok", True):
            recommendations.append("Market volatility too high - wait for calmer conditions")
        
        if not risk_checks.get("account_balance_ok", True):
            recommendations.append("Account balance too low - deposit more funds")
        
        if not risk_checks.get("analysis_confidence_ok", True):
            recommendations.append("Analysis confidence too low - wait for clearer signals")
        
        if risk_level == "HIGH":
            recommendations.append("HIGH RISK - Consider reducing position size or avoiding trade")
        elif risk_level == "MEDIUM":
            recommendations.append("MEDIUM RISK - Trade with caution and smaller position size")
        else:
            recommendations.append("LOW RISK - Normal trading conditions")
        
        return recommendations
    
    async def execute_trade(self, trading_decision: TradingDecision, market_data: MarketData, current_position: Optional[Position]) -> Dict[str, Any]:
        """Execute trade with risk management"""
        try:
            logger.info(f"Executing trade: {trading_decision.signal}")
            
            # Check if we can trade
            risk_assessment = await self.assess_risk(market_data, trading_decision.market_analysis, current_position)
            
            if not risk_assessment["can_trade"]:
                return {
                    "success": False,
                    "error": "Risk checks failed - trade not allowed",
                    "risk_assessment": risk_assessment
                }
            
            # Calculate position size
            position_size = min(
                trading_decision.position_size,
                risk_assessment["max_position_size"]
            )
            
            if position_size < 0.01:  # Minimum position size
                return {
                    "success": False,
                    "error": "Position size too small",
                    "risk_assessment": risk_assessment
                }
            
            # Create order
            order = self._create_order(trading_decision, market_data, position_size)
            
            # Execute order
            result = self.bybit_client.place_order(order)
            
            if result.get("retCode") == 0:
                # Update daily counters
                self.daily_trades += 1
                
                # Log successful trade
                logger.info(f"Trade executed successfully: {result.get('result', {}).get('orderId')}")
                
                return {
                    "success": True,
                    "order_id": result.get("result", {}).get("orderId"),
                    "order": order.dict(),
                    "risk_assessment": risk_assessment
                }
            else:
                return {
                    "success": False,
                    "error": result.get("retMsg", "Unknown error"),
                    "risk_assessment": risk_assessment
                }
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                "success": False,
                "error": str(e),
                "risk_assessment": None
            }
    
    def _create_order(self, trading_decision: TradingDecision, market_data: MarketData, position_size: float) -> Order:
        """Create order based on trading decision"""
        try:
            # Calculate quantity
            quantity = (market_data.price * position_size) / market_data.price
            
            # Determine order side
            if trading_decision.signal == "BUY":
                side = OrderSide.BUY
            elif trading_decision.signal == "SELL":
                side = OrderSide.SELL
            else:
                raise ValueError("Invalid trading signal")
            
            # Create order
            order = Order(
                symbol=config.trading_pair,
                side=side,
                order_type=OrderType.MARKET,  # Use market orders for immediate execution
                quantity=quantity
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
            logger.info("Daily counters reset for new day")
    
    def _get_default_risk_assessment(self) -> Dict[str, Any]:
        """Get default risk assessment when calculation fails"""
        return {
            "risk_level": "HIGH",
            "risk_metrics": self._get_default_risk_metrics(),
            "risk_checks": {"can_trade": False},
            "recommendations": ["Risk calculation failed - trading disabled"],
            "can_trade": False,
            "max_position_size": 0.0,
            "stop_loss_level": 0.0,
            "take_profit_level": 0.0
        }
    
    def _get_default_risk_metrics(self) -> Dict[str, Any]:
        """Get default risk metrics when calculation fails"""
        return {
            "account_balance": 0.0,
            "current_position_value": 0.0,
            "unrealized_pnl": 0.0,
            "position_risk": 1.0,
            "market_volatility": 0.1,
            "market_trend": 0.5,
            "portfolio_risk": 1.0,
            "max_allowed_position_size": 0.0,
            "suggested_stop_loss": 0.0,
            "suggested_take_profit": 0.0,
            "daily_pnl": 0.0,
            "daily_trades": 0
        }