# NIFTY Instrument Not Found - Fix Guide

## ❌ Error
```
ERROR - Failed to find NIFTY instrument: NIFTY 50 instrument not found
```

## 🔍 Step 1: Find Available NIFTY Instruments

Run the debug script to see what NIFTY instruments are available:

```bash
python debug_instruments.py
```

This will show all available NIFTY indices from different exchanges.

**Look for output like:**
```
[INDEX] NIFTY 50          | Nifty 50                | Token: 256265
[INDEX] NIFTY BANK        | Nifty Bank              | Token: 260105
```

## ✅ Step 2: Update Configuration

Once you find the exact instrument name, you have **two options**:

### Option A: Use Manual Token (Quickest)

If you found the instrument token (e.g., `256265`), add it to your `.env` file:

```env
# Add this line to your .env file
NIFTY_INSTRUMENT_TOKEN=256265
```

Then update `config.py` to use it if set:

In `config.py`, change:
```python
# Instrument Tokens (these will be fetched dynamically)
NIFTY_INSTRUMENT_TOKEN = None  # Will be set after authentication
```

To:
```python
# Instrument Tokens
NIFTY_INSTRUMENT_TOKEN = int(os.getenv('NIFTY_INSTRUMENT_TOKEN', '0')) or None
```

### Option B: Fix the Search Logic

If the debug script shows the NIFTY instrument has a different name (e.g., `"Nifty 50"` instead of `"NIFTY 50"`), update the search pattern.

The updated `order_manager.py` already has improved search logic that should handle most variations.

## 🎯 Common NIFTY Instrument Names

Based on Kite API, NIFTY 50 might appear as:
- `NIFTY 50` (most common)
- `NIFTY` 
- `Nifty 50`
- `NIFTY50`

## 🔄 Step 3: Test Again

After applying the fix, run the system:

```bash
python main.py
```

Check the logs:
```bash
tail -20 trading_system.log
```

You should see:
```
INFO - NIFTY 50 instrument found: [name] (token: [number])
```

## 💡 Alternative: Use Hardcoded Token

If you want a quick workaround, you can hardcode the token directly in `strategy.py`:

In `strategy.py`, replace:
```python
self.nifty_token = self.order_manager.find_nifty_instrument_token()
```

With:
```python
# Hardcoded NIFTY 50 token (update with your actual token from debug script)
self.nifty_token = 256265  # Replace with actual token
logger.info(f"Using hardcoded NIFTY token: {self.nifty_token}")
```

**Note:** The token may change, so this is only a temporary solution.

## 🐛 If Still Not Working

1. **Check the debug script output** - Does it show ANY index instruments?
2. **Check your Kite API subscription** - Ensure you have access to NSE/INDICES data
3. **Check market hours** - Some instruments may only appear during trading hours
4. **Try different exchange** - INDICES vs NSE

## 📞 Get the Token Manually

You can also get the instrument token from Kite's instrument dump:

1. Visit: `https://api.kite.trade/instruments`
2. Search for "NIFTY 50" or "Nifty 50"
3. Note the `instrument_token` value
4. Use Option A above to add it to `.env`

## ✅ Verification

Once fixed, you should see in the logs:
```
INFO - NIFTY 50 instrument found: NIFTY 50 (token: 256265)
INFO - Subscribed to instrument: 256265
INFO - Strategy initialized successfully
```

---

**Most likely solution**: Run `python debug_instruments.py` to see the exact instrument name, then the updated code should find it automatically.
