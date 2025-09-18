"""
Анализатор новостей и поиск информации
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import re
from loguru import logger
from dataclasses import dataclass
from config import settings

@dataclass
class NewsItem:
    title: str
    url: str
    snippet: str
    timestamp: datetime
    source: str
    sentiment: Optional[str] = None
    relevance_score: float = 0.0

class NewsAnalyzer:
    def __init__(self):
        self.news_cache = {}
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_news(self, query: str, max_results: int = 10, 
                         time_range: str = "7d") -> List[NewsItem]:
        """Поиск новостей через DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = ddgs.news(
                    query,
                    max_results=max_results,
                    safesearch="moderate",
                    timelimit=time_range
                )
                
                news_items = []
                for result in results:
                    news_item = NewsItem(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        snippet=result.get('body', ''),
                        timestamp=datetime.fromisoformat(
                            result.get('date', datetime.now().isoformat())
                        ),
                        source=result.get('source', 'Unknown')
                    )
                    news_items.append(news_item)
                
                logger.info(f"Найдено {len(news_items)} новостей для запроса: {query}")
                return news_items
                
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            return []
    
    async def get_article_content(self, url: str) -> Optional[str]:
        """Получение полного текста статьи"""
        try:
            if not self.session:
                return None
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Удаляем скрипты и стили
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Ищем основной контент
                    content_selectors = [
                        'article', '.article-content', '.post-content',
                        '.entry-content', '.content', 'main'
                    ]
                    
                    content = None
                    for selector in content_selectors:
                        content = soup.select_one(selector)
                        if content:
                            break
                    
                    if not content:
                        content = soup.find('body')
                    
                    if content:
                        text = content.get_text()
                        # Очистка текста
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text[:5000]  # Ограничиваем размер
                        
        except Exception as e:
            logger.error(f"Ошибка получения контента статьи {url}: {e}")
        
        return None
    
    def analyze_sentiment(self, text: str) -> str:
        """Простой анализ тональности текста"""
        try:
            # Ключевые слова для определения тональности
            positive_words = [
                'bullish', 'rise', 'surge', 'gain', 'profit', 'growth',
                'positive', 'optimistic', 'strong', 'up', 'increase',
                'breakthrough', 'success', 'win', 'victory', 'boom'
            ]
            
            negative_words = [
                'bearish', 'fall', 'drop', 'decline', 'loss', 'crash',
                'negative', 'pessimistic', 'weak', 'down', 'decrease',
                'failure', 'crisis', 'panic', 'sell-off', 'dump'
            ]
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Ошибка анализа тональности: {e}")
            return "neutral"
    
    def calculate_relevance_score(self, news_item: NewsItem, 
                                keywords: List[str]) -> float:
        """Расчет релевантности новости"""
        try:
            text = f"{news_item.title} {news_item.snippet}".lower()
            score = 0.0
            
            # Веса для разных частей
            title_weight = 2.0
            snippet_weight = 1.0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Подсчет в заголовке
                title_count = news_item.title.lower().count(keyword_lower)
                score += title_count * title_weight
                
                # Подсчет в тексте
                snippet_count = news_item.snippet.lower().count(keyword_lower)
                score += snippet_count * snippet_weight
            
            # Нормализация
            max_possible_score = len(keywords) * (title_weight + snippet_weight)
            normalized_score = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"Ошибка расчета релевантности: {e}")
            return 0.0
    
    async def get_crypto_news(self, max_results: int = 20) -> List[NewsItem]:
        """Получение новостей о криптовалютах"""
        try:
            # Ключевые слова для поиска
            crypto_keywords = [
                "bitcoin", "btc", "cryptocurrency", "crypto", "blockchain",
                "ethereum", "eth", "trading", "market", "price"
            ]
            
            # Поиск новостей
            all_news = []
            
            # Основные запросы
            queries = [
                "bitcoin news today",
                "cryptocurrency market news",
                "bitcoin price analysis",
                "crypto trading news",
                "blockchain news"
            ]
            
            for query in queries:
                news_items = await self.search_news(query, max_results=5)
                all_news.extend(news_items)
            
            # Удаление дубликатов по URL
            unique_news = {}
            for item in all_news:
                if item.url not in unique_news:
                    unique_news[item.url] = item
            
            news_list = list(unique_news.values())
            
            # Анализ релевантности и тональности
            for item in news_list:
                item.relevance_score = self.calculate_relevance_score(item, crypto_keywords)
                item.sentiment = self.analyze_sentiment(f"{item.title} {item.snippet}")
            
            # Сортировка по релевантности
            news_list.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Возвращаем топ результатов
            return news_list[:max_results]
            
        except Exception as e:
            logger.error(f"Ошибка получения крипто новостей: {e}")
            return []
    
    async def get_market_sentiment(self) -> Dict:
        """Анализ общего настроения рынка"""
        try:
            news_items = await self.get_crypto_news(max_results=30)
            
            if not news_items:
                return {"sentiment": "neutral", "confidence": 0.0}
            
            # Анализ тональности
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            total_relevance = 0.0
            
            for item in news_items:
                if item.relevance_score > 0.3:  # Только релевантные новости
                    sentiment_counts[item.sentiment] += item.relevance_score
                    total_relevance += item.relevance_score
            
            if total_relevance == 0:
                return {"sentiment": "neutral", "confidence": 0.0}
            
            # Нормализация
            for sentiment in sentiment_counts:
                sentiment_counts[sentiment] /= total_relevance
            
            # Определение доминирующей тональности
            dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
            confidence = sentiment_counts[dominant_sentiment]
            
            return {
                "sentiment": dominant_sentiment,
                "confidence": confidence,
                "distribution": sentiment_counts,
                "news_count": len(news_items),
                "relevant_news": len([item for item in news_items if item.relevance_score > 0.3])
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа настроения рынка: {e}")
            return {"sentiment": "neutral", "confidence": 0.0}
    
    async def get_breaking_news(self) -> List[NewsItem]:
        """Получение экстренных новостей"""
        try:
            # Поиск последних новостей
            breaking_queries = [
                "bitcoin breaking news",
                "crypto market crash",
                "bitcoin surge",
                "cryptocurrency regulation",
                "bitcoin halving"
            ]
            
            all_breaking_news = []
            for query in breaking_queries:
                news_items = await self.search_news(query, max_results=3, time_range="1d")
                all_breaking_news.extend(news_items)
            
            # Фильтрация по времени (последние 24 часа)
            recent_news = []
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for item in all_breaking_news:
                if item.timestamp >= cutoff_time:
                    recent_news.append(item)
            
            # Сортировка по времени
            recent_news.sort(key=lambda x: x.timestamp, reverse=True)
            
            return recent_news[:10]
            
        except Exception as e:
            logger.error(f"Ошибка получения экстренных новостей: {e}")
            return []
    
    async def analyze_news_impact(self, news_items: List[NewsItem]) -> Dict:
        """Анализ влияния новостей на рынок"""
        try:
            if not news_items:
                return {"impact": "neutral", "score": 0.0}
            
            # Анализ ключевых слов влияния
            high_impact_keywords = [
                "regulation", "ban", "approve", "adoption", "institutional",
                "halving", "fork", "upgrade", "hack", "security", "partnership"
            ]
            
            impact_score = 0.0
            high_impact_news = []
            
            for item in news_items:
                item_impact = 0.0
                text = f"{item.title} {item.snippet}".lower()
                
                for keyword in high_impact_keywords:
                    if keyword in text:
                        item_impact += 1.0
                
                if item_impact > 0:
                    high_impact_news.append({
                        "item": item,
                        "impact": item_impact
                    })
                    impact_score += item_impact * item.relevance_score
            
            # Нормализация
            max_possible_impact = len(high_impact_keywords) * len(news_items)
            normalized_impact = min(impact_score / max_possible_impact, 1.0) if max_possible_impact > 0 else 0.0
            
            # Определение уровня влияния
            if normalized_impact > 0.7:
                impact_level = "high"
            elif normalized_impact > 0.3:
                impact_level = "medium"
            else:
                impact_level = "low"
            
            return {
                "impact": impact_level,
                "score": normalized_impact,
                "high_impact_news": high_impact_news,
                "total_news": len(news_items)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа влияния новостей: {e}")
            return {"impact": "neutral", "score": 0.0}