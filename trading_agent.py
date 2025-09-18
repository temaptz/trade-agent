"""
Основной торговый агент на базе LangGraph
"""
import asyncio
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime, timedelta
from loguru import logger
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from ollama_client import OllamaClient
from config import settings

class AgentState(TypedDict):
    """Состояние агента"""
    # Данные рынка
    market_data: Optional[Dict]
    market_analysis: Optional[Dict]
    news_sentiment: Optional[Dict]
    ai_analysis: Optional[Dict]
    
    # Торговые данные
    current_price: Optional[float]
    positions: List[Dict]
    orders: List[Dict]
    balance: Optional[Dict]
    
    # Состояние агента
    last_update: Optional[str]
    trading_enabled: bool
    risk_level: str
    current_action: Optional[str]
    decision_reason: Optional[str]
    
    # Результаты
    trading_plan: Optional[Dict]
    risk_analysis: Optional[Dict]
    final_decision: Optional[Dict]

class TradingAgent:
    def __init__(self):
        self.bybit_client = BybitClient()
        self.market_analyzer = MarketAnalyzer()
        self.news_analyzer = NewsAnalyzer()
        self.ollama_client = OllamaClient()
        
        # Создание графа состояний
        self.graph = self._create_graph()
        
        # Состояние агента
        self.state = {
            "market_data": None,
            "market_analysis": None,
            "news_sentiment": None,
            "ai_analysis": None,
            "current_price": None,
            "positions": [],
            "orders": [],
            "balance": None,
            "last_update": None,
            "trading_enabled": True,
            "risk_level": "medium",
            "current_action": None,
            "decision_reason": None,
            "trading_plan": None,
            "risk_analysis": None,
            "final_decision": None
        }
    
    def _create_graph(self) -> StateGraph:
        """Создание графа состояний агента"""
        graph = StateGraph(AgentState)
        
        # Добавление узлов
        graph.add_node("collect_data", self._collect_market_data)
        graph.add_node("analyze_market", self._analyze_market)
        graph.add_node("analyze_news", self._analyze_news)
        graph.add_node("ai_analysis", self._ai_analysis)
        graph.add_node("risk_assessment", self._risk_assessment)
        graph.add_node("generate_plan", self._generate_trading_plan)
        graph.add_node("make_decision", self._make_trading_decision)
        graph.add_node("execute_trade", self._execute_trade)
        graph.add_node("monitor", self._monitor_positions)
        
        # Добавление рёбер
        graph.add_edge("collect_data", "analyze_market")
        graph.add_edge("analyze_market", "analyze_news")
        graph.add_edge("analyze_news", "ai_analysis")
        graph.add_edge("ai_analysis", "risk_assessment")
        graph.add_edge("risk_assessment", "generate_plan")
        graph.add_edge("generate_plan", "make_decision")
        graph.add_edge("make_decision", "execute_trade")
        graph.add_edge("execute_trade", "monitor")
        graph.add_edge("monitor", END)
        
        # Установка точки входа
        graph.set_entry_point("collect_data")
        
        return graph.compile()
    
    async def _collect_market_data(self, state: AgentState) -> AgentState:
        """Сбор рыночных данных"""
        try:
            logger.info("Сбор рыночных данных...")
            
            # Получение исторических данных
            klines = await self.bybit_client.get_klines(limit=200)
            
            # Получение текущей цены
            current_price = await self.bybit_client.get_current_price()
            
            # Получение баланса
            balance = await self.bybit_client.get_account_balance()
            
            # Получение позиций
            positions = await self.bybit_client.get_positions()
            
            # Получение ордеров
            orders = await self.bybit_client.get_open_orders()
            
            state.update({
                "market_data": klines.to_dict('records') if not klines.empty else [],
                "current_price": current_price,
                "balance": balance,
                "positions": positions,
                "orders": orders,
                "last_update": datetime.now().isoformat()
            })
            
            logger.info(f"Данные собраны: цена {current_price}, позиций {len(positions)}")
            
        except Exception as e:
            logger.error(f"Ошибка сбора данных: {e}")
            state["current_action"] = "error"
            state["decision_reason"] = f"Ошибка сбора данных: {e}"
        
        return state
    
    async def _analyze_market(self, state: AgentState) -> AgentState:
        """Анализ рыночных данных"""
        try:
            logger.info("Анализ рыночных данных...")
            
            if not state.get("market_data"):
                state["current_action"] = "error"
                state["decision_reason"] = "Нет рыночных данных"
                return state
            
            # Конвертация данных в DataFrame
            import pandas as pd
            df = pd.DataFrame(state["market_data"])
            
            if not df.empty:
                # Комплексный анализ
                analysis = await self.market_analyzer.comprehensive_analysis(df)
                state["market_analysis"] = analysis
                
                logger.info(f"Анализ завершен: тренд {analysis.get('trend', {}).get('trend', 'unknown')}")
            else:
                state["current_action"] = "error"
                state["decision_reason"] = "Пустые рыночные данные"
        
        except Exception as e:
            logger.error(f"Ошибка анализа рынка: {e}")
            state["current_action"] = "error"
            state["decision_reason"] = f"Ошибка анализа: {e}"
        
        return state
    
    async def _analyze_news(self, state: AgentState) -> AgentState:
        """Анализ новостей"""
        try:
            logger.info("Анализ новостей...")
            
            async with self.news_analyzer:
                # Получение настроения рынка
                sentiment = await self.news_analyzer.get_market_sentiment()
                state["news_sentiment"] = sentiment
                
                logger.info(f"Настроение рынка: {sentiment.get('sentiment', 'unknown')}")
        
        except Exception as e:
            logger.error(f"Ошибка анализа новостей: {e}")
            state["news_sentiment"] = {"sentiment": "neutral", "confidence": 0.0}
        
        return state
    
    async def _ai_analysis(self, state: AgentState) -> AgentState:
        """ИИ анализ"""
        try:
            logger.info("ИИ анализ...")
            
            if not state.get("market_analysis") or not state.get("news_sentiment"):
                state["current_action"] = "error"
                state["decision_reason"] = "Недостаточно данных для ИИ анализа"
                return state
            
            async with self.ollama_client:
                # Анализ с помощью ИИ
                ai_analysis = await self.ollama_client.analyze_market_data(
                    state["market_analysis"],
                    state["news_sentiment"]
                )
                state["ai_analysis"] = ai_analysis
                
                logger.info("ИИ анализ завершен")
        
        except Exception as e:
            logger.error(f"Ошибка ИИ анализа: {e}")
            state["ai_analysis"] = {"error": str(e)}
        
        return state
    
    async def _risk_assessment(self, state: AgentState) -> AgentState:
        """Оценка рисков"""
        try:
            logger.info("Оценка рисков...")
            
            if not state.get("market_analysis"):
                state["current_action"] = "error"
                state["decision_reason"] = "Нет данных для оценки рисков"
                return state
            
            async with self.ollama_client:
                # Анализ рисков
                risk_analysis = await self.ollama_client.analyze_risk(
                    state["market_analysis"],
                    state.get("positions", [])
                )
                state["risk_analysis"] = risk_analysis
                
                logger.info("Оценка рисков завершена")
        
        except Exception as e:
            logger.error(f"Ошибка оценки рисков: {e}")
            state["risk_analysis"] = {"error": str(e)}
        
        return state
    
    async def _generate_trading_plan(self, state: AgentState) -> AgentState:
        """Генерация торгового плана"""
        try:
            logger.info("Генерация торгового плана...")
            
            if not all([state.get("market_analysis"), state.get("news_sentiment")]):
                state["current_action"] = "error"
                state["decision_reason"] = "Недостаточно данных для плана"
                return state
            
            async with self.ollama_client:
                # Генерация плана
                trading_plan = await self.ollama_client.generate_trading_plan(
                    state["market_analysis"],
                    state["news_sentiment"],
                    state.get("positions", [])
                )
                state["trading_plan"] = trading_plan
                
                logger.info("Торговый план сгенерирован")
        
        except Exception as e:
            logger.error(f"Ошибка генерации плана: {e}")
            state["trading_plan"] = {"error": str(e)}
        
        return state
    
    async def _make_trading_decision(self, state: AgentState) -> AgentState:
        """Принятие торгового решения"""
        try:
            logger.info("Принятие торгового решения...")
            
            # Анализ всех данных
            decision = await self._analyze_decision_factors(state)
            state["final_decision"] = decision
            
            logger.info(f"Решение принято: {decision.get('action', 'HOLD')}")
        
        except Exception as e:
            logger.error(f"Ошибка принятия решения: {e}")
            state["final_decision"] = {"action": "HOLD", "reason": f"Ошибка: {e}"}
        
        return state
    
    async def _analyze_decision_factors(self, state: AgentState) -> Dict:
        """Анализ факторов для принятия решения"""
        try:
            factors = {
                "market_trend": "neutral",
                "news_sentiment": "neutral",
                "ai_recommendation": "HOLD",
                "risk_level": "medium",
                "confidence": 0.5
            }
            
            # Анализ тренда
            if state.get("market_analysis", {}).get("trend"):
                trend = state["market_analysis"]["trend"]
                factors["market_trend"] = trend.get("trend", "neutral")
            
            # Анализ новостей
            if state.get("news_sentiment"):
                sentiment = state["news_sentiment"]
                factors["news_sentiment"] = sentiment.get("sentiment", "neutral")
            
            # ИИ рекомендация
            if state.get("ai_analysis", {}).get("ai_analysis"):
                ai_data = state["ai_analysis"]["ai_analysis"]
                factors["ai_recommendation"] = ai_data.get("recommendation", "HOLD")
                factors["confidence"] = ai_data.get("confidence", 5) / 10.0
            
            # Принятие решения
            decision = self._make_final_decision(factors)
            
            return {
                "action": decision["action"],
                "reason": decision["reason"],
                "confidence": decision["confidence"],
                "factors": factors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа факторов: {e}")
            return {"action": "HOLD", "reason": f"Ошибка анализа: {e}", "confidence": 0.0}
    
    def _make_final_decision(self, factors: Dict) -> Dict:
        """Финальное решение на основе факторов"""
        try:
            # Подсчет голосов
            buy_signals = 0
            sell_signals = 0
            hold_signals = 0
            
            # Тренд
            if factors["market_trend"] == "bullish":
                buy_signals += 1
            elif factors["market_trend"] == "bearish":
                sell_signals += 1
            else:
                hold_signals += 1
            
            # Новости
            if factors["news_sentiment"] == "positive":
                buy_signals += 1
            elif factors["news_sentiment"] == "negative":
                sell_signals += 1
            else:
                hold_signals += 1
            
            # ИИ
            if factors["ai_recommendation"] == "BUY":
                buy_signals += 2  # Больший вес для ИИ
            elif factors["ai_recommendation"] == "SELL":
                sell_signals += 2
            else:
                hold_signals += 1
            
            # Принятие решения
            if buy_signals > sell_signals and buy_signals > hold_signals:
                action = "BUY"
                reason = f"Сигналы покупки: {buy_signals}"
            elif sell_signals > buy_signals and sell_signals > hold_signals:
                action = "SELL"
                reason = f"Сигналы продажи: {sell_signals}"
            else:
                action = "HOLD"
                reason = f"Неопределенность: покупка {buy_signals}, продажа {sell_signals}, удержание {hold_signals}"
            
            confidence = factors["confidence"]
            
            return {
                "action": action,
                "reason": reason,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Ошибка принятия решения: {e}")
            return {"action": "HOLD", "reason": f"Ошибка: {e}", "confidence": 0.0}
    
    async def _execute_trade(self, state: AgentState) -> AgentState:
        """Выполнение торговых операций"""
        try:
            decision = state.get("final_decision")
            if not decision:
                logger.warning("Нет решения для выполнения")
                return state
            
            action = decision.get("action", "HOLD")
            
            if action == "HOLD" or not state.get("trading_enabled", True):
                logger.info("Торговля не выполняется")
                return state
            
            # Проверка рисков
            if not await self._check_risk_limits(state):
                logger.warning("Превышены лимиты риска")
                state["current_action"] = "risk_limit_exceeded"
                return state
            
            # Выполнение операции
            if action == "BUY":
                await self._execute_buy(state)
            elif action == "SELL":
                await self._execute_sell(state)
            
            logger.info(f"Торговая операция выполнена: {action}")
        
        except Exception as e:
            logger.error(f"Ошибка выполнения торговли: {e}")
            state["current_action"] = "error"
            state["decision_reason"] = f"Ошибка торговли: {e}"
        
        return state
    
    async def _check_risk_limits(self, state: AgentState) -> bool:
        """Проверка лимитов риска"""
        try:
            # Проверка максимального риска
            balance = state.get("balance", {})
            if not balance:
                return False
            
            # Простая проверка - можно расширить
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки рисков: {e}")
            return False
    
    async def _execute_buy(self, state: AgentState):
        """Выполнение покупки"""
        try:
            # Расчет размера позиции
            amount = settings.trade_amount
            
            # Размещение ордера
            order = await self.bybit_client.place_order(
                side="Buy",
                qty=amount,
                order_type="Market"
            )
            
            logger.info(f"Ордер на покупку размещен: {order}")
        
        except Exception as e:
            logger.error(f"Ошибка покупки: {e}")
            raise
    
    async def _execute_sell(self, state: AgentState):
        """Выполнение продажи"""
        try:
            # Проверка позиций
            positions = state.get("positions", [])
            if not positions:
                logger.warning("Нет позиций для продажи")
                return
            
            # Закрытие позиций
            for position in positions:
                if position.get("side") == "Buy":
                    await self.bybit_client.close_position()
                    logger.info("Позиция закрыта")
        
        except Exception as e:
            logger.error(f"Ошибка продажи: {e}")
            raise
    
    async def _monitor_positions(self, state: AgentState) -> AgentState:
        """Мониторинг позиций"""
        try:
            logger.info("Мониторинг позиций...")
            
            # Обновление данных о позициях
            positions = await self.bybit_client.get_positions()
            state["positions"] = positions
            
            # Проверка стоп-лоссов и тейк-профитов
            await self._check_stop_losses(state)
            
            logger.info(f"Мониторинг завершен: {len(positions)} позиций")
        
        except Exception as e:
            logger.error(f"Ошибка мониторинга: {e}")
        
        return state
    
    async def _check_stop_losses(self, state: AgentState):
        """Проверка стоп-лоссов"""
        try:
            positions = state.get("positions", [])
            current_price = state.get("current_price")
            
            if not current_price:
                return
            
            for position in positions:
                # Простая логика стоп-лосса
                # Можно расширить более сложной логикой
                pass
        
        except Exception as e:
            logger.error(f"Ошибка проверки стоп-лоссов: {e}")
    
    async def run_cycle(self) -> Dict:
        """Запуск одного цикла агента"""
        try:
            logger.info("Запуск цикла агента...")
            
            # Выполнение графа
            final_state = await self.graph.ainvoke(self.state)
            
            # Обновление состояния
            self.state.update(final_state)
            
            logger.info("Цикл агента завершен")
            return final_state
        
        except Exception as e:
            logger.error(f"Ошибка выполнения цикла: {e}")
            return {"error": str(e)}
    
    async def start_trading(self):
        """Запуск торгового агента"""
        try:
            logger.info("Запуск торгового агента...")
            
            # Подключение к WebSocket
            await self.bybit_client.connect_websocket()
            
            # Основной цикл
            while True:
                try:
                    await self.run_cycle()
                    await asyncio.sleep(settings.market_analysis_interval)
                except KeyboardInterrupt:
                    logger.info("Остановка агента...")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в основном цикле: {e}")
                    await asyncio.sleep(60)  # Пауза при ошибке
        
        except Exception as e:
            logger.error(f"Ошибка запуска агента: {e}")
    
    def get_graph_mermaid(self) -> str:
        """Возвращает Mermaid диаграмму графа агента (flowchart)."""
        try:
            nodes = [
                "collect_data",
                "analyze_market",
                "analyze_news",
                "ai_analysis",
                "risk_assessment",
                "generate_plan",
                "make_decision",
                "execute_trade",
                "monitor",
                "END"
            ]
            edges = [
                ("collect_data", "analyze_market"),
                ("analyze_market", "analyze_news"),
                ("analyze_news", "ai_analysis"),
                ("ai_analysis", "risk_assessment"),
                ("risk_assessment", "generate_plan"),
                ("generate_plan", "make_decision"),
                ("make_decision", "execute_trade"),
                ("execute_trade", "monitor"),
                ("monitor", "END")
            ]
            lines = ["flowchart TD"]
            titles = {
                "collect_data": "Collect Data",
                "analyze_market": "Analyze Market",
                "analyze_news": "Analyze News",
                "ai_analysis": "AI Analysis",
                "risk_assessment": "Risk Assessment",
                "generate_plan": "Generate Plan",
                "make_decision": "Make Decision",
                "execute_trade": "Execute Trade",
                "monitor": "Monitor",
                "END": "END"
            }
            for node in nodes:
                if node == "END":
                    lines.append(f"    {node}((END))")
                else:
                    lines.append(f"    {node}[{titles.get(node, node)}]")
            for src, dst in edges:
                lines.append(f"    {src} --> {dst}")
            lines.append("    classDef action fill:#0ea5e9,stroke:#0369a1,color:#fff;")
            lines.append("    classDef end fill:#a3a3a3,stroke:#525252,color:#fff;")
            lines.append("    class collect_data,analyze_market,analyze_news,ai_analysis,risk_assessment,generate_plan,make_decision,execute_trade,monitor action;")
            lines.append("    class END end;")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Ошибка генерации Mermaid графа: {e}")
            return "flowchart TD\n    A[Error]"