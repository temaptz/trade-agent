"""
Bybit API client for trading operations
"""
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
from loguru import logger
from config import config

class BybitClient:
    """Bybit trading client with comprehensive market data and trading capabilities"""
    
    def __init__(self):
        """Initialize Bybit client"""
        self.exchange = ccxt.bybit({
            'apiKey': config.bybit_api_key,
            'secret': config.bybit_secret_key,
            'sandbox': config.bybit_testnet,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # or 'future' for futures trading
            }
        })
        
        self.symbol = config.trading_symbol
        self.interval = config.trading_interval
        
    async def get_market_data(self, symbol: str = None, timeframe: str = None, limit: int = 100) -> pd.DataFrame:
        """Get OHLCV market data"""
        try:
            symbol = symbol or self.symbol
            timeframe = timeframe or self.interval
            
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_ohlcv, 
                symbol, 
                timeframe, 
                None, 
                limit
            )
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Retrieved {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            raise
    
    async def get_ticker(self, symbol: str = None) -> Dict:
        """Get current ticker data"""
        try:
            symbol = symbol or self.symbol
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_ticker, 
                symbol
            )
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise
    
    async def get_orderbook(self, symbol: str = None, limit: int = 20) -> Dict:
        """Get order book data"""
        try:
            symbol = symbol or self.symbol
            orderbook = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_order_book, 
                symbol, 
                limit
            )
            return orderbook
        except Exception as e:
            logger.error(f"Error fetching orderbook: {e}")
            raise
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_balance
            )
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    async def place_market_order(self, symbol: str, side: str, amount: float) -> Dict:
        """Place market order"""
        try:
            order = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.create_market_order, 
                symbol, 
                side, 
                amount
            )
            logger.info(f"Market order placed: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise
    
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict:
        """Place limit order"""
        try:
            order = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.create_limit_order, 
                symbol, 
                side, 
                amount, 
                price
            )
            logger.info(f"Limit order placed: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str = None) -> Dict:
        """Cancel order"""
        try:
            symbol = symbol or self.symbol
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.cancel_order, 
                order_id, 
                symbol
            )
            logger.info(f"Order cancelled: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            symbol = symbol or self.symbol
            orders = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_open_orders, 
                symbol
            )
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    async def get_trades(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get recent trades"""
        try:
            symbol = symbol or self.symbol
            trades = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_my_trades, 
                symbol, 
                None, 
                limit
            )
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            raise