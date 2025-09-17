"""
Advanced sentiment analysis using Ollama LLM
"""
import ollama
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from models import NewsItem, MarketAnalysis, TradingDecision
from config import config

class SentimentAnalyzer:
    """Advanced sentiment analyzer using Ollama LLM"""
    
    def __init__(self):
        self.client = ollama.Client(host=config.ollama_base_url)
        self.model = config.ollama_model
        
    def analyze_sentiment_advanced(self, news_items: List[NewsItem], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced sentiment analysis using LLM"""
        try:
            logger.info("Starting advanced sentiment analysis...")
            
            # Prepare context for LLM
            context = self._prepare_analysis_context(news_items, market_data)
            
            # Generate sentiment analysis prompt
            prompt = self._create_sentiment_prompt(context)
            
            # Get LLM analysis
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cryptocurrency market analyst specializing in Bitcoin sentiment analysis. Analyze news, market data, and provide detailed sentiment assessment with confidence levels."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse LLM response
            analysis_result = self._parse_llm_response(response['message']['content'])
            
            logger.info("Advanced sentiment analysis completed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in advanced sentiment analysis: {e}")
            return self._get_default_sentiment()
    
    def _prepare_analysis_context(self, news_items: List[NewsItem], market_data: Dict[str, Any]) -> str:
        """Prepare context for LLM analysis"""
        try:
            context_parts = []
            
            # Market data context
            context_parts.append("=== MARKET DATA ===")
            context_parts.append(f"Current Price: ${market_data.get('price', 'N/A')}")
            context_parts.append(f"24h Change: {market_data.get('change_percent_24h', 'N/A')}%")
            context_parts.append(f"24h Volume: {market_data.get('volume', 'N/A')}")
            context_parts.append(f"24h High: ${market_data.get('high_24h', 'N/A')}")
            context_parts.append(f"24h Low: ${market_data.get('low_24h', 'N/A')}")
            
            # News context
            if news_items:
                context_parts.append("\n=== RECENT NEWS ===")
                for i, item in enumerate(news_items[:5], 1):  # Top 5 news items
                    context_parts.append(f"\n{i}. {item.title}")
                    if item.content:
                        context_parts.append(f"   Content: {item.content[:200]}...")
                    if item.sentiment_score:
                        context_parts.append(f"   Initial Sentiment: {item.sentiment_score:.2f}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error preparing analysis context: {e}")
            return "Context preparation error"
    
    def _create_sentiment_prompt(self, context: str) -> str:
        """Create detailed sentiment analysis prompt"""
        return f"""
Analyze the following Bitcoin market data and news to provide a comprehensive sentiment assessment:

{context}

Please provide your analysis in the following JSON format:
{{
    "overall_sentiment": "bullish|bearish|neutral",
    "sentiment_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "key_factors": [
        "Factor 1: Description",
        "Factor 2: Description"
    ],
    "market_outlook": "Short description of market outlook",
    "risk_assessment": "low|medium|high",
    "trading_recommendation": "buy|sell|hold",
    "reasoning": "Detailed explanation of your analysis"
}}

Consider:
1. Technical indicators and price action
2. News sentiment and market impact
3. Volume and volatility patterns
4. Market structure and trends
5. Risk factors and opportunities
6. Short-term vs long-term outlook

Be specific and provide actionable insights.
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract sentiment data"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                analysis = json.loads(json_str)
                
                # Validate and normalize the response
                return self._validate_analysis(analysis)
            else:
                # Fallback: extract sentiment from text
                return self._extract_sentiment_from_text(response)
                
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}")
            return self._get_default_sentiment()
    
    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize analysis data"""
        try:
            # Ensure required fields exist
            validated = {
                "overall_sentiment": analysis.get("overall_sentiment", "neutral"),
                "sentiment_score": float(analysis.get("sentiment_score", 0.5)),
                "confidence": float(analysis.get("confidence", 0.5)),
                "key_factors": analysis.get("key_factors", []),
                "market_outlook": analysis.get("market_outlook", "No clear outlook"),
                "risk_assessment": analysis.get("risk_assessment", "medium"),
                "trading_recommendation": analysis.get("trading_recommendation", "hold"),
                "reasoning": analysis.get("reasoning", "Analysis incomplete")
            }
            
            # Normalize sentiment score
            validated["sentiment_score"] = max(0.0, min(1.0, validated["sentiment_score"]))
            validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))
            
            # Normalize sentiment labels
            sentiment = validated["overall_sentiment"].lower()
            if sentiment in ["bullish", "positive", "up", "buy"]:
                validated["overall_sentiment"] = "bullish"
            elif sentiment in ["bearish", "negative", "down", "sell"]:
                validated["overall_sentiment"] = "bearish"
            else:
                validated["overall_sentiment"] = "neutral"
            
            # Normalize risk assessment
            risk = validated["risk_assessment"].lower()
            if risk in ["high", "h"]:
                validated["risk_assessment"] = "high"
            elif risk in ["low", "l"]:
                validated["risk_assessment"] = "low"
            else:
                validated["risk_assessment"] = "medium"
            
            # Normalize trading recommendation
            rec = validated["trading_recommendation"].lower()
            if rec in ["buy", "long", "bullish"]:
                validated["trading_recommendation"] = "buy"
            elif rec in ["sell", "short", "bearish"]:
                validated["trading_recommendation"] = "sell"
            else:
                validated["trading_recommendation"] = "hold"
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating analysis: {e}")
            return self._get_default_sentiment()
    
    def _extract_sentiment_from_text(self, text: str) -> Dict[str, Any]:
        """Extract sentiment from unstructured text response"""
        try:
            text_lower = text.lower()
            
            # Extract sentiment indicators
            bullish_indicators = ["bullish", "positive", "up", "rise", "gain", "buy", "strong"]
            bearish_indicators = ["bearish", "negative", "down", "fall", "drop", "sell", "weak"]
            
            bullish_count = sum(1 for indicator in bullish_indicators if indicator in text_lower)
            bearish_count = sum(1 for indicator in bearish_indicators if indicator in text_lower)
            
            if bullish_count > bearish_count:
                sentiment = "bullish"
                score = 0.6 + min(0.3, bullish_count * 0.05)
            elif bearish_count > bullish_count:
                sentiment = "bearish"
                score = 0.4 - min(0.3, bearish_count * 0.05)
            else:
                sentiment = "neutral"
                score = 0.5
            
            return {
                "overall_sentiment": sentiment,
                "sentiment_score": max(0.0, min(1.0, score)),
                "confidence": 0.6,
                "key_factors": ["LLM text analysis"],
                "market_outlook": "Analysis based on text patterns",
                "risk_assessment": "medium",
                "trading_recommendation": "hold",
                "reasoning": f"Extracted from text: {text[:200]}..."
            }
            
        except Exception as e:
            logger.error(f"Error extracting sentiment from text: {e}")
            return self._get_default_sentiment()
    
    def _get_default_sentiment(self) -> Dict[str, Any]:
        """Get default sentiment when analysis fails"""
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.5,
            "confidence": 0.3,
            "key_factors": ["Analysis failed - using default"],
            "market_outlook": "Unable to determine outlook",
            "risk_assessment": "medium",
            "trading_recommendation": "hold",
            "reasoning": "Sentiment analysis failed - defaulting to neutral"
        }
    
    def generate_trading_decision(self, market_analysis: MarketAnalysis, sentiment_analysis: Dict[str, Any]) -> TradingDecision:
        """Generate trading decision based on market and sentiment analysis"""
        try:
            # Combine technical and sentiment scores
            technical_weight = 0.4
            sentiment_weight = 0.3
            news_weight = 0.3
            
            combined_score = (
                market_analysis.technical_score * technical_weight +
                sentiment_analysis["sentiment_score"] * sentiment_weight +
                market_analysis.news_score * news_weight
            )
            
            # Determine signal
            if combined_score > 0.7:
                signal = "BUY"
                confidence = min(0.9, combined_score + 0.1)
            elif combined_score < 0.3:
                signal = "SELL"
                confidence = min(0.9, (1 - combined_score) + 0.1)
            else:
                signal = "HOLD"
                confidence = 0.5
            
            # Calculate position size based on confidence and risk
            position_size = self._calculate_position_size(confidence, sentiment_analysis["risk_assessment"])
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = self._calculate_stop_take_profit(
                signal, confidence, sentiment_analysis["risk_assessment"]
            )
            
            # Generate reasoning
            reasoning = self._generate_decision_reasoning(
                market_analysis, sentiment_analysis, signal, combined_score
            )
            
            return TradingDecision(
                signal=signal,
                confidence=confidence,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                market_analysis=market_analysis
            )
            
        except Exception as e:
            logger.error(f"Error generating trading decision: {e}")
            return TradingDecision(
                signal="HOLD",
                confidence=0.3,
                position_size=0.0,
                reasoning="Error in decision generation",
                market_analysis=market_analysis
            )
    
    def _calculate_position_size(self, confidence: float, risk_level: str) -> float:
        """Calculate position size based on confidence and risk"""
        try:
            base_size = config.max_position_size
            
            # Adjust for confidence
            confidence_multiplier = confidence
            
            # Adjust for risk level
            risk_multipliers = {
                "low": 1.2,
                "medium": 1.0,
                "high": 0.6
            }
            risk_multiplier = risk_multipliers.get(risk_level, 1.0)
            
            # Calculate final position size
            position_size = base_size * confidence_multiplier * risk_multiplier
            
            return max(0.0, min(1.0, position_size))
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def _calculate_stop_take_profit(self, signal: str, confidence: float, risk_level: str) -> tuple:
        """Calculate stop loss and take profit levels"""
        try:
            # Base percentages
            base_stop_loss = config.stop_loss_percentage / 100
            base_take_profit = config.take_profit_percentage / 100
            
            # Adjust for risk level
            risk_multipliers = {
                "low": 0.8,
                "medium": 1.0,
                "high": 1.5
            }
            risk_multiplier = risk_multipliers.get(risk_level, 1.0)
            
            # Adjust for confidence
            confidence_multiplier = 1.0 + (1.0 - confidence) * 0.5
            
            stop_loss = base_stop_loss * risk_multiplier * confidence_multiplier
            take_profit = base_take_profit * risk_multiplier
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating stop/take profit: {e}")
            return None, None
    
    def _generate_decision_reasoning(self, market_analysis: MarketAnalysis, sentiment_analysis: Dict[str, Any], signal: str, combined_score: float) -> str:
        """Generate detailed reasoning for trading decision"""
        try:
            reasoning_parts = []
            
            # Technical analysis reasoning
            reasoning_parts.append(f"Technical Score: {market_analysis.technical_score:.2f}")
            
            # Sentiment reasoning
            reasoning_parts.append(f"Sentiment: {sentiment_analysis['overall_sentiment']} ({sentiment_analysis['sentiment_score']:.2f})")
            
            # News reasoning
            reasoning_parts.append(f"News Score: {market_analysis.news_score:.2f}")
            
            # Combined score
            reasoning_parts.append(f"Combined Score: {combined_score:.2f}")
            
            # Key factors
            if sentiment_analysis.get("key_factors"):
                reasoning_parts.append(f"Key Factors: {', '.join(sentiment_analysis['key_factors'][:3])}")
            
            # Risk assessment
            reasoning_parts.append(f"Risk Level: {sentiment_analysis['risk_assessment']}")
            
            # Market outlook
            if sentiment_analysis.get("market_outlook"):
                reasoning_parts.append(f"Outlook: {sentiment_analysis['market_outlook']}")
            
            return " | ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Error generating decision reasoning: {e}")
            return "Reasoning generation error"