"""
Utility functions for the trading system.

Includes logging setup, time utilities, and helper functions.
"""

import logging
from datetime import datetime, time
from typing import Optional
import pytz
from config import Config


def setup_logging():
    """
    Configure logging for the application.
    
    Sets up file and console logging with appropriate formats.
    """
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (only warnings and errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.info("="*60)
    logging.info("Trading System Started")
    logging.info("="*60)


def get_ist_now() -> datetime:
    """
    Get current time in IST timezone.
    
    Returns:
        Current datetime in IST
    """
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)


def get_current_time() -> time:
    """
    Get current time (without date) in IST.
    
    Returns:
        Current time in IST
    """
    return get_ist_now().time()


def is_market_hours() -> bool:
    """
    Check if current time is within market hours.
    
    Returns:
        True if market is open, False otherwise
    """
    current = get_current_time()
    return Config.MARKET_START_TIME <= current <= Config.MARKET_END_TIME


def is_late_entry() -> bool:
    """
    Check if current time is past the late entry warning threshold.
    
    Returns:
        True if past warning time, False otherwise
    """
    current = get_current_time()
    return current >= Config.LATE_ENTRY_WARNING_TIME


def should_close_eod() -> bool:
    """
    Check if positions should be closed for end of day.
    
    Returns:
        True if past EOD close time, False otherwise
    """
    current = get_current_time()
    return current >= Config.EOD_CLOSE_TIME


def format_currency(amount: float) -> str:
    """
    Format amount as Indian currency.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    return f"₹ {amount:,.2f}"


def format_percentage(value: float) -> str:
    """
    Format value as percentage with sign.
    
    Args:
        value: Percentage value
        
    Returns:
        Formatted percentage string
    """
    sign = '+' if value >= 0 else ''
    return f"{sign}{value:.2f}%"


def calculate_pnl(entry_price: float, exit_price: float, quantity: int, option_type: str) -> float:
    """
    Calculate P&L for a position.
    
    Args:
        entry_price: Entry premium price
        exit_price: Exit premium price
        quantity: Number of units
        option_type: 'CALL' or 'PUT'
        
    Returns:
        P&L amount
    """
    return (exit_price - entry_price) * quantity


def calculate_return_percentage(entry_price: float, exit_price: float) -> float:
    """
    Calculate return percentage.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        
    Returns:
        Return percentage
    """
    if entry_price == 0:
        return 0.0
    return ((exit_price - entry_price) / entry_price) * 100


def get_atm_strike(spot_price: float, strike_interval: int = 50) -> int:
    """
    Calculate ATM (At-The-Money) strike price.
    
    Args:
        spot_price: Current spot price of Nifty
        strike_interval: Strike interval (default 50 for Nifty)
        
    Returns:
        ATM strike price
    """
    return round(spot_price / strike_interval) * strike_interval


def determine_lot_size(risk_points: float) -> int:
    """
    Determine number of lots based on risk points.
    
    Args:
        risk_points: Calculated risk points (in premium)
        
    Returns:
        Number of lots to trade
    """
    if risk_points > 10:
        return 1
    elif risk_points > 5:
        return 2
    else:
        return 3
