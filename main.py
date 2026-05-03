#!/usr/bin/env python3
"""
NIFTY50 Algorithmic Trading System - Main Entry Point

This is the main entry point for the trading system.
It orchestrates all modules and starts the trading strategy.
"""

import sys
import logging
from config import Config
from utils import setup_logging
from auth import KiteAuthenticator
from data_stream import DataStream
from order_manager import OrderManager
from strategy import Strategy

logger = logging.getLogger(__name__)


def main():
    """Main function to start the trading system."""
    
    # Setup logging
    setup_logging()
    
    print("="*60)
    print("    NIFTY50 ALGORITHMIC TRADING SYSTEM")
    print("="*60)
    print()
    
    try:
        # Validate configuration
        print("📋 Validating configuration...")
        Config.validate()
        print("✓ Configuration valid\n")
        
        # Authenticate with Kite Connect
        print("🔐 Authenticating with Kite Connect...")
        authenticator = KiteAuthenticator()
        kite = authenticator.authenticate()
        print("✓ Authentication successful\n")
        
        # Get user profile
        profile = kite.profile()
        print(f"👤 Logged in as: {profile.get('user_name')} ({profile.get('email')})")
        print()
        
        # Initialize order manager
        print("📊 Initializing order manager...")
        order_manager = OrderManager(kite)
        print("✓ Order manager initialized\n")
        
        # Initialize data stream
        print("📡 Initializing data stream...")
        data_stream = DataStream(Config.KITE_API_KEY, authenticator.access_token)
        data_stream.start()
        print("✓ Data stream initialized\n")
        
        # Initialize strategy
        print("🎯 Initializing trading strategy...")
        strategy = Strategy(kite, order_manager, data_stream)
        strategy.initialize()
        print("✓ Strategy initialized\n")
        
        # Display system information
        print("="*60)
        print("SYSTEM READY")
        print("="*60)
        print(f"Market Hours: {Config.MARKET_START_TIME} - {Config.MARKET_END_TIME}")
        print(f"EOD Close Time: {Config.EOD_CLOSE_TIME}")
        print(f"Lot Size: {Config.NIFTY_LOT_SIZE}")
        print(f"Trading Journal: {Config.JOURNAL_FILE}")
        print(f"Log File: {Config.LOG_FILE}")
        print("="*60)
        print()
        
        input("Press ENTER to start the trading system...")
        print()
        
        # Start strategy
        logger.info("Starting trading strategy")
        strategy.run()
        
    except KeyboardInterrupt:
        print("\n\n🛑 System stopped by user")
        logger.info("System stopped by user (KeyboardInterrupt)")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        print(f"\n\n❌ System Error: {e}")
        print("\nPlease check the log file for details: trading_system.log")
        sys.exit(1)


if __name__ == "__main__":
    main()
