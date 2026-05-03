# NIFTY50 Algorithmic Trading System

A production-ready, fully automated trading system for NIFTY50 index options using a breakout-based strategy with Zerodha's Kite Connect API.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Quick Start Guides](#quick-start-guides)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Strategy Details](#strategy-details)
- [Troubleshooting](#troubleshooting)
- [Logging & Monitoring](#logging--monitoring)
- [Safety & Risk Management](#safety--risk-management)

## 🚀 Quick Start Guides

**New to the system? Start here:**

- **Mac/Linux Users**: See [QUICKSTART.md](QUICKSTART.md)
- **Windows Users**: See [QUICKSTART_WINDOWS.md](QUICKSTART_WINDOWS.md)

These guides will get you up and running in 5 minutes!

## 🎯 Overview

This system implements a fully automated breakout trading strategy for NIFTY50 index options. It monitors live market data, detects breakouts from a user-designated entry candle, and executes trades with predefined stop-loss and target levels.

### Key Features

- ✅ Real-time market data via WebSocket
- ✅ Automated breakout detection
- ✅ Dynamic ATM option selection
- ✅ Risk-based position sizing
- ✅ Live P&L tracking with rich terminal dashboard
- ✅ Automated stop-loss and target management
- ✅ End-of-day position auto-closure
- ✅ Comprehensive trade journaling
- ✅ Robust error handling and auto-reconnect

## 💻 System Requirements

- Python 3.8 or higher
- Active Zerodha trading account
- Kite Connect API subscription
- Stable internet connection
- Terminal with color support (for rich UI)

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
cd StopLossTrading
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Configuration

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

## ⚙️ Configuration

Edit the `.env` file with your credentials and preferences:

```env
# Zerodha Kite Connect API Credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here

# Trading Configuration
NIFTY_LOT_SIZE=65
EOD_CLOSE_TIME=15:15:00
LATE_ENTRY_WARNING_TIME=15:00:00
MARKET_START_TIME=09:15:00
MARKET_END_TIME=15:30:00

# Dashboard Refresh Rate (seconds)
DASHBOARD_REFRESH_RATE=1
```

### Getting Kite Connect API Credentials

1. Visit [Kite Connect](https://developers.kite.trade/)
2. Sign up for API access (₹2000/month)
3. Create a new app
4. Copy your API Key and API Secret

## 📖 Usage

### Starting the System

```bash
python main.py
```

### First-Time Authentication

On first run, the system will:
1. Open your browser for Zerodha login
2. Ask you to paste the request token from the redirect URL
3. Generate and save an access token for future use

### System Workflow

1. **Idle State**: System monitors live NIFTY50 price
   - Press **ENTER** to designate the **current 1-minute candle that is forming** as "Entry Candle"
   - Example: Press ENTER at 10:30:15 → Entry Candle = 10:30:00 to 10:31:00

2. **Entry Candle**: Wait for the candle to close at the next minute boundary
   - System records the High and Low of the candle from all ticks received

3. **Breakout Monitoring**: System watches for price breakout
   - **Breakout Above High** → Buy ATM Call Option
   - **Breakout Below Low** → Buy ATM Put Option

4. **Position Active**: Real-time dashboard shows:
   - Current P&L
   - Entry/Current/Target/Stop-Loss prices
   - Return percentage

5. **Auto Exit** when:
   - Target is hit (2x risk-reward)
   - Stop-loss is hit
   - 3:15 PM (EOD close time)

6. **Trade Summary**: Displays final results and logs to journal

7. Return to **Idle State** for next trade

### Keyboard Commands

- **ENTER** (Idle): Designate entry candle
- **M** (Position Active): Modify stop-loss *(planned feature)*
- **Q** (Position Active): Force exit *(planned feature)*
- **Ctrl+C**: Stop system

## 📊 Strategy Details

### Breakout Logic

```
Entry Candle: [High: 22,550 | Low: 22,530]

CALL Trigger: Spot Price > 22,550 → Buy ATM Call
PUT Trigger: Spot Price < 22,530 → Buy ATM Put
```

### Position Sizing (Based on Risk Points)

```
Risk Points = |Entry Price - Stop Loss Price|

If Risk Points > 10  → 1 Lot
If Risk Points ≤ 10 and > 5 → 2 Lots  
If Risk Points ≤ 5  → 3 Lots
```

### Stop Loss & Target

```
For CALL:
  SL (Index) = Entry Candle Low - 1
  Target = Entry Price + (Risk Points × 2)

For PUT:
  SL (Index) = Entry Candle High + 1  
  Target = Entry Price + (Risk Points × 2)
```

Risk-to-Reward Ratio: **1:2**

## 🔍 Troubleshooting

### WebSocket Connection Issues

- Check your internet connection
- System auto-reconnects up to 5 times
- If persistent, restart the system

### Authentication Errors

- Verify API Key and Secret in `.env`
- Check if access token has expired (re-login required daily)
- Ensure API subscription is active

### Order Placement Failures

- Check available margin
- Verify market hours (9:15 AM - 3:30 PM IST)
- Check if instrument is available for trading
- Review `trading_system.log` for detailed errors

### No NIFTY Price Updates

- Ensure market is open
- Check WebSocket connection status
- Verify instrument token is correct

## 📝 Logging & Monitoring

### Log File

All events are logged to `trading_system.log`:
- Authentication events
- Order placements and executions
- Entry/Exit signals
- Errors and exceptions

### Trading Journal

All trades are automatically recorded in `trading_journal.xlsx` with:
- Serial Number
- Date & Time
- Entry Candle High/Low
- Breakout Direction
- Option Details (Type, Strike)
- Entry/Exit Prices
- Stop Loss & Target
- Exit Reason
- P&L and Return %

## 🛡️ Safety & Risk Management

### Built-in Safety Features

1. **Margin Validation**: Checks available margin before placing orders
2. **Late Entry Warning**: Warns if entering trade after 3:00 PM
3. **EOD Auto-Close**: Automatically closes positions at 3:15 PM
4. **Error Handling**: Comprehensive error handling with graceful fallbacks
5. **Position Limits**: Risk-based position sizing prevents over-leveraging

### Risk Warnings

⚠️ **IMPORTANT DISCLAIMERS:**

- This is a trading system that involves real financial risk
- Past performance does not guarantee future results
- Always test in paper trading mode first
- Never risk more than you can afford to lose
- Monitor your positions actively
- Understand the strategy before deploying
- Options trading involves significant risk
- The developers are not responsible for any financial losses

### Recommended Practices

1. **Start Small**: Begin with minimum position sizes
2. **Paper Trade First**: Test the system thoroughly without real money
3. **Monitor Actively**: Don't leave the system completely unattended
4. **Set Account Limits**: Use broker's risk management features
5. **Review Logs**: Regularly check logs and journal for issues
6. **Backup Strategy**: Have manual intervention capabilities
7. **Internet Backup**: Ensure stable internet or have mobile backup

## 📂 Project Structure

```
StopLossTrading/
├── main.py                 # Entry point
├── config.py               # Configuration management
├── auth.py                 # Kite authentication
├── data_stream.py          # WebSocket data streaming
├── strategy.py             # Core strategy logic
├── order_manager.py        # Order placement & management
├── dashboard.py            # Terminal UI
├── utils.py                # Helper functions
├── requirements.txt        # Python dependencies
├── .env.example            # Configuration template
├── .env                    # Your configuration (create this)
├── README.md               # This file
├── trading_system.log      # Generated log file
├── trading_journal.xlsx    # Generated trade journal
└── access_token.txt        # Generated access token cache
```

## 🔄 System Flow

```
START
  ↓
[Authentication]
  ↓
[Initialize WebSocket]
  ↓
[IDLE STATE]
  ← Wait for ENTER
  ↓
[Entry Candle Designation]
  ← Wait 1 minute for candle close
  ↓
[Breakout Monitoring]
  ├─→ No breakout → Continue monitoring
  ├─→ EOD time → Return to IDLE
  └─→ Breakout detected
      ↓
[Execute Trade]
  ├─→ Find ATM option
  ├─→ Check margin
  ├─→ Place order
  └─→ Wait for fill
      ↓
[Position Active]
  ├─→ Monitor price
  ├─→ Update dashboard
  └─→ Check exit conditions
      ↓
[Exit Position]
  ├─→ Target hit / SL hit / EOD
  ├─→ Place exit order
  ├─→ Log to journal
  └─→ Show summary
      ↓
[Return to IDLE]
```

## 🐛 Known Limitations

1. **User Input**: Dashboard refresh currently blocks user input for M/Q commands (can be enhanced with async input)
2. **Stop Loss Calculation**: Uses simplified approach; can be enhanced with option Greeks
3. **Single Position**: Currently supports one position at a time
4. **Order Types**: Only market orders are supported
5. **Manual Intervention**: Limited manual control during active positions

## 🔮 Future Enhancements

- [ ] Non-blocking keyboard input for dashboard
- [ ] Multiple position support
- [ ] Option Greeks-based SL calculation
- [ ] Historical backtesting module
- [ ] Telegram/Email notifications
- [ ] Advanced order types (limit, stop-loss orders)
- [ ] Performance analytics dashboard
- [ ] Multi-strategy support
- [ ] Mobile app integration

## 📞 Support

For issues or questions:
1. Check the log file: `trading_system.log`
2. Review this README
3. Verify your configuration
4. Check Zerodha API documentation: https://kite.trade/docs/connect/v3/

## 📄 License

This project is for educational and personal use only. Use at your own risk.

## 🙏 Acknowledgments

- Zerodha for Kite Connect API
- Python community for excellent libraries
- All contributors and testers

---

**Happy Trading! 📈**

*Remember: Trade responsibly and never risk more than you can afford to lose.*

