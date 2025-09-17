"""Trading management system for Bybit API."""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pybit.unified_trading import HTTP
from loguru import logger
import json

class BybitTradingManager:
    """Manages trading operations on Bybit."""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # Initialize Bybit client
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=secret_key,
        )
        
        self.positions = {}
        self.orders = {}
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")
            return response
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get current positions."""
        try:
            response = self.session.get_positions(
                category="linear",
                symbol=symbol
            )
            return response
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    def get_current_price(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """Get current market price."""
        try:
            response = self.session.get_tickers(
                category="linear",
                symbol=symbol
            )
            if response['retCode'] == 0 and response['result']['list']:
                return float(response['result']['list'][0]['lastPrice'])
            return None
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    def place_market_order(self, symbol: str, side: str, qty: float, 
                          stop_loss: Optional[float] = None, 
                          take_profit: Optional[float] = None) -> Dict[str, Any]:
        """Place a market order."""
        try:
            # Place main order
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": "Market",
                "qty": str(qty),
                "timeInForce": "IOC"
            }
            
            response = self.session.place_order(**order_params)
            
            if response['retCode'] == 0:
                order_id = response['result']['orderId']
                logger.info(f"Order placed successfully: {order_id}")
                
                # Place stop loss if specified
                if stop_loss:
                    self._place_stop_loss(symbol, side, qty, stop_loss)
                
                # Place take profit if specified
                if take_profit:
                    self._place_take_profit(symbol, side, qty, take_profit)
                
                return response
            else:
                logger.error(f"Order failed: {response}")
                return response
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    def _place_stop_loss(self, symbol: str, side: str, qty: float, stop_price: float) -> None:
        """Place stop loss order."""
        try:
            stop_side = "Sell" if side == "Buy" else "Buy"
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": stop_side,
                "orderType": "Stop",
                "qty": str(qty),
                "stopPrice": str(stop_price),
                "timeInForce": "GTC"
            }
            
            response = self.session.place_order(**order_params)
            if response['retCode'] == 0:
                logger.info(f"Stop loss placed: {response['result']['orderId']}")
            else:
                logger.error(f"Stop loss failed: {response}")
                
        except Exception as e:
            logger.error(f"Error placing stop loss: {e}")
    
    def _place_take_profit(self, symbol: str, side: str, qty: float, take_profit_price: float) -> None:
        """Place take profit order."""
        try:
            tp_side = "Sell" if side == "Buy" else "Buy"
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": tp_side,
                "orderType": "Limit",
                "qty": str(qty),
                "price": str(take_profit_price),
                "timeInForce": "GTC"
            }
            
            response = self.session.place_order(**order_params)
            if response['retCode'] == 0:
                logger.info(f"Take profit placed: {response['result']['orderId']}")
            else:
                logger.error(f"Take profit failed: {response}")
                
        except Exception as e:
            logger.error(f"Error placing take profit: {e}")
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close all positions for a symbol."""
        try:
            positions = self.get_positions(symbol)
            if not positions or positions['retCode'] != 0:
                return {"retCode": -1, "retMsg": "No positions found"}
            
            results = []
            for position in positions['result']['list']:
                if float(position['size']) > 0:
                    side = "Sell" if position['side'] == "Buy" else "Buy"
                    qty = position['size']
                    
                    order_params = {
                        "category": "linear",
                        "symbol": symbol,
                        "side": side,
                        "orderType": "Market",
                        "qty": qty,
                        "timeInForce": "IOC"
                    }
                    
                    response = self.session.place_order(**order_params)
                    results.append(response)
                    logger.info(f"Closing position: {response}")
            
            return {"retCode": 0, "results": results}
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    def get_order_history(self, symbol: str = "BTCUSDT", limit: int = 10) -> List[Dict[str, Any]]:
        """Get order history."""
        try:
            response = self.session.get_order_history(
                category="linear",
                symbol=symbol,
                limit=limit
            )
            if response['retCode'] == 0:
                return response['result']['list']
            return []
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            return []
    
    def calculate_position_size(self, account_balance: float, risk_percent: float, 
                              entry_price: float, stop_loss_price: float) -> float:
        """Calculate position size based on risk management."""
        try:
            risk_amount = account_balance * (risk_percent / 100)
            price_risk = abs(entry_price - stop_loss_price)
            
            if price_risk == 0:
                return 0
            
            position_size = risk_amount / price_risk
            return round(position_size, 6)
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

class RiskManager:
    """Manages trading risks and position sizing."""
    
    def __init__(self, max_position_size: float, stop_loss_percent: float, 
                 take_profit_percent: float, risk_per_trade: float):
        self.max_position_size = max_position_size
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.risk_per_trade = risk_per_trade
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price."""
        if side == "Buy":
            return entry_price * (1 - self.stop_loss_percent / 100)
        else:
            return entry_price * (1 + self.stop_loss_percent / 100)
    
    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price."""
        if side == "Buy":
            return entry_price * (1 + self.take_profit_percent / 100)
        else:
            return entry_price * (1 - self.take_profit_percent / 100)
    
    def validate_trade(self, side: str, quantity: float, current_price: float) -> Dict[str, Any]:
        """Validate trade parameters."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check position size
        if quantity > self.max_position_size:
            validation['valid'] = False
            validation['errors'].append(f"Position size {quantity} exceeds maximum {self.max_position_size}")
        
        # Check if quantity is positive
        if quantity <= 0:
            validation['valid'] = False
            validation['errors'].append("Position size must be positive")
        
        # Check price
        if current_price <= 0:
            validation['valid'] = False
            validation['errors'].append("Invalid current price")
        
        return validation