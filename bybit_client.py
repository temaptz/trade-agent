"""
Модуль для работы с Bybit API
"""
import time
from typing import Dict, List, Optional, Tuple
from pybit.unified_trading import HTTP
from loguru import logger
from config import settings

class BybitClient:
    """Клиент для работы с Bybit API"""
    
    def __init__(self):
        """Инициализация клиента Bybit"""
        self.session = HTTP(
            testnet=settings.bybit_testnet,
            api_key=settings.bybit_api_key,
            api_secret=settings.bybit_secret_key,
        )
        self.trading_pair = settings.trading_pair
        logger.info(f"Bybit клиент инициализирован для {self.trading_pair}")
    
    def get_account_balance(self) -> Dict:
        """Получить баланс аккаунта"""
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")
            if response['retCode'] == 0:
                return response['result']
            else:
                logger.error(f"Ошибка получения баланса: {response['retMsg']}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return {}
    
    def get_current_price(self) -> Optional[float]:
        """Получить текущую цену торговой пары"""
        try:
            response = self.session.get_tickers(category="spot", symbol=self.trading_pair)
            if response['retCode'] == 0 and response['result']['list']:
                price = float(response['result']['list'][0]['lastPrice'])
                logger.info(f"Текущая цена {self.trading_pair}: {price}")
                return price
            else:
                logger.error(f"Ошибка получения цены: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении цены: {e}")
            return None
    
    def get_kline_data(self, interval: str = "1h", limit: int = 100) -> List[Dict]:
        """Получить исторические данные свечей"""
        try:
            response = self.session.get_kline(
                category="spot",
                symbol=self.trading_pair,
                interval=interval,
                limit=limit
            )
            if response['retCode'] == 0:
                klines = response['result']['list']
                # Конвертируем в удобный формат
                formatted_klines = []
                for kline in klines:
                    formatted_klines.append({
                        'timestamp': int(kline[0]),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                logger.info(f"Получено {len(formatted_klines)} свечей")
                return formatted_klines
            else:
                logger.error(f"Ошибка получения kline данных: {response['retMsg']}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении kline данных: {e}")
            return []
    
    def place_market_order(self, side: str, quantity: float) -> Dict:
        """Разместить рыночный ордер"""
        try:
            response = self.session.place_order(
                category="spot",
                symbol=self.trading_pair,
                side=side,
                orderType="Market",
                qty=str(quantity)
            )
            
            if response['retCode'] == 0:
                logger.info(f"Ордер размещен: {side} {quantity} {self.trading_pair}")
                return response['result']
            else:
                logger.error(f"Ошибка размещения ордера: {response['retMsg']}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка при размещении ордера: {e}")
            return {}
    
    def place_limit_order(self, side: str, quantity: float, price: float) -> Dict:
        """Разместить лимитный ордер"""
        try:
            response = self.session.place_order(
                category="spot",
                symbol=self.trading_pair,
                side=side,
                orderType="Limit",
                qty=str(quantity),
                price=str(price)
            )
            
            if response['retCode'] == 0:
                logger.info(f"Лимитный ордер размещен: {side} {quantity} {self.trading_pair} @ {price}")
                return response['result']
            else:
                logger.error(f"Ошибка размещения лимитного ордера: {response['retMsg']}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка при размещении лимитного ордера: {e}")
            return {}
    
    def get_open_orders(self) -> List[Dict]:
        """Получить открытые ордера"""
        try:
            response = self.session.get_open_orders(
                category="spot",
                symbol=self.trading_pair
            )
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                logger.error(f"Ошибка получения открытых ордеров: {response['retMsg']}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении открытых ордеров: {e}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """Отменить ордер"""
        try:
            response = self.session.cancel_order(
                category="spot",
                symbol=self.trading_pair,
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
    
    def get_positions(self) -> List[Dict]:
        """Получить текущие позиции"""
        try:
            response = self.session.get_positions(
                category="spot",
                symbol=self.trading_pair
            )
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                logger.error(f"Ошибка получения позиций: {response['retMsg']}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении позиций: {e}")
            return []
    
    def calculate_position_size(self, price: float, risk_percent: float = 1.0) -> float:
        """Рассчитать размер позиции на основе риска"""
        try:
            balance = self.get_account_balance()
            if not balance or 'list' not in balance:
                return settings.position_size
            
            # Получаем USDT баланс
            usdt_balance = 0
            for asset in balance['list']:
                if asset['coin'] == 'USDT':
                    usdt_balance = float(asset['totalWalletBalance'])
                    break
            
            if usdt_balance == 0:
                logger.warning("USDT баланс не найден, используем дефолтный размер позиции")
                return settings.position_size
            
            # Рассчитываем размер позиции
            risk_amount = usdt_balance * (risk_percent / 100)
            position_size = risk_amount / price
            
            # Ограничиваем максимальным размером позиции
            max_size = settings.max_position_size
            if position_size > max_size:
                position_size = max_size
                logger.warning(f"Размер позиции ограничен до {max_size}")
            
            logger.info(f"Рассчитанный размер позиции: {position_size:.6f}")
            return round(position_size, 6)
            
        except Exception as e:
            logger.error(f"Ошибка при расчете размера позиции: {e}")
            return settings.position_size