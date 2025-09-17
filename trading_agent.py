"""
LangGraph агент для торговых решений
"""
import logging
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import json

from langchain_ollama import OllamaLLM
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage, SystemMessage

from config import Config
from market_tools import MarketDataTool, NewsSearchTool, TechnicalAnalysisTool
from bybit_client import BybitClient
from error_handler import error_handler, retry_on_error, ErrorLogger, TradingError, APIError, MarketDataError

logger = logging.getLogger(__name__)

class TradingState(TypedDict):
    """Состояние торгового агента"""
    current_price: float
    market_data: Dict[str, Any]
    news_data: str
    technical_analysis: str
    account_balance: Dict[str, Any]
    decision: str
    reasoning: str
    action: Optional[Dict[str, Any]]
    error: Optional[str]

class TradingAgent:
    """Торговый агент на основе LangGraph"""
    
    def __init__(self, config: Config):
        self.config = config
        self.error_logger = ErrorLogger(logger)
        
        try:
            self.llm = OllamaLLM(
                base_url=config.OLLAMA_BASE_URL,
                model=config.OLLAMA_MODEL,
                temperature=0.1
            )
            
            # Инициализируем инструменты
            self.market_data_tool = MarketDataTool()
            self.news_tool = NewsSearchTool()
            self.technical_analysis_tool = TechnicalAnalysisTool()
            
            # Инициализируем клиент Bybit
            self.bybit_client = BybitClient(config)
            
            # Создаем граф состояний
            self.graph = self._create_graph()
            
        except Exception as e:
            self.error_logger.log_trading_error("initialization", e)
            raise TradingError(f"Ошибка инициализации торгового агента: {e}") from e
    
    def _create_graph(self) -> StateGraph:
        """Создает граф состояний для торгового агента"""
        
        # Создаем граф
        workflow = StateGraph(TradingState)
        
        # Добавляем узлы
        workflow.add_node("analyze_market", self._analyze_market)
        workflow.add_node("search_news", self._search_news)
        workflow.add_node("technical_analysis", self._technical_analysis)
        workflow.add_node("get_balance", self._get_balance)
        workflow.add_node("make_decision", self._make_decision)
        workflow.add_node("execute_trade", self._execute_trade)
        
        # Определяем поток выполнения
        workflow.set_entry_point("analyze_market")
        
        workflow.add_edge("analyze_market", "search_news")
        workflow.add_edge("search_news", "technical_analysis")
        workflow.add_edge("technical_analysis", "get_balance")
        workflow.add_edge("get_balance", "make_decision")
        workflow.add_conditional_edges(
            "make_decision",
            self._should_execute_trade,
            {
                "execute": "execute_trade",
                "wait": END
            }
        )
        workflow.add_edge("execute_trade", END)
        
        return workflow.compile()
    
    @error_handler
    @retry_on_error(max_retries=3, delay=2.0)
    def _analyze_market(self, state: TradingState) -> TradingState:
        """Анализирует рыночные данные"""
        try:
            logger.info("Анализ рыночных данных...")
            
            # Получаем текущую цену
            current_price = self.bybit_client.get_current_price()
            
            # Получаем рыночные данные
            market_data_str = self.market_data_tool._run(
                symbol=self.config.TRADING_SYMBOL,
                timeframe="1h",
                limit=100
            )
            
            # Парсим данные
            market_data = self._parse_market_data(market_data_str)
            
            state.update({
                "current_price": current_price,
                "market_data": market_data
            })
            
            logger.info(f"Текущая цена BTC: {current_price}")
            
        except Exception as e:
            logger.error(f"Ошибка анализа рынка: {e}")
            state["error"] = str(e)
        
        return state
    
    @error_handler
    @retry_on_error(max_retries=2, delay=1.0)
    def _search_news(self, state: TradingState) -> TradingState:
        """Ищет новости о криптовалютах"""
        try:
            logger.info("Поиск новостей...")
            
            # Поиск новостей о Bitcoin
            news_data = self.news_tool._run(
                query="Bitcoin BTC cryptocurrency news",
                days=3
            )
            
            state["news_data"] = news_data
            logger.info("Новости получены")
            
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            state["news_data"] = "Ошибка получения новостей"
        
        return state
    
    @error_handler
    @retry_on_error(max_retries=2, delay=1.0)
    def _technical_analysis(self, state: TradingState) -> TradingState:
        """Выполняет технический анализ"""
        try:
            logger.info("Технический анализ...")
            
            technical_analysis = self.technical_analysis_tool._run(
                symbol=self.config.TRADING_SYMBOL,
                timeframe="1h"
            )
            
            state["technical_analysis"] = technical_analysis
            logger.info("Технический анализ завершен")
            
        except Exception as e:
            logger.error(f"Ошибка технического анализа: {e}")
            state["technical_analysis"] = "Ошибка технического анализа"
        
        return state
    
    @error_handler
    @retry_on_error(max_retries=3, delay=1.0)
    def _get_balance(self, state: TradingState) -> TradingState:
        """Получает баланс аккаунта"""
        try:
            logger.info("Получение баланса аккаунта...")
            
            balance = self.bybit_client.get_account_balance()
            state["account_balance"] = balance
            
            logger.info(f"Баланс BTC: {balance['btc_balance']}, USDT: {balance['usdt_balance']}")
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            state["account_balance"] = {}
        
        return state
    
    def _make_decision(self, state: TradingState) -> TradingState:
        """Принимает торговое решение на основе анализа"""
        try:
            logger.info("Принятие торгового решения...")
            
            # Формируем контекст для ИИ
            context = self._build_decision_context(state)
            
            # Системное сообщение с инструкциями
            system_prompt = """
Ты - профессиональный торговый аналитик и трейдер. Твоя задача - проанализировать рыночную ситуацию и принять решение о покупке или продаже Bitcoin.

Доступные действия:
1. BUY - купить Bitcoin
2. SELL - продать Bitcoin  
3. HOLD - не торговать, ждать

При принятии решения учитывай:
- Технические индикаторы (RSI, MACD, скользящие средние)
- Рыночные новости и настроения
- Текущий баланс аккаунта
- Уровень риска

Отвечай в формате JSON:
{
    "decision": "BUY/SELL/HOLD",
    "reasoning": "Подробное обоснование решения",
    "confidence": 0.0-1.0
}
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context)
            ]
            
            # Получаем ответ от ИИ
            response = self.llm.invoke(messages)
            
            # Парсим ответ
            decision_data = self._parse_decision(response.content)
            
            state.update({
                "decision": decision_data["decision"],
                "reasoning": decision_data["reasoning"],
                "action": {
                    "type": decision_data["decision"],
                    "confidence": decision_data.get("confidence", 0.5)
                }
            })
            
            logger.info(f"Решение принято: {decision_data['decision']}")
            logger.info(f"Обоснование: {decision_data['reasoning']}")
            
        except Exception as e:
            logger.error(f"Ошибка принятия решения: {e}")
            state.update({
                "decision": "HOLD",
                "reasoning": f"Ошибка анализа: {str(e)}",
                "action": None
            })
        
        return state
    
    def _should_execute_trade(self, state: TradingState) -> str:
        """Определяет, нужно ли выполнять торговую операцию"""
        decision = state.get("decision", "HOLD")
        action = state.get("action", {})
        confidence = action.get("confidence", 0.0) if action else 0.0
        
        # Выполняем торговлю только если уверенность высокая и решение не HOLD
        if decision in ["BUY", "SELL"] and confidence > 0.7:
            return "execute"
        else:
            return "wait"
    
    @error_handler
    def _execute_trade(self, state: TradingState) -> TradingState:
        """Выполняет торговую операцию"""
        try:
            decision = state.get("decision")
            current_price = state.get("current_price", 0)
            balance = state.get("account_balance", {})
            
            if decision == "BUY":
                # Покупаем Bitcoin
                usdt_balance = balance.get("usdt_balance", 0)
                if usdt_balance > 10:  # Минимальная сумма для покупки
                    amount = self.bybit_client.calculate_position_size(
                        self.config.RISK_PERCENTAGE,
                        current_price
                    )
                    
                    order = self.bybit_client.place_buy_order(amount)
                    state["action"] = {
                        "type": "BUY",
                        "amount": amount,
                        "order_id": order.get("id"),
                        "status": "executed"
                    }
                    logger.info(f"Покупка выполнена: {amount} BTC")
                else:
                    logger.warning("Недостаточно средств для покупки")
                    state["action"] = {"type": "BUY", "status": "insufficient_funds"}
            
            elif decision == "SELL":
                # Продаем Bitcoin
                btc_balance = balance.get("btc_balance", 0)
                if btc_balance > 0.0001:  # Минимальная сумма для продажи
                    amount = min(btc_balance, self.config.MAX_POSITION_SIZE)
                    
                    order = self.bybit_client.place_sell_order(amount)
                    state["action"] = {
                        "type": "SELL",
                        "amount": amount,
                        "order_id": order.get("id"),
                        "status": "executed"
                    }
                    logger.info(f"Продажа выполнена: {amount} BTC")
                else:
                    logger.warning("Недостаточно BTC для продажи")
                    state["action"] = {"type": "SELL", "status": "insufficient_btc"}
            
        except Exception as e:
            logger.error(f"Ошибка выполнения торговой операции: {e}")
            state["action"] = {"type": decision, "status": "error", "error": str(e)}
        
        return state
    
    def _build_decision_context(self, state: TradingState) -> str:
        """Строит контекст для принятия решения"""
        context_parts = []
        
        # Рыночные данные
        market_data = state.get("market_data", {})
        if market_data:
            context_parts.append(f"Рыночные данные: {market_data}")
        
        # Технический анализ
        technical_analysis = state.get("technical_analysis", "")
        if technical_analysis:
            context_parts.append(f"Технический анализ: {technical_analysis}")
        
        # Новости
        news_data = state.get("news_data", "")
        if news_data:
            context_parts.append(f"Новости: {news_data}")
        
        # Баланс
        balance = state.get("account_balance", {})
        if balance:
            context_parts.append(f"Баланс: BTC={balance.get('btc_balance', 0)}, USDT={balance.get('usdt_balance', 0)}")
        
        return "\n\n".join(context_parts)
    
    def _parse_market_data(self, market_data_str: str) -> Dict[str, Any]:
        """Парсит строку с рыночными данными"""
        try:
            # Извлекаем числовые значения из строки
            import re
            
            price_match = re.search(r'current_price[:\s]+([\d.]+)', market_data_str)
            rsi_match = re.search(r'rsi[:\s]+([\d.]+)', market_data_str)
            macd_match = re.search(r'macd[:\s]+([\d.-]+)', market_data_str)
            
            return {
                "current_price": float(price_match.group(1)) if price_match else 0,
                "rsi": float(rsi_match.group(1)) if rsi_match else 0,
                "macd": float(macd_match.group(1)) if macd_match else 0
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга рыночных данных: {e}")
            return {}
    
    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """Парсит ответ ИИ с решением"""
        try:
            # Ищем JSON в ответе
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                decision_data = json.loads(json_match.group(0))
                return decision_data
            else:
                # Если JSON не найден, пытаемся извлечь решение из текста
                decision = "HOLD"
                if "BUY" in response.upper():
                    decision = "BUY"
                elif "SELL" in response.upper():
                    decision = "SELL"
                
                return {
                    "decision": decision,
                    "reasoning": response,
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Ошибка парсинга решения: {e}")
            return {
                "decision": "HOLD",
                "reasoning": "Ошибка парсинга ответа ИИ",
                "confidence": 0.0
            }
    
    def run_analysis(self) -> Dict[str, Any]:
        """Запускает полный цикл анализа и торговли"""
        try:
            logger.info("Запуск торгового анализа...")
            
            # Инициализируем состояние
            initial_state = TradingState(
                current_price=0.0,
                market_data={},
                news_data="",
                technical_analysis="",
                account_balance={},
                decision="HOLD",
                reasoning="",
                action=None,
                error=None
            )
            
            # Запускаем граф
            result = self.graph.invoke(initial_state)
            
            logger.info("Анализ завершен")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка выполнения анализа: {e}")
            return {
                "error": str(e),
                "decision": "HOLD",
                "reasoning": "Критическая ошибка системы"
            }