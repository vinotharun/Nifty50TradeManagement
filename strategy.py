"""
Strategy module containing core trading logic.

Implements the state machine for the breakout strategy.
"""

import logging
import time
import threading
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
        
        # Position tracking
        self.position = None  # Will store position details
        self.option_instrument_token = None
        
        # User input handling
        self.user_command = None
        self.command_lock = threading.Lock()
        
        # NIFTY instrument token
        self.nifty_token = None
    
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
        self.current_nifty_price = tick.get('last_price')
        
        # Store tick data for candle formation
        if self.state == TradingState.WAITING_CANDLE_CLOSE:
            self.candle_data.append({
                'price': self.current_nifty_price,
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
        if self.position:
            current_price = tick.get('last_price')
            self.position['current_price'] = current_price
            
            # Check for exit conditions
            self._check_exit_conditions()
    
    def run(self):
        """Main strategy loop."""
        logger.info("Starting strategy main loop")
        
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
        self.dashboard.show_idle_state(self.current_nifty_price)

        # Wait for Enter key
        input()

        # Get current time
        now = get_ist_now()

        # Calculate the start of the current 1-minute candle
        # Round down to the nearest minute
        candle_start = now.replace(second=0, microsecond=0)

        # Calculate when this candle will close (next minute boundary)
        candle_close = candle_start + timedelta(minutes=1)

        # Store entry candle timing
        self.entry_candle_start_time = candle_start
        self.entry_candle_close_time = candle_close
        self.candle_data = []
        self.state = TradingState.WAITING_CANDLE_CLOSE

        seconds_remaining = (candle_close - now).total_seconds()

        logger.info(f"Entry candle designated: {candle_start.strftime('%H:%M:%S')} to {candle_close.strftime('%H:%M:%S')}")
        logger.info(f"Current time: {now.strftime('%H:%M:%S')}, waiting {seconds_remaining:.0f}s for candle to close")

        print(f"\n✓ Entry candle designated: {candle_start.strftime('%H:%M:%S')} to {candle_close.strftime('%H:%M:%S')}")
        print(f"  Current time: {now.strftime('%H:%M:%S')}")
        print(f"  Waiting {seconds_remaining:.0f} seconds for candle to close...")

    def _handle_waiting_candle_close(self):
        """Handle WAITING_CANDLE_CLOSE state."""
        # Check if candle has closed
        now = get_ist_now()

        if now >= self.entry_candle_close_time:
            # Candle closed, fetch historical data to get accurate High/Low
            try:
                print("\n📊 Fetching entry candle data...")

                # Fetch 1-minute historical data for NIFTY
                from_date = self.entry_candle_start_time
                to_date = self.entry_candle_close_time

                # Get historical data (1-minute interval)
                historical_data = self.kite.historical_data(
                    instrument_token=self.nifty_token,
                    from_date=from_date,
                    to_date=to_date,
                    interval="minute"
                )

                if historical_data and len(historical_data) > 0:
                    # Get the last candle (our entry candle)
                    entry_candle = historical_data[-1]
                    self.entry_candle_high = entry_candle['high']
                    self.entry_candle_low = entry_candle['low']

                    logger.info(f"Entry candle from historical data - High: {self.entry_candle_high}, Low: {self.entry_candle_low}")
                else:
                    # Fallback to collected ticks
                    logger.warning("No historical data received, using collected ticks")
                    if self.candle_data:
                        prices = [d['price'] for d in self.candle_data]
                        self.entry_candle_high = max(prices)
                        self.entry_candle_low = min(prices)
                    else:
                        self.entry_candle_high = self.current_nifty_price
                        self.entry_candle_low = self.current_nifty_price

            except Exception as e:
                logger.error(f"Failed to fetch historical data: {e}")
                # Fallback to collected ticks
                if self.candle_data:
                    prices = [d['price'] for d in self.candle_data]
                    self.entry_candle_high = max(prices)
                    self.entry_candle_low = min(prices)
                else:
                    self.entry_candle_high = self.current_nifty_price
                    self.entry_candle_low = self.current_nifty_price

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
        """Handle WAITING_BREAKOUT state."""
        # Check for EOD
        if should_close_eod():
            logger.info("EOD time reached, returning to idle")
            self.state = TradingState.IDLE
            return

        # Breakout check is done in _on_nifty_tick callback
        # Just update display
        time.sleep(0.5)

    def _check_breakout(self):
        """Check if breakout has occurred."""
        if not self.current_nifty_price:
            return

        # Check for call breakout (above high)
        if self.current_nifty_price > self.entry_candle_high:
            logger.info(f"Call breakout detected at {self.current_nifty_price}")
            self.dashboard.show_breakout("CALL", self.current_nifty_price, self.entry_candle_high)
            time.sleep(2)  # Brief pause to show breakout message
            self._execute_trade("CE", self.entry_candle_low - 1)

        # Check for put breakout (below low)
        elif self.current_nifty_price < self.entry_candle_low:
            logger.info(f"Put breakout detected at {self.current_nifty_price}")
            self.dashboard.show_breakout("PUT", self.current_nifty_price, self.entry_candle_low)
            time.sleep(2)  # Brief pause to show breakout message
            self._execute_trade("PE", self.entry_candle_high + 1)

    def _execute_trade(self, option_type: str, sl_trigger_index: float):
        """
        Execute the trade after breakout.

        Args:
            option_type: 'CE' for Call, 'PE' for Put
            sl_trigger_index: Index level that triggers stop loss
        """
        try:
            print("\n📊 Finding option instrument...")

            # Find option instrument
            option_instrument = self.order_manager.find_option_instrument(
                self.current_nifty_price,
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
            lots = determine_lot_size(estimated_risk_points)
            quantity = lots * Config.NIFTY_LOT_SIZE

            print(f"\n📋 Order details:")
            print(f"   Lots: {lots}")
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

            # Calculate SL and target in premium terms
            if option_type == "CE":
                sl_price = filled_price - risk_points
                target_price = filled_price + (risk_points * 2)
            else:  # PE
                sl_price = filled_price - risk_points
                target_price = filled_price + (risk_points * 2)

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

        # Calculate P&L
        pnl = calculate_pnl(
            self.position['entry_price'],
            self.position['current_price'],
            self.position['quantity_units'],
            self.position['direction']
        )

        return_pct = calculate_return_percentage(
            self.position['entry_price'],
            self.position['current_price']
        )

        # Update dashboard
        self.dashboard.show_position_dashboard(
            direction=self.position['direction'],
            quantity_lots=self.position['quantity_lots'],
            quantity_units=self.position['quantity_units'],
            entry_price=self.position['entry_price'],
            current_price=self.position['current_price'],
            stop_loss=self.position['stop_loss'],
            target=self.position['target'],
            pnl=pnl,
            return_pct=return_pct,
            trading_symbol=self.position['trading_symbol']
        )

        # Check for user commands (M for modify SL, Q for exit)
        # This would need non-blocking input in production
        # For now, exit conditions are checked in _check_exit_conditions

        time.sleep(Config.DASHBOARD_REFRESH_RATE)

    def _check_exit_conditions(self):
        """Check if position should be exited."""
        if not self.position:
            return

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

            self.state = TradingState.POSITION_CLOSED

        except Exception as e:
            logger.error(f"Failed to exit position: {e}", exc_info=True)
            print(f"\n❌ Exit failed: {e}")

    def _handle_position_closed(self):
        """Handle POSITION_CLOSED state - wait for user to continue."""
        # Wait for Enter key
        input()

        # Reset position
        self.position = None
        self.option_instrument_token = None
        self.entry_candle_high = None
        self.entry_candle_low = None

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
                'Entry Candle High': self.entry_candle_high,
                'Entry Candle Low': self.entry_candle_low,
                'Breakout Direction': self.position['direction'],
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
