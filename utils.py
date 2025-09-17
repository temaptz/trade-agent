"""Utility functions for the trading bot."""
import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger

def load_config(config_file: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_config(config: Dict[str, Any], config_file: str = "config.yaml"):
    """Save configuration to YAML file."""
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount."""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "BTC":
        return f"{amount:.8f} BTC"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage value."""
    return f"{value:.{decimals}f}%"

def calculate_risk_reward_ratio(entry_price: float, stop_loss: float, take_profit: float) -> float:
    """Calculate risk-reward ratio."""
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    
    if risk == 0:
        return 0
    
    return reward / risk

def calculate_position_value(quantity: float, price: float) -> float:
    """Calculate position value."""
    return quantity * price

def calculate_pnl(entry_price: float, current_price: float, quantity: float, side: str) -> float:
    """Calculate profit/loss."""
    if side.lower() == "buy":
        return (current_price - entry_price) * quantity
    else:
        return (entry_price - current_price) * quantity

def is_market_hours() -> bool:
    """Check if it's market hours (crypto markets are 24/7, but this can be customized)."""
    # For crypto, markets are always open
    return True

def get_market_session() -> str:
    """Get current market session."""
    # For crypto, this is always "24/7"
    return "24/7"

def validate_api_keys(api_key: str, secret_key: str) -> bool:
    """Validate API keys format."""
    if not api_key or not secret_key:
        return False
    
    # Basic validation - check if keys are not empty and have reasonable length
    if len(api_key) < 10 or len(secret_key) < 10:
        return False
    
    return True

def create_backup(filename: str, data: Dict[str, Any]):
    """Create backup of data."""
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{backup_dir}/{filename}_{timestamp}.json"
    
    with open(backup_filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Backup created: {backup_filename}")
    return backup_filename

def load_backup(filename: str) -> Optional[Dict[str, Any]]:
    """Load data from backup."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return None

def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    import platform
    import psutil
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_usage": psutil.disk_usage('/').percent
    }

def check_dependencies() -> Dict[str, bool]:
    """Check if all required dependencies are available."""
    dependencies = {
        "langchain": False,
        "langgraph": False,
        "langchain_ollama": False,
        "pybit": False,
        "yfinance": False,
        "duckduckgo_search": False,
        "ccxt": False,
        "ta": False,
        "pandas": False,
        "numpy": False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
        except ImportError:
            dependencies[dep] = False
    
    return dependencies

def cleanup_old_logs(days: int = 30):
    """Clean up old log files."""
    import glob
    
    log_patterns = [
        "logs/*.log",
        "logs/*.log.*",
        "backups/*.json"
    ]
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cleaned_files = []
    
    for pattern in log_patterns:
        for filepath in glob.glob(pattern):
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)
                    cleaned_files.append(filepath)
            except Exception as e:
                logger.warning(f"Could not clean up {filepath}: {e}")
    
    if cleaned_files:
        logger.info(f"Cleaned up {len(cleaned_files)} old files")
    
    return cleaned_files

def send_notification(message: str, level: str = "info"):
    """Send notification (placeholder for future implementation)."""
    # This can be extended to send notifications via email, Slack, Discord, etc.
    logger.info(f"NOTIFICATION [{level.upper()}]: {message}")

def emergency_stop():
    """Emergency stop function."""
    logger.critical("EMERGENCY STOP ACTIVATED")
    # This can be extended to close all positions, send alerts, etc.
    send_notification("Emergency stop activated", "critical")

def health_check() -> Dict[str, Any]:
    """Perform health check of the system."""
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    # Check dependencies
    deps = check_dependencies()
    health["checks"]["dependencies"] = {
        "status": "pass" if all(deps.values()) else "fail",
        "details": deps
    }
    
    # Check log files
    log_files_exist = all([
        os.path.exists("logs/trading_bot.log"),
        os.path.exists("logs/trading_decisions.log")
    ])
    health["checks"]["log_files"] = {
        "status": "pass" if log_files_exist else "fail",
        "details": {"log_files_exist": log_files_exist}
    }
    
    # Check configuration
    config_exists = os.path.exists(".env")
    health["checks"]["configuration"] = {
        "status": "pass" if config_exists else "fail",
        "details": {"config_exists": config_exists}
    }
    
    # Overall status
    all_checks_pass = all(
        check["status"] == "pass" 
        for check in health["checks"].values()
    )
    health["status"] = "healthy" if all_checks_pass else "unhealthy"
    
    return health

if __name__ == "__main__":
    # Run health check
    health = health_check()
    print(json.dumps(health, indent=2))