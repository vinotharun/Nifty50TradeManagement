# Setup Instructions for New Users

## 🎯 What You Received

This is a complete algorithmic trading system for NIFTY50 options using Zerodha Kite Connect API.

## ⚠️ IMPORTANT - Read First

- **This system trades REAL MONEY** - Use with extreme caution
- **Test in paper trading mode first** if possible
- **Start with minimum positions** when going live
- **Never risk more than you can afford to lose**
- **Monitor actively** - Don't leave unattended
- The provider of this code is **NOT responsible** for any financial losses

## 📋 Prerequisites

1. **Python 3.8 or higher**
   - Windows: Download from https://python.org
   - Mac: Usually pre-installed, or use `brew install python3`
   - Linux: `sudo apt install python3 python3-pip`

2. **Zerodha Trading Account**
   - Active Zerodha account with funds
   
3. **Kite Connect API Subscription**
   - Subscribe at https://developers.kite.trade/ (₹2000/month)
   - Create a new app to get API Key and Secret

4. **Stable Internet Connection**

## 🚀 Quick Setup (5 Minutes)

### Step 1: Extract/Download the Code

If you received a ZIP file:
```bash
unzip StopLossTrading.zip
cd StopLossTrading
```

If you received a GitHub link:
```bash
git clone [GITHUB_URL]
cd [FOLDER_NAME]
```

### Step 2: Install Dependencies

**Mac/Linux:**
```bash
pip3 install -r requirements.txt
```

**Windows:**
```cmd
pip install -r requirements.txt
```

**Having issues?** See `INSTALLATION_TROUBLESHOOTING.md`

### Step 3: Configure Your Credentials

1. Copy the example config:
   ```bash
   # Mac/Linux
   cp .env.example .env
   
   # Windows
   copy .env.example .env
   ```

2. Edit `.env` file:
   ```bash
   # Mac/Linux
   nano .env
   
   # Windows
   notepad .env
   ```

3. Add your credentials:
   ```env
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   NIFTY_INSTRUMENT_TOKEN=256265
   ```

4. Save and close

### Step 4: Run the System

```bash
# Mac/Linux
python3 main.py

# Windows
python main.py
```

### Step 5: First-Time Authentication

1. Browser will open for Zerodha login
2. Login with your credentials
3. Copy the `request_token` from redirect URL
4. Paste in terminal when prompted
5. Access token will be saved for future use

### Step 6: Start Trading

Once you see the IDLE state:
- Press **ENTER** to designate entry candle
- System will automatically monitor and trade
- Press **Ctrl+C** to stop system

## 📚 Documentation

Read these before using:

1. **QUICKSTART.md** (Mac/Linux) or **QUICKSTART_WINDOWS.md** (Windows)
   - Detailed setup guide
   - Example trade walkthrough
   
2. **README.md**
   - Complete system documentation
   - Strategy explanation
   - Safety features

3. **ENTRY_CANDLE_EXPLAINED.md**
   - How the entry candle logic works
   
4. **INSTALLATION_TROUBLESHOOTING.md**
   - Solutions for common installation issues

## ⚙️ Configuration

You can customize in `.env` file:

```env
NIFTY_LOT_SIZE=65                    # Lot size (verify current value)
EOD_CLOSE_TIME=15:15:00              # Auto-close time
LATE_ENTRY_WARNING_TIME=15:00:00    # Warning threshold
MARKET_START_TIME=09:15:00           # Market open
MARKET_END_TIME=15:30:00             # Market close
DASHBOARD_REFRESH_RATE=1             # Seconds
```

## 📊 Generated Files

When you run the system:
- `trading_system.log` - All events and errors
- `trading_journal.xlsx` - Trade history (Excel format)
- `access_token.txt` - Cached access token

## 🛡️ Safety Features

The system includes:
- ✅ Pre-trade margin validation
- ✅ Late entry warning (after 3 PM)
- ✅ Auto-close at 3:15 PM
- ✅ Risk-based position sizing
- ✅ Stop-loss and target management
- ✅ Complete trade logging

## 🐛 Troubleshooting

### System won't start
1. Check Python version: `python --version` (need 3.8+)
2. Check dependencies installed: `pip list`
3. Check `.env` file has correct credentials
4. Check logs: `cat trading_system.log`

### NIFTY instrument not found
1. Run: `python debug_instruments.py`
2. Find NIFTY 50 token
3. Add to `.env`: `NIFTY_INSTRUMENT_TOKEN=[token]`

### Installation errors
See `INSTALLATION_TROUBLESHOOTING.md`

## 📞 Support

1. Check the log file: `trading_system.log`
2. Read the relevant documentation file
3. Search the error message online
4. Contact the person who provided this code

## ⚖️ Legal Disclaimer

This software is provided "AS IS" without warranty of any kind. The user assumes all responsibility and risk for the use of this software. The creators and distributors are not liable for any financial losses incurred.

Trading in stock markets involves substantial risk. Only trade with money you can afford to lose.

## ✅ Final Checklist Before Live Trading

- [ ] Python 3.8+ installed
- [ ] All dependencies installed successfully
- [ ] Kite Connect API subscription active
- [ ] `.env` configured with correct credentials
- [ ] System starts without errors
- [ ] Read and understood README.md
- [ ] Tested in paper trading mode (if available)
- [ ] Sufficient margin in trading account
- [ ] Stable internet connection
- [ ] Ready to monitor actively

---

**You're ready! Start with observation mode first, then small positions.** 📈

**Good luck and trade responsibly!** 🍀
