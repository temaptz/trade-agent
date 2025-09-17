"""
Торговый агент с использованием LangGraph и Ollama
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from config import settings
from models import TradingState, TradingSignal, TradeAction, Position, MarketAnalysis
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer

class TradingAgent:
    def __init__(self):
        self.bybit_client = BybitClient()
        self.market_analyzer = MarketAnalyzer(self.bybit_client)
        self.news_analyzer = NewsAnalyzer()
        
        # Инициализация Ollama
        self.llm = OllamaLLM(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url
        )
        
        # Создание графа состояний
        self.graph = self._create_trading_graph()
        
        # Текущее состояние
        self.current_state = TradingState()
        
    def _create_trading_graph(self) -> StateGraph:
        """Создание графа состояний для торгового агента"""
        
        # Определяем узлы графа
        workflow = StateGraph(TradingState)
        
        # Добавляем узлы
        workflow.add_node("analyze_market", self._analyze_market_node)
        workflow.add_node("analyze_news", self._analyze_news_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("execute_trade", self._execute_trade_node)
        workflow.add_node("update_position", self._update_position_node)
        workflow.add_node("risk_check", self._risk_check_node)
        
        # Определяем переходы
        workflow.set_entry_point("analyze_market")
        
        workflow.add_edge("analyze_market", "analyze_news")
        workflow.add_edge("analyze_news", "make_decision")
        workflow.add_edge("make_decision", "risk_check")
        workflow.add_edge("risk_check", "execute_trade")
        workflow.add_edge("execute_trade", "update_position")
        workflow.add_edge("update_position", END)
        
        return workflow.compile()
    
    async def _analyze_market_node(self, state: TradingState) -> Dict[str, Any]:
        """Анализ рыночных данных"""
        try:
            logger.info("Начинаем анализ рынка...")
            
            # Получаем анализ рынка
            market_analysis = await self.market_analyzer.analyze_market()
            
            # Обновляем состояние
            state.last_analysis = market_analysis
            
            logger.info(f"Анализ рынка завершен. Состояние: {market_analysis.market_condition}")
            logger.info(f"Рекомендация: {market_analysis.recommendation}, Уверенность: {market_analysis.confidence}")
            
            return {"last_analysis": market_analysis}
            
        except Exception as e:
            logger.error(f"Ошибка анализа рынка: {e}")
            return {}
    
    async def _analyze_news_node(self, state: TradingState) -> Dict[str, Any]:
        """Анализ новостей"""
        try:
            logger.info("Начинаем анализ новостей...")
            
            # Получаем анализ новостей
            news_analysis = await self.news_analyzer.get_comprehensive_news_analysis()
            
            # Обновляем анализ рынка с информацией о новостях
            if state.last_analysis:
                state.last_analysis.news_sentiment = news_analysis["sentiment_analysis"]["sentiment"]
            
            logger.info(f"Анализ новостей завершен. Тональность: {news_analysis['sentiment_analysis']['sentiment']}")
            logger.info(f"Найдено новостей: {news_analysis['total_news']}, Релевантных: {news_analysis['relevant_news']}")
            
            return {"news_analysis": news_analysis}
            
        except Exception as e:
            logger.error(f"Ошибка анализа новостей: {e}")
            return {}
    
    async def _make_decision_node(self, state: TradingState) -> Dict[str, Any]:
        """Принятие торгового решения с использованием LLM"""
        try:
            logger.info("Принимаем торговое решение...")
            
            if not state.last_analysis:
                logger.warning("Нет данных анализа рынка для принятия решения")
                return {"last_signal": TradingSignal(action=TradeAction.HOLD, confidence=0.0, reason="Нет данных анализа")}
            
            # Подготавливаем контекст для LLM
            context = self._prepare_llm_context(state)
            
            # Создаем промпт для LLM
            prompt = self._create_trading_prompt(context)
            
            # Получаем ответ от LLM
            messages = [
                SystemMessage(content="Ты опытный трейдер с 20-летним стажем. Анализируй данные и принимай обоснованные торговые решения."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Парсим ответ LLM
            trading_signal = self._parse_llm_response(str(response), state)
            
            # Обновляем состояние
            state.last_signal = trading_signal
            
            logger.info(f"Торговое решение принято: {trading_signal.action}")
            logger.info(f"Причина: {trading_signal.reason}")
            logger.info(f"Уверенность: {trading_signal.confidence}")
            
            return {"last_signal": trading_signal}
            
        except Exception as e:
            logger.error(f"Ошибка принятия решения: {e}")
            return {"last_signal": TradingSignal(action=TradeAction.HOLD, confidence=0.0, reason=f"Ошибка: {e}")}
    
    async def _risk_check_node(self, state: TradingState) -> Dict[str, Any]:
        """Проверка рисков"""
        try:
            logger.info("Проверяем риски...")
            
            if not state.last_signal:
                return {}
            
            # Проверяем максимальное количество убытков подряд
            if state.consecutive_losses >= 3:
                logger.warning("Слишком много убытков подряд, принудительно HOLD")
                state.last_signal.action = TradeAction.HOLD
                state.last_signal.reason += " (принудительный HOLD из-за серии убытков)"
                return {"last_signal": state.last_signal}
            
            # Проверяем минимальную уверенность
            if state.last_signal.confidence < 0.6:
                logger.warning("Низкая уверенность, принудительно HOLD")
                state.last_signal.action = TradeAction.HOLD
                state.last_signal.reason += " (принудительный HOLD из-за низкой уверенности)"
                return {"last_signal": state.last_signal}
            
            # Проверяем время последней сделки
            if state.last_trade_time:
                time_since_last_trade = datetime.now() - state.last_trade_time
                if time_since_last_trade < timedelta(minutes=30):
                    logger.warning("Слишком частые сделки, принудительно HOLD")
                    state.last_signal.action = TradeAction.HOLD
                    state.last_signal.reason += " (принудительный HOLD из-за частых сделок)"
                    return {"last_signal": state.last_signal}
            
            logger.info("Проверка рисков пройдена")
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка проверки рисков: {e}")
            return {}
    
    async def _execute_trade_node(self, state: TradingState) -> Dict[str, Any]:
        """Выполнение торговой операции"""
        try:
            logger.info("Выполняем торговую операцию...")
            
            if not state.last_signal or state.last_signal.action == TradeAction.HOLD:
                logger.info("Нет торгового сигнала или HOLD")
                return {}
            
            # Получаем текущую цену
            current_price = self.bybit_client.get_current_price()
            if not current_price:
                logger.error("Не удалось получить текущую цену")
                return {}
            
            # Получаем баланс аккаунта
            balance_data = self.bybit_client.get_account_balance()
            if not balance_data:
                logger.error("Не удалось получить баланс аккаунта")
                return {}
            
            # Извлекаем доступный баланс
            available_balance = 0.0
            if "list" in balance_data and balance_data["list"]:
                for account in balance_data["list"]:
                    if "coin" in account and account["coin"]:
                        for coin in account["coin"]:
                            if coin["coin"] == "USDT":
                                available_balance = float(coin["availableToWithdraw"])
                                break
            
            if available_balance < 10:  # Минимальный баланс $10
                logger.warning("Недостаточно средств для торговли")
                return {}
            
            # Рассчитываем размер позиции
            position_size = self.bybit_client.calculate_position_size(
                available_balance, 
                settings.risk_percentage, 
                current_price, 
                current_price * (1 - settings.stop_loss_percentage / 100)
            )
            
            if position_size < 0.001:  # Минимальный размер позиции
                logger.warning("Слишком малый размер позиции")
                return {}
            
            # Определяем сторону сделки
            side = "Buy" if state.last_signal.action == TradeAction.BUY else "Sell"
            
            # Рассчитываем уровни стоп-лосса и тейк-профита
            stop_loss = None
            take_profit = None
            
            if state.last_signal.action == TradeAction.BUY:
                stop_loss = current_price * (1 - settings.stop_loss_percentage / 100)
                take_profit = current_price * (1 + settings.take_profit_percentage / 100)
            else:
                stop_loss = current_price * (1 + settings.stop_loss_percentage / 100)
                take_profit = current_price * (1 - settings.take_profit_percentage / 100)
            
            # Размещаем ордер
            order_result = self.bybit_client.place_order(
                side=side,
                quantity=position_size,
                order_type="Market",
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if order_result:
                logger.info(f"Сделка выполнена: {side} {position_size} {settings.trading_symbol}")
                state.last_trade_time = datetime.now()
                
                # Обновляем счетчик убытков
                if state.last_signal.action in [TradeAction.BUY, TradeAction.SELL]:
                    # Здесь можно добавить логику отслеживания результата сделки
                    pass
            else:
                logger.error("Не удалось выполнить сделку")
            
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка выполнения сделки: {e}")
            return {}
    
    async def _update_position_node(self, state: TradingState) -> Dict[str, Any]:
        """Обновление информации о позициях"""
        try:
            logger.info("Обновляем информацию о позициях...")
            
            # Получаем текущие позиции
            positions = self.bybit_client.get_positions()
            
            if positions:
                state.current_position = positions[0]  # Берем первую позицию
                logger.info(f"Текущая позиция: {state.current_position.side} {state.current_position.size}")
            else:
                state.current_position = None
                logger.info("Нет открытых позиций")
            
            # Получаем баланс аккаунта
            balance_data = self.bybit_client.get_account_balance()
            if balance_data and "list" in balance_data and balance_data["list"]:
                for account in balance_data["list"]:
                    if "coin" in account and account["coin"]:
                        for coin in account["coin"]:
                            if coin["coin"] == "USDT":
                                state.account_balance = float(coin["walletBalance"])
                                state.available_balance = float(coin["availableToWithdraw"])
                                break
            
            logger.info(f"Баланс аккаунта: {state.account_balance} USDT")
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка обновления позиций: {e}")
            return {}
    
    def _prepare_llm_context(self, state: TradingState) -> Dict[str, Any]:
        """Подготовка контекста для LLM"""
        context = {
            "current_time": datetime.now().isoformat(),
            "trading_symbol": settings.trading_symbol,
            "account_balance": state.account_balance,
            "available_balance": state.available_balance,
            "consecutive_losses": state.consecutive_losses,
            "current_position": None
        }
        
        if state.current_position:
            context["current_position"] = {
                "side": state.current_position.side,
                "size": state.current_position.size,
                "entry_price": state.current_position.entry_price,
                "current_price": state.current_position.current_price,
                "unrealized_pnl": state.current_position.unrealized_pnl
            }
        
        if state.last_analysis:
            context["market_analysis"] = {
                "market_condition": state.last_analysis.market_condition,
                "price_trend": state.last_analysis.price_trend,
                "volatility": state.last_analysis.volatility,
                "recommendation": state.last_analysis.recommendation,
                "confidence": state.last_analysis.confidence,
                "news_sentiment": state.last_analysis.news_sentiment,
                "technical_indicators": {
                    "rsi": state.last_analysis.technical_indicators.rsi,
                    "macd": state.last_analysis.technical_indicators.macd,
                    "macd_signal": state.last_analysis.technical_indicators.macd_signal,
                    "sma_20": state.last_analysis.technical_indicators.sma_20,
                    "sma_50": state.last_analysis.technical_indicators.sma_50
                }
            }
        
        return context
    
    def _create_trading_prompt(self, context: Dict[str, Any]) -> str:
        """Создание промпта для LLM"""
        prompt = f"""
Анализируй следующие данные и прими торговое решение:

ТЕКУЩЕЕ ВРЕМЯ: {context['current_time']}
ТОРГОВЫЙ СИМВОЛ: {context['trading_symbol']}
БАЛАНС АККАУНТА: {context['account_balance']} USDT
ДОСТУПНЫЙ БАЛАНС: {context['available_balance']} USDT
ПОДРЯД УБЫТКОВ: {context['consecutive_losses']}

"""
        
        if context.get('current_position'):
            pos = context['current_position']
            prompt += f"""
ТЕКУЩАЯ ПОЗИЦИЯ:
- Сторона: {pos['side']}
- Размер: {pos['size']}
- Цена входа: {pos['entry_price']}
- Текущая цена: {pos['current_price']}
- Нереализованная P&L: {pos['unrealized_pnl']}

"""
        
        if context.get('market_analysis'):
            ma = context['market_analysis']
            prompt += f"""
АНАЛИЗ РЫНКА:
- Состояние рынка: {ma['market_condition']}
- Тренд цены: {ma['price_trend']}
- Волатильность: {ma['volatility']:.2f}%
- Рекомендация: {ma['recommendation']}
- Уверенность: {ma['confidence']:.2f}
- Тональность новостей: {ma.get('news_sentiment', 'неизвестно')}

ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:
- RSI: {ma['technical_indicators'].get('rsi', 'N/A')}
- MACD: {ma['technical_indicators'].get('macd', 'N/A')}
- MACD Signal: {ma['technical_indicators'].get('macd_signal', 'N/A')}
- SMA 20: {ma['technical_indicators'].get('sma_20', 'N/A')}
- SMA 50: {ma['technical_indicators'].get('sma_50', 'N/A')}

"""
        
        prompt += """
ПРИНЯТИЕ РЕШЕНИЯ:
Проанализируй все данные и прими решение: BUY, SELL или HOLD.

Ответь в формате JSON:
{
    "action": "BUY|SELL|HOLD",
    "confidence": 0.0-1.0,
    "reason": "подробное обоснование решения",
    "price_target": "целевая цена (если есть)",
    "stop_loss": "уровень стоп-лосса (если есть)",
    "take_profit": "уровень тейк-профита (если есть)"
}

Учитывай:
1. Технический анализ
2. Тональность новостей
3. Текущую позицию
4. Риск-менеджмент
5. Общую рыночную ситуацию
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, state: TradingState) -> TradingSignal:
        """Парсинг ответа LLM"""
        try:
            import json
            import re
            
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                action = TradeAction(data.get("action", "HOLD"))
                confidence = float(data.get("confidence", 0.5))
                reason = data.get("reason", "Решение принято LLM")
                price_target = data.get("price_target")
                stop_loss = data.get("stop_loss")
                take_profit = data.get("take_profit")
                
                return TradingSignal(
                    action=action,
                    confidence=confidence,
                    reason=reason,
                    price_target=float(price_target) if price_target else None,
                    stop_loss=float(stop_loss) if stop_loss else None,
                    take_profit=float(take_profit) if take_profit else None
                )
            else:
                # Если JSON не найден, пытаемся извлечь информацию из текста
                action = TradeAction.HOLD
                confidence = 0.5
                reason = "Не удалось распарсить ответ LLM"
                
                if "BUY" in response.upper():
                    action = TradeAction.BUY
                elif "SELL" in response.upper():
                    action = TradeAction.SELL
                
                return TradingSignal(
                    action=action,
                    confidence=confidence,
                    reason=reason
                )
                
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа LLM: {e}")
            return TradingSignal(
                action=TradeAction.HOLD,
                confidence=0.0,
                reason=f"Ошибка парсинга: {e}"
            )
    
    async def run_trading_cycle(self) -> Dict[str, Any]:
        """Запуск одного цикла торговли"""
        try:
            logger.info("Запускаем торговый цикл...")
            
            # Запускаем граф состояний
            result = await self.graph.ainvoke(self.current_state)
            
            logger.info("Торговый цикл завершен")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка торгового цикла: {e}")
            return {}
    
    async def start_trading(self, interval_minutes: int = 30):
        """Запуск непрерывной торговли"""
        try:
            logger.info(f"Запускаем торговлю с интервалом {interval_minutes} минут")
            
            while True:
                try:
                    await self.run_trading_cycle()
                    await asyncio.sleep(interval_minutes * 60)
                except KeyboardInterrupt:
                    logger.info("Получен сигнал остановки")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в торговом цикле: {e}")
                    await asyncio.sleep(60)  # Ждем минуту перед повтором
                    
        except Exception as e:
            logger.error(f"Критическая ошибка торговли: {e}")
        finally:
            await self.bybit_client.disconnect_websocket()