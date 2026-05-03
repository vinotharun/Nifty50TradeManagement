# Quick Start Guide - Windows

Get your NIFTY50 trading system up and running on Windows in 5 minutes!

## 🚀 Step-by-Step Setup

### Step 1: Install Python

1. Download Python 3.8 or higher from https://www.python.org/downloads/
2. **Important**: During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Install Python Dependencies

1. Open Command Prompt (cmd) or PowerShell
2. Navigate to the project folder:
   ```cmd
   cd StopLossTrading
   ```
3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

   **Having installation issues?** See [INSTALLATION_TROUBLESHOOTING.md](INSTALLATION_TROUBLESHOOTING.md)

### Step 3: Get Kite Connect API Credentials

1. Go to https://developers.kite.trade/
2. Sign up for Kite Connect API (₹2000/month)
3. Create a new app
4. Note down your **API Key** and **API Secret**

### Step 4: Configure Your System

1. Copy the example configuration:
   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` file using Notepad:
   ```cmd
   notepad .env
   ```

3. Add your credentials:
   ```env
   KITE_API_KEY=your_actual_api_key
   KITE_API_SECRET=your_actual_api_secret
   ```

4. Save and close Notepad

### Step 5: Run the System

```cmd
python main.py
```

### Step 6: First-Time Authentication

1. System will open your browser for Zerodha login
2. Login with your Zerodha credentials
3. After login, you'll be redirected to a URL like:
   ```
   http://127.0.0.1/?request_token=ABC123XYZ&action=login&status=success
   ```
4. Copy the `request_token` value (ABC123XYZ)
5. Paste it in the Command Prompt when prompted
6. System will generate and save an access token

### Step 7: Start Trading

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
            → System finds ATM Call: 22550CE
            → Checks margin: ✓ OK
            → Places buy order: 2 lots (130 units)
            → Order filled at ₹150
            → SL: ₹142 | Target: ₹166

10:45:00 AM - Price hits ₹166 (Target!)
            → Auto-exit at ₹166
            → P&L: ₹2,080 profit
            → Trade logged to journal
         
Press ENTER to return to IDLE state
```

## 🛟 Quick Troubleshooting

### "python is not recognized as an internal or external command"
→ Python not in PATH. Reinstall Python and check "Add Python to PATH"
→ Or use full path: `C:\Python39\python.exe main.py`

### "Configuration errors: KITE_API_KEY is not set"
→ Edit `.env` file and add your API credentials
→ Make sure there are no extra spaces

### "Authentication failed"
→ Check API Key/Secret are correct
→ Ensure request token is fresh (expires in minutes)

### "WebSocket connection timeout"
→ Check internet connection
→ Check Windows Firewall settings
→ System will retry automatically

### "Insufficient margin"
→ Add funds to your account
→ Reduce position size in strategy

### No NIFTY price showing
→ Ensure market is open (9:15 AM - 3:30 PM IST)
→ Check WebSocket connection in logs

### Terminal/Command Prompt closes immediately
→ Run from Command Prompt (don't double-click main.py)
→ Open cmd, navigate to folder, then run `python main.py`

## 📁 Important Files

- `trading_system.log` - All system events and errors
- `trading_journal.xlsx` - All your trades with P&L (open with Excel)
- `.env` - Your configuration (keep this secret!)
- `access_token.txt` - Cached access token

## 💡 Windows-Specific Tips

### Using Virtual Environment (Recommended)

1. Create virtual environment:
   ```cmd
   python -m venv venv
   ```

2. Activate virtual environment:
   ```cmd
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

4. Run the system:
   ```cmd
   python main.py
   ```

5. Deactivate when done:
   ```cmd
   deactivate
   ```

### Running in PowerShell

If using PowerShell instead of Command Prompt:

1. You may need to enable script execution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. Activate virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

### Opening Files in Windows

- Edit `.env`: `notepad .env`
- View logs: `notepad trading_system.log`
- View journal: Open `trading_journal.xlsx` in Microsoft Excel

### Windows Defender / Firewall

If you get connection issues:
1. Allow Python through Windows Firewall
2. Allow Python through Windows Defender
3. Or temporarily disable for testing (not recommended for long-term)

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

You now have a fully functional algorithmic trading system on Windows.

**Remember**: Start small, test thoroughly, and never risk more than you can afford to lose!

---

**Happy Trading! 📈**

*Tested on: Windows 10, Windows 11*
