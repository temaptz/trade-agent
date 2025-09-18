"""
Main entry point for Bitcoin trading agent
"""
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
import json

from config import config
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from ollama_client import OllamaClient
from trading_agent import BitcoinTradingAgent
from trading_strategies import RiskManager, TechnicalStrategy, SentimentStrategy, PortfolioManager

class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        # Initialize components
        self.bybit_client = BybitClient()
        self.market_analyzer = MarketAnalyzer(self.bybit_client)
        self.news_analyzer = NewsAnalyzer()
        self.ollama_client = OllamaClient()
        
        # Initialize trading agent
        self.trading_agent = BitcoinTradingAgent()
        
        # Initialize strategies
        self.risk_manager = RiskManager()
        self.technical_strategy = TechnicalStrategy(self.risk_manager)
        self.sentiment_strategy = SentimentStrategy(self.risk_manager)
        self.portfolio_manager = PortfolioManager(self.risk_manager)
        
        # Bot state
        self.is_running = False
        self.last_analysis_time = None
        self.analysis_count = 0
        
        # Setup logging
        logger.add("trading_bot.log", rotation="1 day", retention="7 days")
        
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            logger.info("Initializing Bitcoin trading bot...")
            
            # Check Ollama model availability
            async with self.ollama_client as ollama:
                if not await ollama.check_model_availability():
                    logger.warning(f"Model {config.ollama_model} not available, attempting to pull...")
                    if not await ollama.pull_model():
                        logger.error("Failed to pull Ollama model")
                        return False
            
            # Test Bybit connection
            try:
                balance = await self.bybit_client.get_balance()
                logger.info("Bybit connection successful")
            except Exception as e:
                logger.error(f"Bybit connection failed: {e}")
                return False
            
            # Test news analyzer
            try:
                async with self.news_analyzer as news:
                    news_items = await news.search_bitcoin_news(max_results=5)
                    logger.info(f"News analyzer working, found {len(news_items)} news items")
            except Exception as e:
                logger.error(f"News analyzer failed: {e}")
                return False
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def run_analysis_cycle(self) -> Dict:
        """Run a complete analysis cycle"""
        try:
            logger.info("Starting analysis cycle...")
            self.analysis_count += 1
            
            # Run the trading agent workflow
            result = await self.trading_agent.run_analysis_cycle()
            
            if result['success']:
                logger.info("Analysis cycle completed successfully")
                self.last_analysis_time = datetime.now()
            else:
                logger.error(f"Analysis cycle failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analysis cycle: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_continuous_trading(self):
        """Run continuous trading loop"""
        try:
            logger.info("Starting continuous trading mode...")
            self.is_running = True
            
            while self.is_running:
                try:
                    # Run analysis cycle
                    result = await self.run_analysis_cycle()
                    
                    if result['success']:
                        # Log the results
                        self._log_analysis_results(result)
                        
                        # Check for any stop loss or take profit triggers
                        await self._check_position_triggers()
                    
                    # Wait for next analysis interval
                    await asyncio.sleep(config.market_analysis_interval)
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
            
        except Exception as e:
            logger.error(f"Error in continuous trading: {e}")
        finally:
            self.is_running = False
    
    async def run_single_analysis(self) -> Dict:
        """Run a single analysis cycle"""
        try:
            logger.info("Running single analysis...")
            result = await self.run_analysis_cycle()
            self._log_analysis_results(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in single analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_market_summary(self) -> Dict:
        """Get current market summary"""
        try:
            return await self.trading_agent.get_market_summary()
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {'error': str(e)}
    
    def _log_analysis_results(self, result: Dict):
        """Log analysis results"""
        try:
            if result.get('success'):
                analysis_result = result.get('result', {})
                
                # Log market data
                market_data = analysis_result.get('market_data')
                if market_data:
                    price = market_data.get('price_data', {}).get('current_price', 0)
                    logger.info(f"Current Bitcoin price: ${price:.2f}")
                
                # Log news sentiment
                news_data = analysis_result.get('news_data')
                if news_data:
                    sentiment = news_data.get('sentiment', {})
                    overall_sentiment = sentiment.get('overall_sentiment', 'unknown')
                    logger.info(f"News sentiment: {overall_sentiment}")
                
                # Log recommendation
                recommendation = analysis_result.get('recommendation')
                if recommendation:
                    action = recommendation.get('action', 'HOLD')
                    confidence = recommendation.get('confidence', 0)
                    logger.info(f"Trading recommendation: {action} (confidence: {confidence}%)")
                
                # Log trading decision
                trading_decision = analysis_result.get('trading_decision')
                if trading_decision:
                    logger.info(f"Trading decision: {trading_decision}")
            
        except Exception as e:
            logger.error(f"Error logging analysis results: {e}")
    
    async def _check_position_triggers(self):
        """Check for stop loss and take profit triggers"""
        try:
            # Get current price
            ticker = await self.bybit_client.get_ticker()
            current_price = ticker.get('last', 0)
            
            if current_price > 0:
                # Check portfolio triggers
                triggers = self.portfolio_manager.check_stop_loss_take_profit(
                    config.trading_symbol, current_price
                )
                
                for trigger in triggers:
                    logger.warning(f"Position trigger: {trigger}")
                    # Here you would implement the actual trade execution
                    
        except Exception as e:
            logger.error(f"Error checking position triggers: {e}")
    
    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.is_running = False

async def main():
    """Main function"""
    try:
        # Create trading bot
        bot = TradingBot()
        
        # Initialize bot
        if not await bot.initialize():
            logger.error("Failed to initialize trading bot")
            return
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            bot.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "single":
                # Run single analysis
                logger.info("Running single analysis mode")
                result = await bot.run_single_analysis()
                print(json.dumps(result, indent=2))
                
            elif command == "summary":
                # Get market summary
                logger.info("Getting market summary")
                summary = await bot.get_market_summary()
                print(json.dumps(summary, indent=2))
                
            elif command == "continuous":
                # Run continuous trading
                logger.info("Running continuous trading mode")
                await bot.run_continuous_trading()
                
            else:
                print("Usage: python main.py [single|summary|continuous]")
        else:
            # Default: run single analysis
            logger.info("Running single analysis mode (default)")
            result = await bot.run_single_analysis()
            print(json.dumps(result, indent=2))
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        logger.info("Trading bot stopped")

if __name__ == "__main__":
    asyncio.run(main())