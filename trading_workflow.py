"""
LangGraph workflow for Bitcoin trading decisions
"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from models import TradingState, MarketData, TradingDecision, TradeSignal
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from sentiment_analyzer import SentimentAnalyzer
from risk_manager import RiskManager
from config import config

class TradingWorkflow:
    """LangGraph workflow for comprehensive trading decisions"""
    
    def __init__(self):
        self.bybit_client = BybitClient()
        self.market_analyzer = MarketAnalyzer(self.bybit_client)
        self.news_analyzer = NewsAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_manager = RiskManager(self.bybit_client)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(TradingState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("get_market_data", self._get_market_data)
        workflow.add_node("analyze_technical", self._analyze_technical)
        workflow.add_node("analyze_news", self._analyze_news)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment)
        workflow.add_node("assess_risk", self._assess_risk)
        workflow.add_node("make_decision", self._make_decision)
        workflow.add_node("execute_trade", self._execute_trade)
        workflow.add_node("handle_error", self._handle_error)
        
        # Add edges
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "get_market_data")
        workflow.add_edge("get_market_data", "analyze_technical")
        workflow.add_edge("analyze_technical", "analyze_news")
        workflow.add_edge("analyze_news", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "assess_risk")
        workflow.add_edge("assess_risk", "make_decision")
        workflow.add_edge("make_decision", "execute_trade")
        workflow.add_edge("execute_trade", END)
        
        # Error handling
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _initialize(self, state: TradingState) -> TradingState:
        """Initialize the trading workflow"""
        try:
            logger.info("Initializing trading workflow...")
            
            state.step = "get_market_data"
            state.error = None
            
            # Check if we're in trading hours (optional)
            current_hour = datetime.now().hour
            if not (6 <= current_hour <= 22):  # Trade only during active hours
                logger.info("Outside trading hours, skipping analysis")
                state.step = "end"
            
            return state
            
        except Exception as e:
            logger.error(f"Error in initialization: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _get_market_data(self, state: TradingState) -> TradingState:
        """Get current market data"""
        try:
            logger.info("Getting market data...")
            
            market_data = self.bybit_client.get_market_data(config.trading_pair)
            state.market_data = market_data
            
            logger.info(f"Market data retrieved: Price=${market_data.price}, Change={market_data.change_percent_24h:.2f}%")
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _analyze_technical(self, state: TradingState) -> TradingState:
        """Analyze technical indicators"""
        try:
            logger.info("Analyzing technical indicators...")
            
            market_analysis = self.market_analyzer.analyze_market_data(config.trading_pair)
            state.market_analysis = market_analysis
            
            logger.info(f"Technical analysis completed: Score={market_analysis.technical_score:.3f}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _analyze_news(self, state: TradingState) -> TradingState:
        """Analyze news and sentiment"""
        try:
            logger.info("Analyzing news and sentiment...")
            
            news_items = await self.news_analyzer.analyze_news(config.trading_pair)
            state.news_items = news_items
            
            # Update market analysis with news
            if state.market_analysis and news_items:
                state.market_analysis = self.news_analyzer.update_market_analysis_with_news(
                    state.market_analysis, news_items
                )
            
            logger.info(f"News analysis completed: {len(news_items)} news items analyzed")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in news analysis: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _analyze_sentiment(self, state: TradingState) -> TradingState:
        """Advanced sentiment analysis using LLM"""
        try:
            logger.info("Performing advanced sentiment analysis...")
            
            if not state.market_data or not state.market_analysis:
                logger.warning("Missing market data or analysis for sentiment analysis")
                return state
            
            # Prepare market data for sentiment analysis
            market_data_dict = {
                "price": state.market_data.price,
                "change_percent_24h": state.market_data.change_percent_24h,
                "volume": state.market_data.volume,
                "high_24h": state.market_data.high_24h,
                "low_24h": state.market_data.low_24h
            }
            
            # Perform advanced sentiment analysis
            sentiment_result = self.sentiment_analyzer.analyze_sentiment_advanced(
                state.news_items, market_data_dict
            )
            
            # Update market analysis with sentiment
            if state.market_analysis:
                state.market_analysis.sentiment_score = sentiment_result["sentiment_score"]
                state.market_analysis.overall_score = (
                    state.market_analysis.technical_score * 0.4 +
                    sentiment_result["sentiment_score"] * 0.3 +
                    state.market_analysis.news_score * 0.3
                )
            
            logger.info(f"Sentiment analysis completed: {sentiment_result['overall_sentiment']} ({sentiment_result['sentiment_score']:.3f})")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _assess_risk(self, state: TradingState) -> TradingState:
        """Assess risk and position management"""
        try:
            logger.info("Assessing risk and position management...")
            
            if not state.market_data or not state.market_analysis:
                logger.warning("Missing data for risk assessment")
                return state
            
            # Get current positions
            positions = self.bybit_client.get_positions(config.trading_pair)
            state.current_position = positions[0] if positions else None
            
            # Assess risk
            risk_assessment = self.risk_manager.assess_risk(
                state.market_data,
                state.market_analysis,
                state.current_position
            )
            
            logger.info(f"Risk assessment completed: {risk_assessment['risk_level']}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _make_decision(self, state: TradingState) -> TradingState:
        """Make final trading decision"""
        try:
            logger.info("Making trading decision...")
            
            if not state.market_analysis or not state.market_data:
                logger.warning("Missing analysis data for decision making")
                return state
            
            # Prepare sentiment data for decision making
            sentiment_data = {
                "sentiment_score": state.market_analysis.sentiment_score,
                "overall_sentiment": "bullish" if state.market_analysis.sentiment_score > 0.6 else "bearish" if state.market_analysis.sentiment_score < 0.4 else "neutral",
                "confidence": state.market_analysis.confidence,
                "risk_assessment": state.market_analysis.risk_level
            }
            
            # Generate trading decision
            trading_decision = self.sentiment_analyzer.generate_trading_decision(
                state.market_analysis, sentiment_data
            )
            
            state.trading_decision = trading_decision
            
            logger.info(f"Trading decision made: {trading_decision.signal} (confidence: {trading_decision.confidence:.3f})")
            
            return state
            
        except Exception as e:
            logger.error(f"Error making trading decision: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _execute_trade(self, state: TradingState) -> TradingState:
        """Execute trading decision"""
        try:
            logger.info("Executing trading decision...")
            
            if not state.trading_decision:
                logger.warning("No trading decision to execute")
                return state
            
            # Check if we should execute the trade
            if state.trading_decision.signal == "HOLD":
                logger.info("Decision is to HOLD - no trade execution needed")
                return state
            
            # Execute the trade through risk manager
            execution_result = await self.risk_manager.execute_trade(
                state.trading_decision,
                state.market_data,
                state.current_position
            )
            
            if execution_result.get("success"):
                logger.info(f"Trade executed successfully: {execution_result.get('order_id')}")
            else:
                logger.warning(f"Trade execution failed: {execution_result.get('error')}")
                state.error = execution_result.get("error")
            
            return state
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            state.error = str(e)
            state.step = "handle_error"
            return state
    
    async def _handle_error(self, state: TradingState) -> TradingState:
        """Handle errors in the workflow"""
        try:
            logger.error(f"Workflow error: {state.error}")
            
            # Log error details
            error_details = {
                "error": state.error,
                "step": state.step,
                "timestamp": datetime.now().isoformat(),
                "market_data": state.market_data.dict() if state.market_data else None,
                "trading_decision": state.trading_decision.dict() if state.trading_decision else None
            }
            
            # Save error log
            logger.error(f"Error details: {error_details}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in error handling: {e}")
            return state
    
    async def run_analysis(self) -> TradingState:
        """Run the complete trading analysis workflow"""
        try:
            logger.info("Starting trading analysis workflow...")
            
            # Initialize state
            initial_state = TradingState()
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            logger.info("Trading analysis workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Error running trading workflow: {e}")
            return TradingState(error=str(e))
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "workflow_ready": True,
            "components": {
                "bybit_client": self.bybit_client is not None,
                "market_analyzer": self.market_analyzer is not None,
                "news_analyzer": self.news_analyzer is not None,
                "sentiment_analyzer": self.sentiment_analyzer is not None,
                "risk_manager": self.risk_manager is not None
            },
            "config": {
                "trading_pair": config.trading_pair,
                "max_position_size": config.max_position_size,
                "risk_percentage": config.risk_percentage
            }
        }