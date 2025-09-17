"""
Tests for News Analyzer
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from news_analyzer import NewsAnalyzer
from models import NewsItem, MarketAnalysis

class TestNewsAnalyzer:
    """Test cases for NewsAnalyzer"""
    
    @pytest.fixture
    def news_analyzer(self):
        """Create NewsAnalyzer instance"""
        return NewsAnalyzer()
    
    def test_analyze_sentiment(self, news_analyzer):
        """Test sentiment analysis"""
        # Test positive sentiment
        positive_text = "Bitcoin price surges to new all-time high, bullish momentum continues"
        sentiment = news_analyzer._analyze_sentiment(positive_text, "")
        assert 0.5 < sentiment <= 1.0
        
        # Test negative sentiment
        negative_text = "Bitcoin crashes, market panic, bearish outlook"
        sentiment = news_analyzer._analyze_sentiment(negative_text, "")
        assert 0.0 <= sentiment < 0.5
        
        # Test neutral sentiment
        neutral_text = "Bitcoin price remains stable, no significant changes"
        sentiment = news_analyzer._analyze_sentiment(neutral_text, "")
        assert 0.4 <= sentiment <= 0.6
    
    def test_calculate_relevance(self, news_analyzer):
        """Test relevance calculation"""
        # Test high relevance
        relevant_text = "Bitcoin BTC cryptocurrency price analysis market trading"
        relevance = news_analyzer._calculate_relevance(relevant_text, "")
        assert relevance > 0.5
        
        # Test low relevance
        irrelevant_text = "Weather forecast sunny day temperature"
        relevance = news_analyzer._calculate_relevance(irrelevant_text, "")
        assert relevance < 0.5
        
        # Test medium relevance
        medium_text = "Bitcoin mentioned in financial news"
        relevance = news_analyzer._calculate_relevance(medium_text, "")
        assert 0.2 <= relevance <= 0.8
    
    def test_apply_advanced_sentiment_analysis(self, news_analyzer):
        """Test advanced sentiment analysis"""
        # Test with price mentions
        text_with_price = "Bitcoin reaches $50,000, up 5% today"
        base_score = 0.5
        advanced_score = news_analyzer._apply_advanced_sentiment_analysis(text_with_price, base_score)
        assert advanced_score != base_score
        
        # Test with institutional keywords
        institutional_text = "Institutional adoption of Bitcoin increases"
        advanced_score = news_analyzer._apply_advanced_sentiment_analysis(institutional_text, base_score)
        assert advanced_score > base_score
        
        # Test with negative keywords
        negative_text = "Bitcoin hack scam fraud regulation ban"
        advanced_score = news_analyzer._apply_advanced_sentiment_analysis(negative_text, base_score)
        assert advanced_score < base_score
    
    def test_generate_news_reasoning(self, news_analyzer):
        """Test news reasoning generation"""
        # Test with positive news
        positive_news = [
            NewsItem(
                title="Bitcoin bullish",
                content="",
                url="",
                source="",
                published_at=datetime.now(),
                sentiment_score=0.8,
                relevance_score=0.7
            ),
            NewsItem(
                title="Crypto adoption",
                content="",
                url="",
                source="",
                published_at=datetime.now(),
                sentiment_score=0.7,
                relevance_score=0.6
            )
        ]
        
        reasoning = news_analyzer._generate_news_reasoning(positive_news)
        assert "Positive sentiment" in reasoning
        
        # Test with negative news
        negative_news = [
            NewsItem(
                title="Bitcoin crash",
                content="",
                url="",
                source="",
                published_at=datetime.now(),
                sentiment_score=0.2,
                relevance_score=0.7
            )
        ]
        
        reasoning = news_analyzer._generate_news_reasoning(negative_news)
        assert "Negative sentiment" in reasoning
        
        # Test with no news
        reasoning = news_analyzer._generate_news_reasoning([])
        assert "No recent news" in reasoning
    
    def test_update_market_analysis_with_news(self, news_analyzer):
        """Test updating market analysis with news"""
        # Create market analysis
        market_analysis = MarketAnalysis(
            technical_score=0.6,
            sentiment_score=0.5,
            news_score=0.5,
            overall_score=0.5,
            confidence=0.7,
            reasoning="Technical analysis",
            risk_level="MEDIUM"
        )
        
        # Create news items
        news_items = [
            NewsItem(
                title="Bitcoin bullish news",
                content="",
                url="",
                source="",
                published_at=datetime.now(),
                sentiment_score=0.8,
                relevance_score=0.7
            )
        ]
        
        # Update analysis
        updated_analysis = news_analyzer.update_market_analysis_with_news(market_analysis, news_items)
        
        assert updated_analysis.news_score > 0.5
        assert updated_analysis.sentiment_score > 0.5
        assert updated_analysis.overall_score > 0.5
        assert "News:" in updated_analysis.reasoning
    
    def test_update_market_analysis_without_news(self, news_analyzer):
        """Test updating market analysis without news"""
        market_analysis = MarketAnalysis(
            technical_score=0.6,
            sentiment_score=0.5,
            news_score=0.5,
            overall_score=0.5,
            confidence=0.7,
            reasoning="Technical analysis",
            risk_level="MEDIUM"
        )
        
        updated_analysis = news_analyzer.update_market_analysis_with_news(market_analysis, [])
        
        assert updated_analysis.news_score == 0.5
        assert updated_analysis.sentiment_score == 0.5
        assert updated_analysis.overall_score == 0.5
    
    @pytest.mark.asyncio
    async def test_analyze_news(self, news_analyzer):
        """Test news analysis with mocked search"""
        with patch.object(news_analyzer, '_search_news', return_value=[]):
            result = await news_analyzer.analyze_news("BTCUSDT")
            assert isinstance(result, list)
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_article_content(self, news_analyzer):
        """Test article content extraction"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html><body><p>Bitcoin price analysis</p></body></html>")
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            content = await news_analyzer._get_article_content("https://example.com/article")
            assert "Bitcoin price analysis" in content
    
    def test_sentiment_analysis_edge_cases(self, news_analyzer):
        """Test sentiment analysis edge cases"""
        # Empty text
        sentiment = news_analyzer._analyze_sentiment("", "")
        assert sentiment == 0.5
        
        # Very long text
        long_text = "bitcoin " * 1000
        sentiment = news_analyzer._analyze_sentiment(long_text, "")
        assert 0 <= sentiment <= 1
        
        # Text with only numbers
        numeric_text = "123 456 789"
        sentiment = news_analyzer._analyze_sentiment(numeric_text, "")
        assert 0 <= sentiment <= 1
    
    def test_relevance_calculation_edge_cases(self, news_analyzer):
        """Test relevance calculation edge cases"""
        # Empty text
        relevance = news_analyzer._calculate_relevance("", "")
        assert relevance == 0.5
        
        # Text with only Bitcoin mentions
        bitcoin_text = "bitcoin bitcoin bitcoin"
        relevance = news_analyzer._calculate_relevance(bitcoin_text, "")
        assert relevance > 0.5
        
        # Text with price mentions but no Bitcoin
        price_text = "$50,000 $60,000 price"
        relevance = news_analyzer._calculate_relevance(price_text, "")
        assert relevance < 0.5