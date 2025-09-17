"""
Клиент для работы с Bybit API
"""
import ccxt
import logging
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class BybitClient:
    """Клиент для работы с Bybit API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.exchange = ccxt.bybit({
            'apiKey': config.BYBIT_API_KEY,
            'secret': config.BYBIT_SECRET_KEY,
            'sandbox': config.BYBIT_TESTNET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # Используем спотовую торговлю
            }
        })
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Получает баланс аккаунта"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance.get('total', {}),
                'free': balance.get('free', {}),
                'used': balance.get('used', {}),
                'btc_balance': balance.get('free', {}).get('BTC', 0),
                'usdt_balance': balance.get('free', {}).get('USDT', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            raise
    
    def get_current_price(self, symbol: str = None) -> float:
        """Получает текущую цену"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            raise
    
    def place_buy_order(self, amount: float, symbol: str = None) -> Dict[str, Any]:
        """Размещает ордер на покупку"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            order = self.exchange.create_market_buy_order(symbol, amount)
            logger.info(f"Ордер на покупку размещен: {order}")
            return order
        except Exception as e:
            logger.error(f"Ошибка размещения ордера на покупку: {e}")
            raise
    
    def place_sell_order(self, amount: float, symbol: str = None) -> Dict[str, Any]:
        """Размещает ордер на продажу"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            order = self.exchange.create_market_sell_order(symbol, amount)
            logger.info(f"Ордер на продажу размещен: {order}")
            return order
        except Exception as e:
            logger.error(f"Ошибка размещения ордера на продажу: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Получает открытые ордера"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Ошибка получения открытых ордеров: {e}")
            return []
    
    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Отменяет ордер"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Ордер {order_id} отменен")
            return True
        except Exception as e:
            logger.error(f"Ошибка отмены ордера: {e}")
            return False
    
    def get_trading_fees(self, symbol: str = None) -> Dict[str, float]:
        """Получает торговые комиссии"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            fees = self.exchange.fetch_trading_fees(symbol)
            return fees
        except Exception as e:
            logger.error(f"Ошибка получения комиссий: {e}")
            return {'maker': 0.001, 'taker': 0.001}  # Дефолтные комиссии
    
    def calculate_position_size(self, risk_percentage: float, current_price: float) -> float:
        """Вычисляет размер позиции на основе риска"""
        try:
            balance = self.get_account_balance()
            usdt_balance = balance['usdt_balance']
            
            # Рассчитываем размер позиции на основе процента риска
            risk_amount = usdt_balance * (risk_percentage / 100)
            position_size = risk_amount / current_price
            
            # Ограничиваем максимальным размером позиции
            max_size = self.config.MAX_POSITION_SIZE
            return min(position_size, max_size)
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return self.config.TRADE_AMOUNT
    
    def get_market_data(self, symbol: str = None, timeframe: str = '1h', limit: int = 100) -> List[Dict[str, Any]]:
        """Получает рыночные данные"""
        try:
            symbol = symbol or self.config.TRADING_SYMBOL
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            data = []
            for candle in ohlcv:
                data.append({
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return data
        except Exception as e:
            logger.error(f"Ошибка получения рыночных данных: {e}")
            return []