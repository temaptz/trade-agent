"""
LangGraph агент для торговли биткойном
"""
from typing import Dict, List, Optional, Any, TypedDict
from langchain_ollama import OllamaLLM
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from loguru import logger
import json
import time

from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from config import settings

class TradingState(TypedDict):
    """Состояние торгового агента"""
    messages: List[Any]
    current_price: Optional[float]
    market_analysis: Optional[Dict]
    news_analysis: Optional[Dict]
    trading_decision: Optional[Dict]
    confidence: float
    reasoning: str

class TradingAgent:
    """Торговый агент на основе LangGraph"""
    
    def __init__(self):
        """Инициализация агента"""
        self.llm = OllamaLLM(model="gemma2:9b")
        self.bybit_client = BybitClient()
        self.market_analyzer = MarketAnalyzer()
        self.news_analyzer = NewsAnalyzer()
        
        # Создаем граф
        self.graph = self._create_graph()
        logger.info("TradingAgent инициализирован")
    
    def _create_graph(self) -> StateGraph:
        """Создать граф состояний агента"""
        
        # Определяем узлы
        workflow = StateGraph(TradingState)
        
        # Добавляем узлы
        workflow.add_node("analyze_market", self._analyze_market_node)
        workflow.add_node("analyze_news", self._analyze_news_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("execute_trade", self._execute_trade_node)
        
        # Определяем переходы
        workflow.set_entry_point("analyze_market")
        workflow.add_edge("analyze_market", "analyze_news")
        workflow.add_edge("analyze_news", "make_decision")
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
    
    def _analyze_market_node(self, state: TradingState) -> TradingState:
        """Узел анализа рынка"""
        try:
            logger.info("Анализируем состояние рынка...")
            
            # Получаем текущую цену
            current_price = self.bybit_client.get_current_price()
            
            # Получаем анализ рынка
            market_analysis = self.market_analyzer.get_market_summary()
            
            state["current_price"] = current_price
            state["market_analysis"] = market_analysis
            
            logger.info(f"Анализ рынка завершен. Цена: {current_price}")
            return state
            
        except Exception as e:
            logger.error(f"Ошибка при анализе рынка: {e}")
            state["market_analysis"] = {"error": str(e)}
            return state
    
    def _analyze_news_node(self, state: TradingState) -> TradingState:
        """Узел анализа новостей"""
        try:
            logger.info("Анализируем новостной фон...")
            
            # Получаем анализ новостей
            news_analysis = self.news_analyzer.get_news_summary()
            
            state["news_analysis"] = news_analysis
            
            logger.info("Анализ новостей завершен")
            return state
            
        except Exception as e:
            logger.error(f"Ошибка при анализе новостей: {e}")
            state["news_analysis"] = {"error": str(e)}
            return state
    
    def _make_decision_node(self, state: TradingState) -> TradingState:
        """Узел принятия торгового решения"""
        try:
            logger.info("Принимаем торговое решение...")
            
            # Подготавливаем данные для ИИ
            market_data = state.get("market_analysis", {})
            news_data = state.get("news_analysis", {})
            current_price = state.get("current_price", 0)
            
            # Создаем промпт для ИИ
            prompt = self._create_decision_prompt(market_data, news_data, current_price)
            
            # Получаем решение от ИИ
            response = self.llm.invoke(prompt)
            
            # Парсим ответ
            decision = self._parse_ai_decision(str(response))
            
            state["trading_decision"] = decision
            state["confidence"] = decision.get("confidence", 0)
            state["reasoning"] = decision.get("reasoning", "")
            
            logger.info(f"Торговое решение принято: {decision.get('action', 'WAIT')}")
            return state
            
        except Exception as e:
            logger.error(f"Ошибка при принятии решения: {e}")
            state["trading_decision"] = {"action": "WAIT", "confidence": 0, "reasoning": f"Ошибка: {e}"}
            return state
    
    def _execute_trade_node(self, state: TradingState) -> TradingState:
        """Узел выполнения торговой операции"""
        try:
            decision = state.get("trading_decision", {})
            action = decision.get("action", "WAIT")
            confidence = decision.get("confidence", 0)
            
            if action == "WAIT" or confidence < settings.min_confidence_threshold:
                logger.info("Торговая операция не выполняется - низкая уверенность")
                return state
            
            current_price = state.get("current_price", 0)
            if current_price == 0:
                logger.error("Не удалось получить текущую цену")
                return state
            
            # Рассчитываем размер позиции
            position_size = self.bybit_client.calculate_position_size(current_price)
            
            if action == "BUY":
                logger.info(f"Выполняем покупку {position_size} BTC по цене {current_price}")
                result = self.bybit_client.place_market_order("Buy", position_size)
                
            elif action == "SELL":
                logger.info(f"Выполняем продажу {position_size} BTC по цене {current_price}")
                result = self.bybit_client.place_market_order("Sell", position_size)
            
            else:
                logger.info("Неизвестное действие, пропускаем")
                return state
            
            # Обновляем состояние
            state["trading_decision"]["executed"] = True
            state["trading_decision"]["result"] = result
            
            logger.info("Торговая операция выполнена")
            return state
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении торговой операции: {e}")
            state["trading_decision"]["error"] = str(e)
            return state
    
    def _should_execute_trade(self, state: TradingState) -> str:
        """Определить, нужно ли выполнять торговую операцию"""
        decision = state.get("trading_decision", {})
        action = decision.get("action", "WAIT")
        confidence = decision.get("confidence", 0)
        
        if action != "WAIT" and confidence >= settings.min_confidence_threshold:
            return "execute"
        else:
            return "wait"
    
    def _create_decision_prompt(self, market_data: Dict, news_data: Dict, current_price: float) -> str:
        """Создать промпт для принятия решения"""
        
        prompt = f"""
Ты - профессиональный торговый ИИ-агент для торговли биткойном. Проанализируй следующие данные и прими торговое решение.

ТЕКУЩАЯ ЦЕНА: {current_price} USDT

АНАЛИЗ РЫНКА:
{json.dumps(market_data, indent=2, ensure_ascii=False)}

АНАЛИЗ НОВОСТЕЙ:
{json.dumps(news_data, indent=2, ensure_ascii=False)}

ИНСТРУКЦИИ:
1. Проанализируй технические индикаторы (RSI, MACD, Bollinger Bands, SMA)
2. Учти новостной фон и общую тональность рынка
3. Оцени риск и потенциальную прибыль
4. Прими решение: BUY, SELL или WAIT
5. Оцени свою уверенность от 0 до 1
6. Объясни свое решение

ОТВЕТ В ФОРМАТЕ JSON:
{{
    "action": "BUY|SELL|WAIT",
    "confidence": 0.85,
    "reasoning": "Детальное объяснение решения",
    "risk_assessment": "Оценка рисков",
    "expected_outcome": "Ожидаемый результат"
}}

ВАЖНО: Будь осторожен и консервативен. Не торгуй при высокой неопределенности.
"""
        return prompt
    
    def _parse_ai_decision(self, response: str) -> Dict:
        """Парсить решение ИИ из ответа"""
        try:
            # Ищем JSON в ответе
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                decision = json.loads(json_match.group())
                return decision
            else:
                # Если JSON не найден, пытаемся извлечь информацию из текста
                return self._extract_decision_from_text(response)
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге решения ИИ: {e}")
            return {"action": "WAIT", "confidence": 0, "reasoning": f"Ошибка парсинга: {e}"}
    
    def _extract_decision_from_text(self, text: str) -> Dict:
        """Извлечь решение из текстового ответа"""
        text_lower = text.lower()
        
        # Определяем действие
        if "buy" in text_lower and "sell" not in text_lower:
            action = "BUY"
        elif "sell" in text_lower and "buy" not in text_lower:
            action = "SELL"
        else:
            action = "WAIT"
        
        # Извлекаем уверенность (ищем числа от 0 до 1)
        import re
        confidence_match = re.search(r'0\.\d+', text)
        confidence = float(confidence_match.group()) if confidence_match else 0.5
        
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": text[:200] + "..." if len(text) > 200 else text
        }
    
    def run_trading_cycle(self) -> Dict:
        """Запустить один цикл торговли"""
        try:
            logger.info("Запускаем торговый цикл...")
            
            # Инициализируем состояние
            initial_state = {
                "messages": [],
                "current_price": None,
                "market_analysis": None,
                "news_analysis": None,
                "trading_decision": None,
                "confidence": 0,
                "reasoning": ""
            }
            
            # Запускаем граф
            result = self.graph.invoke(initial_state)
            
            logger.info("Торговый цикл завершен")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в торговом цикле: {e}")
            return {"error": str(e)}
    
    def get_trading_summary(self) -> Dict:
        """Получить сводку по торговле"""
        try:
            # Получаем текущую цену
            current_price = self.bybit_client.get_current_price()
            
            # Получаем баланс
            balance = self.bybit_client.get_account_balance()
            
            # Получаем открытые ордера
            open_orders = self.bybit_client.get_open_orders()
            
            # Получаем позиции
            positions = self.bybit_client.get_positions()
            
            summary = {
                "current_price": current_price,
                "balance": balance,
                "open_orders": len(open_orders),
                "positions": len(positions),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка при получении сводки: {e}")
            return {"error": str(e)}