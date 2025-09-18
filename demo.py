"""
Demo script for Bitcoin trading agent
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

from trading_agent import BitcoinTradingAgent
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from ollama_client import OllamaClient

async def demo_market_analysis():
    """Demo market analysis"""
    print("🔍 Market Analysis Demo")
    print("=" * 50)
    
    try:
        # Initialize components
        bybit_client = BybitClient()
        market_analyzer = MarketAnalyzer(bybit_client)
        
        # Get market data
        print("📊 Fetching market data...")
        market_data = await market_analyzer.analyze_market()
        
        # Display results
        price_data = market_data['price_data']
        print(f"💰 Current Price: ${price_data['current_price']:.2f}")
        print(f"📈 24h Change: {price_data['price_change_24h']:.2f}%")
        print(f"📊 Volume: {price_data['volume_24h']:,.0f}")
        
        # Technical indicators
        indicators = market_data['indicators']
        print(f"\n📊 Technical Indicators:")
        print(f"   RSI: {indicators['rsi']:.2f}")
        print(f"   MACD: {indicators['macd']:.4f}")
        print(f"   BB Position: {indicators['bb_position']:.2f}")
        
        # Sentiment
        sentiment = market_data['sentiment']
        print(f"\n😊 Market Sentiment: {sentiment['overall']}")
        print(f"   Score: {sentiment['score']}")
        
        # Recommendation
        recommendation = market_data['recommendation']
        print(f"\n🎯 Recommendation: {recommendation['action']}")
        print(f"   Confidence: {recommendation['confidence']:.1f}%")
        
        return market_data
        
    except Exception as e:
        print(f"❌ Error in market analysis: {e}")
        return None

async def demo_news_analysis():
    """Demo news analysis"""
    print("\n📰 News Analysis Demo")
    print("=" * 50)
    
    try:
        async with NewsAnalyzer() as news_analyzer:
            # Search for Bitcoin news
            print("🔍 Searching for Bitcoin news...")
            news_items = await news_analyzer.search_bitcoin_news(max_results=5)
            
            print(f"📰 Found {len(news_items)} news items")
            
            # Analyze sentiment
            sentiment_analysis = await news_analyzer.analyze_news_sentiment(news_items)
            
            print(f"\n📊 News Sentiment: {sentiment_analysis['overall_sentiment']}")
            print(f"   Score: {sentiment_analysis['sentiment_score']:.2f}")
            
            # Display top news
            print(f"\n📰 Top News Items:")
            for i, item in enumerate(news_items[:3], 1):
                print(f"   {i}. {item.title}")
                print(f"      Source: {item.source}")
                print(f"      Sentiment: {item.sentiment_score:.2f}")
                print()
            
            return {
                'news_items': news_items,
                'sentiment': sentiment_analysis
            }
            
    except Exception as e:
        print(f"❌ Error in news analysis: {e}")
        return None

async def demo_llm_analysis():
    """Demo LLM analysis"""
    print("\n🤖 LLM Analysis Demo")
    print("=" * 50)
    
    try:
        async with OllamaClient() as ollama_client:
            # Check if model is available
            if not await ollama_client.check_model_availability():
                print("⚠️  Ollama model not available. Please install gemma2:9b")
                return None
            
            # Sample market data
            market_data = {
                'price_data': {'current_price': 50000, 'price_change_24h': 2.5},
                'indicators': {'rsi': 45, 'macd': 100},
                'sentiment': {'overall': 'Bullish', 'score': 2}
            }
            
            # Sample news data
            news_data = {
                'sentiment': {'overall_sentiment': 'positive', 'sentiment_score': 0.3}
            }
            
            print("🧠 Analyzing with LLM...")
            analysis = await ollama_client.analyze_market_data(market_data, news_data)
            
            print("📝 LLM Analysis:")
            print(f"   {analysis['llm_analysis']}")
            
            return analysis
            
    except Exception as e:
        print(f"❌ Error in LLM analysis: {e}")
        return None

async def demo_trading_agent():
    """Demo trading agent"""
    print("\n🤖 Trading Agent Demo")
    print("=" * 50)
    
    try:
        # Initialize trading agent
        agent = BitcoinTradingAgent()
        
        print("🔄 Running analysis cycle...")
        result = await agent.run_analysis_cycle()
        
        if result['success']:
            print("✅ Analysis completed successfully")
            
            # Display results
            analysis_result = result.get('result', {})
            
            if 'market_data' in analysis_result:
                market_data = analysis_result['market_data']
                price = market_data.get('price_data', {}).get('current_price', 0)
                print(f"💰 Current Price: ${price:.2f}")
            
            if 'recommendation' in analysis_result:
                recommendation = analysis_result['recommendation']
                print(f"🎯 Recommendation: {recommendation.get('action', 'HOLD')}")
                print(f"   Confidence: {recommendation.get('confidence', 0)}%")
            
            if 'trading_decision' in analysis_result:
                decision = analysis_result['trading_decision']
                print(f"📊 Trading Decision: {decision}")
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in trading agent demo: {e}")
        return None

async def demo_portfolio_management():
    """Demo portfolio management"""
    print("\n💼 Portfolio Management Demo")
    print("=" * 50)
    
    try:
        from trading_strategies import PortfolioManager, Position, RiskManager
        
        # Initialize portfolio manager
        risk_manager = RiskManager()
        portfolio_manager = PortfolioManager(risk_manager)
        
        # Add sample position
        position = Position(
            symbol="BTCUSDT",
            side="long",
            size=0.1,
            entry_price=50000,
            current_price=51000,
            unrealized_pnl=100,
            stop_loss=48000,
            take_profit=52000,
            timestamp=datetime.now()
        )
        
        portfolio_manager.add_position(position)
        
        # Get portfolio summary
        summary = portfolio_manager.get_portfolio_summary()
        
        print(f"📊 Portfolio Summary:")
        print(f"   Total Positions: {summary['total_positions']}")
        print(f"   Total PnL: ${summary['total_pnl']:.2f}")
        print(f"   Total Value: ${summary['total_value']:.2f}")
        
        # Check triggers
        triggers = portfolio_manager.check_stop_loss_take_profit("BTCUSDT", 53000)
        if triggers:
            print(f"🚨 Triggers: {triggers}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error in portfolio management demo: {e}")
        return None

async def main():
    """Main demo function"""
    print("🚀 Bitcoin Trading Agent Demo")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run demos
    demos = [
        ("Market Analysis", demo_market_analysis),
        ("News Analysis", demo_news_analysis),
        ("LLM Analysis", demo_llm_analysis),
        ("Trading Agent", demo_trading_agent),
        ("Portfolio Management", demo_portfolio_management)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*60}")
            result = await demo_func()
            results[demo_name] = result is not None
        except Exception as e:
            print(f"❌ Demo '{demo_name}' failed: {e}")
            results[demo_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Demo Summary:")
    for demo_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {demo_name}")
    
    print(f"\n🏁 Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())