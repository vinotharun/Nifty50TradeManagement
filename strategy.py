"""
Strategy module containing core trading logic.

Implements the state machine for the breakout strategy.
"""

import logging
import time
import threading
import sys
import select
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict
from kiteconnect import KiteConnect
from config import Config
from utils import (
    get_ist_now, is_market_hours, should_close_eod, is_late_entry,
    calculate_pnl, calculate_return_percentage, determine_lot_size
)
from order_manager import OrderManager
from data_stream import DataStream
from dashboard import Dashboard
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


class TradingState(Enum):
    """Enum for trading system states."""
    IDLE = "IDLE"
    WAITING_CANDLE_CLOSE = "WAITING_CANDLE_CLOSE"
    WAITING_BREAKOUT = "WAITING_BREAKOUT"
    POSITION_ACTIVE = "POSITION_ACTIVE"
    POSITION_CLOSED = "POSITION_CLOSED"


class Strategy:
    """Implements the breakout trading strategy."""
    
    def __init__(self, kite: KiteConnect, order_manager: OrderManager, data_stream: DataStream):
        """
        Initialize the strategy.
        
        Args:
            kite: Authenticated KiteConnect instance
            order_manager: OrderManager instance
            data_stream: DataStream instance
        """
        self.kite = kite
        self.order_manager = order_manager
        self.data_stream = data_stream
        self.dashboard = Dashboard()
        
        # State management
        self.state = TradingState.IDLE
        self.current_nifty_price = None
        
        # Entry candle tracking
        self.entry_candle_high = None
        self.entry_candle_low = None
        self.entry_candle_start_time = None
        self.entry_candle_close_time = None
        self.candle_data = []  # Store tick data for candle formation

        # Direction tracking
        self.chosen_direction = None  # 'CALL' or 'PUT' chosen by user

        # Entry candle choice
        self.entry_candle_choice = None  # 'CURRENT' or 'PREVIOUS'

        # Position tracking
        self.position = None  # Will store position details
        self.option_instrument_token = None

        # User input handling
        self.user_command = None
        self.command_lock = threading.Lock()
        self.cancel_monitoring = False  # Flag for Q key cancellation
        self.position_command = None  # Command during active position (M/Q)

        # Thread safety locks
        self.price_lock = threading.Lock()  # Protects current_nifty_price
        self.position_lock = threading.Lock()  # Protects position dictionary

        # NIFTY instrument token
        self.nifty_token = None

        # Capital management
        self.capital = None  # User's trading capital
        self.capital_multiplier = 1  # Multiplier based on capital (capital / 100000)

    def _get_entry_candle_choice(self):
        """
        Prompt user to choose current or previous candle.

        Returns:
            'CURRENT' or 'PREVIOUS'
        """
        self.dashboard.clear_screen()

        now = get_ist_now()
        current_start = now.replace(second=0, microsecond=0)
        current_end = current_start + timedelta(minutes=1)
        prev_start = current_start - timedelta(minutes=1)
        prev_end = current_start

        elapsed = (now - current_start).total_seconds()
        wait_time = (current_end - now).total_seconds()

        # Check if it's the first candle of the day (market just opened)
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        is_first_candle = (current_start.hour == 9 and current_start.minute == 15)

        print("\n" + "="*60)
        print("         ENTRY CANDLE SELECTION")
        print("="*60)
        print(f"\nCurrent Time: {now.strftime('%H:%M:%S')}")
        print()
        print("Choose Entry Candle:")
        print()
        print(f"[1] Current Candle ({current_start.strftime('%H:%M:%S')} - {current_end.strftime('%H:%M:%S')})")
        print(f"    - Status: In progress ({elapsed:.0f} seconds elapsed)")
        print(f"    - Wait time: {wait_time:.0f} seconds until close")
        print(f"    - Includes current price action")
        print()

        if is_first_candle:
            print(f"[2] Previous Candle - NOT AVAILABLE")
            print(f"    - Market just opened (first candle of the day)")
            print(f"    - No previous candle exists")
            print()
            print("Only option [1] is available.")
            print()

            input("Press ENTER to continue with Current Candle...")
            logger.info("User chose: Current candle (first candle of day, no choice)")
            return 'CURRENT'
        else:
            print(f"[2] Previous Candle ({prev_start.strftime('%H:%M:%S')} - {prev_end.strftime('%H:%M:%S')})")
            print(f"    - Status: Already closed")
            print(f"    - Wait time: None (instant)")
            print(f"    - Historical data available immediately")
            print()

            while True:
                choice = input("Enter your choice (1/2): ").strip()
                if choice == '1':
                    logger.info("User chose: Current candle")
                    return 'CURRENT'
                elif choice == '2':
                    logger.info("User chose: Previous candle")
                    return 'PREVIOUS'
                else:
                    print("Invalid choice. Please enter 1 or 2.")

    def _get_direction_from_user(self):
        """Get trading direction (CALL/PUT) from user."""
        self.dashboard.clear_screen()
        print("\n" + "="*60)
        print("         TRADING DIRECTION SETUP")
        print("="*60)
        print("\nChoose trading direction:")
        print("  [C] CALL - Monitor for breakout ABOVE entry candle high")
        print("  [P] PUT  - Monitor for breakout BELOW entry candle low")
        print()

        while True:
            direction_input = input("Enter your choice (C/P): ").strip().upper()
            if direction_input == 'C':
                self.chosen_direction = 'CALL'
                break
            elif direction_input == 'P':
                self.chosen_direction = 'PUT'
                break
            else:
                print("Invalid choice. Please enter C or P.")

        logger.info(f"User chose direction: {self.chosen_direction}")

    def _fetch_entry_candle_data(self):
        """
        Fetch historical data for entry candle.
        Sets self.entry_candle_high and self.entry_candle_low
        """
        try:
            print("\n📊 Fetching entry candle data...")

            # Fetch 1-minute historical data for NIFTY
            from_date = self.entry_candle_start_time
            to_date = self.entry_candle_close_time

            historical_data = self.kite.historical_data(
                instrument_token=self.nifty_token,
                from_date=from_date,
                to_date=to_date,
                interval='minute',
                timeout=Config.API_TIMEOUT
            )

            if historical_data and len(historical_data) > 0:
                candle = historical_data[-1]  # Get the last (most recent) candle
                self.entry_candle_high = candle['high']
                self.entry_candle_low = candle['low']

                logger.info(f"Entry candle data from Historical API: High={self.entry_candle_high}, Low={self.entry_candle_low}")
                print(f"✓ Entry Candle: High = {self.entry_candle_high:,.2f} | Low = {self.entry_candle_low:,.2f}")
                return True
            else:
                logger.warning("No historical data returned, using WebSocket tick data as fallback")
                print("⚠️  Historical data unavailable, using tick data")
                # Fallback would go here if needed
                return False

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            print(f"✗ Error fetching historical data: {e}")
            return False

    def _get_capital_from_user(self):
        """
        Get trading capital from user at startup.
        Validates capital and calculates multiplier.
        """
        self.dashboard.clear_screen()
        print("\n" + "="*60)
        print("         TRADING CAPITAL SETUP")
        print("="*60)
        print()

        # Get available margin from Zerodha
        try:
            margins = self.kite.margins()
            equity_margin = margins.get('equity', {})
            available_margin = equity_margin.get('available', {}).get('live_balance', 0)

            print(f"📊 Available Margin in Zerodha: ₹{available_margin:,.2f}")
            print()
        except Exception as e:
            logger.warning(f"Could not fetch margin data: {e}")
            available_margin = None
            print("⚠️  Could not fetch margin data from Zerodha")
            print()

        while True:
            print("Enter your trading capital:")
            print("  - Must be in multiples of ₹1,00,000")
            print("  - Minimum: ₹1,00,000")
            if available_margin:
                print(f"  - Maximum: ₹{available_margin:,.2f} (available margin)")
            print()

            capital_input = input("Enter capital (or 'Q' to quit): ").strip()

            # Check for exit
            if capital_input.upper() == 'Q':
                print("\n✗ Exiting trading system...")
                logger.info("User chose to exit during capital setup")
                return False

            # Validate input is a number
            try:
                capital = float(capital_input)
            except ValueError:
                print("\n✗ Invalid input. Please enter a valid number.")
                print()
                continue

            # Validate minimum capital
            if capital < Config.MIN_CAPITAL:
                print(f"\n✗ ERROR: Capital must be at least ₹{Config.MIN_CAPITAL:,.2f}")
                print("  This system is designed for capital above ₹1,00,000")
                print()
                continue

            # Validate maximum capital (risk control)
            if capital > Config.MAX_CAPITAL:
                print(f"\n✗ ERROR: Capital (₹{capital:,.2f}) exceeds maximum allowed (₹{Config.MAX_CAPITAL:,.2f})")
                print("  Maximum capital is limited to ₹10 crores for risk control")
                print()
                continue

            # Validate against available margin
            if available_margin and capital > available_margin:
                print(f"\n✗ ERROR: Capital (₹{capital:,.2f}) exceeds available margin (₹{available_margin:,.2f})")
                print("  Please enter a lower amount or add funds to your account")
                print()
                continue

            # Floor to nearest 100000
            floored_capital = int(capital // 100000) * 100000

            if floored_capital != capital:
                print(f"\n⚠️  Capital adjusted to nearest ₹1,00,000: ₹{capital:,.2f} → ₹{floored_capital:,.2f}")

            # Calculate multiplier
            self.capital = floored_capital
            self.capital_multiplier = floored_capital / 100000

            print(f"\n✓ Trading Capital Set: ₹{self.capital:,.2f}")
            print(f"✓ Capital Multiplier: {self.capital_multiplier:.0f}x")
            print(f"  (Quantity will be {self.capital_multiplier:.0f}x the base calculation)")
            print()

            logger.info(f"Trading capital set: ₹{self.capital:,.2f}, Multiplier: {self.capital_multiplier:.0f}x")

            time.sleep(2)
            return True

    def _keyboard_listener(self):
        """
        Listen for Q key press in a separate thread during breakout monitoring.
        Sets cancel_monitoring flag when Q is pressed.
        """
        try:
            while self.state == TradingState.WAITING_BREAKOUT:
                try:
                    key = input()  # This will block in its own thread
                    key_upper = key.strip().upper()
                    logger.debug(f"Key pressed during monitoring: '{key_upper}'")
                    if key_upper == 'Q':
                        logger.info("Q key pressed - cancelling monitoring")
                        self.cancel_monitoring = True
                        break
                except EOFError:
                    # stdin closed, exit gracefully
                    break
                except Exception as e:
                    logger.debug(f"Keyboard listener error: {e}")
                    break
        except:
            pass  # Thread will exit when state changes

    def _position_keyboard_listener(self):
        """
        Listen for M/T/Q key press in a separate thread during active position.
        Sets position_command when M, T, or Q is pressed.
        """
        try:
            while self.state == TradingState.POSITION_ACTIVE:
                try:
                    key = input()  # This will block in its own thread
                    key_upper = key.strip().upper()
                    logger.debug(f"Key pressed during position: '{key_upper}'")
                    if key_upper in ['M', 'T', 'Q']:
                        logger.info(f"{key_upper} key pressed during active position")
                        self.position_command = key_upper
                        break
                except EOFError:
                    # stdin closed, exit gracefully
                    break
                except Exception as e:
                    logger.debug(f"Position keyboard listener error: {e}")
                    break
        except:
            pass  # Thread will exit when state changes
    
    def initialize(self):
        """Initialize the strategy by finding NIFTY instrument and subscribing."""
        logger.info("Initializing strategy...")

        # Find NIFTY instrument token
        # Use config token if available, otherwise search for it
        if Config.NIFTY_INSTRUMENT_TOKEN:
            self.nifty_token = Config.NIFTY_INSTRUMENT_TOKEN
            logger.info(f"Using NIFTY token from config: {self.nifty_token}")
        else:
            self.nifty_token = self.order_manager.find_nifty_instrument_token()

        # Subscribe to NIFTY price updates
        self.data_stream.subscribe(self.nifty_token, self._on_nifty_tick)

        logger.info("Strategy initialized successfully")
    
    def _on_nifty_tick(self, tick: Dict):
        """
        Handle NIFTY price tick updates.

        Args:
            tick: Tick data dictionary
        """
        # Thread-safe price update
        with self.price_lock:
            self.current_nifty_price = tick.get('last_price')
            current_price = self.current_nifty_price  # Local copy for use below

        # Store tick data for candle formation
        if self.state == TradingState.WAITING_CANDLE_CLOSE:
            self.candle_data.append({
                'price': current_price,
                'timestamp': get_ist_now()
            })
        
        # Check for breakout
        if self.state == TradingState.WAITING_BREAKOUT:
            self._check_breakout()
    
    def _on_option_tick(self, tick: Dict):
        """
        Handle option price tick updates.

        Args:
            tick: Tick data dictionary
        """
        # Thread-safe position update
        with self.position_lock:
            if self.position:
                current_price = tick.get('last_price')
                self.position['current_price'] = current_price

        # Check for exit conditions (outside lock to avoid deadlock)
        if self.position:
            self._check_exit_conditions()
    
    def run(self):
        """Main strategy loop."""
        logger.info("Starting strategy main loop")

        # Get capital from user at startup
        if not self._get_capital_from_user():
            logger.info("User exited during capital setup")
            return

        try:
            while True:
                if not is_market_hours():
                    self.dashboard.show_header()
                    print("\n⏰ Market is closed. System will activate during market hours.")
                    print(f"   Market hours: {Config.MARKET_START_TIME} - {Config.MARKET_END_TIME}")
                    time.sleep(60)
                    continue

                # State machine
                if self.state == TradingState.IDLE:
                    self._handle_idle_state()
                
                elif self.state == TradingState.WAITING_CANDLE_CLOSE:
                    self._handle_waiting_candle_close()
                
                elif self.state == TradingState.WAITING_BREAKOUT:
                    self._handle_waiting_breakout()
                
                elif self.state == TradingState.POSITION_ACTIVE:
                    self._handle_position_active()
                
                elif self.state == TradingState.POSITION_CLOSED:
                    self._handle_position_closed()
                
                time.sleep(0.1)  # Small delay to prevent CPU overuse
                
        except KeyboardInterrupt:
            logger.info("Strategy stopped by user")
            print("\n\n🛑 System stopped by user")
        except Exception as e:
            logger.error(f"Strategy error: {e}", exc_info=True)
            print(f"\n\n❌ Error: {e}")
        finally:
            self.cleanup()

    def _handle_idle_state(self):
        """Handle IDLE state - waiting for user to press Enter."""
        # Thread-safe price read
        with self.price_lock:
            current_price = self.current_nifty_price

        self.dashboard.show_idle_state(current_price)

        # Wait for Enter key
        input()

        # Get entry candle choice (CURRENT or PREVIOUS)
        self.entry_candle_choice = self._get_entry_candle_choice()

        # Get current time
        now = get_ist_now()
        candle_start = now.replace(second=0, microsecond=0)

        if self.entry_candle_choice == 'CURRENT':
            # CURRENT CANDLE: Need to wait for it to close
            candle_close = candle_start + timedelta(minutes=1)

            # Store entry candle timing
            self.entry_candle_start_time = candle_start
            self.entry_candle_close_time = candle_close
            self.candle_data = []

            # Get direction from user
            self._get_direction_from_user()

            # Move to WAITING_CANDLE_CLOSE state
            self.state = TradingState.WAITING_CANDLE_CLOSE

            seconds_remaining = (candle_close - now).total_seconds()

            logger.info(f"Entry candle designated: {candle_start.strftime('%H:%M:%S')} to {candle_close.strftime('%H:%M:%S')}")
            logger.info(f"Current time: {now.strftime('%H:%M:%S')}, waiting {seconds_remaining:.0f}s for candle to close")

            print(f"\n✓ Entry candle designated: {candle_start.strftime('%H:%M:%S')} to {candle_close.strftime('%H:%M:%S')}")
            print(f"✓ Direction chosen: {self.chosen_direction}")
            print(f"✓ Entry Candle Type: CURRENT")
            print(f"  Current time: {now.strftime('%H:%M:%S')}")
            print(f"  Waiting {seconds_remaining:.0f} seconds for candle to close...")

        elif self.entry_candle_choice == 'PREVIOUS':
            # PREVIOUS CANDLE: Already closed, fetch data immediately
            prev_candle_end = candle_start
            prev_candle_start = candle_start - timedelta(minutes=1)

            # Store entry candle timing
            self.entry_candle_start_time = prev_candle_start
            self.entry_candle_close_time = prev_candle_end

            logger.info(f"Entry candle designated: {prev_candle_start.strftime('%H:%M:%S')} to {prev_candle_end.strftime('%H:%M:%S')} (Previous candle)")

            print(f"\n✓ Entry candle designated: {prev_candle_start.strftime('%H:%M:%S')} to {prev_candle_end.strftime('%H:%M:%S')}")
            print(f"✓ Entry Candle Type: PREVIOUS (already closed)")

            # Fetch historical data immediately (no waiting!)
            if self._fetch_entry_candle_data():
                # Get direction from user
                self._get_direction_from_user()

                print(f"✓ Direction chosen: {self.chosen_direction}")

                # Show entry candle details
                self.dashboard.show_header()
                self.dashboard.show_entry_candle(self.entry_candle_high, self.entry_candle_low)

                # Skip directly to WAITING_BREAKOUT (no need to wait!)
                self.state = TradingState.WAITING_BREAKOUT
                self.candle_data = []

                logger.info("Skipping WAITING_CANDLE_CLOSE, moving directly to WAITING_BREAKOUT")
                print("\n✓ Ready to monitor for breakout immediately!")
                time.sleep(2)  # Brief pause to show messages
            else:
                # Error fetching data, return to idle
                logger.error("Failed to fetch previous candle data, returning to IDLE")
                print("\n✗ Failed to fetch previous candle data")
                print("  Returning to IDLE state...")
                time.sleep(3)
                self.state = TradingState.IDLE

    def _handle_waiting_candle_close(self):
        """Handle WAITING_CANDLE_CLOSE state."""
        # Check if candle has closed
        now = get_ist_now()

        if now >= self.entry_candle_close_time:
            # Candle closed, fetch historical data using the extracted method
            self._fetch_entry_candle_data()

            logger.info(f"Entry candle closed at {now.strftime('%H:%M:%S')} - High: {self.entry_candle_high}, Low: {self.entry_candle_low}")

            self.dashboard.show_header()
            self.dashboard.show_entry_candle(self.entry_candle_high, self.entry_candle_low)

            self.state = TradingState.WAITING_BREAKOUT
            self.candle_data = []  # Clear candle data
        else:
            # Still waiting
            remaining = (self.entry_candle_close_time - now).total_seconds()
            print(f"\r⏳ Waiting for candle to close... {remaining:.0f}s remaining", end='', flush=True)
            time.sleep(0.5)

    def _handle_waiting_breakout(self):
        """Handle WAITING_BREAKOUT state - with directional monitoring."""
        # Start keyboard listener thread on first entry to this state
        if not hasattr(self, '_listener_started') or not self._listener_started:
            self._listener_started = True
            self.cancel_monitoring = False
            listener_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
            listener_thread.start()
            logger.info("Keyboard listener started for breakout monitoring")

        # Check for manual cancellation (Q pressed)
        if self.cancel_monitoring:
            logger.info("Monitoring cancelled by user")
            print("\n\n❌ Monitoring cancelled by user")
            print("   Returning to IDLE state...")
            print("\nPress ENTER to continue...")
            input()
            self.state = TradingState.IDLE
            self.chosen_direction = None
            self.cancel_monitoring = False
            self._listener_started = False
            return

        # Check for EOD
        if should_close_eod():
            logger.info("EOD time reached without breakout, returning to idle")
            print("\n\n⏰ EOD TIME REACHED (3:15 PM)")
            print("   No breakout occurred")
            print("   Returning to IDLE state...")
            print("\nPress ENTER to continue...")
            input()
            self.state = TradingState.IDLE
            self.chosen_direction = None
            self._listener_started = False
            return

        # Thread-safe price read for display
        with self.price_lock:
            current_price = self.current_nifty_price

        # Show monitoring dashboard
        self.dashboard.show_breakout_monitoring(
            direction=self.chosen_direction,
            entry_candle_high=self.entry_candle_high,
            entry_candle_low=self.entry_candle_low,
            entry_candle_start=self.entry_candle_start_time,
            entry_candle_end=self.entry_candle_close_time,
            current_price=current_price
        )

        # Sleep before next update
        time.sleep(1)

    def _check_breakout(self):
        """Check if breakout has occurred in the chosen direction only."""
        # Thread-safe price read
        with self.price_lock:
            current_price = self.current_nifty_price

        if not current_price:
            return

        # Only check for breakout in the chosen direction
        if self.chosen_direction == 'CALL':
            # Check for call breakout (above high)
            if current_price > self.entry_candle_high:
                logger.info(f"CALL breakout detected at {current_price}")
                self.dashboard.show_breakout("CALL", current_price, self.entry_candle_high)
                time.sleep(2)  # Brief pause to show breakout message
                self._execute_trade("CE", self.entry_candle_low - 1)
            # Ignore if price breaks below (PUT direction)
            elif current_price < self.entry_candle_low:
                logger.debug(f"Price broke below (PUT direction) but ignoring as CALL was chosen")
                # Do nothing - continue monitoring for CALL breakout

        elif self.chosen_direction == 'PUT':
            # Check for put breakout (below low)
            if current_price < self.entry_candle_low:
                logger.info(f"PUT breakout detected at {current_price}")
                self.dashboard.show_breakout("PUT", current_price, self.entry_candle_low)
                time.sleep(2)  # Brief pause to show breakout message
                self._execute_trade("PE", self.entry_candle_high + 1)
            # Ignore if price breaks above (CALL direction)
            elif current_price > self.entry_candle_high:
                logger.debug(f"Price broke above (CALL direction) but ignoring as PUT was chosen")
                # Do nothing - continue monitoring for PUT breakout

    def _execute_trade(self, option_type: str, sl_trigger_index: float):
        """
        Execute the trade after breakout.

        Args:
            option_type: 'CE' for Call, 'PE' for Put
            sl_trigger_index: Index level that triggers stop loss
        """
        try:
            print("\n📊 Finding option instrument...")

            # Thread-safe price read
            with self.price_lock:
                spot_price = self.current_nifty_price

            # Find option instrument
            option_instrument = self.order_manager.find_option_instrument(
                spot_price,
                option_type
            )

            trading_symbol = option_instrument['tradingsymbol']
            instrument_token = option_instrument['instrument_token']

            print(f"✓ Option selected: {trading_symbol}")

            # Check for late entry warning
            if is_late_entry():
                print("\n⚠️  WARNING: Position will auto-close at 3:15 PM.")
                response = input("Continue? (y/n): ").strip().lower()
                if response != 'y':
                    logger.info("Trade cancelled by user due to late entry")
                    self.state = TradingState.IDLE
                    return

            # For simplicity, we'll estimate risk points before placing order
            # In real implementation, you might want to get option price quotes first
            estimated_risk_points = 8  # Placeholder - will be updated after entry
            base_lots = determine_lot_size(estimated_risk_points)

            # Apply capital multiplier
            lots = int(base_lots * self.capital_multiplier)

            # Validate maximum lot size (risk control)
            if lots > Config.MAX_LOTS_PER_ORDER:
                logger.error(f"Order rejected: Lots ({lots}) exceeds maximum ({Config.MAX_LOTS_PER_ORDER})")
                print(f"\n❌ ERROR: Order size ({lots} lots) exceeds maximum allowed ({Config.MAX_LOTS_PER_ORDER} lots)")
                print("  This is a risk control measure. Please reduce capital or contact support.")
                self.state = TradingState.IDLE
                return

            quantity = lots * Config.NIFTY_LOT_SIZE

            print(f"\n📋 Order details:")
            print(f"   Capital: ₹{self.capital:,.2f} ({self.capital_multiplier:.0f}x base)")
            print(f"   Base Lots: {base_lots} → Adjusted Lots: {lots}")
            print(f"   Quantity: {quantity} units")

            # Check margin
            print("\n💰 Checking margin...")
            if not self.order_manager.check_margin(trading_symbol, quantity):
                print("❌ Insufficient margin. Trade cancelled.")
                logger.error("Insufficient margin for trade")
                self.state = TradingState.IDLE
                return

            print("✓ Margin sufficient")

            # Place order
            print("\n📤 Placing order...")
            order_id = self.order_manager.place_order(trading_symbol, quantity)

            print(f"✓ Order placed: {order_id}")
            print("⏳ Waiting for order completion...")

            # Wait for order completion
            success, filled_price = self.order_manager.wait_for_order_completion(order_id)

            if not success:
                print("❌ Order failed or rejected")
                logger.error(f"Order {order_id} failed")
                self.state = TradingState.IDLE
                return

            print(f"✓ Order filled at {filled_price}")

            # Calculate actual risk points and position sizing
            # For this implementation, we use a simplified approach
            # In production, you'd calculate expected SL price based on option Greeks
            risk_points = filled_price * 0.05  # 5% of entry price as risk

            # Calculate SL and target in premium terms (1:3 risk-reward)
            if option_type == "CE":
                sl_price = filled_price - risk_points
                target_price = filled_price + (risk_points * 3)
            else:  # PE
                sl_price = filled_price - risk_points
                target_price = filled_price + (risk_points * 3)

            # Create position object
            self.position = {
                'direction': 'CALL' if option_type == 'CE' else 'PUT',
                'trading_symbol': trading_symbol,
                'instrument_token': instrument_token,
                'entry_price': filled_price,
                'current_price': filled_price,
                'stop_loss': sl_price,
                'target': target_price,
                'quantity_lots': lots,
                'quantity_units': quantity,
                'entry_time': get_ist_now(),
                'sl_trigger_index': sl_trigger_index,
                'option_type': option_type
            }

            logger.info(f"Position opened: {self.position}")

            # Subscribe to option price updates
            self.option_instrument_token = instrument_token
            self.data_stream.subscribe(instrument_token, self._on_option_tick)

            # Reset monitoring flags
            self._listener_started = False
            self.cancel_monitoring = False

            self.state = TradingState.POSITION_ACTIVE

        except Exception as e:
            logger.error(f"Trade execution failed: {e}", exc_info=True)
            print(f"\n❌ Trade execution failed: {e}")
            self.state = TradingState.IDLE

    def _handle_position_active(self):
        """Handle POSITION_ACTIVE state - monitor position and update dashboard."""
        if not self.position:
            self.state = TradingState.IDLE
            return

        # Start position keyboard listener thread on first entry to this state
        if not hasattr(self, '_position_listener_started') or not self._position_listener_started:
            self._position_listener_started = True
            self.position_command = None
            listener_thread = threading.Thread(target=self._position_keyboard_listener, daemon=True)
            listener_thread.start()
            logger.info("Position keyboard listener started")

        # Check for position commands (M or Q)
        if self.position_command == 'M':
            logger.info("User requested SL modification")
            self._handle_modify_stop_loss()
            self.position_command = None
            # Restart listener
            self._position_listener_started = False
            return

        elif self.position_command == 'T':
            logger.info("User requested target modification")
            self._handle_modify_target()
            self.position_command = None
            # Restart listener
            self._position_listener_started = False
            return

        elif self.position_command == 'Q':
            logger.info("User requested force exit")
            print("\n\n⚠️  FORCE EXIT requested by user")
            print("   Closing position...")
            self._exit_position("Manual Exit (User Forced)")
            self.position_command = None
            self._position_listener_started = False
            return

        # Thread-safe read of position data for display
        with self.position_lock:
            entry_price = self.position['entry_price']
            current_price = self.position['current_price']
            quantity_units = self.position['quantity_units']
            direction = self.position['direction']
            quantity_lots = self.position['quantity_lots']
            stop_loss = self.position['stop_loss']
            target = self.position['target']
            trading_symbol = self.position['trading_symbol']

        # Calculate P&L (outside lock)
        pnl = calculate_pnl(entry_price, current_price, quantity_units, direction)
        return_pct = calculate_return_percentage(entry_price, current_price)

        # Update dashboard
        self.dashboard.show_position_dashboard(
            direction=direction,
            quantity_lots=quantity_lots,
            quantity_units=quantity_units,
            entry_price=entry_price,
            current_price=current_price,
            stop_loss=stop_loss,
            target=target,
            pnl=pnl,
            return_pct=return_pct,
            trading_symbol=trading_symbol
        )

        time.sleep(Config.DASHBOARD_REFRESH_RATE)

    def _handle_modify_stop_loss(self):
        """Handle user request to modify stop loss."""
        self.dashboard.clear_screen()
        print("\n" + "="*60)
        print("         MODIFY STOP LOSS")
        print("="*60)

        # Thread-safe read of position data
        with self.position_lock:
            current_sl = self.position['stop_loss']
            current_price = self.position['current_price']
            direction = self.position['direction']

        print(f"\nCurrent Stop Loss: ₹{current_sl:.2f}")
        print(f"Current Price: ₹{current_price:.2f}")
        print(f"Direction: {direction}")
        print()

        # Get new SL from user
        try:
            new_sl_str = input("Enter new Stop Loss price (or press ENTER to cancel): ").strip()

            if not new_sl_str:
                print("✗ Modification cancelled")
                time.sleep(2)
                return

            new_sl = float(new_sl_str)

            # Validate new SL
            if direction == 'CALL':
                if new_sl >= current_price:
                    print(f"✗ Invalid: CALL stop loss must be BELOW current price ({current_price:.2f})")
                    time.sleep(3)
                    return
            else:  # PUT
                if new_sl <= current_price:
                    print(f"✗ Invalid: PUT stop loss must be ABOVE current price ({current_price:.2f})")
                    time.sleep(3)
                    return

            # Thread-safe update of SL
            with self.position_lock:
                old_sl = self.position['stop_loss']
                self.position['stop_loss'] = new_sl

            logger.info(f"Stop loss modified: {old_sl:.2f} → {new_sl:.2f}")
            print(f"\n✓ Stop Loss updated: ₹{old_sl:.2f} → ₹{new_sl:.2f}")
            time.sleep(2)

        except ValueError:
            print("✗ Invalid input. Please enter a valid number.")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error modifying SL: {e}")
            print(f"✗ Error: {e}")
            time.sleep(3)

    def _handle_modify_target(self):
        """Handle user request to modify target price."""
        self.dashboard.clear_screen()
        print("\n" + "="*60)
        print("         MODIFY TARGET PRICE")
        print("="*60)

        # Thread-safe read of position data
        with self.position_lock:
            current_target = self.position['target']
            current_price = self.position['current_price']
            entry_price = self.position['entry_price']
            direction = self.position['direction']

        print(f"\nCurrent Target: ₹{current_target:.2f}")
        print(f"Current Price: ₹{current_price:.2f}")
        print(f"Entry Price: ₹{entry_price:.2f}")
        print(f"Direction: {direction}")
        print()

        # Get new target from user
        try:
            new_target_str = input("Enter new Target price (or press ENTER to cancel): ").strip()

            if not new_target_str:
                print("✗ Modification cancelled")
                time.sleep(2)
                return

            new_target = float(new_target_str)

            # Validate new target (should be above entry price for profit)
            if new_target <= entry_price:
                print(f"✗ Invalid: Target must be ABOVE entry price (₹{entry_price:.2f}) for profit")
                time.sleep(3)
                return

            # Optional: Warning if target is below current price (position already in profit)
            if new_target < current_price:
                print(f"⚠️  Warning: New target (₹{new_target:.2f}) is BELOW current price (₹{current_price:.2f})")
                confirm = input("Continue? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("✗ Modification cancelled")
                    time.sleep(2)
                    return

            # Thread-safe update of target
            with self.position_lock:
                old_target = self.position['target']
                self.position['target'] = new_target

            logger.info(f"Target modified: {old_target:.2f} → {new_target:.2f}")
            print(f"\n✓ Target updated: ₹{old_target:.2f} → ₹{new_target:.2f}")
            time.sleep(2)

        except ValueError:
            print("✗ Invalid input. Please enter a valid number.")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error modifying target: {e}")
            print(f"✗ Error: {e}")
            time.sleep(3)

    def _check_exit_conditions(self):
        """Check if position should be exited."""
        if not self.position:
            return

        # Thread-safe read of position data
        with self.position_lock:
            current_price = self.position['current_price']
            stop_loss = self.position['stop_loss']
            target = self.position['target']

        exit_reason = None

        # Check for target hit
        if current_price >= target:
            exit_reason = "Target Hit"
            logger.info(f"Target hit: {current_price} >= {target}")

        # Check for stop loss hit
        elif current_price <= stop_loss:
            exit_reason = "Stop Loss"
            logger.info(f"Stop loss hit: {current_price} <= {stop_loss}")

        # Check for EOD close
        elif should_close_eod():
            exit_reason = "EOD Close"
            logger.info("EOD close time reached")

        # Exit if needed
        if exit_reason:
            self._exit_position(exit_reason)

    def _exit_position(self, exit_reason: str):
        """
        Exit the current position.

        Args:
            exit_reason: Reason for exit
        """
        try:
            print(f"\n\n🔔 Exiting position: {exit_reason}")

            # Place exit order
            order_id = self.order_manager.exit_position(
                self.position['trading_symbol'],
                self.position['quantity_units']
            )

            print(f"✓ Exit order placed: {order_id}")
            print("⏳ Waiting for order completion...")

            # Wait for order completion
            success, exit_price = self.order_manager.wait_for_order_completion(order_id)

            if not success:
                logger.error(f"Exit order {order_id} failed")
                exit_price = self.position['current_price']  # Use last known price

            # Calculate final P&L
            final_pnl = calculate_pnl(
                self.position['entry_price'],
                exit_price,
                self.position['quantity_units'],
                self.position['direction']
            )

            return_pct = calculate_return_percentage(
                self.position['entry_price'],
                exit_price
            )

            # Log trade to journal
            self._log_trade_to_journal(exit_price, exit_reason, final_pnl, return_pct)

            # Show summary
            self.dashboard.show_trade_summary(
                direction=self.position['direction'],
                entry_price=self.position['entry_price'],
                exit_price=exit_price,
                exit_reason=exit_reason,
                pnl=final_pnl,
                return_pct=return_pct,
                trading_symbol=self.position['trading_symbol']
            )

            logger.info(f"Position closed - P&L: {final_pnl}, Return: {return_pct}%")

            # Unsubscribe from option updates
            if self.option_instrument_token:
                self.data_stream.unsubscribe(self.option_instrument_token)

            # Store exit details for summary display
            self.position['exit_price'] = exit_price
            self.position['exit_reason'] = exit_reason
            self.position['final_pnl'] = final_pnl
            self.position['return_pct'] = return_pct

            # Reset position listener flag
            self._position_listener_started = False

            self.state = TradingState.POSITION_CLOSED

        except Exception as e:
            logger.error(f"Failed to exit position: {e}", exc_info=True)
            print(f"\n❌ Exit failed: {e}")

    def _handle_position_closed(self):
        """Handle POSITION_CLOSED state - wait for user to continue."""
        # Wait for Enter key
        input()

        # Reset position and direction
        self.position = None
        self.option_instrument_token = None
        self.entry_candle_high = None
        self.entry_candle_low = None
        self.chosen_direction = None
        self.entry_candle_choice = None

        # Return to idle
        self.state = TradingState.IDLE
        logger.info("Returning to idle state")

    def _log_trade_to_journal(self, exit_price: float, exit_reason: str, pnl: float, return_pct: float):
        """
        Log trade to the trading journal.

        Args:
            exit_price: Exit price
            exit_reason: Reason for exit
            pnl: Final P&L
            return_pct: Return percentage
        """
        try:
            journal_file = Path(Config.JOURNAL_FILE)

            # Create new row
            trade_data = {
                'Serial Number': None,  # Will be set based on row count
                'Date': self.position['entry_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'Entry Candle Type': self.entry_candle_choice,  # CURRENT or PREVIOUS
                'Chosen Direction': self.chosen_direction,  # What user selected
                'Entry Candle High': self.entry_candle_high,
                'Entry Candle Low': self.entry_candle_low,
                'Breakout Direction': self.position['direction'],  # Actual breakout
                'Option Type': self.position['option_type'],
                'Option Strike': self.position['trading_symbol'],
                'Entry Price': self.position['entry_price'],
                'Stop Loss': self.position['stop_loss'],
                'Target': self.position['target'],
                'Exit Price': exit_price,
                'Exit Reason': exit_reason,
                'P&L': pnl,
                'Return %': return_pct
            }

            # Load existing journal or create new
            if journal_file.exists():
                df = pd.read_excel(journal_file)
                trade_data['Serial Number'] = len(df) + 1
                df = pd.concat([df, pd.DataFrame([trade_data])], ignore_index=True)
            else:
                trade_data['Serial Number'] = 1
                df = pd.DataFrame([trade_data])

            # Save to file
            df.to_excel(journal_file, index=False)
            logger.info(f"Trade logged to journal: {journal_file}")

        except Exception as e:
            logger.error(f"Failed to log trade to journal: {e}", exc_info=True)

    def cleanup(self):
        """Cleanup resources before exit."""
        logger.info("Cleaning up strategy resources...")

        # Close any open positions
        if self.position and self.state == TradingState.POSITION_ACTIVE:
            print("\n\n⚠️  Closing open position before exit...")
            self._exit_position("Manual - System Shutdown")

        # Stop data stream
        self.data_stream.stop()

        logger.info("Cleanup complete")
