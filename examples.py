"""Example usage of the AI Trading Bot."""

import asyncio
from trading_agent import TradingAgent
from market_tools import MarketAnalyzer, NewsAnalyzer
from trading_manager import BybitTradingManager
from monitor import TradingMonitor
from utils import health_check, get_system_info
from logger_config import setup_logging
from config import settings

async def example_market_analysis():
    """Example of market analysis."""
    print("🔍 Market Analysis Example")
    print("=" * 50)
    
    analyzer = MarketAnalyzer()
    analysis = analyzer.get_comprehensive_analysis("BTCUSDT")
    
    print(f"Current Price: ${analysis.get('current_price', 'N/A')}")
    print(f"Market Trend: {analysis.get('market_trend', 'N/A')}")
    print(f"Volatility: {analysis.get('volatility', 'N/A')}")
    print(f"Sentiment: {analysis.get('sentiment_analysis', {}).get('sentiment_text', 'N/A')}")
    
    # Technical indicators
    indicators = analysis.get('technical_indicators', {})
    print(f"\nTechnical Indicators:")
    print(f"RSI: {indicators.get('rsi', 'N/A')}")
    print(f"MACD: {indicators.get('macd', 'N/A')}")
    print(f"SMA 20: {indicators.get('sma_20', 'N/A')}")
    print(f"SMA 50: {indicators.get('sma_50', 'N/A')}")

async def example_news_analysis():
    """Example of news analysis."""
    print("\n📰 News Analysis Example")
    print("=" * 50)
    
    news_analyzer = NewsAnalyzer()
    news = news_analyzer.search_crypto_news("bitcoin", 5)
    sentiment = news_analyzer.analyze_sentiment(news)
    
    print(f"Found {len(news)} news articles")
    print(f"Sentiment Score: {sentiment.get('sentiment_score', 'N/A')}")
    print(f"Sentiment: {sentiment.get('sentiment_text', 'N/A')}")
    
    print(f"\nRecent News Headlines:")
    for i, article in enumerate(news[:3], 1):
        print(f"{i}. {article.get('title', 'No title')}")

async def example_trading_decision():
    """Example of trading decision making."""
    print("\n🤖 Trading Decision Example")
    print("=" * 50)
    
    agent = TradingAgent()
    result = await agent.run_trading_cycle()
    
    print(f"Decision: {result.get('decision', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")
    print(f"Action Taken: {result.get('action_taken', 'N/A')}")

def example_monitoring():
    """Example of monitoring and reporting."""
    print("\n📊 Monitoring Example")
    print("=" * 50)
    
    monitor = TradingMonitor()
    
    # Get performance stats
    stats = monitor.get_performance_stats(days=1)
    print(f"Total Decisions: {stats['total_decisions']}")
    print(f"Buy Decisions: {stats['buy_decisions']}")
    print(f"Sell Decisions: {stats['sell_decisions']}")
    print(f"Average Confidence: {stats['average_confidence']:.2f}")
    print(f"Executed Trades: {stats['executed_trades']}")
    
    # Generate report
    report = monitor.generate_report(days=1)
    print(f"\nReport Preview:")
    print(report[:500] + "..." if len(report) > 500 else report)

def example_system_check():
    """Example of system health check."""
    print("\n🔧 System Health Check")
    print("=" * 50)
    
    # Health check
    health = health_check()
    print(f"Overall Status: {health['status']}")
    
    for check_name, check_data in health['checks'].items():
        status = "✅" if check_data['status'] == 'pass' else "❌"
        print(f"{status} {check_name}: {check_data['status']}")
    
    # System info
    system_info = get_system_info()
    print(f"\nSystem Information:")
    print(f"Platform: {system_info['platform']}")
    print(f"Python Version: {system_info['python_version']}")
    print(f"CPU Cores: {system_info['cpu_count']}")

async def example_risk_management():
    """Example of risk management calculations."""
    print("\n⚠️ Risk Management Example")
    print("=" * 50)
    
    from trading_manager import RiskManager
    from utils import calculate_risk_reward_ratio, calculate_position_value
    
    risk_manager = RiskManager(
        max_position_size=0.1,
        stop_loss_percent=2.0,
        take_profit_percent=3.0,
        risk_per_trade=2.0
    )
    
    # Example trade parameters
    entry_price = 50000
    side = "Buy"
    account_balance = 10000
    
    # Calculate stop loss and take profit
    stop_loss = risk_manager.calculate_stop_loss(entry_price, side)
    take_profit = risk_manager.calculate_take_profit(entry_price, side)
    
    print(f"Entry Price: ${entry_price:,.2f}")
    print(f"Stop Loss: ${stop_loss:,.2f}")
    print(f"Take Profit: ${take_profit:,.2f}")
    
    # Calculate position size
    from trading_manager import BybitTradingManager
    trading_manager = BybitTradingManager("dummy", "dummy", testnet=True)
    position_size = trading_manager.calculate_position_size(
        account_balance, 2.0, entry_price, stop_loss
    )
    
    position_value = calculate_position_value(position_size, entry_price)
    risk_reward = calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)
    
    print(f"Position Size: {position_size:.6f} BTC")
    print(f"Position Value: ${position_value:,.2f}")
    print(f"Risk-Reward Ratio: {risk_reward:.2f}")

async def run_all_examples():
    """Run all examples."""
    print("🚀 AI Trading Bot Examples")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    try:
        await example_market_analysis()
        await example_news_analysis()
        await example_trading_decision()
        example_monitoring()
        example_system_check()
        await example_risk_management()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")

if __name__ == "__main__":
    asyncio.run(run_all_examples())