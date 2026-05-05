# NIFTY50 Algorithmic Trading System - Implementation Specification

## Role
Act as an expert quantitative developer and algorithmic trading specialist for NIFTY50 index options trading.

## Objective
Create a production-ready, fully documented trading script in Python to execute a breakout-based options trading strategy on the Nifty50 Index using Zerodha's Kite Connect API.

---

## Architecture
- **Code Structure**: Modular architecture (separate modules for authentication, data streaming, strategy logic, order management, UI/dashboard)
- **Concurrency Model**: Hybrid approach (Threading for blocking operations + Asyncio for network I/O)
- **User Input Handling**: Background threads for non-blocking keyboard input during dashboard refresh
- **Configuration**: Use `.env` file for API credentials (API Key, API Secret)
- **UI/Dashboard**: Use libraries like `rich` or `curses` for professional terminal formatting with clean screen refresh

---

## Core Strategy Logic

### 0. Capital Setup (At Startup)
**Before any trading begins**, immediately after system starts, prompt user for trading capital:

- **Prompt**: "Enter your trading capital"
- **Validation**:
  1. Must be ≥ ₹1,00,000 (minimum)
  2. Must be ≤ Available Margin in Zerodha account
  3. If capital < ₹1,00,000 → Show error: "This system works only for capital above ₹1,00,000"
  4. If capital > Available Margin → Show error: "Capital exceeds available margin. Enter lower amount or add funds"
- **Floor to nearest ₹1,00,000**: If user enters ₹5,50,000 → Floor to ₹5,00,000
- **Capital Multiplier**: Calculate multiplier = capital / 100000
  - ₹1,00,000 → 1x multiplier
  - ₹5,00,000 → 5x multiplier
  - ₹10,00,000 → 10x multiplier
- **User Options**:
  - Enter valid capital → Proceed to Idle State
  - Type 'Q' → Exit trading system
- **Display**: Show capital, multiplier, and quantity impact
- **Quantity Logic**: All lot calculations are multiplied by capital_multiplier
  - Base system designed for ₹1,00,000 capital
  - If ₹5,00,000 entered → Quantity = 5x base calculation

**Example Flow**:
```
Enter your trading capital: 550000
⚠️  Capital adjusted: ₹5,50,000 → ₹5,00,000
✓ Trading Capital Set: ₹5,00,000
✓ Capital Multiplier: 5x
  (Quantity will be 5x the base calculation)
```

### 1. Idle State (Monitoring Phase)
- Run continuously and monitor live Nifty50 spot price via **Kite Connect WebSocket ticks**
- Display current Nifty50 spot price in real-time
- Execute no trades
- Wait for user to press the **Enter key**
- **Market Hours**: System should only operate during market hours (9:15 AM - 3:30 PM IST)
- Handle daily session re-authentication automatically when access tokens expire

### 1.5 Entry Candle Selection
**After user presses Enter**, prompt for entry candle choice:

- **Option 1: Current Candle** (In Progress)
  - Use the current 1-minute candle that is forming
  - Clock-aligned (e.g., if Enter pressed at 10:30:15, Entry Candle = 10:30:00 to 10:31:00)
  - Must wait for candle to fully close at next minute boundary
  - Includes current price action

- **Option 2: Previous Candle** (Already Closed)
  - Use the previous 1-minute candle (already completed)
  - Example: If Enter pressed at 10:30:15, Entry Candle = 10:29:00 to 10:30:00
  - No waiting required - fetch data immediately
  - Instant transition to breakout monitoring

**Special Cases:**
- **First Candle of Day (9:15 AM)**: Previous candle option NOT available
  - Show error: "Market just opened (first candle of the day). No previous candle exists."
  - Force user to select Current Candle
- **Any other time**: Both options available

**Display Format:**
```
Choose Entry Candle:

[1] Current Candle (10:30:00 - 10:31:00)
    - Status: In progress (15 seconds elapsed)
    - Wait time: 45 seconds until close
    - Includes current price action

[2] Previous Candle (10:29:00 - 10:30:00)
    - Status: Already closed
    - Wait time: None (instant)
    - Historical data available immediately

Enter your choice (1/2): _
```

### 1.6 Direction Selection
- After entry candle selection, prompt for trading direction
- User chooses:
  - **C** for CALL (monitor for breakout ABOVE entry candle high)
  - **P** for PUT (monitor for breakout BELOW entry candle low)
- Display chosen direction clearly
- This determines which breakout to monitor for

### 2. Entry Candle Data Collection
- **For Current Candle**: Wait for candle to close, then fetch data
- **For Previous Candle**: Fetch data immediately (already closed)
- **Fetch complete candle data** using Kite Connect **Historical Data API** to ensure accurate High/Low
  - This captures price action from the entire candle
  - Example: If using 10:30-10:31 candle, API captures all ticks including before user action
  - **Note**: Do NOT pass `timeout` parameter to `historical_data()` - not supported by KiteConnect library
- Record the **High** and **Low** of the completed Entry Candle
- Display Entry Candle details: `High: XXXXX.XX | Low: XXXXX.XX`

**Error Handling & Fallback:**
- If Historical API fails, implement fallback to WebSocket tick data:
  - **For Current Candle**: Calculate High/Low from collected WebSocket ticks
  - **For Previous Candle**: No fallback available - must return to IDLE state
- Always validate data before proceeding:
  ```python
  if entry_candle_high is None or entry_candle_low is None:
      # Return to IDLE, show error message
  ```
- Handle API failures gracefully with helpful error messages

### 3. Breakout Monitoring (Directional)
Monitor live WebSocket ticks for breakout **ONLY in the chosen direction**:

- **If CALL chosen**: Monitor for breakout **above** Entry Candle High only
  - If price crosses above High → Trigger CALL trade
  - If price crosses below Low → **IGNORE** (wrong direction, continue monitoring)

- **If PUT chosen**: Monitor for breakout **below** Entry Candle Low only
  - If price crosses below Low → Trigger PUT trade
  - If price crosses above High → **IGNORE** (wrong direction, continue monitoring)

**User Controls During Monitoring:**
- Type **'Q'** and press **ENTER** to cancel monitoring and return to Idle State (manual cancellation)
- Non-blocking input: Background thread listens for 'Q' key while main thread refreshes dashboard
- If **EOD time** (3:15 PM) reached without breakout → Auto-return to Idle State
- **No timeout** - system monitors indefinitely until breakout, cancellation, or EOD

### 4. Option Selection & Order Execution

#### ITM (In-The-Money) Option Selection
- Determine ITM strike: **1 strike in the money** at the time of breakout
- Strike interval: **50 points** for NIFTY options
- **For CALL**: Strike price should be **one level below** current spot price
  - Example: If spot = 22,550 → CALL strike = 22,500
  - If spot = 22,525 (between strikes) → Round down to 22,500, then ITM = 22,450
- **For PUT**: Strike price should be **one level above** current spot price
  - Example: If spot = 22,550 → PUT strike = 22,600
  - If spot = 22,525 (between strikes) → Round up to 22,550, then ITM = 22,600

#### Expiry Selection Logic
- **Primary Rule**: Use nearest available expiry
- **Special Rule**: **If today is an expiry day**, skip today's expiry and use the **next available expiry**
  - Prevents taking positions that expire on the same day
  - Ensures sufficient time for trade to play out
  - Example: If today is Thursday (weekly expiry day), skip Thursday expiry, use next Thursday's expiry
- **Fallback**: If all options expire today (unlikely edge case), use nearest expiry
- Use Kite Connect's **instrument lookup/search API** to get exact trading symbols (e.g., `NIFTY26MAY23500CE`)

**Important: Handle Different Date Types**
- KiteConnect API may return `option['expiry']` as either:
  - `datetime.datetime` object (has `.date()` method)
  - `datetime.date` object (already a date, no `.date()` method)
- Always check type before calling `.date()`:
  ```python
  option_expiry = option['expiry']
  if hasattr(option_expiry, 'date'):
      option_expiry_date = option_expiry.date()  # datetime object
  else:
      option_expiry_date = option_expiry  # already date object
  ```

#### Trade Execution Logic

**Order Type: LIMIT Orders (Not Market)**
- Zerodha API does not allow pure market orders via API for risk protection
- Use **LIMIT orders with 2% buffer** for immediate execution:
  - **BUY**: Limit price = LTP × 1.02 (2% above last traded price)
  - **SELL**: Limit price = LTP × 0.98 (2% below last traded price)
- This ensures immediate execution while complying with API restrictions
- Typical slippage: 0.5-1% (acceptable for this strategy)

**For Path 1 (Call Option):**
```
1. Get current option LTP (Last Traded Price)
2. Calculate limit price = LTP × 1.02
3. Place LIMIT BUY order at calculated price
Stop Loss (SL) Price = Entry Candle Low - 1
Risk Points = Entry Price - SL Price
```

**For Path 2 (Put Option):**
```
1. Get current option LTP (Last Traded Price)
2. Calculate limit price = LTP × 1.02
3. Place LIMIT BUY order at calculated price
Stop Loss (SL) Price = Entry Candle High + 1
Risk Points = SL Price - Entry Price
```

**Important**:
- "Entry Price" = **Option premium price** at which the order is filled
- "Risk Points" calculation uses the **option premium**, not the underlying index
- Use `kite.quote()` to get current LTP before placing order
- Round limit price to 1 decimal place for options pricing

#### Position Sizing (Based on Risk Points and Capital)
**Base Position Sizing (for ₹1,00,000 capital):**
- If Risk Points > 10: Buy **1 Lot**
- If Risk Points ≤ 10 and > 5: Buy **2 Lots**
- If Risk Points ≤ 5: Buy **3 Lots**

**Capital Multiplier Applied:**
- Final Lots = Base Lots × Capital Multiplier
- Capital Multiplier = Capital / 100000
- Examples:
  - Capital ₹1,00,000 (1x): Base 2 lots → Final 2 lots
  - Capital ₹5,00,000 (5x): Base 2 lots → Final 10 lots
  - Capital ₹10,00,000 (10x): Base 2 lots → Final 20 lots

**Configuration**: Lot size for Nifty50 options = **65** (should be configurable in code)

#### Target Calculation
- Target Price = Entry Price + (Risk Points × 3)
  - For Call: Entry Price + (Risk Points × 3)
  - For Put: Entry Price + (Risk Points × 3)
- Risk-to-Reward Ratio: **1:3**
- Note: Target can be modified by user during active position

#### Pre-Order Validations
1. **Margin Check**: Verify available margin before placing order
2. **Time Warning**: If order is being placed **post 3:00 PM**, display warning:
   ```
   ⚠️  WARNING: Position will auto-close at 3:15 PM. Continue? (y/n)
   ```
   Only proceed after user confirmation
3. **Error Handling**: If order placement fails, display the error message clearly

---

## 5. Breakout Monitoring Dashboard

### Dashboard Display During Monitoring (Refresh every 1 second)
```
═══════════════════════════════════════════════════
         MONITORING [CALL/PUT] BREAKOUT
═══════════════════════════════════════════════════
Entry Candle (HH:MM:00 - HH:MM:00):
  High: XX,XXX.XX
  Low:  XX,XXX.XX

Direction       : [CALL / PUT]
Breakout Trigger: Price [> / <] XX,XXX.XX
Current NIFTY   : XX,XXX.XX

⏳ Waiting for [CALL/PUT] breakout...
═══════════════════════════════════════════════════
Type 'Q' and press ENTER to cancel monitoring
═══════════════════════════════════════════════════
```

**Note:** The 'Q' input is handled by a background thread, so the dashboard can continue refreshing without clearing user input.

## 6. Active Position Monitoring & Live Dashboard

### Dashboard Display After Trade Execution (Refresh every 1 second)
```
═══════════════════════════════════════════════════
         ACTIVE POSITION DASHBOARD
═══════════════════════════════════════════════════
Direction       : [CALL / PUT]
Quantity Open   : [X Lots (XXX units)]
Entry Price     : ₹ 00000.00
Current Price   : ₹ 00000.00
Stop Loss       : ₹ 00000.00
Target          : ₹ 00000.00
Return %        : [+X.XX% / -X.XX%]
P&L (Unrealized): ₹ +XXXX.XX / -XXXX.XX
═══════════════════════════════════════════════════
'M' + ENTER: Modify Stop Loss | 'T' + ENTER: Modify Target | 'Q' + ENTER: Force Exit
═══════════════════════════════════════════════════
```

**Note:** The 'M', 'T', and 'Q' inputs are handled by a background thread, so the dashboard can continue refreshing without clearing user input.

### Monitoring Logic (Breakout Phase)
- **Price Source**: Monitor NIFTY spot price via WebSocket
- **Direction Check**: Only trigger trade if breakout occurs in chosen direction
- **Wrong Direction**: Silently ignore breakouts in opposite direction, continue monitoring
- **Dashboard Refresh**: Update every 1 second with current NIFTY price
- **User Controls**: Non-blocking 'Q' key detection for manual cancellation
  - Background thread: `_keyboard_listener()` runs separately from main loop
  - Listens for 'Q' + ENTER input continuously
  - Sets `cancel_monitoring` flag when Q is pressed
  - Main thread checks flag each iteration and exits cleanly
- **EOD Check**: Auto-return to Idle if 3:15 PM reached without breakout

### Monitoring Logic (Active Position)
- **Price Source**: Monitor option premium price via WebSocket (subscribe to the traded option instrument)
- **SL/Target Monitoring**: Based on **option premium price**, not underlying Nifty50
- **Dashboard Refresh**: Clear screen and update every 1 second
- **User Controls**: Non-blocking 'M', 'T', and 'Q' key detection
  - Background thread: `_position_keyboard_listener()` runs separately from main loop
  - Listens for 'M', 'T', or 'Q' + ENTER input continuously
  - Sets `position_command` flag when M, T, or Q is pressed
  - Main thread checks flag each iteration:
    - **M** → Opens SL modification dialog
    - **T** → Opens Target modification dialog
    - **Q** → Forces immediate position exit

---

## 7. User Interactivity & Exit Conditions

### Manual Cancellation (During Breakout Monitoring)
- User types **'Q'** and presses **ENTER** → Cancel monitoring and return to Idle State
- Background thread captures input without blocking dashboard refresh
- Display confirmation message: "❌ Monitoring cancelled by user"
- No trade is executed
- System returns to Idle State

### Manual Stop Loss Modification (During Active Position)
- User types **'M'** and presses **ENTER** → Opens SL modification dialog
- Background thread captures input without blocking dashboard refresh
- Dialog displays:
  - Current Stop Loss price
  - Current option price
  - Direction (CALL/PUT)
- User enters new SL price (or ENTER to cancel)
- **Validation**:
  - **IMPORTANT**: We are BUYING options (LONG position) for both CALL and PUT
  - New SL must be **below** current price (for both CALL and PUT)
  - This protects against option premium dropping
  - When option price rises → profit; when it falls → loss (regardless of CALL/PUT)
  - Common use case: Trailing stop loss to lock in profits
  - Display error if invalid, allow retry
- Update `self.position['stop_loss']` immediately (with thread lock)
- Display confirmation: "✓ Stop Loss updated: ₹X → ₹Y"
- Return to position monitoring dashboard

**Conceptual Note:**
- Direction (CALL/PUT) affects which strike we select and when breakout triggers
- Direction does NOT affect option P&L behavior: we're always LONG the option
- For LONG positions: Option price UP = profit, DOWN = loss
- Therefore: Stop loss is always BELOW current price (same for CALL and PUT)

### Manual Target Modification (During Active Position)
- User types **'T'** and presses **ENTER** → Opens Target modification dialog
- Background thread captures input without blocking dashboard refresh
- Dialog displays:
  - Current Target price
  - Current option price
  - Entry price
  - Direction (CALL/PUT)
- User enters new Target price (or ENTER to cancel)
- **Validation**:
  - Target must be **above** entry price (for profit)
  - If target < current price: Show warning, ask for confirmation
  - Display error if invalid (target ≤ entry price)
- Update `self.position['target']` immediately
- Display confirmation: "✓ Target updated: ₹X → ₹Y"
- **Note**: This overrides the initial 1:3 risk-reward target calculation
- Return to position monitoring dashboard

### Manual Force Exit (During Active Position)
- User types **'Q'** and presses **ENTER** → Force immediate exit
- Background thread captures input without blocking dashboard refresh
- Display warning: "⚠️ FORCE EXIT requested by user"
- Execute market order to close position
- Display trade summary
- Return to Idle State

### Auto-Exit Conditions (Active Position)
1. **Target Hit**: Current option price reaches Target → Exit position
2. **Stop Loss Hit**: Current option price hits SL → Exit position
3. **End of Day**: Auto-close position at **3:15 PM** regardless of P&L

### Exit Summary
After exit, display trade summary:
```
═══════════════════════════════════════════════════
                   TRADE SUMMARY
═══════════════════════════════════════════════════
Direction       : [CALL / PUT]
Entry Price     : ₹ XXX.XX
Exit Price      : ₹ XXX.XX
Exit Reason     : [Target Hit / Stop Loss / EOD Close / Manual]
Total P&L       : ₹ +XXXX.XX / -XXXX.XX
Return %        : +X.XX% / -X.XX%
═══════════════════════════════════════════════════
Press Enter to return to Idle State...
═══════════════════════════════════════════════════
```

Return to **Idle State** (wait for new Enter keypress and new Entry Candle)

### Trading Journal
Record all entries in a trading journal for later analysis. It should be in a spreadsheet format with the following columns: Serial Number, Date, Entry Candle Type, Chosen Direction, Entry Candle High, Entry Candle Low, Breakout Direction, Option Type, Option Strike, Entry Price, Stop Loss, Target, Exit Price, Exit Reason, P&L, Return %

**Notes:**
- "Entry Candle Type" shows CURRENT or PREVIOUS
- "Chosen Direction" shows what user selected (CALL/PUT)
- "Breakout Direction" shows actual breakout that triggered the trade

---

## Technical Requirements

### 1. Authentication & Session Management
- Store API Key and API Secret in `.env` file
- Implement browser-based login flow:
  1. Open Zerodha login URL in browser
  2. User completes login and copies request token
  3. User pastes token back into terminal
  4. Generate and store access token
- Handle daily session expiry with automatic re-authentication prompt
- **IP Whitelist Requirement**: Add your IP address to Kite Developer Console
  - Go to https://developers.kite.trade/
  - Open your app settings
  - Add allowed IPs under "Allowed IPs" section
  - Required for API calls to work

### 2. Data Streaming
- Use **Kite Connect WebSocket (KiteTicker)** for:
  - Live Nifty50 spot price (instrument: NIFTY 50)
  - Live option premium prices after order execution
- Subscribe to relevant instrument tokens dynamically

### 3. Error Handling & Resilience
Follow industry best practices:
- **WebSocket Disconnect**: Auto-reconnect with exponential backoff (max 5 retries), alert user if fails
- **Network Errors**: Retry API calls (max 3 attempts), log errors, alert user
- **Order Failures**: Display exact error message from API, do not proceed
- **Invalid User Input**: Validate and prompt again

### 4. Logging
- Log all events to `trading_system.log`:
  - Authentication events
  - Entry candle detection
  - Direction selection (CALL/PUT)
  - Keyboard input events (Q, M commands)
  - Monitoring cancellations
  - Order placements (with order ID, price, quantity)
  - SL/Target modifications
  - Exit events with P&L
  - Errors and exceptions
- Use Python `logging` module with timestamps

### 5. Threading & Concurrency
- **Main Thread**: Strategy loop, dashboard updates, WebSocket handling
- **Keyboard Listener Threads**: Non-blocking input capture
  - `_keyboard_listener()`: Runs during WAITING_BREAKOUT state
  - `_position_keyboard_listener()`: Runs during POSITION_ACTIVE state
- **Thread Safety**: Use flags (`cancel_monitoring`, `position_command`) for communication
- **Clean Shutdown**: Daemon threads automatically terminate when main thread exits

---

## Deliverables

### 1. Code
- **Modular Python codebase** with clear separation of concerns:
  ```
  ├── main.py                 # Entry point
  ├── config.py               # Configuration loader (.env)
  ├── auth.py                 # Kite authentication
  ├── data_stream.py          # WebSocket ticker management
  ├── strategy.py             # Core strategy logic
  ├── order_manager.py        # Order placement & management
  ├── dashboard.py            # UI/Terminal dashboard
  ├── utils.py                # Helper functions
  ├── .env.example            # Template for credentials
  └── requirements.txt        # Dependencies
  ```

### 2. Documentation
- **Thorough docstrings** for all functions/classes (Google/NumPy style)
- **Inline comments** explaining complex logic
- **README.md** with:
  - Setup instructions
  - Configuration guide
  - Usage examples
  - Troubleshooting

### 3. Flow Diagrams
- **PNG Flowchart**: Visual diagram showing complete system flow (states, transitions, decision points)
- **Textual Pseudocode**: Step-by-step algorithm in comments/markdown

---

## Example Walkthrough

### Scenario 1: Successful CALL Trade

```
1. User presses Enter at 10:30:15 AM
2. System prompts: "Choose direction (C/P):"
3. User types: C (for CALL)
4. Entry Candle designated: 10:30:00 to 10:31:00 (current clock-aligned candle)
5. System waits 45 seconds for candle to close at 10:31:00
6. At 10:31:00, system fetches historical candle data via API
7. Entry Candle: High = 22,550 | Low = 22,530 (includes complete candle data)
8. Dashboard shows: "Monitoring CALL breakout (price > 22,550.00)"
9. At 10:31:30, Nifty50 spot = 22,551 → Breakout above High → Trigger CALL
10. System finds ITM Call: Spot = 22,551 → ATM = 22,550 → ITM = 22,500 CE (nearest expiry)
11. Market order placed, filled at ₹180.00 (Entry Price - ITM options cost more)
12. Calculate Stop Loss:
    - SL trigger: Entry Candle Low - 1 = 22,530 - 1 = 22,529
    - When Nifty spot reaches 22,529, estimate option price would be ~₹170
    - SL Price (option premium) = ₹170.00
13. Risk Points = Entry Price - SL Price = ₹180 - ₹170 = ₹10
14. Position Sizing: Risk Points = 10 (≤10 and >5) → Buy 2 Lots (2 × 65 = 130 units)
15. Target = Entry Price + (Risk Points × 2) = ₹180 + ₹20 = ₹200.00
16. Dashboard shows live updates every 1 second with current option price
17. At 11:00 AM, option price hits ₹200 → Auto-exit, sell at ₹200
18. P&L = (₹200 - ₹180) × 130 units = ₹2,600 profit
19. Display trade summary, return to Idle State
```

### Scenario 2: Wrong Direction Ignored

```
1. User presses Enter at 10:30:15 AM
2. User chooses: C (for CALL)
3. Entry Candle: High = 22,550 | Low = 22,530
4. Dashboard: "Monitoring CALL breakout (price > 22,550.00)"
5. At 10:32:00, Nifty50 spot = 22,528 → Breakout BELOW Low (PUT direction)
6. System IGNORES this breakout (wrong direction)
7. Dashboard continues: "Waiting for CALL breakout..." (no trade executed)
8. At 10:35:00, Nifty50 spot = 22,552 → Breakout ABOVE High (CALL direction)
9. Now CALL trade is triggered and executed
```

### Scenario 3: Manual Cancellation

```
1. User presses Enter at 10:30:15 AM
2. User chooses: P (for PUT)
3. Entry Candle: High = 22,550 | Low = 22,530
4. Dashboard: "Monitoring PUT breakout (price < 22,530.00)"
5. Price stays between 22,530 - 22,550 for several minutes
6. User decides to cancel, presses 'Q'
7. System: "Monitoring cancelled by user"
8. Return to Idle State, no trade executed
```

**Note on Stop Loss Calculation**: Since SL is defined in terms of the underlying index (Entry Candle Low - 1 for CALL, High + 1 for PUT), but monitoring happens on option premium, the system uses:
- **Simplified approach**: Monitor option premium price for SL/Target hits
- Risk Points are calculated based on option premium at entry
- This approach is practical and avoids complexity of real-time Greeks calculation
- The option premium naturally reflects the underlying index movement

---

## Critical Implementation Details

### Stop Loss & Target Monitoring Strategy
Since the strategy defines SL based on the underlying index (Entry Candle High/Low ± 1) but trades options, implement the following approach:

**At Entry Time**:
1. Record Entry Candle High/Low
2. Calculate index-based SL trigger level (Entry Candle Low - 1 for Call, High + 1 for Put)
3. Record option Entry Price (filled premium)
4. Monitor current option premium in real-time

**During Position Monitoring**:
- **Primary Method**: Monitor the **option premium price** for SL/Target hits
- **Risk Calculation**: Since "Risk Points" is defined as the difference in option premium (Entry Price - SL Price), this is already in premium terms
- **Important**: The SL is calculated at entry based on option premium at that moment, NOT the index points

**Practical Example**:
```
Entry Candle: High = 22,550, Low = 22,530
Breakout at 22,551 → Buy Call at premium ₹150
SL in premium terms = ₹150 - Risk Points (you determine risk based on position sizing)
Risk Points guide lot size, but actual SL monitoring is on option premium
Target = Entry Premium + (Risk Points × 2)
```

**Alternative Interpretation** (if you prefer index-based SL):
Monitor Nifty50 index price. When index crosses Entry Candle Low - 1, exit the option position at market price. This is simpler but may result in different P&L than premium-based SL.

**Recommendation**: Clarify with your trading plan which approach you prefer. The prompt currently specifies premium-based monitoring per your answer to question #4.

---

## Key Implementation Details

### Non-Blocking Keyboard Input Implementation
The system uses **background threads** to handle keyboard input without blocking dashboard refresh:

**During Breakout Monitoring:**
```python
def _keyboard_listener(self):
    """Listen for Q key in separate thread"""
    while self.state == TradingState.WAITING_BREAKOUT:
        key = input()  # Blocks in this thread only
        if key.upper() == 'Q':
            self.cancel_monitoring = True
            break

# In main loop:
if self.cancel_monitoring:
    # Cancel monitoring and return to IDLE
```

**During Active Position:**
```python
def _position_keyboard_listener(self):
    """Listen for M/Q keys in separate thread"""
    while self.state == TradingState.POSITION_ACTIVE:
        key = input()  # Blocks in this thread only
        if key.upper() in ['M', 'Q']:
            self.position_command = key.upper()
            break

# In main loop:
if self.position_command == 'M':
    # Open SL modification dialog
elif self.position_command == 'Q':
    # Force exit position
```

**Benefits:**
- Dashboard refreshes every second without clearing user input
- User can type commands at any time
- Clean separation between UI updates and input handling
- No race conditions with proper flag management

### Entry Candle Data Collection
The system uses **Kite Connect Historical Data API** (`kite.historical_data()`) to fetch complete candle data after the candle closes. This ensures:
- Accurate High/Low from the entire 1-minute candle
- Data includes price action from BEFORE user pressed Enter
- Matches exactly what traders see on charts
- Fallback to WebSocket ticks if API fails

### ITM Strike Calculation
```python
# Example implementation logic:
spot_price = 22,525  # Current NIFTY spot

# For CALL (1 strike below spot):
atm_strike = round(spot_price / 50) * 50  # 22,550
itm_call_strike = atm_strike - 50  # 22,500

# For PUT (1 strike above spot):
atm_strike = round(spot_price / 50) * 50  # 22,550
itm_put_strike = atm_strike + 50  # 22,600
```

### NIFTY Instrument Token
The system can auto-detect the NIFTY 50 instrument token from INDICES/NSE exchange, or use a manually configured token from `.env` file:
```env
NIFTY_INSTRUMENT_TOKEN=256265  # Optional: Set if auto-detection fails
```

## Dependencies (Suggested)
```
kiteconnect>=4.0.0,<6.0.0
python-dotenv>=1.0.0
rich>=13.0.0 (for terminal UI with colors, tables, panels)
asyncio (standard library - for WebSocket async operations)
threading (standard library - for non-blocking keyboard input)
select (standard library - for Unix/Mac input detection)
sys (standard library - for stdin handling)
pandas>=2.0.0 (for data handling and trading journal)
openpyxl>=3.1.0 (for Excel export)
pytz>=2023.3 (for timezone management)
```

---

## Code Quality & Security

### Thread Safety Requirements

**Critical: All shared state MUST use threading locks**

The system uses multiple threads:
- **WebSocket Thread**: Updates prices and position data via callbacks
- **Main Thread**: Reads prices for decision-making and display
- **Keyboard Listener Threads**: Capture user input

**Thread Safety Implementation:**

```python
class Strategy:
    def __init__(self):
        # Required locks
        self.price_lock = threading.Lock()      # Protects current_nifty_price
        self.position_lock = threading.Lock()   # Protects position dictionary
```

**Required Patterns:**

1. **Price Updates (WebSocket Thread):**
```python
def _on_nifty_tick(self, tick):
    with self.price_lock:
        self.current_nifty_price = tick.get('last_price')
```

2. **Price Reads (Main Thread):**
```python
def _check_breakout(self):
    with self.price_lock:
        current_price = self.current_nifty_price
    # Use local copy outside lock
    if current_price > self.entry_candle_high:
        ...
```

3. **Position Updates (WebSocket Thread):**
```python
def _on_option_tick(self, tick):
    with self.position_lock:
        if self.position:
            self.position['current_price'] = tick.get('last_price')
```

4. **Position Reads (Main Thread):**
```python
def _handle_position_active(self):
    with self.position_lock:
        entry_price = self.position['entry_price']
        current_price = self.position['current_price']
        # ... copy all needed fields
    # Use local copies outside lock
```

**Why This Matters:**
- Without locks: Risk of reading partially-updated data
- Race conditions can cause incorrect P&L calculations
- Position modifications could be lost or corrupted

---

### Risk Controls & Circuit Breakers

**Capital Limits:**
```python
# config.py
MIN_CAPITAL = 100000           # ₹1,00,000
MAX_CAPITAL = 100000000        # ₹10,00,00,000 (10 crores)
MAX_LOTS_PER_ORDER = 100       # Maximum 100 lots per order
```

**Validation Flow:**
1. **Capital Input:**
   - Min: ₹1,00,000 (system designed for this base)
   - Max: ₹10 crores (risk control limit)
   - Must be ≤ Available Margin
   - Auto-floor to ₹1,00,000 multiples

2. **Position Sizing:**
   - Calculate: `lots = base_lots × capital_multiplier`
   - Validate: `lots ≤ MAX_LOTS_PER_ORDER`
   - Reject order if exceeds limit

**Example:**
```python
# Capital: ₹15 crores → multiplier = 150
# Base lots: 2 → Calculated lots: 300
# Validation: 300 > 100 (MAX_LOTS) → REJECTED
```

**Why This Matters:**
- Prevents runaway position sizes
- Limits maximum risk per trade
- Circuit breaker against bugs or misconfiguration

---

### API Timeout Configuration

**All network calls must have timeout protection:**

```python
# config.py
API_TIMEOUT = 30  # seconds

# Usage
historical_data = self.kite.historical_data(
    instrument_token=token,
    from_date=from_date,
    to_date=to_date,
    interval='minute',
    timeout=Config.API_TIMEOUT  # ← Critical!
)
```

**Why This Matters:**
- Prevents system freeze on network issues
- Historical data fetch blocks main thread during candle close
- Without timeout: System could hang indefinitely

---

### Input Validation Rules

**All user inputs must be validated:**

1. **Capital Input:**
   - Must be numeric
   - Range: ₹1L to ₹10 crores
   - Must be ≤ available margin

2. **Stop Loss Modification:**
   - CALL: New SL < Current Price
   - PUT: New SL > Current Price

3. **Target Modification:**
   - Target > Entry Price (for profit)
   - Warning if Target < Current Price

**Example:**
```python
try:
    capital = float(user_input)
except ValueError:
    print("Invalid input")
    return

if capital < Config.MIN_CAPITAL:
    print(f"Minimum: ₹{Config.MIN_CAPITAL:,}")
    return
```

---

### Error Handling Best Practices

**1. Catch Specific Exceptions:**
```python
# Bad
except Exception as e:
    pass

# Good
except (NetworkError, TimeoutError) as e:
    logger.error(f"Network error: {e}")
    # Specific recovery logic
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise  # Re-raise unexpected errors
```

**2. Always Log Errors:**
```python
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    print(f"✗ Error: {e}")
```

**3. Graceful Degradation:**
```python
try:
    # Try Historical API
    data = kite.historical_data(...)
except Exception as e:
    logger.warning(f"Historical API failed: {e}")
    # Fallback to WebSocket data
    data = self.candle_data
```

---

### Critical Code Sections

**Areas requiring extra care:**

1. **Order Placement** - Double-check quantity, symbol, order type
2. **Exit Order** - Must complete even if errors occur
3. **Position Tracking** - Always protected by `position_lock`
4. **WebSocket Reconnection** - Handle gracefully, re-subscribe
5. **Journal Logging** - File I/O could fail, wrap in try/except
6. **Historical API Calls** - May return None or empty data, always validate
7. **Date Type Handling** - Check if expiry is datetime or date object before calling .date()
8. **Dashboard Display** - Always check for None values before formatting

**Pre-Order Checklist:**
- ✅ Margin verified
- ✅ Lot size validated (≤ MAX_LOTS)
- ✅ Symbol verified
- ✅ Quantity calculated correctly
- ✅ Late entry warning shown (if after 3 PM)
- ✅ LTP fetched for limit price calculation
- ✅ Limit price calculated (LTP ± 2%)

**Common API Gotchas:**
1. **historical_data()** - Does NOT accept `timeout` parameter
2. **Market orders** - NOT allowed via API, use LIMIT orders
3. **Date objects** - May be datetime.datetime OR datetime.date
4. **IP Whitelist** - Must add IP to Kite Developer Console
5. **None values** - Always check before formatting (e.g., `f"{value:.2f}"` fails if value is None)
6. **Stop Loss validation** - We're LONG options (buying), so SL < current price for BOTH CALL and PUT

---

### Security Requirements

**1. Credential Management:**
- Never commit `.env` file
- Store API keys in environment variables only
- `.gitignore` must include: `.env`, `access_token.txt`

**2. Access Token Storage:**
- Store in `access_token.txt` (add to `.gitignore`)
- Refresh automatically when expired
- Log security events (auth failures)

**3. API Key Protection:**
- No API keys in code
- No API keys in logs
- Example: `logger.info(f"API Key: {api_key[:4]}***")` ← Masked

---

### Performance Considerations

**1. Lock Duration:**
- Hold locks for **minimum time** necessary
- Copy data inside lock, process outside:
```python
with self.position_lock:
    data = self.position.copy()  # Quick copy
# Process data outside lock (slow operations)
```

**2. Dashboard Refresh:**
- Limit to 1 second intervals (configurable)
- Don't block on I/O during refresh

**3. WebSocket Callbacks:**
- Keep callbacks fast
- Don't block WebSocket thread with heavy processing

---

### Testing Requirements

**Must test before production:**

1. **Thread Safety:**
   - Concurrent price updates during monitoring
   - Position modification during active trade
   - Multiple rapid user commands

2. **Edge Cases:**
   - Capital: ₹50,000 (too low)
   - Capital: ₹20 crores (too high)
   - Lots: 150 (exceeds max)
   - Network disconnection during order
   - WebSocket reconnection during position

3. **Error Scenarios:**
   - API timeout during historical data fetch
   - Insufficient margin
   - Order rejection
   - System restart with open position

---

### Configuration Parameters

**All limits in `config.py`:**
```python
# Capital & Position Limits
MIN_CAPITAL = 100000              # Minimum ₹1L
MAX_CAPITAL = 100000000           # Maximum ₹10 crores
MAX_LOTS_PER_ORDER = 100          # Max lots per order

# API & Network
API_TIMEOUT = 30                  # Note: KiteConnect handles timeout internally
API_MAX_RETRIES = 3               # Retry attempts
WS_MAX_RETRIES = 5                # WebSocket reconnection

# Trading Parameters
NIFTY_LOT_SIZE = 65               # Current lot size
MARKET_START_TIME = time(9, 15)   # Market hours
EOD_CLOSE_TIME = time(15, 15)     # Auto-close time
```

---

## Common Issues & Troubleshooting

### Issue 1: "Market orders not allowed via API"
**Error:** `Market orders without market protection are not allowed via API`

**Solution:** Use LIMIT orders with 2% buffer
```python
# Get LTP
quote = kite.quote(f"NFO:{trading_symbol}")
ltp = quote[f"NFO:{trading_symbol}"]["last_price"]

# Calculate limit price
if transaction_type == "BUY":
    limit_price = round(ltp * 1.02, 1)  # 2% above
else:
    limit_price = round(ltp * 0.98, 1)  # 2% below

# Place limit order
kite.place_order(..., order_type=kite.ORDER_TYPE_LIMIT, price=limit_price)
```

---

### Issue 2: "No IPs configured for this app"
**Error:** `No IPs configured for this app. Add allowed IPs on Kite developer console`

**Solution:**
1. Go to https://developers.kite.trade/
2. Open your app settings
3. Add your IP to "Allowed IPs"
4. Wait 1-2 minutes for propagation
5. Restart trading system

---

### Issue 3: "unsupported format string passed to NoneType"
**Error:** `TypeError: unsupported format string passed to NoneType.__format__`

**Solution:** Always validate data before formatting
```python
# Bad
print(f"{value:.2f}")  # Crashes if value is None

# Good
if value is None:
    print("Data unavailable")
    return
print(f"{value:.2f}")
```

---

### Issue 4: "datetime.date object has no attribute 'date'"
**Error:** `AttributeError: 'datetime.date' object has no attribute 'date'`

**Solution:** Check type before calling .date()
```python
# Handle both datetime and date objects
if hasattr(option_expiry, 'date'):
    option_expiry_date = option_expiry.date()
else:
    option_expiry_date = option_expiry
```

---

### Issue 5: "historical_data() got unexpected keyword 'timeout'"
**Error:** `TypeError: historical_data() got an unexpected keyword argument 'timeout'`

**Solution:** Don't pass timeout parameter
```python
# Wrong
data = kite.historical_data(..., timeout=30)

# Correct
data = kite.historical_data(...)  # Library handles timeout internally
```

---

### Issue 6: Historical API returns no data
**Error:** Empty list or None from `historical_data()`

**Solution:** Implement WebSocket fallback
```python
try:
    data = kite.historical_data(...)
    if not data or len(data) == 0:
        # Use WebSocket fallback
        high = max([tick['price'] for tick in self.candle_data])
        low = min([tick['price'] for tick in self.candle_data])
except Exception as e:
    logger.error(f"Historical API failed: {e}")
    # Fallback or return to IDLE
```

---

### Issue 7: "PUT stop loss must be ABOVE current price" (Invalid validation)
**Error:** `✗ Invalid: PUT stop loss must be ABOVE current price`

**Problem:** When trying to set stop loss below current price for PUT option

**Root Cause:** Misunderstanding of option trading - we're BUYING options (LONG position)

**Solution:** Stop loss must be BELOW current price for BOTH CALL and PUT
```python
# WRONG - Different validation for CALL and PUT
if direction == 'CALL':
    if new_sl >= current_price:
        return "Invalid"
else:  # PUT
    if new_sl <= current_price:  # ❌ WRONG!
        return "Invalid"

# CORRECT - Same validation for both (we're LONG the option)
# For LONG positions: option price UP = profit, DOWN = loss
# Stop loss protects against price drop (regardless of CALL/PUT)
if new_sl >= current_price:
    print("Stop loss must be BELOW current price")
    print("(You're buying the option - SL protects against price drop)")
    return
```

**Key Understanding:**
- We BUY options (both CALL and PUT) - we're LONG
- When option premium rises → profit
- When option premium falls → loss
- Stop loss: exit if premium drops to this level
- Direction (CALL/PUT) affects strike selection, NOT how P&L works

**Example:**
```
PUT Option: NIFTY23500PE
Entry: ₹180
Current: ₹241.65 (in profit!)
Setting SL: ₹233 (trail stop to lock profit)
Validation: ✅ PASS (233 < 241.65)
```

---

## Notes
- Prioritize **code safety** and **error handling** over speed
- Make all critical parameters **configurable** (lot size, market hours, EOD close time)
- Write **defensive code** assuming network/API failures will occur
- Test thoroughly in paper trading mode before live deployment
- **Thread safety is non-negotiable** - all shared state must use locks
- **Validate all inputs** - never trust user input or API responses
- **Log everything** - debugging production issues requires good logs
- **Always check for None** - format strings crash on None values
- **Use LIMIT orders** - Market orders not allowed via API
- **Handle date types** - API may return datetime.datetime OR datetime.date
- **LONG position logic** - We BUY options, so SL < current price for BOTH CALL and PUT
- **Don't confuse direction with position** - Direction affects strike selection, not P&L behavior