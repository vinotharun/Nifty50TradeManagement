#!/usr/bin/env python3
"""
Debug script to list available instruments and find NIFTY 50.

Run this if you're having trouble finding the NIFTY instrument.
"""

from auth import KiteAuthenticator
from config import Config

def main():
    print("="*60)
    print("INSTRUMENT FINDER - Debug Tool")
    print("="*60)
    print()
    
    # Validate config
    Config.validate()
    
    # Authenticate
    print("Authenticating...")
    authenticator = KiteAuthenticator()
    kite = authenticator.authenticate()
    print("✓ Authenticated\n")
    
    # Try different exchanges
    exchanges = ["INDICES", "NSE", "NFO"]
    
    for exchange in exchanges:
        print(f"\n{'='*60}")
        print(f"Checking {exchange} exchange...")
        print('='*60)
        
        try:
            instruments = kite.instruments(exchange)
            print(f"✓ Found {len(instruments)} instruments in {exchange}")
            
            # Look for NIFTY-related indices
            print(f"\nSearching for NIFTY indices in {exchange}:")
            nifty_count = 0
            
            for inst in instruments:
                symbol = inst.get('tradingsymbol', '')
                name = inst.get('name', '')
                inst_type = inst.get('instrument_type', '')
                token = inst.get('instrument_token', '')
                
                # Show all INDEX type instruments in INDICES exchange
                if exchange == "INDICES" and inst_type == "INDEX":
                    print(f"  [{inst_type}] {symbol:25} | {name:30} | Token: {token}")
                    nifty_count += 1
                
                # Show NIFTY-related in other exchanges
                elif 'NIFTY' in symbol.upper() and inst_type in ['INDEX', 'EQ']:
                    print(f"  [{inst_type}] {symbol:25} | {name:30} | Token: {token}")
                    nifty_count += 1
                    
                    if nifty_count >= 20:  # Limit output
                        print(f"  ... (showing first 20 matches)")
                        break
            
            if nifty_count == 0:
                print(f"  No NIFTY instruments found in {exchange}")
                
        except Exception as e:
            print(f"✗ Error accessing {exchange}: {e}")
    
    print("\n" + "="*60)
    print("SEARCH COMPLETE")
    print("="*60)
    print("\nLook for an instrument like:")
    print("  - NIFTY 50")
    print("  - NIFTY")
    print("  - Nifty 50")
    print("\nCopy the exact 'tradingsymbol' value and update the code if needed.")
    print()

if __name__ == "__main__":
    main()
