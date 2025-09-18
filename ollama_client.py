"""
Ollama client for LLM integration with Gemma model
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
from loguru import logger
from config import config

class OllamaClient:
    """Ollama client for LLM operations with Gemma model"""
    
    def __init__(self):
        self.base_url = config.ollama_base_url
        self.model = config.ollama_model
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate response using Ollama model"""
        try:
            if not self.session:
                raise Exception("Session not initialized")
            
            # Prepare the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '').strip()
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""
    
    async def generate_streaming_response(self, prompt: str, system_prompt: str = None,
                                        temperature: float = 0.7, max_tokens: int = 1000) -> AsyncGenerator[str, None]:
        """Generate streaming response using Ollama model"""
        try:
            if not self.session:
                raise Exception("Session not initialized")
            
            # Prepare the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data:
                                    yield data['response']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama streaming API error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
    
    async def analyze_market_data(self, market_analysis: Dict, news_analysis: Dict) -> Dict:
        """Analyze market data using LLM"""
        try:
            system_prompt = """You are an expert cryptocurrency trading analyst. Analyze the provided market data and news to make informed trading decisions. Consider technical indicators, market sentiment, news impact, and risk factors. Provide a clear recommendation with reasoning."""
            
            prompt = f"""
            Market Analysis Data:
            {json.dumps(market_analysis, indent=2)}
            
            News Analysis Data:
            {json.dumps(news_analysis, indent=2)}
            
            Please analyze this data and provide:
            1. Overall market assessment
            2. Key factors influencing the market
            3. Risk assessment
            4. Trading recommendation (BUY/SELL/HOLD)
            5. Confidence level (0-100%)
            6. Reasoning for your recommendation
            """
            
            response = await self.generate_response(prompt, system_prompt, temperature=0.3)
            
            # Parse the response to extract structured data
            analysis = self._parse_llm_analysis(response)
            
            return {
                'llm_analysis': response,
                'structured_analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market data with LLM: {e}")
            return {
                'llm_analysis': 'Error in analysis',
                'structured_analysis': {},
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_trading_strategy(self, market_conditions: Dict) -> Dict:
        """Generate trading strategy based on market conditions"""
        try:
            system_prompt = """You are a professional cryptocurrency trading strategist. Create detailed trading strategies based on market conditions. Consider risk management, position sizing, entry/exit points, and market volatility."""
            
            prompt = f"""
            Current Market Conditions:
            {json.dumps(market_conditions, indent=2)}
            
            Please create a comprehensive trading strategy including:
            1. Market outlook and key trends
            2. Entry conditions and signals
            3. Exit conditions and stop-loss levels
            4. Position sizing recommendations
            5. Risk management rules
            6. Time horizon for the strategy
            7. Key indicators to monitor
            """
            
            response = await self.generate_response(prompt, system_prompt, temperature=0.4)
            
            return {
                'strategy': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating trading strategy: {e}")
            return {
                'strategy': 'Error generating strategy',
                'timestamp': datetime.now().isoformat()
            }
    
    async def analyze_news_sentiment(self, news_items: List[Dict]) -> Dict:
        """Analyze news sentiment using LLM"""
        try:
            system_prompt = """You are a financial news analyst specializing in cryptocurrency markets. Analyze news articles for their potential impact on Bitcoin prices. Consider market sentiment, regulatory implications, adoption news, and technical developments."""
            
            # Prepare news summary
            news_summary = []
            for item in news_items[:10]:  # Limit to top 10 news items
                news_summary.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'source': item.get('source', ''),
                    'sentiment_score': item.get('sentiment_score', 0)
                })
            
            prompt = f"""
            Recent Bitcoin News:
            {json.dumps(news_summary, indent=2)}
            
            Please analyze these news items and provide:
            1. Overall market sentiment from news
            2. Key themes and trends
            3. Potential price impact (positive/negative/neutral)
            4. Most significant news items
            5. Risk factors mentioned
            6. Opportunities identified
            """
            
            response = await self.generate_response(prompt, system_prompt, temperature=0.3)
            
            return {
                'sentiment_analysis': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return {
                'sentiment_analysis': 'Error in sentiment analysis',
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_llm_analysis(self, response: str) -> Dict:
        """Parse LLM response to extract structured data"""
        try:
            analysis = {
                'recommendation': 'HOLD',
                'confidence': 50,
                'reasoning': response,
                'risk_level': 'MEDIUM'
            }
            
            # Extract recommendation
            response_lower = response.lower()
            if 'buy' in response_lower and 'strong buy' in response_lower:
                analysis['recommendation'] = 'STRONG_BUY'
            elif 'buy' in response_lower:
                analysis['recommendation'] = 'BUY'
            elif 'sell' in response_lower and 'strong sell' in response_lower:
                analysis['recommendation'] = 'STRONG_SELL'
            elif 'sell' in response_lower:
                analysis['recommendation'] = 'SELL'
            elif 'hold' in response_lower:
                analysis['recommendation'] = 'HOLD'
            
            # Extract confidence level
            import re
            confidence_match = re.search(r'confidence[:\s]*(\d+)%?', response_lower)
            if confidence_match:
                analysis['confidence'] = int(confidence_match.group(1))
            
            # Extract risk level
            if 'high risk' in response_lower or 'very risky' in response_lower:
                analysis['risk_level'] = 'HIGH'
            elif 'low risk' in response_lower or 'safe' in response_lower:
                analysis['risk_level'] = 'LOW'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing LLM analysis: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 50,
                'reasoning': response,
                'risk_level': 'MEDIUM'
            }
    
    async def check_model_availability(self) -> bool:
        """Check if Ollama model is available"""
        try:
            if not self.session:
                return False
            
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    return self.model in models
                return False
                
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def pull_model(self) -> bool:
        """Pull the model if not available"""
        try:
            if not self.session:
                return False
            
            payload = {
                "name": self.model,
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False