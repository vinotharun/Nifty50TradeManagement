# Quick Fix: NIFTY Instrument Token

## ✅ You Found It!

NIFTY 50 Token: **256265**

## 🚀 Two Ways to Fix

### Option 1: Auto-Detection (Try First)

The updated code should now find it automatically. Just run:

```bash
python main.py
```

The system will search for "NIFTY 50" in the INDICES exchange and find token 256265.

---

### Option 2: Manual Configuration (If Option 1 Fails)

Add the token to your `.env` file:

**Step 1:** Open `.env` file
```bash
nano .env
# or
notepad .env  # Windows
```

**Step 2:** Add or update this line:
```env
NIFTY_INSTRUMENT_TOKEN=256265
```

**Step 3:** Save and run:
```bash
python main.py
```

---

## 🎯 What Changed

The system now:
1. ✅ Checks `.env` for manual token first
2. ✅ Searches INDICES exchange (more reliable for indices)
3. ✅ Looks for exact match "NIFTY 50"
4. ✅ Falls back to NSE if INDICES unavailable
5. ✅ Tries multiple name variations

---

## ✅ Verify It Worked

After running `python main.py`, check the logs:

```bash
tail -20 trading_system.log
```

You should see:
```
INFO - ✓ NIFTY 50 instrument found: 'NIFTY 50' (token: 256265)
INFO - Subscribed to instrument: 256265
INFO - Strategy initialized successfully
```

---

## 🎉 Ready to Trade!

Once you see "Strategy initialized successfully", the system is ready and will:
1. Show IDLE state with live NIFTY price
2. Wait for you to press ENTER
3. Start the trading workflow

---

**Most likely**: The updated code will find it automatically (Option 1). If not, use Option 2 with the manual token.
