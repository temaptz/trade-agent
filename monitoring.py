"""
Comprehensive monitoring and logging system for Bitcoin trading agent
"""
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from loguru import logger
import schedule
import time
import threading

from models import TradingState, TradingDecision, MarketData, Position
from config import config

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""
    timestamp: datetime
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_pnl: float
    daily_pnl: float
    win_rate: float
    avg_trade_size: float
    max_drawdown: float
    sharpe_ratio: float
    current_position_value: float
    account_balance: float

@dataclass
class SystemHealth:
    """System health metrics"""
    timestamp: datetime
    api_connection: bool
    ollama_connection: bool
    news_service: bool
    market_data_fresh: bool
    last_trade_time: Optional[datetime]
    error_count: int
    memory_usage: float
    cpu_usage: float

class TradingMonitor:
    """Comprehensive trading monitoring system"""
    
    def __init__(self):
        self.log_file = config.log_file
        self.performance_file = "logs/performance.json"
        self.health_file = "logs/health.json"
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.health_history: List[SystemHealth] = []
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Performance tracking
        self.trade_history: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.initial_balance = 0.0
        
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        try:
            # Remove default handler
            logger.remove()
            
            # Console logging
            logger.add(
                sink=lambda msg: print(msg, end=""),
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=config.log_level,
                colorize=True
            )
            
            # File logging
            logger.add(
                sink=self.log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level="DEBUG",
                rotation="1 day",
                retention="30 days",
                compression="zip"
            )
            
            # Performance logging
            logger.add(
                sink="logs/performance.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
                level="INFO",
                rotation="1 day",
                retention="90 days",
                filter=lambda record: "PERFORMANCE" in record["message"]
            )
            
            # Error logging
            logger.add(
                sink="logs/errors.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level="ERROR",
                rotation="1 day",
                retention="90 days"
            )
            
            logger.info("Logging system initialized")
            
        except Exception as e:
            print(f"Error setting up logging: {e}")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        try:
            if self.is_monitoring:
                logger.warning("Monitoring already running")
                return
            
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Trading monitor started")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        try:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("Trading monitor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Schedule monitoring tasks
                schedule.run_pending()
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def log_trade_execution(self, trading_decision: TradingDecision, execution_result: Dict[str, Any], market_data: MarketData):
        """Log trade execution details"""
        try:
            trade_log = {
                "timestamp": datetime.now().isoformat(),
                "signal": trading_decision.signal,
                "confidence": trading_decision.confidence,
                "position_size": trading_decision.position_size,
                "reasoning": trading_decision.reasoning,
                "market_price": market_data.price,
                "market_change_24h": market_data.change_percent_24h,
                "execution_success": execution_result.get("success", False),
                "order_id": execution_result.get("order_id"),
                "error": execution_result.get("error")
            }
            
            self.trade_history.append(trade_log)
            
            # Log to file
            logger.info(f"PERFORMANCE: Trade executed - {trade_log}")
            
            # Update performance metrics
            self._update_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error logging trade execution: {e}")
    
    def log_market_analysis(self, market_analysis: Any, news_count: int, analysis_time: float):
        """Log market analysis results"""
        try:
            analysis_log = {
                "timestamp": datetime.now().isoformat(),
                "technical_score": market_analysis.technical_score,
                "sentiment_score": market_analysis.sentiment_score,
                "news_score": market_analysis.news_score,
                "overall_score": market_analysis.overall_score,
                "confidence": market_analysis.confidence,
                "risk_level": market_analysis.risk_level,
                "news_count": news_count,
                "analysis_time": analysis_time
            }
            
            logger.info(f"PERFORMANCE: Market analysis - {analysis_log}")
            
        except Exception as e:
            logger.error(f"Error logging market analysis: {e}")
    
    def log_system_health(self, health_status: SystemHealth):
        """Log system health status"""
        try:
            self.health_history.append(health_status)
            
            # Keep only last 1000 health records
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-1000:]
            
            # Log to file
            logger.info(f"HEALTH: {asdict(health_status)}")
            
            # Save to JSON file
            self._save_health_to_file()
            
        except Exception as e:
            logger.error(f"Error logging system health: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            if not self.trade_history:
                return
            
            # Calculate metrics
            total_trades = len(self.trade_history)
            successful_trades = sum(1 for trade in self.trade_history if trade.get("execution_success", False))
            failed_trades = total_trades - successful_trades
            
            # Calculate PnL (simplified - would need actual position tracking)
            total_pnl = 0.0  # This would be calculated from actual positions
            daily_pnl = 0.0  # This would be calculated from daily positions
            
            win_rate = successful_trades / total_trades if total_trades > 0 else 0
            
            # Calculate average trade size
            avg_trade_size = sum(trade.get("position_size", 0) for trade in self.trade_history) / total_trades if total_trades > 0 else 0
            
            # Create performance metrics
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                total_trades=total_trades,
                successful_trades=successful_trades,
                failed_trades=failed_trades,
                total_pnl=total_pnl,
                daily_pnl=daily_pnl,
                win_rate=win_rate,
                avg_trade_size=avg_trade_size,
                max_drawdown=0.0,  # Would need historical data
                sharpe_ratio=0.0,  # Would need historical data
                current_position_value=0.0,  # Would need current position data
                account_balance=0.0  # Would need account data
            )
            
            self.performance_history.append(metrics)
            
            # Keep only last 1000 performance records
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
            
            # Save to file
            self._save_performance_to_file()
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _save_performance_to_file(self):
        """Save performance metrics to JSON file"""
        try:
            performance_data = [asdict(metric) for metric in self.performance_history]
            
            with open(self.performance_file, 'w') as f:
                json.dump(performance_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving performance to file: {e}")
    
    def _save_health_to_file(self):
        """Save health metrics to JSON file"""
        try:
            health_data = [asdict(health) for health in self.health_history]
            
            with open(self.health_file, 'w') as f:
                json.dump(health_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving health to file: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        try:
            if not self.performance_history:
                return {"error": "No performance data available"}
            
            latest = self.performance_history[-1]
            
            # Calculate additional metrics
            uptime = datetime.now() - self.start_time
            
            return {
                "uptime_hours": uptime.total_seconds() / 3600,
                "total_trades": latest.total_trades,
                "successful_trades": latest.successful_trades,
                "failed_trades": latest.failed_trades,
                "win_rate": latest.win_rate,
                "total_pnl": latest.total_pnl,
                "daily_pnl": latest.daily_pnl,
                "avg_trade_size": latest.avg_trade_size,
                "current_position_value": latest.current_position_value,
                "account_balance": latest.account_balance,
                "last_update": latest.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            if not self.health_history:
                return {"error": "No health data available"}
            
            latest = self.health_history[-1]
            
            return {
                "timestamp": latest.timestamp.isoformat(),
                "api_connection": latest.api_connection,
                "ollama_connection": latest.ollama_connection,
                "news_service": latest.news_service,
                "market_data_fresh": latest.market_data_fresh,
                "last_trade_time": latest.last_trade_time.isoformat() if latest.last_trade_time else None,
                "error_count": latest.error_count,
                "memory_usage": latest.memory_usage,
                "cpu_usage": latest.cpu_usage,
                "overall_health": self._calculate_overall_health(latest)
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_health(self, health: SystemHealth) -> str:
        """Calculate overall system health status"""
        try:
            health_score = 0
            total_checks = 0
            
            # API connection check
            if health.api_connection:
                health_score += 1
            total_checks += 1
            
            # Ollama connection check
            if health.ollama_connection:
                health_score += 1
            total_checks += 1
            
            # News service check
            if health.news_service:
                health_score += 1
            total_checks += 1
            
            # Market data freshness check
            if health.market_data_fresh:
                health_score += 1
            total_checks += 1
            
            # Error count check
            if health.error_count < 10:
                health_score += 1
            total_checks += 1
            
            # Calculate health percentage
            health_percentage = (health_score / total_checks) * 100
            
            if health_percentage >= 90:
                return "EXCELLENT"
            elif health_percentage >= 75:
                return "GOOD"
            elif health_percentage >= 50:
                return "FAIR"
            else:
                return "POOR"
                
        except Exception as e:
            logger.error(f"Error calculating overall health: {e}")
            return "UNKNOWN"
    
    def generate_report(self) -> str:
        """Generate comprehensive trading report"""
        try:
            performance = self.get_performance_summary()
            health = self.get_system_health()
            
            report = f"""
=== BITCOIN TRADING AGENT REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PERFORMANCE METRICS:
- Uptime: {performance.get('uptime_hours', 0):.2f} hours
- Total Trades: {performance.get('total_trades', 0)}
- Successful Trades: {performance.get('successful_trades', 0)}
- Failed Trades: {performance.get('failed_trades', 0)}
- Win Rate: {performance.get('win_rate', 0):.2%}
- Total PnL: ${performance.get('total_pnl', 0):.2f}
- Daily PnL: ${performance.get('daily_pnl', 0):.2f}
- Avg Trade Size: {performance.get('avg_trade_size', 0):.4f}

SYSTEM HEALTH:
- Overall Health: {health.get('overall_health', 'UNKNOWN')}
- API Connection: {'✓' if health.get('api_connection') else '✗'}
- Ollama Connection: {'✓' if health.get('ollama_connection') else '✗'}
- News Service: {'✓' if health.get('news_service') else '✗'}
- Market Data Fresh: {'✓' if health.get('market_data_fresh') else '✗'}
- Error Count: {health.get('error_count', 0)}
- Memory Usage: {health.get('memory_usage', 0):.1f}%
- CPU Usage: {health.get('cpu_usage', 0):.1f}%

RECENT TRADES:
"""
            
            # Add recent trades
            recent_trades = self.trade_history[-5:] if self.trade_history else []
            for trade in recent_trades:
                report += f"- {trade.get('timestamp', 'N/A')}: {trade.get('signal', 'N/A')} (Confidence: {trade.get('confidence', 0):.2f})\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"
    
    def export_data(self, filepath: str = None) -> str:
        """Export all monitoring data to JSON file"""
        try:
            if filepath is None:
                filepath = f"logs/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "performance_history": [asdict(metric) for metric in self.performance_history],
                "health_history": [asdict(health) for health in self.health_history],
                "trade_history": self.trade_history,
                "performance_summary": self.get_performance_summary(),
                "system_health": self.get_system_health()
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Data exported to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return f"Error: {e}"