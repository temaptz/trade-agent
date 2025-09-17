"""Main trading bot script."""
import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
import schedule
import time
from loguru import logger

from trading_agent import TradingAgent
from logger_config import setup_logging, log_trading_decision, log_market_analysis
from config import settings

class TradingBot:
    """Main trading bot class."""
    
    def __init__(self):
        self.agent = TradingAgent()
        self.running = False
        self.cycle_count = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def run_single_cycle(self) -> dict:
        """Run a single trading cycle."""
        logger.info(f"Starting trading cycle #{self.cycle_count + 1}")
        
        try:
            result = await self.agent.run_trading_cycle()
            
            # Log results
            if result.get("market_analysis"):
                log_market_analysis(result["market_analysis"])
            
            if result.get("action_taken"):
                log_trading_decision(result)
            
            self.cycle_count += 1
            logger.info(f"Trading cycle #{self.cycle_count} completed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trading cycle #{self.cycle_count + 1}: {e}")
            return {"error": str(e)}
    
    async def run_continuous(self, interval_minutes: int = 30):
        """Run the bot continuously with specified interval."""
        logger.info(f"Starting continuous trading with {interval_minutes} minute intervals")
        self.running = True
        
        while self.running:
            try:
                await self.run_single_cycle()
                
                if self.running:
                    logger.info(f"Waiting {interval_minutes} minutes until next cycle...")
                    await asyncio.sleep(interval_minutes * 60)
                    
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in continuous mode: {e}")
                if self.running:
                    logger.info("Waiting 5 minutes before retry...")
                    await asyncio.sleep(300)  # Wait 5 minutes before retry
        
        logger.info("Trading bot stopped")
    
    def run_scheduled(self):
        """Run the bot on a schedule."""
        logger.info("Starting scheduled trading bot")
        
        # Schedule trading cycles
        schedule.every(30).minutes.do(self._run_scheduled_cycle)
        schedule.every().hour.do(self._log_status)
        schedule.every().day.at("09:00").do(self._daily_report)
        
        self.running = True
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in scheduled mode: {e}")
                time.sleep(60)  # Wait 1 minute before retry
        
        logger.info("Scheduled trading bot stopped")
    
    def _run_scheduled_cycle(self):
        """Run a scheduled trading cycle."""
        logger.info("Running scheduled trading cycle")
        try:
            # Run in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_single_cycle())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error in scheduled cycle: {e}")
            return {"error": str(e)}
    
    def _log_status(self):
        """Log current status."""
        logger.info(f"Bot status: Running, Cycles completed: {self.cycle_count}")
    
    def _daily_report(self):
        """Generate daily report."""
        logger.info(f"Daily report: Completed {self.cycle_count} trading cycles today")

async def main():
    """Main function."""
    # Setup logging
    setup_logging()
    
    logger.info("Starting Trading Bot")
    logger.info(f"Configuration: {settings.trading_pair}, Testnet: {settings.bybit_testnet}")
    
    # Create bot instance
    bot = TradingBot()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "single":
            # Run single cycle
            logger.info("Running in single cycle mode")
            result = await bot.run_single_cycle()
            logger.info(f"Single cycle result: {result}")
            
        elif mode == "continuous":
            # Run continuously
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            logger.info(f"Running in continuous mode with {interval} minute intervals")
            await bot.run_continuous(interval)
            
        elif mode == "scheduled":
            # Run on schedule
            logger.info("Running in scheduled mode")
            bot.run_scheduled()
            
        else:
            logger.error(f"Unknown mode: {mode}")
            logger.info("Available modes: single, continuous [interval], scheduled")
            sys.exit(1)
    else:
        # Default: run single cycle
        logger.info("Running in single cycle mode (default)")
        result = await bot.run_single_cycle()
        logger.info(f"Single cycle result: {result}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)