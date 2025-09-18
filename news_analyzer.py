"""
News analysis module using DuckDuckGo search and web scraping
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
from loguru import logger
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import time

@dataclass
class NewsItem:
    """News item data structure"""
    title: str
    url: str
    snippet: str
    published_date: Optional[datetime]
    source: str
    sentiment_score: float = 0.0
    relevance_score: float = 0.0
    content: Optional[str] = None

class NewsAnalyzer:
    """News analysis using DuckDuckGo search and sentiment analysis"""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.session = None
        self.bitcoin_keywords = [
            'bitcoin', 'btc', 'cryptocurrency', 'crypto', 'blockchain',
            'bitcoin price', 'btc price', 'bitcoin news', 'crypto news',
            'bitcoin regulation', 'crypto regulation', 'bitcoin adoption',
            'bitcoin etf', 'crypto etf', 'bitcoin halving', 'bitcoin mining'
        ]
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_bitcoin_news(self, max_results: int = 20, time_range: str = '7d') -> List[NewsItem]:
        """Search for Bitcoin-related news using DuckDuckGo"""
        try:
            news_items = []
            
            # Search queries for different aspects of Bitcoin news
            search_queries = [
                'bitcoin price news today',
                'bitcoin cryptocurrency news',
                'bitcoin regulation news',
                'bitcoin adoption news',
                'bitcoin etf news',
                'bitcoin halving news',
                'bitcoin mining news',
                'bitcoin institutional news'
            ]
            
            for query in search_queries:
                try:
                    # Search using DuckDuckGo
                    results = self.ddgs.news(
                        query,
                        max_results=max_results // len(search_queries),
                        safesearch='moderate'
                    )
                    
                    for result in results:
                        news_item = NewsItem(
                            title=result.get('title', ''),
                            url=result.get('url', ''),
                            snippet=result.get('body', ''),
                            published_date=self._parse_date(result.get('date', '')),
                            source=result.get('source', ''),
                            content=None
                        )
                        
                        # Calculate relevance score
                        news_item.relevance_score = self._calculate_relevance(news_item)
                        
                        if news_item.relevance_score > 0.3:  # Filter relevant news
                            news_items.append(news_item)
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error searching for query '{query}': {e}")
                    continue
            
            # Remove duplicates and sort by relevance
            news_items = self._remove_duplicates(news_items)
            news_items.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(news_items)} relevant Bitcoin news items")
            return news_items[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching Bitcoin news: {e}")
            return []
    
    async def get_news_content(self, news_item: NewsItem) -> str:
        """Extract full content from news article"""
        try:
            if not self.session:
                raise Exception("Session not initialized")
            
            async with self.session.get(news_item.url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Try to find main content
                    content_selectors = [
                        'article',
                        '.article-content',
                        '.post-content',
                        '.entry-content',
                        '.content',
                        'main',
                        '.main-content'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        elements = soup.select(selector)
                        if elements:
                            content = ' '.join([elem.get_text() for elem in elements])
                            break
                    
                    if not content:
                        # Fallback to body text
                        content = soup.get_text()
                    
                    # Clean up content
                    content = re.sub(r'\s+', ' ', content).strip()
                    return content[:5000]  # Limit content length
                
        except Exception as e:
            logger.warning(f"Error extracting content from {news_item.url}: {e}")
            return news_item.snippet
    
    async def analyze_news_sentiment(self, news_items: List[NewsItem]) -> Dict:
        """Analyze sentiment of news items"""
        try:
            if not news_items:
                return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0, 'analysis': []}
            
            # Simple sentiment analysis based on keywords
            positive_keywords = [
                'bullish', 'surge', 'rally', 'gains', 'up', 'rise', 'increase',
                'adoption', 'institutional', 'etf', 'approval', 'positive',
                'breakthrough', 'milestone', 'success', 'growth', 'optimistic'
            ]
            
            negative_keywords = [
                'bearish', 'crash', 'drop', 'fall', 'decline', 'down', 'loss',
                'regulation', 'ban', 'restriction', 'negative', 'concern',
                'risk', 'volatility', 'uncertainty', 'fear', 'pessimistic'
            ]
            
            sentiment_scores = []
            analysis = []
            
            for item in news_items:
                text = f"{item.title} {item.snippet}".lower()
                
                positive_count = sum(1 for keyword in positive_keywords if keyword in text)
                negative_count = sum(1 for keyword in negative_keywords if keyword in text)
                
                if positive_count > negative_count:
                    sentiment = 'positive'
                    score = min(positive_count / 10, 1.0)
                elif negative_count > positive_count:
                    sentiment = 'negative'
                    score = -min(negative_count / 10, 1.0)
                else:
                    sentiment = 'neutral'
                    score = 0.0
                
                item.sentiment_score = score
                sentiment_scores.append(score)
                
                analysis.append({
                    'title': item.title,
                    'sentiment': sentiment,
                    'score': score,
                    'source': item.source
                })
            
            # Calculate overall sentiment
            overall_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
            if overall_score > 0.2:
                overall_sentiment = 'positive'
            elif overall_score < -0.2:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_score': overall_score,
                'analysis': analysis,
                'total_news': len(news_items)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0, 'analysis': []}
    
    async def get_market_impact_news(self) -> Dict:
        """Get news that could impact Bitcoin market"""
        try:
            # Search for high-impact news
            high_impact_queries = [
                'bitcoin etf approval',
                'bitcoin regulation announcement',
                'bitcoin institutional adoption',
                'bitcoin halving news',
                'bitcoin mining difficulty',
                'bitcoin network upgrade',
                'bitcoin security news',
                'bitcoin exchange news'
            ]
            
            high_impact_news = []
            
            for query in high_impact_queries:
                try:
                    results = self.ddgs.news(query, max_results=5, safesearch='moderate')
                    
                    for result in results:
                        news_item = NewsItem(
                            title=result.get('title', ''),
                            url=result.get('url', ''),
                            snippet=result.get('body', ''),
                            published_date=self._parse_date(result.get('date', '')),
                            source=result.get('source', ''),
                            relevance_score=1.0  # High impact news gets high relevance
                        )
                        high_impact_news.append(news_item)
                    
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    logger.warning(f"Error searching high-impact news for '{query}': {e}")
                    continue
            
            # Remove duplicates
            high_impact_news = self._remove_duplicates(high_impact_news)
            
            return {
                'high_impact_news': high_impact_news[:10],
                'total_found': len(high_impact_news)
            }
            
        except Exception as e:
            logger.error(f"Error getting market impact news: {e}")
            return {'high_impact_news': [], 'total_found': 0}
    
    def _calculate_relevance(self, news_item: NewsItem) -> float:
        """Calculate relevance score for news item"""
        try:
            text = f"{news_item.title} {news_item.snippet}".lower()
            score = 0.0
            
            # Bitcoin-specific keywords
            bitcoin_keywords = ['bitcoin', 'btc', 'cryptocurrency', 'crypto']
            for keyword in bitcoin_keywords:
                if keyword in text:
                    score += 0.3
            
            # Market-related keywords
            market_keywords = ['price', 'market', 'trading', 'exchange', 'volume']
            for keyword in market_keywords:
                if keyword in text:
                    score += 0.2
            
            # Recent news gets higher score
            if news_item.published_date:
                days_old = (datetime.now() - news_item.published_date).days
                if days_old <= 1:
                    score += 0.3
                elif days_old <= 3:
                    score += 0.2
                elif days_old <= 7:
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        try:
            if not date_str:
                return None
            
            # Common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%d/%m/%Y',
                '%m/%d/%Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return None
    
    def _remove_duplicates(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate news items based on title similarity"""
        try:
            unique_items = []
            seen_titles = set()
            
            for item in news_items:
                # Simple deduplication based on title similarity
                title_words = set(item.title.lower().split())
                is_duplicate = False
                
                for seen_title in seen_titles:
                    seen_words = set(seen_title.lower().split())
                    similarity = len(title_words.intersection(seen_words)) / len(title_words.union(seen_words))
                    
                    if similarity > 0.7:  # 70% similarity threshold
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_items.append(item)
                    seen_titles.add(item.title)
            
            return unique_items
            
        except Exception as e:
            logger.error(f"Error removing duplicates: {e}")
            return news_items