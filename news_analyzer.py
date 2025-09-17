"""
Модуль для поиска и анализа новостей
"""
import re
from typing import Dict, List, Optional
from duckduckgo_search import DDGS
from loguru import logger
import time

class NewsAnalyzer:
    """Анализатор новостей с использованием DuckDuckGo"""
    
    def __init__(self):
        """Инициализация анализатора новостей"""
        self.ddgs = DDGS()
        logger.info("NewsAnalyzer инициализирован")
    
    def search_crypto_news(self, query: str = "bitcoin", max_results: int = 10) -> List[Dict]:
        """Поиск новостей о криптовалютах"""
        try:
            # Добавляем ключевые слова для более релевантных результатов
            search_query = f"{query} cryptocurrency bitcoin news"
            
            results = []
            for result in self.ddgs.news(search_query, max_results=max_results):
                results.append({
                    'title': result.get('title', ''),
                    'body': result.get('body', ''),
                    'url': result.get('url', ''),
                    'date': result.get('date', ''),
                    'source': result.get('source', '')
                })
            
            logger.info(f"Найдено {len(results)} новостей по запросу: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске новостей: {e}")
            return []
    
    def search_market_news(self, max_results: int = 15) -> List[Dict]:
        """Поиск общих рыночных новостей"""
        try:
            market_queries = [
                "cryptocurrency market news",
                "bitcoin price analysis",
                "crypto market trends",
                "blockchain technology news",
                "digital currency regulation"
            ]
            
            all_news = []
            for query in market_queries:
                try:
                    results = []
                    for result in self.ddgs.news(query, max_results=max_results//len(market_queries)):
                        results.append({
                            'title': result.get('title', ''),
                            'body': result.get('body', ''),
                            'url': result.get('url', ''),
                            'date': result.get('date', ''),
                            'source': result.get('source', ''),
                            'query': query
                        })
                    all_news.extend(results)
                    time.sleep(1)  # Пауза между запросами
                except Exception as e:
                    logger.warning(f"Ошибка при поиске по запросу {query}: {e}")
                    continue
            
            # Удаляем дубликаты по URL
            unique_news = []
            seen_urls = set()
            for news in all_news:
                if news['url'] not in seen_urls:
                    unique_news.append(news)
                    seen_urls.add(news['url'])
            
            logger.info(f"Найдено {len(unique_news)} уникальных новостей")
            return unique_news[:max_results]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске рыночных новостей: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Простой анализ тональности текста"""
        try:
            # Ключевые слова для определения тональности
            positive_words = [
                'bullish', 'rise', 'surge', 'gain', 'increase', 'up', 'positive',
                'growth', 'adoption', 'breakthrough', 'success', 'profit', 'win',
                'strong', 'robust', 'optimistic', 'confidence', 'rally', 'boom'
            ]
            
            negative_words = [
                'bearish', 'fall', 'drop', 'decline', 'decrease', 'down', 'negative',
                'crash', 'loss', 'risk', 'concern', 'fear', 'uncertainty', 'volatile',
                'weak', 'pessimistic', 'doubt', 'sell-off', 'correction', 'bubble'
            ]
            
            # Нормализуем текст
            text_lower = text.lower()
            
            # Подсчитываем положительные и отрицательные слова
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total_words = len(text.split())
            if total_words == 0:
                return {"sentiment": 0, "confidence": 0}
            
            # Рассчитываем тональность
            sentiment_score = (positive_count - negative_count) / total_words
            confidence = min((positive_count + negative_count) / total_words, 1.0)
            
            # Нормализуем оценку от -1 до 1
            sentiment = max(-1, min(1, sentiment_score * 10))
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "positive_words": positive_count,
                "negative_words": negative_count
            }
            
        except Exception as e:
            logger.error(f"Ошибка при анализе тональности: {e}")
            return {"sentiment": 0, "confidence": 0}
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Извлечь ключевые фразы из текста"""
        try:
            # Простое извлечение ключевых фраз
            # Ищем слова, связанные с криптовалютами и финансами
            crypto_keywords = [
                'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'crypto',
                'blockchain', 'defi', 'nft', 'trading', 'investment', 'market',
                'price', 'volatility', 'regulation', 'adoption', 'institutional'
            ]
            
            text_lower = text.lower()
            found_phrases = []
            
            for keyword in crypto_keywords:
                if keyword in text_lower:
                    found_phrases.append(keyword)
            
            return found_phrases
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых фраз: {e}")
            return []
    
    def get_news_summary(self, max_news: int = 20) -> Dict[str, any]:
        """Получить сводку новостей с анализом тональности"""
        try:
            # Получаем новости
            news = self.search_market_news(max_results=max_news)
            
            if not news:
                return {"error": "Не удалось получить новости"}
            
            # Анализируем каждую новость
            analyzed_news = []
            total_sentiment = 0
            total_confidence = 0
            valid_news = 0
            
            for article in news:
                # Объединяем заголовок и текст для анализа
                full_text = f"{article['title']} {article['body']}"
                
                # Анализируем тональность
                sentiment_analysis = self.analyze_sentiment(full_text)
                
                # Извлекаем ключевые фразы
                key_phrases = self.extract_key_phrases(full_text)
                
                analyzed_article = {
                    **article,
                    'sentiment_analysis': sentiment_analysis,
                    'key_phrases': key_phrases
                }
                
                analyzed_news.append(analyzed_article)
                
                # Накапливаем статистику
                if sentiment_analysis['confidence'] > 0.1:  # Только для новостей с достаточной уверенностью
                    total_sentiment += sentiment_analysis['sentiment']
                    total_confidence += sentiment_analysis['confidence']
                    valid_news += 1
            
            # Рассчитываем общую тональность
            if valid_news > 0:
                avg_sentiment = total_sentiment / valid_news
                avg_confidence = total_confidence / valid_news
            else:
                avg_sentiment = 0
                avg_confidence = 0
            
            # Определяем общий настрой рынка
            if avg_sentiment > 0.2:
                market_sentiment = "positive"
            elif avg_sentiment < -0.2:
                market_sentiment = "negative"
            else:
                market_sentiment = "neutral"
            
            summary = {
                "total_news": len(news),
                "analyzed_news": valid_news,
                "market_sentiment": market_sentiment,
                "average_sentiment": avg_sentiment,
                "average_confidence": avg_confidence,
                "news_articles": analyzed_news[:10],  # Возвращаем только первые 10 для краткости
                "last_update": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Сводка новостей подготовлена: {market_sentiment} (sentiment: {avg_sentiment:.2f})")
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка при создании сводки новостей: {e}")
            return {"error": str(e)}
    
    def search_specific_news(self, keywords: List[str], max_results: int = 10) -> List[Dict]:
        """Поиск новостей по конкретным ключевым словам"""
        try:
            query = " ".join(keywords)
            news = self.search_crypto_news(query, max_results)
            
            # Анализируем найденные новости
            analyzed_news = []
            for article in news:
                full_text = f"{article['title']} {article['body']}"
                sentiment_analysis = self.analyze_sentiment(full_text)
                key_phrases = self.extract_key_phrases(full_text)
                
                analyzed_news.append({
                    **article,
                    'sentiment_analysis': sentiment_analysis,
                    'key_phrases': key_phrases
                })
            
            logger.info(f"Найдено {len(analyzed_news)} новостей по ключевым словам: {keywords}")
            return analyzed_news
            
        except Exception as e:
            logger.error(f"Ошибка при поиске специфических новостей: {e}")
            return []