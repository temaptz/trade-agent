"""LangGraph trading agent with decision-making logic."""
from typing import Dict, List, Any, Optional, TypedDict
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from loguru import logger
import json
from datetime import datetime

from market_tools import MarketAnalyzer
from trading_manager import BybitTradingManager, RiskManager
from config import settings

class TradingState(TypedDict):
    """State for the trading agent."""
    market_analysis: Dict[str, Any]
    current_position: Optional[Dict[str, Any]]
    account_balance: float
    decision: str
    confidence: float
    reasoning: str
    action_taken: Optional[Dict[str, Any]]
    error: Optional[str]

class TradingAgent:
    """Main trading agent using LangGraph."""
    
    def __init__(self):
        # Initialize LLM
        self.llm = OllamaLLM(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.1
        )
        
        # Initialize components
        self.market_analyzer = MarketAnalyzer()
        self.trading_manager = BybitTradingManager(
            api_key=settings.bybit_api_key,
            secret_key=settings.bybit_secret_key,
            testnet=settings.bybit_testnet
        )
        self.risk_manager = RiskManager(
            max_position_size=settings.max_position_size,
            stop_loss_percent=settings.stop_loss_percent,
            take_profit_percent=settings.take_profit_percent,
            risk_per_trade=settings.risk_per_trade
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(TradingState)
        
        # Add nodes
        workflow.add_node("analyze_market", self._analyze_market)
        workflow.add_node("check_position", self._check_position)
        workflow.add_node("make_decision", self._make_decision)
        workflow.add_node("execute_trade", self._execute_trade)
        workflow.add_node("handle_error", self._handle_error)
        
        # Add edges
        workflow.set_entry_point("analyze_market")
        workflow.add_edge("analyze_market", "check_position")
        workflow.add_edge("check_position", "make_decision")
        workflow.add_conditional_edges(
            "make_decision",
            self._should_execute_trade,
            {
                "execute": "execute_trade",
                "skip": END,
                "error": "handle_error"
            }
        )
        workflow.add_edge("execute_trade", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _analyze_market(self, state: TradingState) -> TradingState:
        """Analyze market conditions."""
        logger.info("Starting market analysis...")
        
        try:
            analysis = self.market_analyzer.get_comprehensive_analysis(settings.trading_pair)
            state["market_analysis"] = analysis
            logger.info("Market analysis completed")
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            state["error"] = str(e)
        
        return state
    
    def _check_position(self, state: TradingState) -> TradingState:
        """Check current position and account balance."""
        logger.info("Checking current position...")
        
        try:
            # Get account info
            account_info = self.trading_manager.get_account_info()
            if account_info and account_info.get('retCode') == 0:
                # Extract balance (simplified - you may need to adjust based on actual response)
                balance_data = account_info.get('result', {}).get('list', [])
                if balance_data:
                    state["account_balance"] = float(balance_data[0].get('totalWalletBalance', 0))
                else:
                    state["account_balance"] = 0
            else:
                state["account_balance"] = 0
            
            # Get current position
            positions = self.trading_manager.get_positions(settings.trading_pair)
            if positions and positions.get('retCode') == 0:
                position_list = positions.get('result', {}).get('list', [])
                if position_list and float(position_list[0].get('size', 0)) > 0:
                    state["current_position"] = position_list[0]
                else:
                    state["current_position"] = None
            else:
                state["current_position"] = None
            
            logger.info(f"Account balance: {state['account_balance']}")
            logger.info(f"Current position: {state['current_position']}")
            
        except Exception as e:
            logger.error(f"Error checking position: {e}")
            state["error"] = str(e)
        
        return state
    
    def _make_decision(self, state: TradingState) -> TradingState:
        """Make trading decision using LLM."""
        logger.info("Making trading decision...")
        
        try:
            if "error" in state and state["error"]:
                state["decision"] = "error"
                state["reasoning"] = f"Error occurred: {state['error']}"
                return state
            
            # Prepare context for LLM
            market_data = state.get("market_analysis", {})
            current_position = state.get("current_position")
            account_balance = state.get("account_balance", 0)
            
            # Create prompt
            prompt = self._create_decision_prompt(market_data, current_position, account_balance)
            
            # Get LLM response
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse response
            decision_data = self._parse_llm_response(response.content)
            
            state["decision"] = decision_data.get("decision", "hold")
            state["confidence"] = decision_data.get("confidence", 0.0)
            state["reasoning"] = decision_data.get("reasoning", "")
            
            logger.info(f"Decision: {state['decision']}, Confidence: {state['confidence']}")
            
        except Exception as e:
            logger.error(f"Error making decision: {e}")
            state["error"] = str(e)
            state["decision"] = "error"
        
        return state
    
    def _create_decision_prompt(self, market_data: Dict, current_position: Optional[Dict], account_balance: float) -> str:
        """Create prompt for LLM decision making."""
        prompt = f"""
        You are an expert cryptocurrency trading AI. Analyze the following market data and make a trading decision.

        MARKET DATA:
        - Current Price: {market_data.get('current_price', 'N/A')}
        - Market Trend: {market_data.get('market_trend', 'N/A')}
        - Volatility: {market_data.get('volatility', 'N/A')}
        - RSI: {market_data.get('technical_indicators', {}).get('rsi', 'N/A')}
        - MACD: {market_data.get('technical_indicators', {}).get('macd', 'N/A')}
        - Sentiment: {market_data.get('sentiment_analysis', {}).get('sentiment_text', 'N/A')}
        - Sentiment Score: {market_data.get('sentiment_analysis', {}).get('sentiment_score', 'N/A')}

        CURRENT POSITION:
        {current_position if current_position else "No current position"}

        ACCOUNT BALANCE: {account_balance}

        RISK PARAMETERS:
        - Max Position Size: {settings.max_position_size}
        - Stop Loss: {settings.stop_loss_percent}%
        - Take Profit: {settings.take_profit_percent}%
        - Risk Per Trade: {settings.risk_per_trade}%

        Make a decision based on:
        1. Technical analysis indicators
        2. Market sentiment
        3. Current position (if any)
        4. Risk management rules
        5. Market volatility

        Respond in JSON format:
        {{
            "decision": "buy" | "sell" | "hold" | "close",
            "confidence": 0.0-1.0,
            "reasoning": "Detailed explanation of your decision",
            "quantity": 0.0 (if buying/selling),
            "stop_loss": 0.0 (if applicable),
            "take_profit": 0.0 (if applicable)
        }}
        """
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM."""
        return """
        You are an expert cryptocurrency trading AI with the following characteristics:
        
        1. You are conservative and prioritize capital preservation
        2. You use technical analysis, sentiment analysis, and risk management
        3. You only trade when you have high confidence (>0.7)
        4. You always consider stop-loss and take-profit levels
        5. You avoid overtrading and respect position sizing rules
        6. You consider market volatility and news sentiment
        7. You prefer to hold when market conditions are unclear
        
        Your decisions should be based on:
        - Technical indicators (RSI, MACD, moving averages, Bollinger Bands)
        - Market sentiment and news
        - Current position and risk exposure
        - Market volatility and trend direction
        - Risk management principles
        
        Always provide clear reasoning for your decisions.
        """
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract decision data."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {
                    "decision": "hold",
                    "confidence": 0.5,
                    "reasoning": "Could not parse LLM response",
                    "quantity": 0.0,
                    "stop_loss": 0.0,
                    "take_profit": 0.0
                }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "decision": "hold",
                "confidence": 0.0,
                "reasoning": f"Error parsing response: {e}",
                "quantity": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0
            }
    
    def _should_execute_trade(self, state: TradingState) -> str:
        """Determine if trade should be executed."""
        if "error" in state and state["error"]:
            return "error"
        
        decision = state.get("decision", "hold")
        confidence = state.get("confidence", 0.0)
        
        # Only execute if confidence is high enough and decision is not hold
        if confidence >= 0.7 and decision in ["buy", "sell", "close"]:
            return "execute"
        else:
            return "skip"
    
    def _execute_trade(self, state: TradingState) -> TradingState:
        """Execute the trading decision."""
        logger.info("Executing trade...")
        
        try:
            decision = state.get("decision", "hold")
            confidence = state.get("confidence", 0.0)
            reasoning = state.get("reasoning", "")
            
            if decision == "close" and state.get("current_position"):
                # Close existing position
                result = self.trading_manager.close_position(settings.trading_pair)
                state["action_taken"] = {
                    "action": "close_position",
                    "result": result,
                    "reasoning": reasoning
                }
                logger.info("Position closed")
                
            elif decision in ["buy", "sell"] and confidence >= 0.7:
                # Calculate position size
                current_price = state["market_analysis"].get("current_price", 0)
                if current_price > 0:
                    stop_loss = self.risk_manager.calculate_stop_loss(
                        current_price, decision
                    )
                    take_profit = self.risk_manager.calculate_take_profit(
                        current_price, decision
                    )
                    
                    # Calculate quantity based on risk management
                    quantity = self.trading_manager.calculate_position_size(
                        state["account_balance"],
                        settings.risk_per_trade,
                        current_price,
                        stop_loss
                    )
                    
                    # Validate trade
                    validation = self.risk_manager.validate_trade(
                        decision, quantity, current_price
                    )
                    
                    if validation["valid"]:
                        # Execute trade
                        result = self.trading_manager.place_market_order(
                            symbol=settings.trading_pair,
                            side=decision.capitalize(),
                            qty=quantity,
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )
                        
                        state["action_taken"] = {
                            "action": f"{decision}_order",
                            "quantity": quantity,
                            "price": current_price,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "result": result,
                            "reasoning": reasoning
                        }
                        logger.info(f"Trade executed: {decision} {quantity} at {current_price}")
                    else:
                        state["action_taken"] = {
                            "action": "validation_failed",
                            "errors": validation["errors"],
                            "reasoning": reasoning
                        }
                        logger.warning(f"Trade validation failed: {validation['errors']}")
                else:
                    state["action_taken"] = {
                        "action": "invalid_price",
                        "reasoning": "Invalid current price"
                    }
            else:
                state["action_taken"] = {
                    "action": "no_action",
                    "reasoning": f"Decision: {decision}, Confidence: {confidence}"
                }
                logger.info(f"No action taken: {decision} (confidence: {confidence})")
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            state["error"] = str(e)
            state["action_taken"] = {
                "action": "error",
                "error": str(e)
            }
        
        return state
    
    def _handle_error(self, state: TradingState) -> TradingState:
        """Handle errors in the trading process."""
        logger.error(f"Handling error: {state.get('error', 'Unknown error')}")
        state["action_taken"] = {
            "action": "error_handled",
            "error": state.get("error", "Unknown error")
        }
        return state
    
    async def run_trading_cycle(self) -> Dict[str, Any]:
        """Run a complete trading cycle."""
        logger.info("Starting trading cycle...")
        
        initial_state = {
            "market_analysis": {},
            "current_position": None,
            "account_balance": 0.0,
            "decision": "hold",
            "confidence": 0.0,
            "reasoning": "",
            "action_taken": None,
            "error": None
        }
        
        try:
            result = await self.graph.ainvoke(initial_state)
            logger.info("Trading cycle completed")
            return result
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return {
                **initial_state,
                "error": str(e),
                "action_taken": {"action": "cycle_error", "error": str(e)}
            }