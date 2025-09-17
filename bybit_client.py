"""
Bybit API client for trading operations
"""
import hmac
import hashlib
import time
import json
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime
import websocket
import threading
from loguru import logger

from config import config, BYBIT_BASE_URL
from models import MarketData, Order, Position, OrderSide, OrderType

class BybitClient:
    """Bybit API client for trading operations"""
    
    def __init__(self):
        self.api_key = config.bybit_api_key
        self.secret_key = config.bybit_secret_key
        self.base_url = BYBIT_BASE_URL
        self.session = requests.Session()
        self.ws = None
        self.ws_thread = None
        self.market_data_callback = None
        
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Generate API signature for authentication"""
        param_str = f"{timestamp}{self.api_key}5000{params}"
        return hmac.new(
            self.secret_key.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, params: str = "") -> Dict[str, str]:
        """Get headers for API requests"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(params, timestamp)
        
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": "5000",
            "Content-Type": "application/json"
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            url = f"{self.base_url}/v5/account/wallet-balance"
            params = {"accountType": "UNIFIED"}
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
            
            response = self.session.get(
                url,
                headers=self._get_headers(params_str),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise
    
    def get_market_data(self, symbol: str = None) -> MarketData:
        """Get current market data for symbol"""
        try:
            if symbol is None:
                symbol = config.trading_pair
                
            url = f"{self.base_url}/v5/market/tickers"
            params = {"category": "spot", "symbol": symbol}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["retCode"] != 0:
                raise Exception(f"API Error: {data['retMsg']}")
            
            ticker = data["result"]["list"][0]
            
            return MarketData(
                symbol=ticker["symbol"],
                price=float(ticker["lastPrice"]),
                volume=float(ticker["volume24h"]),
                timestamp=datetime.now(),
                high_24h=float(ticker["highPrice24h"]),
                low_24h=float(ticker["lowPrice24h"]),
                change_24h=float(ticker["price24hPcnt"]) * float(ticker["lastPrice"]),
                change_percent_24h=float(ticker["price24hPcnt"]) * 100
            )
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> List[Dict[str, Any]]:
        """Get historical kline data"""
        try:
            url = f"{self.base_url}/v5/market/kline"
            params = {
                "category": "spot",
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["retCode"] != 0:
                raise Exception(f"API Error: {data['retMsg']}")
            
            return data["result"]["list"]
        except Exception as e:
            logger.error(f"Error getting klines: {e}")
            raise
    
    def place_order(self, order: Order) -> Dict[str, Any]:
        """Place a trading order"""
        try:
            url = f"{self.base_url}/v5/order/create"
            
            payload = {
                "category": "spot",
                "symbol": order.symbol,
                "side": order.side.value,
                "orderType": order.order_type.value,
                "qty": str(order.quantity),
                "timeInForce": order.time_in_force
            }
            
            if order.price:
                payload["price"] = str(order.price)
            if order.stop_price:
                payload["stopPrice"] = str(order.stop_price)
            if order.reduce_only:
                payload["reduceOnly"] = order.reduce_only
            
            params_str = json.dumps(payload, separators=(',', ':'))
            
            response = self.session.post(
                url,
                headers=self._get_headers(params_str),
                data=params_str
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        """Get current positions"""
        try:
            url = f"{self.base_url}/v5/position/list"
            params = {"category": "spot"}
            if symbol:
                params["symbol"] = symbol
            
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
            
            response = self.session.get(
                url,
                headers=self._get_headers(params_str),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data["retCode"] != 0:
                raise Exception(f"API Error: {data['retMsg']}")
            
            positions = []
            for pos in data["result"]["list"]:
                if float(pos["size"]) > 0:  # Only non-zero positions
                    positions.append(Position(
                        symbol=pos["symbol"],
                        side=pos["side"],
                        size=float(pos["size"]),
                        entry_price=float(pos["avgPrice"]),
                        mark_price=float(pos["markPrice"]),
                        unrealized_pnl=float(pos["unrealisedPnl"]),
                        realized_pnl=float(pos["realisedPnl"])
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            url = f"{self.base_url}/v5/order/cancel"
            
            payload = {
                "category": "spot",
                "symbol": symbol,
                "orderId": order_id
            }
            
            params_str = json.dumps(payload, separators=(',', ':'))
            
            response = self.session.post(
                url,
                headers=self._get_headers(params_str),
                data=params_str
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            raise
    
    def start_websocket(self, callback=None):
        """Start websocket connection for real-time data"""
        self.market_data_callback = callback
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if self.market_data_callback:
                    self.market_data_callback(data)
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
        
        def on_open(ws):
            logger.info("WebSocket connection opened")
            # Subscribe to ticker data
            subscribe_msg = {
                "op": "subscribe",
                "args": [f"tickers.{config.trading_pair}"]
            }
            ws.send(json.dumps(subscribe_msg))
        
        def run_websocket():
            self.ws = websocket.WebSocketApp(
                "wss://stream-testnet.bybit.com/v5/public/spot",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            self.ws.run_forever()
        
        self.ws_thread = threading.Thread(target=run_websocket, daemon=True)
        self.ws_thread.start()
    
    def stop_websocket(self):
        """Stop websocket connection"""
        if self.ws:
            self.ws.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=5)