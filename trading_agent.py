"""
LangGraph trading agent with comprehensive tools and decision making
"""
import asyncio
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime, timedelta
import json
from loguru import logger

from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from ollama_client import OllamaClient
from config import config

class AgentState(TypedDict):
    """State for the trading agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    market_data: Optional[Dict]
    news_data: Optional[Dict]
    analysis: Optional[Dict]
    recommendation: Optional[Dict]
    trading_decision: Optional[Dict]
    error: Optional[str]

class TradingTools:
    """Collection of trading tools for the agent"""
    
    def __init__(self, bybit_client: BybitClient, market_analyzer: MarketAnalyzer, 
                 news_analyzer: NewsAnalyzer, ollama_client: OllamaClient):
        self.bybit_client = bybit_client
        self.market_analyzer = market_analyzer
        self.news_analyzer = news_analyzer
        self.ollama_client = ollama_client
    
    def get_market_data(self, symbol: str = None, timeframe: str = None) -> Dict:
        """Get current market data and technical analysis"""
        try:
            loop = asyncio.get_event_loop()
            analysis = loop.run_until_complete(
                self.market_analyzer.analyze_market(timeframe or config.trading_interval)
            )
            return {
                'success': True,
                'data': analysis,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_news_analysis(self, max_news: int = 20) -> Dict:
        """Get and analyze Bitcoin news"""
        try:
            loop = asyncio.get_event_loop()
            news_items = loop.run_until_complete(
                self.news_analyzer.search_bitcoin_news(max_results=max_news)
            )
            sentiment_analysis = loop.run_until_complete(
                self.news_analyzer.analyze_news_sentiment(news_items)
            )
            return {
                'success': True,
                'news_items': [item.__dict__ for item in news_items],
                'sentiment': sentiment_analysis,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting news analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_account_balance(self) -> Dict:
        """Get current account balance"""
        try:
            loop = asyncio.get_event_loop()
            balance = loop.run_until_complete(self.bybit_client.get_balance())
            return {
                'success': True,
                'balance': balance,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_open_orders(self) -> Dict:
        """Get current open orders"""
        try:
            loop = asyncio.get_event_loop()
            orders = loop.run_until_complete(self.bybit_client.get_open_orders())
            return {
                'success': True,
                'orders': orders,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def place_market_order(self, side: str, amount: float, symbol: str = None) -> Dict:
        """Place a market order"""
        try:
            symbol = symbol or config.trading_symbol
            loop = asyncio.get_event_loop()
            order = loop.run_until_complete(
                self.bybit_client.place_market_order(symbol, side, amount)
            )
            return {
                'success': True,
                'order': order,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def place_limit_order(self, side: str, amount: float, price: float, symbol: str = None) -> Dict:
        """Place a limit order"""
        try:
            symbol = symbol or config.trading_symbol
            loop = asyncio.get_event_loop()
            order = loop.run_until_complete(
                self.bybit_client.place_limit_order(symbol, side, amount, price)
            )
            return {
                'success': True,
                'order': order,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def cancel_order(self, order_id: str, symbol: str = None) -> Dict:
        """Cancel an order"""
        try:
            symbol = symbol or config.trading_symbol
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                self.bybit_client.cancel_order(order_id, symbol)
            )
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_with_llm(self, market_data: Dict, news_data: Dict) -> Dict:
        """Analyze market data using LLM"""
        try:
            loop = asyncio.get_event_loop()
            analysis = loop.run_until_complete(
                self.ollama_client.analyze_market_data(market_data, news_data)
            )
            return {
                'success': True,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing with LLM: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class BitcoinTradingAgent:
    """Main trading agent using LangGraph"""
    
    def __init__(self):
        # Initialize components
        self.bybit_client = BybitClient()
        self.market_analyzer = MarketAnalyzer(self.bybit_client)
        self.news_analyzer = NewsAnalyzer()
        self.ollama_client = OllamaClient()
        
        # Initialize tools
        self.trading_tools = TradingTools(
            self.bybit_client, 
            self.market_analyzer, 
            self.news_analyzer, 
            self.ollama_client
        )
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        # Define the workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_market", self._analyze_market_node)
        workflow.add_node("analyze_news", self._analyze_news_node)
        workflow.add_node("llm_analysis", self._llm_analysis_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("execute_trade", self._execute_trade_node)
        
        # Add edges
        workflow.add_edge("analyze_market", "analyze_news")
        workflow.add_edge("analyze_news", "llm_analysis")
        workflow.add_edge("llm_analysis", "make_decision")
        workflow.add_edge("make_decision", "execute_trade")
        workflow.add_edge("execute_trade", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_market")
        
        return workflow.compile()
    
    async def _analyze_market_node(self, state: AgentState) -> AgentState:
        """Analyze market data node"""
        try:
            logger.info("Analyzing market data...")
            
            # Get market analysis
            market_data = self.trading_tools.get_market_data()
            
            if market_data['success']:
                state['market_data'] = market_data['data']
                state['messages'].append(AIMessage(
                    content=f"Market analysis completed. Current price: {market_data['data']['price_data']['current_price']:.2f}"
                ))
            else:
                state['error'] = f"Market analysis failed: {market_data['error']}"
                state['messages'].append(AIMessage(content="Market analysis failed"))
            
            return state
            
        except Exception as e:
            logger.error(f"Error in market analysis node: {e}")
            state['error'] = str(e)
            return state
    
    async def _analyze_news_node(self, state: AgentState) -> AgentState:
        """Analyze news node"""
        try:
            logger.info("Analyzing news...")
            
            # Get news analysis
            news_data = self.trading_tools.get_news_analysis()
            
            if news_data['success']:
                state['news_data'] = news_data
                state['messages'].append(AIMessage(
                    content=f"News analysis completed. Sentiment: {news_data['sentiment']['overall_sentiment']}"
                ))
            else:
                state['error'] = f"News analysis failed: {news_data['error']}"
                state['messages'].append(AIMessage(content="News analysis failed"))
            
            return state
            
        except Exception as e:
            logger.error(f"Error in news analysis node: {e}")
            state['error'] = str(e)
            return state
    
    async def _llm_analysis_node(self, state: AgentState) -> AgentState:
        """LLM analysis node"""
        try:
            logger.info("Performing LLM analysis...")
            
            if state.get('market_data') and state.get('news_data'):
                # Perform LLM analysis
                llm_analysis = self.trading_tools.analyze_with_llm(
                    state['market_data'], 
                    state['news_data']
                )
                
                if llm_analysis['success']:
                    state['analysis'] = llm_analysis['analysis']
                    state['messages'].append(AIMessage(
                        content="LLM analysis completed successfully"
                    ))
                else:
                    state['error'] = f"LLM analysis failed: {llm_analysis['error']}"
            else:
                state['error'] = "Missing market or news data for LLM analysis"
            
            return state
            
        except Exception as e:
            logger.error(f"Error in LLM analysis node: {e}")
            state['error'] = str(e)
            return state
    
    async def _make_decision_node(self, state: AgentState) -> AgentState:
        """Make trading decision node"""
        try:
            logger.info("Making trading decision...")
            
            if state.get('analysis'):
                # Extract recommendation from analysis
                structured_analysis = state['analysis'].get('structured_analysis', {})
                recommendation = structured_analysis.get('recommendation', 'HOLD')
                confidence = structured_analysis.get('confidence', 50)
                
                # Create trading decision
                decision = {
                    'action': recommendation,
                    'confidence': confidence,
                    'reasoning': structured_analysis.get('reasoning', ''),
                    'timestamp': datetime.now().isoformat()
                }
                
                state['recommendation'] = decision
                state['messages'].append(AIMessage(
                    content=f"Trading decision: {recommendation} (confidence: {confidence}%)"
                ))
            else:
                state['error'] = "No analysis data available for decision making"
            
            return state
            
        except Exception as e:
            logger.error(f"Error in decision making node: {e}")
            state['error'] = str(e)
            return state
    
    async def _execute_trade_node(self, state: AgentState) -> AgentState:
        """Execute trade node"""
        try:
            logger.info("Executing trade...")
            
            if state.get('recommendation'):
                recommendation = state['recommendation']
                action = recommendation.get('action', 'HOLD')
                
                # Only execute trades with high confidence
                if recommendation.get('confidence', 0) >= 70:
                    if action in ['BUY', 'STRONG_BUY']:
                        # Place buy order (example with small amount)
                        trade_result = self.trading_tools.place_market_order('buy', 0.001)
                        state['trading_decision'] = trade_result
                        state['messages'].append(AIMessage(
                            content=f"Buy order executed: {trade_result}"
                        ))
                    elif action in ['SELL', 'STRONG_SELL']:
                        # Place sell order (example with small amount)
                        trade_result = self.trading_tools.place_market_order('sell', 0.001)
                        state['trading_decision'] = trade_result
                        state['messages'].append(AIMessage(
                            content=f"Sell order executed: {trade_result}"
                        ))
                    else:
                        state['messages'].append(AIMessage(
                            content="No trade executed - holding position"
                        ))
                else:
                    state['messages'].append(AIMessage(
                        content=f"Confidence too low ({recommendation.get('confidence', 0)}%) - no trade executed"
                    ))
            else:
                state['error'] = "No recommendation available for trade execution"
            
            return state
            
        except Exception as e:
            logger.error(f"Error in trade execution node: {e}")
            state['error'] = str(e)
            return state
    
    async def run_analysis_cycle(self) -> Dict:
        """Run a complete analysis cycle"""
        try:
            # Initialize state
            initial_state = {
                'messages': [SystemMessage(content="Starting Bitcoin trading analysis cycle")],
                'market_data': None,
                'news_data': None,
                'analysis': None,
                'recommendation': None,
                'trading_decision': None,
                'error': None
            }
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                'success': result.get('error') is None,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error running analysis cycle: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_market_summary(self) -> Dict:
        """Get a quick market summary"""
        try:
            # Get market data
            market_data = self.trading_tools.get_market_data()
            
            # Get news data
            news_data = self.trading_tools.get_news_analysis(max_news=10)
            
            # Get account balance
            balance = self.trading_tools.get_account_balance()
            
            return {
                'market': market_data,
                'news': news_data,
                'balance': balance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }