"""
Клиент для работы с Bybit API
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from config import settings

class BybitClient:
    def __init__(self):
        self.http_client = HTTP(
            testnet=settings.bybit_testnet,
            api_key=settings.bybit_api_key,
            api_secret=settings.bybit_secret_key
        )
        self.ws_client = None
        self.is_connected = False
        
    async def connect_websocket(self):
        """Подключение к WebSocket для получения данных в реальном времени"""
        try:
            self.ws_client = WebSocket(
                testnet=settings.bybit_testnet,
                channel_type="linear"
            )
            await self.ws_client.kline_stream(
                symbol=settings.trading_pair,
                interval=1,
                callback=self._handle_kline_data
            )
            self.is_connected = True
            logger.info("WebSocket подключен успешно")
        except Exception as e:
            logger.error(f"Ошибка подключения WebSocket: {e}")
            
    def _handle_kline_data(self, message):
        """Обработка данных свечей"""
        try:
            data = message.get('data', {})
            if data:
                logger.info(f"Получены данные свечи: {data}")
        except Exception as e:
            logger.error(f"Ошибка обработки данных свечи: {e}")
    
    async def get_account_balance(self) -> Dict:
        """Получение баланса аккаунта"""
        try:
            response = self.http_client.get_wallet_balance(accountType="UNIFIED")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {}
    
    async def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Получение текущей цены"""
        try:
            symbol = symbol or settings.trading_pair
            response = self.http_client.get_tickers(category="linear", symbol=symbol)
            if response.get('result', {}).get('list'):
                price = float(response['result']['list'][0]['lastPrice'])
                return price
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
        return None
    
    async def get_klines(self, symbol: str = None, interval: str = "1", limit: int = 200) -> pd.DataFrame:
        """Получение исторических данных свечей"""
        try:
            symbol = symbol or settings.trading_pair
            response = self.http_client.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if response.get('result', {}).get('list'):
                df = pd.DataFrame(response['result']['list'])
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
                df = df.astype({
                    'open': float, 'high': float, 'low': float, 
                    'close': float, 'volume': float, 'turnover': float
                })
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp')
                return df
        except Exception as e:
            logger.error(f"Ошибка получения исторических данных: {e}")
        return pd.DataFrame()
    
    async def get_orderbook(self, symbol: str = None, depth: int = 25) -> Dict:
        """Получение стакана заявок"""
        try:
            symbol = symbol or settings.trading_pair
            response = self.http_client.get_orderbook(
                category="linear",
                symbol=symbol,
                limit=depth
            )
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Ошибка получения стакана: {e}")
            return {}
    
    async def place_order(self, side: str, qty: float, price: Optional[float] = None, 
                         order_type: str = "Market") -> Dict:
        """Размещение ордера"""
        try:
            params = {
                "category": "linear",
                "symbol": settings.trading_pair,
                "side": side,
                "orderType": order_type,
                "qty": str(qty),
                "timeInForce": "GTC"
            }
            
            if price and order_type == "Limit":
                params["price"] = str(price)
            
            response = self.http_client.place_order(**params)
            logger.info(f"Ордер размещен: {response}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Ошибка размещения ордера: {e}")
            return {}
    
    async def get_open_orders(self) -> List[Dict]:
        """Получение открытых ордеров"""
        try:
            response = self.http_client.get_open_orders(
                category="linear",
                symbol=settings.trading_pair
            )
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Ошибка получения открытых ордеров: {e}")
            return []
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Отмена ордера"""
        try:
            response = self.http_client.cancel_order(
                category="linear",
                symbol=settings.trading_pair,
                orderId=order_id
            )
            logger.info(f"Ордер отменен: {order_id}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Ошибка отмены ордера: {e}")
            return {}
    
    async def get_positions(self) -> List[Dict]:
        """Получение позиций"""
        try:
            response = self.http_client.get_positions(
                category="linear",
                symbol=settings.trading_pair
            )
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Ошибка получения позиций: {e}")
            return []
    
    async def close_position(self, symbol: str = None) -> Dict:
        """Закрытие позиции"""
        try:
            symbol = symbol or settings.trading_pair
            response = self.http_client.close_position(
                category="linear",
                symbol=symbol
            )
            logger.info(f"Позиция закрыта: {symbol}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Ошибка закрытия позиции: {e}")
            return {}