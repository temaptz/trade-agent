"""
Анализатор новостей с использованием DuckDuckGo
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from duckduckgo_search import DDGS
from loguru import logger
from models import NewsItem

class NewsAnalyzer:
    def __init__(self):
        self.ddgs = DDGS()
        self.crypto_keywords = [
            "bitcoin", "btc", "cryptocurrency", "crypto", "blockchain",
            "ethereum", "eth", "binance", "coinbase", "crypto market",
            "bitcoin price", "crypto news", "digital currency", "crypto trading"
        ]
    
    async def search_crypto_news(self, query: str = "bitcoin news", 
                               max_results: int = 10) -> List[NewsItem]:
        """Поиск новостей о криптовалютах"""
        try:
            logger.info(f"Поиск новостей по запросу: {query}")
            
            # Используем DuckDuckGo для поиска новостей
            results = self.ddgs.news(
                keywords=query,
                region="wt-wt",
                safesearch="moderate",
                timelimit="d",  # За последний день
                max_results=max_results
            )
            
            news_items = []
            for result in results:
                try:
                    news_item = NewsItem(
                        title=result.get('title', ''),
                        content=result.get('body', ''),
                        source=result.get('source', 'Unknown'),
                        timestamp=datetime.now(),
                        relevance_score=self._calculate_relevance_score(
                            result.get('title', '') + ' ' + result.get('body', '')
                        )
                    )
                    news_items.append(news_item)
                except Exception as e:
                    logger.warning(f"Ошибка обработки новости: {e}")
                    continue
            
            # Сортируем по релевантности
            news_items.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Найдено {len(news_items)} новостей")
            return news_items
            
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            return []
    
    async def get_market_news(self, symbol: str = "BTC") -> List[NewsItem]:
        """Получение новостей о конкретной криптовалюте"""
        try:
            queries = [
                f"{symbol} news",
                f"{symbol} price",
                f"{symbol} analysis",
                f"{symbol} market",
                f"{symbol} trading"
            ]
            
            all_news = []
            for query in queries:
                news = await self.search_crypto_news(query, max_results=5)
                all_news.extend(news)
            
            # Убираем дубликаты по заголовку
            unique_news = []
            seen_titles = set()
            for news in all_news:
                if news.title.lower() not in seen_titles:
                    unique_news.append(news)
                    seen_titles.add(news.title.lower())
            
            return unique_news[:20]  # Ограничиваем 20 новостями
            
        except Exception as e:
            logger.error(f"Ошибка получения новостей о рынке: {e}")
            return []
    
    async def get_general_crypto_news(self) -> List[NewsItem]:
        """Получение общих новостей о криптовалютах"""
        try:
            queries = [
                "cryptocurrency news",
                "bitcoin news",
                "crypto market news",
                "blockchain news",
                "digital currency news"
            ]
            
            all_news = []
            for query in queries:
                news = await self.search_crypto_news(query, max_results=8)
                all_news.extend(news)
            
            # Убираем дубликаты
            unique_news = []
            seen_titles = set()
            for news in all_news:
                if news.title.lower() not in seen_titles:
                    unique_news.append(news)
                    seen_titles.add(news.title.lower())
            
            return unique_news[:25]  # Ограничиваем 25 новостями
            
        except Exception as e:
            logger.error(f"Ошибка получения общих новостей: {e}")
            return []
    
    def _calculate_relevance_score(self, text: str) -> float:
        """Расчет релевантности новости"""
        try:
            text_lower = text.lower()
            score = 0.0
            
            # Ключевые слова для криптовалют
            crypto_keywords = [
                "bitcoin", "btc", "cryptocurrency", "crypto", "blockchain",
                "ethereum", "eth", "trading", "price", "market", "analysis",
                "bullish", "bearish", "pump", "dump", "volatility", "trend"
            ]
            
            # Подсчитываем количество ключевых слов
            for keyword in crypto_keywords:
                if keyword in text_lower:
                    score += 1.0
            
            # Бонус за финансовые термины
            financial_terms = [
                "price", "market", "trading", "investment", "portfolio",
                "profit", "loss", "gain", "decline", "rise", "fall"
            ]
            
            for term in financial_terms:
                if term in text_lower:
                    score += 0.5
            
            # Нормализуем оценку
            max_possible_score = len(crypto_keywords) + len(financial_terms) * 0.5
            normalized_score = min(1.0, score / max_possible_score) if max_possible_score > 0 else 0.0
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"Ошибка расчета релевантности: {e}")
            return 0.0
    
    async def analyze_news_sentiment(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """Анализ тональности новостей"""
        try:
            if not news_items:
                return {"sentiment": "neutral", "confidence": 0.0, "positive_count": 0, "negative_count": 0}
            
            positive_keywords = [
                "bullish", "rise", "gain", "profit", "growth", "positive", "optimistic",
                "breakthrough", "adoption", "institutional", "pump", "rally", "surge"
            ]
            
            negative_keywords = [
                "bearish", "fall", "decline", "loss", "crash", "negative", "pessimistic",
                "regulation", "ban", "dump", "sell-off", "correction", "volatility"
            ]
            
            positive_count = 0
            negative_count = 0
            total_news = len(news_items)
            
            for news in news_items:
                text = (news.title + " " + news.content).lower()
                
                positive_score = sum(1 for keyword in positive_keywords if keyword in text)
                negative_score = sum(1 for keyword in negative_keywords if keyword in text)
                
                if positive_score > negative_score:
                    positive_count += 1
                elif negative_score > positive_score:
                    negative_count += 1
            
            # Определяем общую тональность
            if positive_count > negative_count:
                sentiment = "positive"
                confidence = positive_count / total_news
            elif negative_count > positive_count:
                sentiment = "negative"
                confidence = negative_count / total_news
            else:
                sentiment = "neutral"
                confidence = 0.5
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "total_news": total_news
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа тональности: {e}")
            return {"sentiment": "neutral", "confidence": 0.0, "positive_count": 0, "negative_count": 0}
    
    async def get_comprehensive_news_analysis(self, symbol: str = "BTC") -> Dict[str, Any]:
        """Комплексный анализ новостей"""
        try:
            # Получаем новости о конкретной криптовалюте
            symbol_news = await self.get_market_news(symbol)
            
            # Получаем общие новости о криптовалютах
            general_news = await self.get_general_crypto_news()
            
            # Объединяем все новости
            all_news = symbol_news + general_news
            
            # Анализируем тональность
            sentiment_analysis = await self.analyze_news_sentiment(all_news)
            
            # Фильтруем самые релевантные новости
            relevant_news = [news for news in all_news if news.relevance_score > 0.3]
            relevant_news.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return {
                "total_news": len(all_news),
                "relevant_news": len(relevant_news),
                "sentiment_analysis": sentiment_analysis,
                "top_news": relevant_news[:10],  # Топ 10 новостей
                "symbol_news_count": len(symbol_news),
                "general_news_count": len(general_news)
            }
            
        except Exception as e:
            logger.error(f"Ошибка комплексного анализа новостей: {e}")
            return {
                "total_news": 0,
                "relevant_news": 0,
                "sentiment_analysis": {"sentiment": "neutral", "confidence": 0.0},
                "top_news": [],
                "symbol_news_count": 0,
                "general_news_count": 0
            }