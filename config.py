"""
Configuration module for NIFTY50 Trading System.

This module loads configuration from environment variables and provides
centralized access to all configurable parameters.
"""

import os
from datetime import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class containing all system parameters."""
    
    # API Credentials
    KITE_API_KEY = os.getenv('KITE_API_KEY', '')
    KITE_API_SECRET = os.getenv('KITE_API_SECRET', '')
    
    # Trading Parameters
    NIFTY_LOT_SIZE = int(os.getenv('NIFTY_LOT_SIZE', '65'))
    
    # Market Hours (IST)
    MARKET_START_TIME = time(9, 15, 0)  # 9:15 AM
    MARKET_END_TIME = time(15, 30, 0)   # 3:30 PM
    EOD_CLOSE_TIME = time(15, 15, 0)    # 3:15 PM - Auto close positions
    LATE_ENTRY_WARNING_TIME = time(15, 0, 0)  # 3:00 PM - Warning threshold
    
    # Dashboard
    DASHBOARD_REFRESH_RATE = float(os.getenv('DASHBOARD_REFRESH_RATE', '1.0'))
    
    # Logging
    LOG_FILE = 'trading_system.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Trading Journal
    JOURNAL_FILE = 'trading_journal.xlsx'
    
    # WebSocket Reconnection
    WS_MAX_RETRIES = 5
    WS_RECONNECT_DELAY = 2  # seconds
    WS_MAX_RECONNECT_DELAY = 60  # seconds
    
    # API Retry Configuration
    API_MAX_RETRIES = 3
    API_RETRY_DELAY = 1  # seconds
    
    # Instrument Tokens
    # Optional: Set manually if auto-detection fails (run debug_instruments.py to find)
    NIFTY_INSTRUMENT_TOKEN = int(os.getenv('NIFTY_INSTRUMENT_TOKEN', '0')) or None
    
    # Access Token Storage
    ACCESS_TOKEN_FILE = 'access_token.txt'
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present.
        
        Raises:
            ValueError: If required configuration is missing.
        """
        errors = []
        
        if not cls.KITE_API_KEY:
            errors.append("KITE_API_KEY is not set in .env file")
        
        if not cls.KITE_API_SECRET:
            errors.append("KITE_API_SECRET is not set in .env file")
        
        if cls.NIFTY_LOT_SIZE <= 0:
            errors.append("NIFTY_LOT_SIZE must be greater than 0")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    @classmethod
    def get_time_string(cls, t: time) -> str:
        """
        Convert time object to string format.
        
        Args:
            t: time object
            
        Returns:
            Time string in HH:MM:SS format
        """
        return t.strftime('%H:%M:%S')
