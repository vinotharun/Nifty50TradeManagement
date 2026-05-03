"""
Data streaming module for live market data.

Manages WebSocket connections for real-time price updates.
"""

import logging
import time
import threading
from typing import Dict, Callable, Optional
from kiteconnect import KiteTicker
from config import Config

logger = logging.getLogger(__name__)


class DataStream:
    """Manages WebSocket connection for live market data streaming."""
    
    def __init__(self, api_key: str, access_token: str):
        """
        Initialize the data stream.
        
        Args:
            api_key: Kite API key
            access_token: Valid access token
        """
        self.api_key = api_key
        self.access_token = access_token
        self.ticker = KiteTicker(api_key, access_token)
        self.subscribed_tokens = set()
        self.tick_callbacks = {}
        self.is_connected = False
        self.reconnect_count = 0
        self.latest_ticks = {}  # Store latest tick data
        
        # Setup callbacks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error
        self.ticker.on_reconnect = self._on_reconnect
        self.ticker.on_noreconnect = self._on_noreconnect
        self.ticker.on_ticks = self._on_ticks
        
    def _on_connect(self, ws, response):
        """Handle WebSocket connection event."""
        self.is_connected = True
        self.reconnect_count = 0
        logger.info("WebSocket connected successfully")
        
        # Resubscribe to instruments if any
        if self.subscribed_tokens:
            logger.info(f"Resubscribing to {len(self.subscribed_tokens)} instruments")
            self.ticker.subscribe(list(self.subscribed_tokens))
            self.ticker.set_mode(self.ticker.MODE_FULL, list(self.subscribed_tokens))
    
    def _on_close(self, ws, code, reason):
        """Handle WebSocket close event."""
        self.is_connected = False
        logger.warning(f"WebSocket closed: {code} - {reason}")
    
    def _on_error(self, ws, code, reason):
        """Handle WebSocket error event."""
        logger.error(f"WebSocket error: {code} - {reason}")
    
    def _on_reconnect(self, ws, attempts_count):
        """Handle WebSocket reconnect event."""
        self.reconnect_count = attempts_count
        logger.info(f"WebSocket reconnecting... Attempt {attempts_count}")
    
    def _on_noreconnect(self, ws):
        """Handle WebSocket no reconnect event."""
        logger.error("WebSocket maximum reconnection attempts reached")
        self.is_connected = False
    
    def _on_ticks(self, ws, ticks):
        """
        Handle incoming tick data.
        
        Args:
            ws: WebSocket instance
            ticks: List of tick data
        """
        for tick in ticks:
            instrument_token = tick.get('instrument_token')
            
            # Store latest tick
            self.latest_ticks[instrument_token] = tick
            
            # Call registered callbacks
            if instrument_token in self.tick_callbacks:
                for callback in self.tick_callbacks[instrument_token]:
                    try:
                        callback(tick)
                    except Exception as e:
                        logger.error(f"Error in tick callback: {e}", exc_info=True)
    
    def subscribe(self, instrument_token: int, callback: Optional[Callable] = None):
        """
        Subscribe to an instrument for live updates.
        
        Args:
            instrument_token: Instrument token to subscribe
            callback: Optional callback function to handle ticks
        """
        self.subscribed_tokens.add(instrument_token)
        
        if callback:
            if instrument_token not in self.tick_callbacks:
                self.tick_callbacks[instrument_token] = []
            self.tick_callbacks[instrument_token].append(callback)
        
        if self.is_connected:
            self.ticker.subscribe([instrument_token])
            self.ticker.set_mode(self.ticker.MODE_FULL, [instrument_token])
            logger.info(f"Subscribed to instrument: {instrument_token}")
    
    def unsubscribe(self, instrument_token: int):
        """
        Unsubscribe from an instrument.
        
        Args:
            instrument_token: Instrument token to unsubscribe
        """
        if instrument_token in self.subscribed_tokens:
            self.subscribed_tokens.remove(instrument_token)
            if instrument_token in self.tick_callbacks:
                del self.tick_callbacks[instrument_token]
            
            if self.is_connected:
                self.ticker.unsubscribe([instrument_token])
                logger.info(f"Unsubscribed from instrument: {instrument_token}")
    
    def get_latest_price(self, instrument_token: int) -> Optional[float]:
        """
        Get the latest price for an instrument.
        
        Args:
            instrument_token: Instrument token
            
        Returns:
            Latest LTP or None if not available
        """
        tick = self.latest_ticks.get(instrument_token)
        if tick:
            return tick.get('last_price')
        return None
    
    def start(self):
        """Start the WebSocket connection in a separate thread."""
        logger.info("Starting WebSocket connection...")
        
        # Run ticker in a separate thread
        ticker_thread = threading.Thread(target=self.ticker.connect, daemon=True)
        ticker_thread.start()
        
        # Wait for connection
        max_wait = 10
        waited = 0
        while not self.is_connected and waited < max_wait:
            time.sleep(0.5)
            waited += 0.5
        
        if self.is_connected:
            logger.info("WebSocket started successfully")
        else:
            logger.warning("WebSocket connection timeout, but will retry in background")
    
    def stop(self):
        """Stop the WebSocket connection."""
        logger.info("Stopping WebSocket connection...")
        self.ticker.close()
        self.is_connected = False
