"""
Authentication module for Kite Connect API.

Handles login flow, token generation, and session management.
"""

import logging
import webbrowser
from pathlib import Path
from kiteconnect import KiteConnect
from config import Config

logger = logging.getLogger(__name__)


class KiteAuthenticator:
    """Handles Kite Connect authentication and session management."""
    
    def __init__(self):
        """Initialize the authenticator with API credentials."""
        self.api_key = Config.KITE_API_KEY
        self.api_secret = Config.KITE_API_SECRET
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = None
        
    def get_login_url(self) -> str:
        """
        Generate the login URL for Kite Connect.
        
        Returns:
            Login URL string
        """
        return self.kite.login_url()
    
    def authenticate(self) -> KiteConnect:
        """
        Perform the complete authentication flow.
        
        Returns:
            Authenticated KiteConnect instance
            
        Raises:
            Exception: If authentication fails
        """
        # Try to load existing access token
        if self._load_access_token():
            if self._validate_token():
                logger.info("Using existing valid access token")
                return self.kite
            else:
                logger.info("Existing access token is invalid, re-authenticating")
        
        # Perform fresh authentication
        return self._fresh_authentication()
    
    def _fresh_authentication(self) -> KiteConnect:
        """
        Perform fresh authentication via browser login.
        
        Returns:
            Authenticated KiteConnect instance
        """
        print("\n" + "="*60)
        print("KITE CONNECT AUTHENTICATION")
        print("="*60)
        
        # Generate and open login URL
        login_url = self.get_login_url()
        print(f"\nOpening browser for Zerodha login...")
        print(f"If browser doesn't open, visit: {login_url}\n")
        
        try:
            webbrowser.open(login_url)
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")
        
        # Get request token from user
        print("After logging in, you will be redirected to a URL.")
        print("Copy the 'request_token' parameter from the URL and paste it below.")
        print("\nExample URL: http://127.0.0.1/?request_token=ABC123&action=login&status=success")
        print("Example token: ABC123")
        
        request_token = input("\nEnter request token: ").strip()
        
        if not request_token:
            raise ValueError("Request token cannot be empty")
        
        # Generate access token
        try:
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
            )
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            # Save access token for future use
            self._save_access_token()
            
            logger.info("Authentication successful")
            print(f"\n✓ Authentication successful!")
            print("="*60 + "\n")
            
            return self.kite
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise Exception(f"Authentication failed: {e}")
    
    def _load_access_token(self) -> bool:
        """
        Load access token from file if it exists.
        
        Returns:
            True if token was loaded, False otherwise
        """
        token_file = Path(Config.ACCESS_TOKEN_FILE)
        
        if token_file.exists():
            try:
                self.access_token = token_file.read_text().strip()
                if self.access_token:
                    self.kite.set_access_token(self.access_token)
                    return True
            except Exception as e:
                logger.warning(f"Could not load access token: {e}")
        
        return False
    
    def _save_access_token(self):
        """Save access token to file."""
        try:
            token_file = Path(Config.ACCESS_TOKEN_FILE)
            token_file.write_text(self.access_token)
            logger.info(f"Access token saved to {Config.ACCESS_TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"Could not save access token: {e}")
    
    def _validate_token(self) -> bool:
        """
        Validate the current access token by making a test API call.
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Try to fetch profile as a validation check
            self.kite.profile()
            return True
        except Exception as e:
            logger.debug(f"Token validation failed: {e}")
            return False
