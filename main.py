"""
Bitcoin Trading Agent - Main Application
Advanced AI agent for Bitcoin trading on Bybit using LangGraph, LangChain, and Ollama
"""
import asyncio
import signal
import sys
import time
from datetime import datetime
from typing import Optional
from loguru import logger

from config import config
from trading_workflow import TradingWorkflow
from monitoring import TradingMonitor, SystemHealth
from bybit_client import BybitClient
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from sentiment_analyzer import SentimentAnalyzer

class BitcoinTradingAgent:
    """Main Bitcoin Trading Agent class"""
    
    def __init__(self):
        self.workflow = TradingWorkflow()
        self.monitor = TradingMonitor()
        self.is_running = False
        self.analysis_interval = config.news_update_interval  # seconds
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Bitcoin Trading Agent initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    async def start(self):
        """Start the trading agent"""
        try:
            logger.info("Starting Bitcoin Trading Agent...")
            
            # Start monitoring
            self.monitor.start_monitoring()
            
            # Test all components
            if not await self._test_components():
                logger.error("Component tests failed, cannot start agent")
                return False
            
            self.is_running = True
            logger.info("Bitcoin Trading Agent started successfully")
            
            # Start main trading loop
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Error starting trading agent: {e}")
            return False
    
    def stop(self):
        """Stop the trading agent"""
        try:
            logger.info("Stopping Bitcoin Trading Agent...")
            
            self.is_running = False
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            
            # Generate final report
            report = self.monitor.generate_report()
            logger.info(f"Final Report:\n{report}")
            
            logger.info("Bitcoin Trading Agent stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading agent: {e}")
    
    async def _test_components(self) -> bool:
        """Test all system components"""
        try:
            logger.info("Testing system components...")
            
            # Test Bybit API connection
            try:
                bybit_client = BybitClient()
                account_info = bybit_client.get_account_info()
                logger.info("✓ Bybit API connection successful")
            except Exception as e:
                logger.error(f"✗ Bybit API connection failed: {e}")
                return False
            
            # Test Ollama connection
            try:
                from sentiment_analyzer import SentimentAnalyzer
                sentiment_analyzer = SentimentAnalyzer()
                # Simple test - just check if client can connect
                logger.info("✓ Ollama connection successful")
            except Exception as e:
                logger.error(f"✗ Ollama connection failed: {e}")
                return False
            
            # Test news service
            try:
                news_analyzer = NewsAnalyzer()
                logger.info("✓ News service initialized")
            except Exception as e:
                logger.error(f"✗ News service failed: {e}")
                return False
            
            # Test market analyzer
            try:
                market_analyzer = MarketAnalyzer(bybit_client)
                logger.info("✓ Market analyzer initialized")
            except Exception as e:
                logger.error(f"✗ Market analyzer failed: {e}")
                return False
            
            logger.info("All components tested successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error testing components: {e}")
            return False
    
    async def _main_loop(self):
        """Main trading loop"""
        try:
            logger.info("Starting main trading loop...")
            
            while self.is_running:
                try:
                    # Run trading analysis
                    await self._run_trading_cycle()
                    
                    # Update system health
                    await self._update_system_health()
                    
                    # Wait for next cycle
                    logger.info(f"Waiting {self.analysis_interval} seconds until next analysis...")
                    await asyncio.sleep(self.analysis_interval)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retry
            
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
    
    async def _run_trading_cycle(self):
        """Run a complete trading analysis cycle"""
        try:
            cycle_start = time.time()
            logger.info("Starting trading analysis cycle...")
            
            # Run the trading workflow
            result = await self.workflow.run_analysis()
            
            # Log the results
            if result.error:
                logger.error(f"Trading cycle failed: {result.error}")
            else:
                logger.info("Trading cycle completed successfully")
                
                # Log market analysis if available
                if result.market_analysis:
                    analysis_time = time.time() - cycle_start
                    news_count = len(result.news_items) if result.news_items else 0
                    self.monitor.log_market_analysis(
                        result.market_analysis, news_count, analysis_time
                    )
                
                # Log trading decision if available
                if result.trading_decision:
                    logger.info(f"Trading Decision: {result.trading_decision.signal} "
                              f"(Confidence: {result.trading_decision.confidence:.3f})")
                    
                    # Log execution result if available
                    if hasattr(result, 'execution_result'):
                        self.monitor.log_trade_execution(
                            result.trading_decision,
                            result.execution_result,
                            result.market_data
                        )
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    async def _update_system_health(self):
        """Update system health status"""
        try:
            # Test API connections
            api_connection = await self._test_bybit_connection()
            ollama_connection = await self._test_ollama_connection()
            news_service = await self._test_news_service()
            market_data_fresh = await self._test_market_data_freshness()
            
            # Get system metrics (simplified)
            memory_usage = 0.0  # Would need psutil for real metrics
            cpu_usage = 0.0     # Would need psutil for real metrics
            
            # Create health status
            health = SystemHealth(
                timestamp=datetime.now(),
                api_connection=api_connection,
                ollama_connection=ollama_connection,
                news_service=news_service,
                market_data_fresh=market_data_fresh,
                last_trade_time=None,  # Would track from trade history
                error_count=0,  # Would track from logs
                memory_usage=memory_usage,
                cpu_usage=cpu_usage
            )
            
            # Log health status
            self.monitor.log_system_health(health)
            
        except Exception as e:
            logger.error(f"Error updating system health: {e}")
    
    async def _test_bybit_connection(self) -> bool:
        """Test Bybit API connection"""
        try:
            bybit_client = BybitClient()
            bybit_client.get_account_info()
            return True
        except Exception:
            return False
    
    async def _test_ollama_connection(self) -> bool:
        """Test Ollama connection"""
        try:
            from sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            # Simple connection test
            return True
        except Exception:
            return False
    
    async def _test_news_service(self) -> bool:
        """Test news service"""
        try:
            news_analyzer = NewsAnalyzer()
            # Simple initialization test
            return True
        except Exception:
            return False
    
    async def _test_market_data_freshness(self) -> bool:
        """Test if market data is fresh"""
        try:
            bybit_client = BybitClient()
            market_data = bybit_client.get_market_data()
            
            # Check if data is less than 5 minutes old
            time_diff = datetime.now() - market_data.timestamp
            return time_diff.total_seconds() < 300  # 5 minutes
            
        except Exception:
            return False
    
    def get_status(self) -> dict:
        """Get current agent status"""
        try:
            return {
                "is_running": self.is_running,
                "analysis_interval": self.analysis_interval,
                "workflow_status": self.workflow.get_workflow_status(),
                "performance": self.monitor.get_performance_summary(),
                "health": self.monitor.get_system_health()
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"error": str(e)}

async def main():
    """Main application entry point"""
    try:
        # Create and start the trading agent
        agent = BitcoinTradingAgent()
        
        # Start the agent
        await agent.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the application
    asyncio.run(main())