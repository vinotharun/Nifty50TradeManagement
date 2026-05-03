# NIFTY50 Algorithmic Trading System - Implementation Specification

## Role
Act as an expert quantitative developer and algorithmic trading specialist for NIFTY50 index options trading.

## Objective
Create a production-ready, fully documented trading script in Python to execute a breakout-based options trading strategy on the Nifty50 Index using Zerodha's Kite Connect API.

---

## Architecture
- **Code Structure**: Modular architecture (separate modules for authentication, data streaming, strategy logic, order management, UI/dashboard)
- **Concurrency Model**: Hybrid approach (Threading for blocking operations + Asyncio for network I/O)
- **Configuration**: Use `.env` file for API credentials (API Key, API Secret)
- **UI/Dashboard**: Use libraries like `rich` or `curses` for professional terminal formatting with clean screen refresh

---

## Core Strategy Logic

### 1. Idle State (Monitoring Phase)
- Run continuously and monitor live Nifty50 spot price via **Kite Connect WebSocket ticks**
- Display current Nifty50 spot price in real-time
- Execute no trades
- Wait for user to press the **Enter key**
- **Market Hours**: System should only operate during market hours (9:15 AM - 3:30 PM IST)
- Handle daily session re-authentication automatically when access tokens expire

### 2. Entry Candle Designation
- When Enter is pressed, designate the **current 1-minute candle that is forming** as the "Entry Candle"
- Wait for this 1-minute candle to **fully close**
- Record the **High** and **Low** of the completed Entry Candle
- Display Entry Candle details: `High: XXXXX.XX | Low: XXXXX.XX`

### 3. Breakout Monitoring (Pending Order State)
Monitor live WebSocket ticks for breakout in either direction:

- **Path 1 (Long/Call)**: If live Nifty50 spot price crosses **above** Entry Candle High → Trigger Long setup
- **Path 2 (Short/Put)**: If live Nifty50 spot price crosses **below** Entry Candle Low → Trigger Short setup

### 4. Option Selection & Order Execution

#### ATM Option Selection
- Determine ATM strike: **Closest to current Nifty50 spot price** at the time of breakout
- Expiry: Use **nearest expiry** (weekly/monthly, whichever is closest)
- Use Kite Connect's **instrument lookup/search API** to get exact trading symbols (e.g., `NIFTY26MAY23500CE`)

#### Trade Execution Logic

**For Path 1 (Call Option):**
```
Instrument: Buy ATM Call Option (market order)
Stop Loss (SL) Price = Entry Candle Low - 1
Risk Points = Entry Price - SL Price
```

**For Path 2 (Put Option):**
```
Instrument: Buy ATM Put Option (market order)
Stop Loss (SL) Price = Entry Candle High + 1
Risk Points = SL Price - Entry Price
```

**Important**: 
- "Entry Price" = **Option premium price** at which the order is filled
- "Risk Points" calculation uses the **option premium**, not the underlying index

#### Position Sizing (Based on Risk Points)
- If Risk Points > 10: Buy **1 Lot**
- If Risk Points ≤ 10 and > 5: Buy **2 Lots**
- If Risk Points ≤ 5: Buy **3 Lots**

**Configuration**: Lot size for Nifty50 options = **65** (should be configurable in code)

#### Target Calculation
- Target Price = Entry Price ± (Risk Points × 2)
  - For Call: Entry Price + (Risk Points × 2)
  - For Put: Entry Price - (Risk Points × 2)
- Risk-to-Reward Ratio: **1:2**

#### Pre-Order Validations
1. **Margin Check**: Verify available margin before placing order
2. **Time Warning**: If order is being placed **post 3:00 PM**, display warning:
   ```
   ⚠️  WARNING: Position will auto-close at 3:15 PM. Continue? (y/n)
   ```
   Only proceed after user confirmation
3. **Error Handling**: If order placement fails, display the error message clearly

---

## 5. Active Position Monitoring & Live Dashboard

### Dashboard Display (Refresh every 1 second)
```
═══════════════════════════════════════════════════
         NIFTY50 OPTIONS TRADING DASHBOARD
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
Press 'M' to modify Stop Loss | 'Q' to force exit
═══════════════════════════════════════════════════
```

### Monitoring Logic
- **Price Source**: Monitor option premium price via WebSocket (subscribe to the traded option instrument)
- **SL/Target Monitoring**: Based on **option premium price**, not underlying Nifty50
- **Dashboard Refresh**: Clear screen and update every 1 second
- **Concurrent Input**: Use async I/O or multi-threading so dashboard refresh doesn't block user input

---

## 6. User Interactivity & Exit Conditions

### Manual Stop Loss Modification
- User presses **'M'** → Prompt: `Enter new Stop Loss price: `
- Update SL variable immediately and reflect in dashboard
- Validate: Ensure new SL is logical (below current price for Call, above for Put)

### Auto-Exit Conditions
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
Record all entries in a trading journal for later analysis. It should be in a spreadsheet format with the following columns: Serial Number, Date, Entry Candle High, Entry Candle Low, Breakout Direction, Option Type, Option Strike, Entry Price, Stop Loss, Target, Exit Price, Exit Reason, P&L, Return %

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
  - Order placements (with order ID, price, quantity)
  - SL/Target modifications
  - Exit events with P&L
  - Errors and exceptions
- Use Python `logging` module with timestamps

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

```
Scenario:
1. User presses Enter at 10:30:00 AM
2. Next 1-min candle starts at 10:30:00, closes at 10:31:00
3. Entry Candle: High = 22,550 | Low = 22,530
4. At 10:31:30, Nifty50 spot = 22,551 → Breakout above High → Trigger CALL
5. System finds ATM Call: 22,550 CE (nearest expiry)
6. Market order placed, filled at ₹150.00 (Entry Price)
7. Calculate Stop Loss:
   - SL trigger: Entry Candle Low - 1 = 22,530 - 1 = 22,529
   - When Nifty spot reaches 22,529, estimate option price would be ~₹142
   - SL Price (option premium) = ₹142.00
8. Risk Points = Entry Price - SL Price = ₹150 - ₹142 = ₹8
9. Position Sizing: Risk Points = 8 (≤10 and >5) → Buy 2 Lots (2 × 65 = 130 units)
10. Target = Entry Price + (Risk Points × 2) = ₹150 + ₹16 = ₹166.00
11. Dashboard shows live updates every 1 second with current option price
12. At 11:00 AM, option price hits ₹166 → Auto-exit, sell at ₹166
13. P&L = (₹166 - ₹150) × 130 units = ₹2,080 profit
14. Display trade summary, return to Idle State
```

**Note on Stop Loss Calculation**: Since SL is defined in terms of the underlying index (Entry Candle Low - 1), but monitoring happens on option premium, the system needs to either:
- **Option A**: Convert the index-based SL to an approximate option premium SL at entry time (using current option Greeks/delta)
- **Option B**: Monitor both index price and option premium, triggering SL when index crosses the threshold
- **Recommended**: Use Option A for simplicity, with a configurable SL buffer percentage

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

## Dependencies (Suggested)
```
kiteconnect
python-dotenv
rich (for terminal UI)
asyncio
threading
pandas (for data handling)
```

---

## Notes
- Prioritize **code safety** and **error handling** over speed
- Make all critical parameters **configurable** (lot size, market hours, EOD close time)
- Write **defensive code** assuming network/API failures will occur
- Test thoroughly in paper trading mode before live deployment
