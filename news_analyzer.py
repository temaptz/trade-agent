"""
News analysis module using DuckDuckGo search and content analysis
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from duckduckgo_search import DDGS
from loguru import logger

from models import NewsItem, MarketAnalysis
from config import config

class NewsAnalyzer:
    """Advanced news analyzer for Bitcoin market sentiment"""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.session = None
        self.bitcoin_keywords = [
            "bitcoin", "btc", "cryptocurrency", "crypto", "blockchain",
            "bitcoin price", "btc price", "bitcoin news", "crypto news",
            "bitcoin analysis", "btc analysis", "bitcoin market", "crypto market"
        ]
        self.negative_keywords = [
            "crash", "dump", "fall", "decline", "bear", "bearish", "sell",
            "panic", "fear", "uncertainty", "risk", "volatile", "bubble",
            "regulation", "ban", "restrict", "hack", "scam", "fraud"
        ]
        self.positive_keywords = [
            "bull", "bullish", "rise", "surge", "rally", "moon", "pump",
            "adoption", "institutional", "etf", "approval", "breakthrough",
            "innovation", "partnership", "investment", "hodl", "buy"
        ]
    
    async def analyze_news(self, symbol: str = "BTCUSDT") -> List[NewsItem]:
        """Analyze recent news for Bitcoin"""
        try:
            logger.info("Starting news analysis...")
            
            # Search for recent news
            news_items = await self._search_news()
            
            # Analyze each news item
            analyzed_news = []
            for item in news_items:
                try:
                    # Get full content
                    content = await self._get_article_content(item.get('href', ''))
                    
                    # Analyze sentiment
                    sentiment_score = self._analyze_sentiment(item.get('title', ''), content)
                    
                    # Calculate relevance
                    relevance_score = self._calculate_relevance(item.get('title', ''), content)
                    
                    news_item = NewsItem(
                        title=item.get('title', ''),
                        content=content[:1000],  # Limit content length
                        url=item.get('href', ''),
                        source=item.get('source', 'Unknown'),
                        published_at=datetime.now(),
                        sentiment_score=sentiment_score,
                        relevance_score=relevance_score
                    )
                    
                    analyzed_news.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"Error analyzing news item: {e}")
                    continue
            
            # Filter by relevance and sort by sentiment
            filtered_news = [
                item for item in analyzed_news 
                if item.relevance_score and item.relevance_score > 0.3
            ]
            filtered_news.sort(key=lambda x: x.sentiment_score or 0, reverse=True)
            
            logger.info(f"Found {len(filtered_news)} relevant news items")
            return filtered_news[:10]  # Return top 10 most relevant
            
        except Exception as e:
            logger.error(f"Error in news analysis: {e}")
            return []
    
    async def _search_news(self) -> List[Dict[str, Any]]:
        """Search for Bitcoin-related news using DuckDuckGo"""
        try:
            news_items = []
            
            # Search for each keyword combination
            for keyword in self.bitcoin_keywords[:5]:  # Limit to avoid rate limiting
                try:
                    results = self.ddgs.news(
                        f"{keyword} bitcoin price news",
                        max_results=5,
                        safesearch="moderate"
                    )
                    
                    for result in results:
                        if result not in news_items:
                            news_items.append(result)
                            
                except Exception as e:
                    logger.warning(f"Error searching for '{keyword}': {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error in news search: {e}")
            return []
    
    async def _get_article_content(self, url: str) -> str:
        """Extract article content from URL"""
        try:
            if not url or not url.startswith('http'):
                return ""
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Extract text content
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return text[:2000]  # Limit content length
                    else:
                        return ""
                        
        except Exception as e:
            logger.warning(f"Error getting article content from {url}: {e}")
            return ""
    
    def _analyze_sentiment(self, title: str, content: str) -> float:
        """Analyze sentiment of news item (0-1, where 0.5 is neutral)"""
        try:
            text = f"{title} {content}".lower()
            
            positive_count = sum(1 for word in self.positive_keywords if word in text)
            negative_count = sum(1 for word in self.negative_keywords if word in text)
            
            total_words = len(text.split())
            if total_words == 0:
                return 0.5
            
            # Calculate sentiment score
            sentiment_ratio = (positive_count - negative_count) / max(positive_count + negative_count, 1)
            
            # Normalize to 0-1 range
            sentiment_score = 0.5 + (sentiment_ratio * 0.5)
            
            # Apply additional analysis
            sentiment_score = self._apply_advanced_sentiment_analysis(text, sentiment_score)
            
            return max(0, min(1, sentiment_score))
            
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {e}")
            return 0.5
    
    def _apply_advanced_sentiment_analysis(self, text: str, base_score: float) -> float:
        """Apply advanced sentiment analysis techniques"""
        try:
            # Price movement indicators
            price_patterns = {
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)': 0.1,  # Price mentions
                r'(\d+(?:\.\d+)?)\s*%': 0.05,  # Percentage changes
                r'(up|down|rise|fall|surge|crash)': 0.1,  # Movement words
            }
            
            sentiment_adjustment = 0
            for pattern, weight in price_patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                sentiment_adjustment += len(matches) * weight
            
            # Market sentiment indicators
            market_indicators = {
                'institutional': 0.2,
                'adoption': 0.15,
                'etf': 0.1,
                'regulation': -0.1,
                'hack': -0.2,
                'scam': -0.3,
                'partnership': 0.1,
                'investment': 0.05
            }
            
            for indicator, weight in market_indicators.items():
                if indicator in text:
                    sentiment_adjustment += weight
            
            # Apply adjustments
            final_score = base_score + sentiment_adjustment
            
            return max(0, min(1, final_score))
            
        except Exception as e:
            logger.warning(f"Error in advanced sentiment analysis: {e}")
            return base_score
    
    def _calculate_relevance(self, title: str, content: str) -> float:
        """Calculate relevance score for news item (0-1)"""
        try:
            text = f"{title} {content}".lower()
            
            # Bitcoin-specific relevance
            bitcoin_mentions = sum(1 for word in ['bitcoin', 'btc', 'crypto', 'cryptocurrency'] if word in text)
            
            # Price relevance
            price_mentions = len(re.findall(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text))
            
            # Market relevance
            market_mentions = sum(1 for word in ['market', 'trading', 'price', 'analysis', 'forecast'] if word in text)
            
            # Calculate relevance score
            relevance_score = (
                min(bitcoin_mentions * 0.3, 0.6) +
                min(price_mentions * 0.1, 0.2) +
                min(market_mentions * 0.05, 0.2)
            )
            
            return max(0, min(1, relevance_score))
            
        except Exception as e:
            logger.warning(f"Error calculating relevance: {e}")
            return 0.5
    
    def update_market_analysis_with_news(self, market_analysis: MarketAnalysis, news_items: List[NewsItem]) -> MarketAnalysis:
        """Update market analysis with news sentiment"""
        try:
            if not news_items:
                market_analysis.news_score = 0.5
                market_analysis.sentiment_score = 0.5
            else:
                # Calculate weighted average sentiment
                weighted_sentiment = 0
                total_weight = 0
                
                for item in news_items:
                    if item.sentiment_score and item.relevance_score:
                        weight = item.relevance_score
                        weighted_sentiment += item.sentiment_score * weight
                        total_weight += weight
                
                if total_weight > 0:
                    avg_sentiment = weighted_sentiment / total_weight
                else:
                    avg_sentiment = 0.5
                
                market_analysis.news_score = avg_sentiment
                market_analysis.sentiment_score = avg_sentiment
                
                # Update overall score
                market_analysis.overall_score = (
                    market_analysis.technical_score * 0.4 +
                    market_analysis.sentiment_score * 0.3 +
                    market_analysis.news_score * 0.3
                )
                
                # Update reasoning
                news_reasoning = self._generate_news_reasoning(news_items)
                market_analysis.reasoning += f" | News: {news_reasoning}"
            
            return market_analysis
            
        except Exception as e:
            logger.error(f"Error updating market analysis with news: {e}")
            return market_analysis
    
    def _generate_news_reasoning(self, news_items: List[NewsItem]) -> str:
        """Generate human-readable news analysis reasoning"""
        try:
            if not news_items:
                return "No recent news"
            
            # Count sentiment categories
            positive_count = sum(1 for item in news_items if item.sentiment_score and item.sentiment_score > 0.6)
            negative_count = sum(1 for item in news_items if item.sentiment_score and item.sentiment_score < 0.4)
            neutral_count = len(news_items) - positive_count - negative_count
            
            if positive_count > negative_count:
                return f"Positive sentiment ({positive_count} positive, {negative_count} negative news)"
            elif negative_count > positive_count:
                return f"Negative sentiment ({negative_count} negative, {positive_count} positive news)"
            else:
                return f"Mixed sentiment ({positive_count} positive, {negative_count} negative, {neutral_count} neutral news)"
                
        except Exception as e:
            logger.warning(f"Error generating news reasoning: {e}")
            return "News analysis error"