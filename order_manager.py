"""
Order management module for placing and managing trades.

Handles order placement, validation, and position tracking.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime
from kiteconnect import KiteConnect
from config import Config
from utils import get_atm_strike, get_ist_now, format_currency

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order placement and position tracking."""
    
    def __init__(self, kite: KiteConnect):
        """
        Initialize the order manager.
        
        Args:
            kite: Authenticated KiteConnect instance
        """
        self.kite = kite
        self.current_position = None
    
    def get_available_margin(self) -> float:
        """
        Get available margin for trading.
        
        Returns:
            Available margin amount
        """
        try:
            margins = self.kite.margins()
            equity_margin = margins.get('equity', {})
            available = equity_margin.get('available', {}).get('live_balance', 0)
            logger.info(f"Available margin: {format_currency(available)}")
            return available
        except Exception as e:
            logger.error(f"Failed to fetch margins: {e}")
            return 0
    
    def find_nifty_instrument_token(self) -> int:
        """
        Find the instrument token for NIFTY 50 index.

        Returns:
            Instrument token for NIFTY 50
        """
        try:
            # Try INDICES exchange first (recommended for indices)
            try:
                instruments = self.kite.instruments("INDICES")
                logger.info(f"Searching in INDICES exchange, found {len(instruments)} instruments")
            except:
                # Fallback to NSE if INDICES not available
                instruments = self.kite.instruments("NSE")
                logger.info(f"Searching in NSE exchange, found {len(instruments)} instruments")

            # Search patterns for NIFTY 50 (in order of preference)
            search_patterns = [
                'NIFTY 50',      # Most common
                'Nifty 50',      # Capitalization variant
                'NIFTY',         # Short form
                'NIFTY50',       # No space
                'Nifty50',       # Capitalization variant
            ]

            for pattern in search_patterns:
                for instrument in instruments:
                    if instrument['tradingsymbol'] == pattern and instrument['instrument_type'] == 'INDEX':
                        token = instrument['instrument_token']
                        logger.info(f"✓ NIFTY 50 instrument found: '{instrument['tradingsymbol']}' (token: {token})")
                        return token

            # Fallback - search by name containing 'NIFTY' and is an INDEX
            logger.info("Trying fallback search for NIFTY index...")
            for instrument in instruments:
                if instrument['instrument_type'] == 'INDEX':
                    name = instrument.get('name', '').upper()
                    symbol = instrument.get('tradingsymbol', '').upper()

                    # Check if it's NIFTY 50 (not BANK NIFTY, NIFTY IT, etc.)
                    if 'NIFTY' in symbol and 'BANK' not in symbol and 'IT' not in symbol:
                        # Prefer exact match to base NIFTY
                        if symbol in ['NIFTY', 'NIFTY50', 'NIFTY 50']:
                            token = instrument['instrument_token']
                            logger.info(f"NIFTY instrument found via fallback: {instrument['tradingsymbol']} (token: {token})")
                            return token

            # If still not found, list available indices for debugging
            logger.info("Available INDEX instruments:")
            index_count = 0
            for instrument in instruments[:50]:  # Show first 50
                if instrument['instrument_type'] == 'INDEX':
                    logger.info(f"  - {instrument['tradingsymbol']} ({instrument.get('name', 'N/A')})")
                    index_count += 1
                    if index_count >= 10:  # Limit to 10 for brevity
                        break

            raise Exception("NIFTY 50 instrument not found. Check logs for available indices.")
        except Exception as e:
            logger.error(f"Failed to find NIFTY instrument: {e}")
            raise
    
    def find_option_instrument(self, spot_price: float, option_type: str, expiry_date: Optional[str] = None) -> Dict:
        """
        Find the appropriate ITM (In-The-Money) option instrument.

        Args:
            spot_price: Current NIFTY spot price
            option_type: 'CE' for Call or 'PE' for Put
            expiry_date: Optional specific expiry date (YYYY-MM-DD format)

        Returns:
            Instrument details dictionary
        """
        try:
            from utils import get_itm_strike

            # Determine option direction for ITM calculation
            direction = 'CALL' if option_type == 'CE' else 'PUT'

            # Calculate ITM strike (1 strike in the money)
            itm_strike = get_itm_strike(spot_price, direction)
            logger.info(f"ITM Strike: {itm_strike} for spot price: {spot_price} ({direction})")

            # Get all NFO instruments
            instruments = self.kite.instruments("NFO")

            # Filter NIFTY options
            nifty_options = [
                inst for inst in instruments
                if inst['name'] == 'NIFTY'
                and inst['instrument_type'] == option_type
                and inst['strike'] == itm_strike
            ]

            if not nifty_options:
                raise Exception(f"No {option_type} options found for strike {itm_strike}")

            # Sort by expiry
            nifty_options.sort(key=lambda x: x['expiry'])

            # Get today's date in IST
            from utils import get_ist_now
            today = get_ist_now().date()

            # Skip today's expiry if it exists, go to next expiry
            selected_option = None
            for option in nifty_options:
                # Handle both datetime.datetime and datetime.date objects
                option_expiry = option['expiry']
                if hasattr(option_expiry, 'date'):
                    option_expiry_date = option_expiry.date()  # datetime.datetime object
                else:
                    option_expiry_date = option_expiry  # Already datetime.date object

                # Skip if expiry is today
                if option_expiry_date == today:
                    logger.info(f"Skipping same-day expiry: {option['tradingsymbol']} (Expiry: {option['expiry']})")
                    continue

                # Select the first non-today expiry
                selected_option = option
                break

            # Fallback: if all options expire today (unlikely), use the nearest anyway
            if selected_option is None:
                logger.warning("All available options expire today. Using nearest expiry as fallback.")
                selected_option = nifty_options[0]

            logger.info(f"Selected ITM option: {selected_option['tradingsymbol']} "
                       f"(Strike: {selected_option['strike']}, Expiry: {selected_option['expiry']})")

            return selected_option

        except Exception as e:
            logger.error(f"Failed to find option instrument: {e}")
            raise
    
    def check_margin(self, trading_symbol: str, quantity: int, transaction_type: str = "BUY") -> bool:
        """
        Check if sufficient margin is available for the order.
        
        Args:
            trading_symbol: Trading symbol
            quantity: Order quantity
            transaction_type: BUY or SELL
            
        Returns:
            True if sufficient margin, False otherwise
        """
        try:
            # Get order margins
            order_param = [{
                "exchange": "NFO",
                "tradingsymbol": trading_symbol,
                "transaction_type": transaction_type,
                "variety": "regular",
                "product": "MIS",
                "order_type": "MARKET",
                "quantity": quantity
            }]
            
            margins = self.kite.order_margins(order_param)
            required_margin = margins[0].get('total', 0)
            available_margin = self.get_available_margin()
            
            logger.info(f"Required margin: {format_currency(required_margin)}, "
                       f"Available: {format_currency(available_margin)}")
            
            return available_margin >= required_margin
            
        except Exception as e:
            logger.error(f"Margin check failed: {e}")
            return False
    
    def place_order(self, trading_symbol: str, quantity: int, transaction_type: str = "BUY") -> Optional[str]:
        """
        Place a limit order at best price (market-like execution).
        Uses limit order to comply with Zerodha API restrictions.

        Args:
            trading_symbol: Trading symbol
            quantity: Order quantity
            transaction_type: BUY or SELL

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Get current LTP (Last Traded Price)
            quote = self.kite.quote(f"NFO:{trading_symbol}")
            ltp = quote[f"NFO:{trading_symbol}"]["last_price"]

            # Add buffer for immediate execution
            # BUY: Add 2% to ensure order fills immediately
            # SELL: Subtract 2% to ensure order fills immediately
            if transaction_type == self.kite.TRANSACTION_TYPE_BUY:
                limit_price = round(ltp * 1.02, 1)  # 2% above LTP
            else:  # SELL
                limit_price = round(ltp * 0.98, 1)  # 2% below LTP

            logger.info(f"Placing limit order: {transaction_type} {quantity} {trading_symbol} @ ₹{limit_price} (LTP: ₹{ltp})")

            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NFO,
                tradingsymbol=trading_symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=limit_price
            )

            logger.info(f"Order placed successfully: {order_id} - {transaction_type} {quantity} {trading_symbol} @ ₹{limit_price}")
            return order_id

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            raise

    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """
        Get details of an order.

        Args:
            order_id: Order ID

        Returns:
            Order details dictionary
        """
        try:
            orders = self.kite.orders()
            for order in orders:
                if order['order_id'] == order_id:
                    return order
            return None
        except Exception as e:
            logger.error(f"Failed to fetch order details: {e}")
            return None

    def wait_for_order_completion(self, order_id: str, max_wait: int = 30) -> Tuple[bool, float]:
        """
        Wait for order to complete and get filled price.

        Args:
            order_id: Order ID
            max_wait: Maximum seconds to wait

        Returns:
            Tuple of (success, filled_price)
        """
        logger.info(f"Waiting for order {order_id} to complete...")

        waited = 0
        while waited < max_wait:
            order = self.get_order_details(order_id)

            if order:
                status = order.get('status')

                if status == 'COMPLETE':
                    filled_price = order.get('average_price', 0)
                    logger.info(f"Order {order_id} completed at price: {filled_price}")
                    return True, filled_price
                elif status in ['REJECTED', 'CANCELLED']:
                    logger.error(f"Order {order_id} {status}")
                    return False, 0

            time.sleep(1)
            waited += 1

        logger.warning(f"Order {order_id} completion timeout")
        return False, 0

    def exit_position(self, trading_symbol: str, quantity: int) -> Optional[str]:
        """
        Exit (sell) a position.

        Args:
            trading_symbol: Trading symbol
            quantity: Quantity to sell

        Returns:
            Order ID if successful
        """
        try:
            return self.place_order(trading_symbol, quantity, transaction_type="SELL")
        except Exception as e:
            logger.error(f"Failed to exit position: {e}")
            raise
