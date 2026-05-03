# Quick Start Guide

Get your NIFTY50 trading system up and running in 5 minutes!

## 🚀 Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
cd StopLossTrading
pip install -r requirements.txt
```

**Having installation issues?** See [INSTALLATION_TROUBLESHOOTING.md](INSTALLATION_TROUBLESHOOTING.md)

### Step 2: Get Kite Connect API Credentials

1. Go to https://developers.kite.trade/
2. Sign up for Kite Connect API (₹2000/month)
3. Create a new app
4. Note down your **API Key** and **API Secret**

### Step 3: Configure Your System

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file:
   ```bash
   nano .env  # or use any text editor
   ```

3. Add your credentials:
   ```env
   KITE_API_KEY=your_actual_api_key
   KITE_API_SECRET=your_actual_api_secret
   ```

### Step 4: Run the System

```bash
python main.py
```

### Step 5: First-Time Authentication

1. System will open your browser for Zerodha login
2. Login with your Zerodha credentials
3. After login, you'll be redirected to a URL like:
   ```
   http://127.0.0.1/?request_token=ABC123XYZ&action=login&status=success
   ```
4. Copy the `request_token` value (ABC123XYZ)
5. Paste it in the terminal when prompted
6. System will generate and save an access token

### Step 6: Start Trading

1. System shows IDLE state with live NIFTY price
2. Press **ENTER** when you want to designate the entry candle
3. Wait for 1-minute candle to close
4. System automatically monitors for breakout
5. When breakout occurs, system executes the trade
6. Dashboard shows live P&L
7. Position auto-exits on target/SL/EOD

## 📊 Trading Workflow

```
Press ENTER → Wait 1 min → Breakout → Auto Trade → Monitor → Auto Exit → Repeat
```

## ⚠️ Important First-Time Notes

### Before Live Trading:

1. **Paper Trade First**: Use demo account or small positions
2. **Check Margin**: Ensure sufficient funds in your account
3. **Verify Lot Size**: Confirm NIFTY lot size in `.env` (currently 65)
4. **Test Connection**: Ensure stable internet
5. **Understand Risk**: Read the strategy section in README.md

### Market Hours

- System only operates during: **9:15 AM - 3:30 PM IST**
- Auto-closes positions at: **3:15 PM**
- Late entry warning after: **3:00 PM**

## 🎯 Example Trade Flow

### Scenario: Call Option Trade

```
10:30:15 AM - Press ENTER (Designate Entry Candle)
            → Entry Candle: 10:30:00 to 10:31:00 (current candle)
            → System waits 45 seconds for candle to close

10:31:00 AM - Candle closes: High=22,550 | Low=22,530
            → Start monitoring for breakout

10:31:30 AM - NIFTY=22,551 (Breakout above High!)
            → System finds ITM Call: 22500CE (1 strike below spot)
            → Checks margin: ✓ OK
            → Places buy order: 2 lots (130 units)
            → Order filled at ₹180 (ITM options cost more)
            → SL: ₹170 | Target: ₹200

10:45:00 AM - Price hits ₹200 (Target!)
            → Auto-exit at ₹200
            → P&L: ₹2,600 profit
            → Trade logged to journal

Press ENTER to return to IDLE state
```

## 🛟 Quick Troubleshooting

### "Configuration errors: KITE_API_KEY is not set"
→ Edit `.env` file and add your API credentials

### "Authentication failed"
→ Check API Key/Secret are correct
→ Ensure request token is fresh (expires in minutes)

### "WebSocket connection timeout"
→ Check internet connection
→ System will retry automatically

### "Insufficient margin"
→ Add funds to your account
→ Reduce position size in strategy

### No NIFTY price showing
→ Ensure market is open (9:15 AM - 3:30 PM IST)
→ Check WebSocket connection in logs

## 📁 Important Files

- `trading_system.log` - All system events and errors
- `trading_journal.xlsx` - All your trades with P&L
- `.env` - Your configuration (keep this secret!)
- `access_token.txt` - Cached access token

## 🔄 Daily Usage

Access tokens expire daily. You'll need to:
1. Re-authenticate each day
2. OR: Implement automatic token refresh (advanced)

The system will prompt you when re-authentication is needed.

## 📞 Need Help?

1. Check `trading_system.log` for detailed error messages
2. Read the full README.md for comprehensive documentation
3. Verify your configuration in `.env`
4. Check Kite Connect API status: https://kite.trade/docs/connect/v3/

## 🎉 You're Ready!

You now have a fully functional algorithmic trading system. 

**Remember**: Start small, test thoroughly, and never risk more than you can afford to lose!

---

**Happy Trading! 📈**
