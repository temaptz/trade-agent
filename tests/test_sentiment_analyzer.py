"""
Tests for Sentiment Analyzer
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from sentiment_analyzer import SentimentAnalyzer
from models import MarketAnalysis, TradingDecision, TradeSignal

class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer"""
    
    @pytest.fixture
    def sentiment_analyzer(self):
        """Create SentimentAnalyzer instance"""
        return SentimentAnalyzer()
    
    def test_prepare_analysis_context(self, sentiment_analyzer):
        """Test context preparation for LLM analysis"""
        market_data = {
            "price": 50000.0,
            "change_percent_24h": 2.5,
            "volume": 1000000.0,
            "high_24h": 51000.0,
            "low_24h": 49000.0
        }
        
        news_items = [
            Mock(
                title="Bitcoin price analysis",
                content="Bitcoin reaches new highs",
                sentiment_score=0.8,
                relevance_score=0.7
            )
        ]
        
        context = sentiment_analyzer._prepare_analysis_context(news_items, market_data)
        
        assert "MARKET DATA" in context
        assert "50000" in context
        assert "2.5" in context
        assert "RECENT NEWS" in context
        assert "Bitcoin price analysis" in context
    
    def test_create_sentiment_prompt(self, sentiment_analyzer):
        """Test sentiment analysis prompt creation"""
        context = "Sample market data and news context"
        prompt = sentiment_analyzer._create_sentiment_prompt(context)
        
        assert "Sample market data and news context" in prompt
        assert "JSON format" in prompt
        assert "overall_sentiment" in prompt
        assert "sentiment_score" in prompt
        assert "confidence" in prompt
    
    def test_parse_llm_response_valid_json(self, sentiment_analyzer):
        """Test parsing valid JSON response from LLM"""
        valid_response = '''
        {
            "overall_sentiment": "bullish",
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "key_factors": ["Strong technical indicators", "Positive news"],
            "market_outlook": "Bullish trend expected",
            "risk_assessment": "medium",
            "trading_recommendation": "buy",
            "reasoning": "Multiple positive factors"
        }
        '''
        
        result = sentiment_analyzer._parse_llm_response(valid_response)
        
        assert result["overall_sentiment"] == "bullish"
        assert result["sentiment_score"] == 0.8
        assert result["confidence"] == 0.9
        assert result["risk_assessment"] == "medium"
        assert result["trading_recommendation"] == "buy"
        assert len(result["key_factors"]) == 2
    
    def test_parse_llm_response_invalid_json(self, sentiment_analyzer):
        """Test parsing invalid JSON response from LLM"""
        invalid_response = "This is not valid JSON response"
        
        result = sentiment_analyzer._parse_llm_response(invalid_response)
        
        # Should fallback to text analysis
        assert "overall_sentiment" in result
        assert "sentiment_score" in result
        assert 0 <= result["sentiment_score"] <= 1
    
    def test_validate_analysis(self, sentiment_analyzer):
        """Test analysis validation and normalization"""
        raw_analysis = {
            "overall_sentiment": "BULLISH",
            "sentiment_score": 1.5,  # Out of range
            "confidence": -0.5,  # Out of range
            "key_factors": ["Factor 1", "Factor 2"],
            "market_outlook": "Very bullish",
            "risk_assessment": "HIGH",
            "trading_recommendation": "BUY",
            "reasoning": "Strong signals"
        }
        
        validated = sentiment_analyzer._validate_analysis(raw_analysis)
        
        assert validated["overall_sentiment"] == "bullish"
        assert validated["sentiment_score"] == 1.0  # Clamped to max
        assert validated["confidence"] == 0.0  # Clamped to min
        assert validated["risk_assessment"] == "high"
        assert validated["trading_recommendation"] == "buy"
    
    def test_extract_sentiment_from_text(self, sentiment_analyzer):
        """Test sentiment extraction from unstructured text"""
        bullish_text = "The market is very bullish with strong positive indicators and buy signals"
        result = sentiment_analyzer._extract_sentiment_from_text(bullish_text)
        
        assert result["overall_sentiment"] == "bullish"
        assert result["sentiment_score"] > 0.5
        
        bearish_text = "Market is bearish with negative indicators and sell signals"
        result = sentiment_analyzer._extract_sentiment_from_text(bearish_text)
        
        assert result["overall_sentiment"] == "bearish"
        assert result["sentiment_score"] < 0.5
    
    def test_get_default_sentiment(self, sentiment_analyzer):
        """Test default sentiment when analysis fails"""
        result = sentiment_analyzer._get_default_sentiment()
        
        assert result["overall_sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.5
        assert result["confidence"] == 0.3
        assert result["risk_assessment"] == "medium"
        assert result["trading_recommendation"] == "hold"
    
    def test_generate_trading_decision(self, sentiment_analyzer):
        """Test trading decision generation"""
        market_analysis = MarketAnalysis(
            technical_score=0.8,
            sentiment_score=0.7,
            news_score=0.6,
            overall_score=0.7,
            confidence=0.8,
            reasoning="Strong technical signals",
            risk_level="LOW"
        )
        
        sentiment_analysis = {
            "sentiment_score": 0.8,
            "overall_sentiment": "bullish",
            "confidence": 0.9,
            "risk_assessment": "low"
        }
        
        decision = sentiment_analyzer.generate_trading_decision(market_analysis, sentiment_analysis)
        
        assert isinstance(decision, TradingDecision)
        assert decision.signal in [TradeSignal.BUY, TradeSignal.SELL, TradeSignal.HOLD]
        assert 0 <= decision.confidence <= 1
        assert 0 <= decision.position_size <= 1
        assert decision.market_analysis == market_analysis
    
    def test_calculate_position_size(self, sentiment_analyzer):
        """Test position size calculation"""
        # High confidence, low risk
        size = sentiment_analyzer._calculate_position_size(0.9, "low")
        assert size > 0
        
        # Low confidence, high risk
        size = sentiment_analyzer._calculate_position_size(0.3, "high")
        assert size < 0.5
        
        # Medium confidence, medium risk
        size = sentiment_analyzer._calculate_position_size(0.6, "medium")
        assert 0 <= size <= 1
    
    def test_calculate_stop_take_profit(self, sentiment_analyzer):
        """Test stop loss and take profit calculation"""
        # Buy signal
        stop_loss, take_profit = sentiment_analyzer._calculate_stop_take_profit("BUY", 0.8, "medium")
        assert stop_loss is not None
        assert take_profit is not None
        assert stop_loss < take_profit
        
        # Sell signal
        stop_loss, take_profit = sentiment_analyzer._calculate_stop_take_profit("SELL", 0.8, "medium")
        assert stop_loss is not None
        assert take_profit is not None
    
    def test_generate_decision_reasoning(self, sentiment_analyzer):
        """Test decision reasoning generation"""
        market_analysis = MarketAnalysis(
            technical_score=0.8,
            sentiment_score=0.7,
            news_score=0.6,
            overall_score=0.7,
            confidence=0.8,
            reasoning="Technical analysis",
            risk_level="LOW"
        )
        
        sentiment_analysis = {
            "sentiment_score": 0.8,
            "overall_sentiment": "bullish",
            "confidence": 0.9,
            "key_factors": ["Factor 1", "Factor 2"],
            "risk_assessment": "low",
            "market_outlook": "Bullish trend"
        }
        
        reasoning = sentiment_analyzer._generate_decision_reasoning(
            market_analysis, sentiment_analysis, "BUY", 0.8
        )
        
        assert isinstance(reasoning, str)
        assert "Technical Score" in reasoning
        assert "Sentiment" in reasoning
        assert "News Score" in reasoning
        assert "Combined Score" in reasoning
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_advanced(self, sentiment_analyzer):
        """Test advanced sentiment analysis with mocked LLM"""
        news_items = [
            Mock(
                title="Bitcoin bullish news",
                content="Bitcoin price analysis shows positive trends",
                sentiment_score=0.8,
                relevance_score=0.7
            )
        ]
        
        market_data = {
            "price": 50000.0,
            "change_percent_24h": 2.5,
            "volume": 1000000.0,
            "high_24h": 51000.0,
            "low_24h": 49000.0
        }
        
        with patch.object(sentiment_analyzer.client, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {
                    'content': '''
                    {
                        "overall_sentiment": "bullish",
                        "sentiment_score": 0.8,
                        "confidence": 0.9,
                        "key_factors": ["Strong technical indicators"],
                        "market_outlook": "Bullish trend expected",
                        "risk_assessment": "medium",
                        "trading_recommendation": "buy",
                        "reasoning": "Multiple positive factors"
                    }
                    '''
                }
            }
            
            result = await sentiment_analyzer.analyze_sentiment_advanced(news_items, market_data)
            
            assert result["overall_sentiment"] == "bullish"
            assert result["sentiment_score"] == 0.8
            assert result["confidence"] == 0.9
    
    def test_error_handling(self, sentiment_analyzer):
        """Test error handling in various methods"""
        # Test with None values
        result = sentiment_analyzer._calculate_position_size(None, None)
        assert result == 0.0
        
        # Test with invalid values
        result = sentiment_analyzer._calculate_position_size(-1, "invalid")
        assert result == 0.0
        
        # Test with empty analysis
        result = sentiment_analyzer._validate_analysis({})
        assert result["overall_sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.5