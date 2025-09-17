"""Test script for the trading bot."""
import asyncio
import os
from loguru import logger

from trading_agent import TradingAgent
from market_tools import MarketAnalyzer, NewsAnalyzer
from trading_manager import BybitTradingManager
from logger_config import setup_logging
from config import settings

async def test_market_analysis():
    """Test market analysis functionality."""
    logger.info("Testing market analysis...")
    
    try:
        analyzer = MarketAnalyzer()
        analysis = analyzer.get_comprehensive_analysis("BTCUSDT")
        
        logger.info("Market analysis test results:")
        logger.info(f"Current price: {analysis.get('current_price')}")
        logger.info(f"Market trend: {analysis.get('market_trend')}")
        logger.info(f"Volatility: {analysis.get('volatility')}")
        logger.info(f"Sentiment: {analysis.get('sentiment_analysis', {}).get('sentiment_text')}")
        
        return True
    except Exception as e:
        logger.error(f"Market analysis test failed: {e}")
        return False

async def test_news_analysis():
    """Test news analysis functionality."""
    logger.info("Testing news analysis...")
    
    try:
        news_analyzer = NewsAnalyzer()
        news = news_analyzer.search_crypto_news("bitcoin", 5)
        sentiment = news_analyzer.analyze_sentiment(news)
        
        logger.info("News analysis test results:")
        logger.info(f"Found {len(news)} news articles")
        logger.info(f"Sentiment score: {sentiment.get('sentiment_score')}")
        logger.info(f"Sentiment: {sentiment.get('sentiment_text')}")
        
        return True
    except Exception as e:
        logger.error(f"News analysis test failed: {e}")
        return False

async def test_trading_manager():
    """Test trading manager functionality."""
    logger.info("Testing trading manager...")
    
    try:
        # Test with dummy credentials (won't actually trade)
        manager = BybitTradingManager("dummy_key", "dummy_secret", testnet=True)
        
        # Test getting current price (this should work even with dummy credentials)
        price = manager.get_current_price("BTCUSDT")
        logger.info(f"Current BTC price: {price}")
        
        # Test position size calculation
        position_size = manager.calculate_position_size(1000, 2, 50000, 49000)
        logger.info(f"Calculated position size: {position_size}")
        
        return True
    except Exception as e:
        logger.error(f"Trading manager test failed: {e}")
        return False

async def test_llm_connection():
    """Test LLM connection."""
    logger.info("Testing LLM connection...")
    
    try:
        from langchain_ollama import OllamaLLM
        
        llm = OllamaLLM(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.1
        )
        
        response = llm.invoke("Hello, are you working?")
        logger.info(f"LLM response: {response}")
        
        return True
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        logger.error("Make sure Ollama is running and the model is available")
        return False

async def test_trading_agent():
    """Test the complete trading agent."""
    logger.info("Testing trading agent...")
    
    try:
        agent = TradingAgent()
        result = await agent.run_trading_cycle()
        
        logger.info("Trading agent test results:")
        logger.info(f"Decision: {result.get('decision')}")
        logger.info(f"Confidence: {result.get('confidence')}")
        logger.info(f"Reasoning: {result.get('reasoning')}")
        logger.info(f"Action taken: {result.get('action_taken')}")
        
        return True
    except Exception as e:
        logger.error(f"Trading agent test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    logger.info("Starting comprehensive bot tests...")
    
    tests = [
        ("Market Analysis", test_market_analysis),
        ("News Analysis", test_news_analysis),
        ("Trading Manager", test_trading_manager),
        ("LLM Connection", test_llm_connection),
        ("Trading Agent", test_trading_agent),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            logger.info(f"Test {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! Bot is ready to use.")
    else:
        logger.warning("Some tests failed. Please check the configuration and dependencies.")
    
    return results

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        logger.error("No .env file found. Please copy .env.example to .env and configure it.")
        exit(1)
    
    # Run tests
    asyncio.run(run_all_tests())