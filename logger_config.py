"""Logging configuration for the trading bot."""
import os
import sys
from loguru import logger
from datetime import datetime
from config import settings

def setup_logging():
    """Setup logging configuration."""
    # Remove default handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # Add separate file for trading decisions
    logger.add(
        "logs/trading_decisions.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        rotation="1 day",
        retention="90 days",
        compression="zip",
        filter=lambda record: "TRADING_DECISION" in record["message"]
    )
    
    # Add separate file for errors
    logger.add(
        "logs/errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("Logging configured successfully")

def log_trading_decision(decision_data: dict):
    """Log trading decision with structured data."""
    logger.bind(TRADING_DECISION=True).info(
        f"DECISION: {decision_data.get('decision', 'unknown')} | "
        f"CONFIDENCE: {decision_data.get('confidence', 0.0)} | "
        f"REASONING: {decision_data.get('reasoning', 'N/A')} | "
        f"ACTION: {decision_data.get('action_taken', {}).get('action', 'N/A')}"
    )

def log_trade_execution(trade_data: dict):
    """Log trade execution details."""
    logger.bind(TRADING_DECISION=True).info(
        f"TRADE_EXECUTED: {trade_data.get('action', 'unknown')} | "
        f"QUANTITY: {trade_data.get('quantity', 0)} | "
        f"PRICE: {trade_data.get('price', 0)} | "
        f"STOP_LOSS: {trade_data.get('stop_loss', 0)} | "
        f"TAKE_PROFIT: {trade_data.get('take_profit', 0)}"
    )

def log_market_analysis(analysis_data: dict):
    """Log market analysis summary."""
    logger.info(
        f"MARKET_ANALYSIS: "
        f"Price: {analysis_data.get('current_price', 'N/A')} | "
        f"Trend: {analysis_data.get('market_trend', 'N/A')} | "
        f"Volatility: {analysis_data.get('volatility', 'N/A')} | "
        f"Sentiment: {analysis_data.get('sentiment_analysis', {}).get('sentiment_text', 'N/A')}"
    )