"""
Клиент для работы с Bybit API
"""
import asyncio
from typing import Optional, Dict, Any, List
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket
from loguru import logger
from config import settings
from models import MarketData, Position, TradingState

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
            await self.ws_client.connect()
            self.is_connected = True
            logger.info("WebSocket подключен к Bybit")
        except Exception as e:
            logger.error(f"Ошибка подключения к WebSocket: {e}")
            self.is_connected = False
    
    async def disconnect_websocket(self):
        """Отключение от WebSocket"""
        if self.ws_client and self.is_connected:
            await self.ws_client.disconnect()
            self.is_connected = False
            logger.info("WebSocket отключен от Bybit")
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Получение баланса аккаунта"""
        try:
            response = self.http_client.get_wallet_balance(accountType="UNIFIED")
            if response['retCode'] == 0:
                return response['result']
            else:
                logger.error(f"Ошибка получения баланса: {response['retMsg']}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return {}
    
    def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Получение текущей цены"""
        try:
            symbol = symbol or settings.trading_symbol
            response = self.http_client.get_tickers(category="linear", symbol=symbol)
            if response['retCode'] == 0 and response['result']['list']:
                return float(response['result']['list'][0]['lastPrice'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            return None
    
    def get_market_data(self, symbol: str = None) -> Optional[MarketData]:
        """Получение рыночных данных"""
        try:
            symbol = symbol or settings.trading_symbol
            response = self.http_client.get_tickers(category="linear", symbol=symbol)
            if response['retCode'] == 0 and response['result']['list']:
                data = response['result']['list'][0]
                return MarketData(
                    symbol=symbol,
                    price=float(data['lastPrice']),
                    volume=float(data['volume24h']),
                    change_24h=float(data['price24hPcnt']) * float(data['lastPrice']),
                    change_percent_24h=float(data['price24hPcnt']) * 100,
                    high_24h=float(data['highPrice24h']),
                    low_24h=float(data['lowPrice24h']),
                    timestamp=data['time']
                )
            return None
        except Exception as e:
            logger.error(f"Ошибка получения рыночных данных: {e}")
            return None
    
    def get_positions(self) -> List[Position]:
        """Получение открытых позиций"""
        try:
            response = self.http_client.get_positions(category="linear", symbol=settings.trading_symbol)
            positions = []
            if response['retCode'] == 0 and response['result']['list']:
                for pos_data in response['result']['list']:
                    if float(pos_data['size']) > 0:  # Только открытые позиции
                        position = Position(
                            symbol=pos_data['symbol'],
                            side=pos_data['side'],
                            size=float(pos_data['size']),
                            entry_price=float(pos_data['avgPrice']),
                            current_price=float(pos_data['markPrice']),
                            unrealized_pnl=float(pos_data['unrealisedPnl']),
                            timestamp=pos_data['updatedTime']
                        )
                        positions.append(position)
            return positions
        except Exception as e:
            logger.error(f"Ошибка получения позиций: {e}")
            return []
    
    def place_order(self, side: str, quantity: float, order_type: str = "Market", 
                   price: Optional[float] = None, stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Dict[str, Any]:
        """Размещение ордера"""
        try:
            order_params = {
                "category": "linear",
                "symbol": settings.trading_symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(quantity),
                "timeInForce": "GTC"
            }
            
            if price and order_type == "Limit":
                order_params["price"] = str(price)
            
            if stop_loss:
                order_params["stopLoss"] = str(stop_loss)
            
            if take_profit:
                order_params["takeProfit"] = str(take_profit)
            
            response = self.http_client.place_order(**order_params)
            
            if response['retCode'] == 0:
                logger.info(f"Ордер размещен успешно: {response['result']}")
                return response['result']
            else:
                logger.error(f"Ошибка размещения ордера: {response['retMsg']}")
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка при размещении ордера: {e}")
            return {}
    
    def cancel_order(self, order_id: str) -> bool:
        """Отмена ордера"""
        try:
            response = self.http_client.cancel_order(
                category="linear",
                symbol=settings.trading_symbol,
                orderId=order_id
            )
            if response['retCode'] == 0:
                logger.info(f"Ордер {order_id} отменен")
                return True
            else:
                logger.error(f"Ошибка отмены ордера: {response['retMsg']}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при отмене ордера: {e}")
            return False
    
    def get_historical_klines(self, symbol: str = None, interval: str = "1", 
                            limit: int = 200) -> List[Dict[str, Any]]:
        """Получение исторических данных свечей"""
        try:
            symbol = symbol or settings.trading_symbol
            response = self.http_client.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=str(limit)
            )
            if response['retCode'] == 0:
                return response['result']['list']
            return []
        except Exception as e:
            logger.error(f"Ошибка получения исторических данных: {e}")
            return []
    
    def calculate_position_size(self, account_balance: float, risk_percentage: float, 
                              entry_price: float, stop_loss_price: float) -> float:
        """Расчет размера позиции на основе риска"""
        try:
            risk_amount = account_balance * (risk_percentage / 100)
            price_difference = abs(entry_price - stop_loss_price)
            if price_difference > 0:
                position_size = risk_amount / price_difference
                # Ограничиваем максимальным размером позиции
                max_size = account_balance * settings.max_position_size / entry_price
                return min(position_size, max_size)
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return 0.0