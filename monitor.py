"""Monitoring utilities for the trading bot."""
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from loguru import logger
import os

class TradingMonitor:
    """Monitor trading bot performance and statistics."""
    
    def __init__(self, log_file: str = "logs/trading_bot.log"):
        self.log_file = log_file
        self.decisions_file = "logs/trading_decisions.log"
    
    def get_recent_decisions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent trading decisions."""
        decisions = []
        
        if not os.path.exists(self.decisions_file):
            return decisions
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(self.decisions_file, 'r') as f:
                for line in f:
                    if 'TRADING_DECISION' in line:
                        try:
                            # Parse log line
                            parts = line.split(' | ')
                            if len(parts) >= 2:
                                timestamp_str = parts[0]
                                message = parts[-1]
                                
                                # Parse timestamp
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                
                                if timestamp >= cutoff_time:
                                    # Extract decision data
                                    decision_data = self._parse_decision_message(message)
                                    decision_data['timestamp'] = timestamp
                                    decisions.append(decision_data)
                        except Exception as e:
                            logger.warning(f"Error parsing decision line: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error reading decisions file: {e}")
        
        return decisions
    
    def _parse_decision_message(self, message: str) -> Dict[str, Any]:
        """Parse decision message from log."""
        decision_data = {}
        
        # Extract decision
        if 'DECISION:' in message:
            decision = message.split('DECISION:')[1].split('|')[0].strip()
            decision_data['decision'] = decision
        
        # Extract confidence
        if 'CONFIDENCE:' in message:
            confidence = message.split('CONFIDENCE:')[1].split('|')[0].strip()
            try:
                decision_data['confidence'] = float(confidence)
            except ValueError:
                decision_data['confidence'] = 0.0
        
        # Extract reasoning
        if 'REASONING:' in message:
            reasoning = message.split('REASONING:')[1].split('|')[0].strip()
            decision_data['reasoning'] = reasoning
        
        # Extract action
        if 'ACTION:' in message:
            action = message.split('ACTION:')[1].strip()
            decision_data['action'] = action
        
        return decision_data
    
    def get_performance_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get performance statistics."""
        decisions = self.get_recent_decisions(hours=days * 24)
        
        if not decisions:
            return {
                'total_decisions': 0,
                'buy_decisions': 0,
                'sell_decisions': 0,
                'hold_decisions': 0,
                'close_decisions': 0,
                'average_confidence': 0.0,
                'high_confidence_decisions': 0,
                'executed_trades': 0
            }
        
        stats = {
            'total_decisions': len(decisions),
            'buy_decisions': sum(1 for d in decisions if d.get('decision') == 'buy'),
            'sell_decisions': sum(1 for d in decisions if d.get('decision') == 'sell'),
            'hold_decisions': sum(1 for d in decisions if d.get('decision') == 'hold'),
            'close_decisions': sum(1 for d in decisions if d.get('decision') == 'close'),
            'average_confidence': sum(d.get('confidence', 0) for d in decisions) / len(decisions),
            'high_confidence_decisions': sum(1 for d in decisions if d.get('confidence', 0) >= 0.7),
            'executed_trades': sum(1 for d in decisions if d.get('action') in ['buy_order', 'sell_order', 'close_position'])
        }
        
        return stats
    
    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Get daily summary for a specific date."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get decisions for the specific date
        decisions = []
        if os.path.exists(self.decisions_file):
            try:
                with open(self.decisions_file, 'r') as f:
                    for line in f:
                        if date in line and 'TRADING_DECISION' in line:
                            try:
                                parts = line.split(' | ')
                                if len(parts) >= 2:
                                    message = parts[-1]
                                    decision_data = self._parse_decision_message(message)
                                    decisions.append(decision_data)
                            except Exception as e:
                                continue
            except Exception as e:
                logger.error(f"Error reading decisions for date {date}: {e}")
        
        return {
            'date': date,
            'total_decisions': len(decisions),
            'decisions': decisions,
            'performance': self.get_performance_stats(days=1)
        }
    
    def generate_report(self, days: int = 7) -> str:
        """Generate a comprehensive report."""
        stats = self.get_performance_stats(days)
        
        report = f"""
🤖 AI Trading Bot Report
{'='*50}
Period: Last {days} days
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DECISION STATISTICS
{'='*50}
Total Decisions: {stats['total_decisions']}
Buy Decisions: {stats['buy_decisions']}
Sell Decisions: {stats['sell_decisions']}
Hold Decisions: {stats['hold_decisions']}
Close Decisions: {stats['close_decisions']}

🎯 CONFIDENCE ANALYSIS
{'='*50}
Average Confidence: {stats['average_confidence']:.2f}
High Confidence Decisions (>0.7): {stats['high_confidence_decisions']}

⚡ TRADE EXECUTION
{'='*50}
Executed Trades: {stats['executed_trades']}
Execution Rate: {(stats['executed_trades'] / max(stats['total_decisions'], 1) * 100):.1f}%

📈 RECENT DECISIONS
{'='*50}
"""
        
        # Add recent decisions
        recent_decisions = self.get_recent_decisions(hours=24)
        for decision in recent_decisions[-5:]:  # Last 5 decisions
            timestamp = decision.get('timestamp', datetime.now())
            decision_type = decision.get('decision', 'unknown')
            confidence = decision.get('confidence', 0.0)
            action = decision.get('action', 'none')
            
            report += f"{timestamp.strftime('%H:%M:%S')} | {decision_type.upper()} | Conf: {confidence:.2f} | Action: {action}\n"
        
        return report
    
    def save_report(self, filename: str = None, days: int = 7):
        """Save report to file."""
        if filename is None:
            filename = f"reports/trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        report = self.generate_report(days)
        
        with open(filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to {filename}")
        return filename

def main():
    """Main function for monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Trading Bot Monitor')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--report', action='store_true', help='Generate and save report')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    monitor = TradingMonitor()
    
    if args.stats:
        stats = monitor.get_performance_stats(args.days)
        print(json.dumps(stats, indent=2))
    
    if args.report:
        filename = monitor.save_report(days=args.days)
        print(f"Report saved to: {filename}")
    else:
        report = monitor.generate_report(args.days)
        print(report)

if __name__ == "__main__":
    main()