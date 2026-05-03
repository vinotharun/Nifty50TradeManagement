# Entry Candle Logic - Detailed Explanation

## How Entry Candle Works

When you press ENTER, the system designates the **current 1-minute candle that is already forming** as the Entry Candle.

### Visual Timeline

```
Time:     10:29:00   10:30:00   10:30:15   10:31:00   10:31:30   10:32:00
          |          |          |          |          |          |
Candle:   [--Previous--][---Entry Candle---][---Next Candle---]
                            ↑                    ↑
                            |                    |
                       Press ENTER         Candle Closes
                                           Start Monitoring
```

## Example Scenarios

### Scenario 1: Press ENTER at 10:30:15

```
Clock Time: 10:30:15 AM
Action: You press ENTER

Entry Candle Designated:
├── Start Time: 10:30:00 AM
├── End Time:   10:31:00 AM
└── Wait Time:  45 seconds (until 10:31:00)

At 10:31:00 AM:
├── Candle closes
├── System calculates High & Low from all ticks between 10:30:00 - 10:31:00
└── Breakout monitoring begins
```

### Scenario 2: Press ENTER at 10:30:45

```
Clock Time: 10:30:45 AM
Action: You press ENTER

Entry Candle Designated:
├── Start Time: 10:30:00 AM
├── End Time:   10:31:00 AM
└── Wait Time:  15 seconds (until 10:31:00)

At 10:31:00 AM:
├── Candle closes
├── System calculates High & Low
└── Breakout monitoring begins
```

### Scenario 3: Press ENTER at 10:30:05 (just after candle starts)

```
Clock Time: 10:30:05 AM
Action: You press ENTER

Entry Candle Designated:
├── Start Time: 10:30:00 AM
├── End Time:   10:31:00 AM
└── Wait Time:  55 seconds (until 10:31:00)

At 10:31:00 AM:
├── Candle closes
├── System calculates High & Low
└── Breakout monitoring begins
```

## Why This Approach?

### ✅ Advantages

1. **Matches Chart Candles**: Entry candle aligns with actual 1-minute candles on your trading chart
2. **Predictable Timing**: Always closes at minute boundaries (10:31:00, 10:32:00, etc.)
3. **Consistent Data**: High/Low matches what you see on charting platforms
4. **Accurate Breakout**: Breakout levels are exactly what traders see on charts

### 📊 Data Collection

**Method: Historical Data API**

When the candle closes at 10:31:00:
- System calls Kite Connect **historical_data()** API
- Fetches the complete 1-minute candle from 10:30:00 to 10:31:00
- Gets the **actual High and Low** from the entire candle
- This includes data from BEFORE you pressed ENTER

**Example:**
```
You press ENTER at 10:30:15
True candle low was at 10:30:07 (before you pressed ENTER)
→ System WILL capture this low using historical data API
→ Entry Candle High/Low matches exactly what you see on charts
```

**Fallback:**
- If historical data API fails, system uses collected WebSocket ticks as backup
- This ensures the system continues working even if API is down

## Complete Flow

```
1. IDLE STATE
   │
   ├─→ [User Presses ENTER at 10:30:15]
   │
2. ENTRY CANDLE DESIGNATION
   │
   ├─→ System: "Current candle is 10:30:00 to 10:31:00"
   ├─→ System: "Waiting 45 seconds for candle to close..."
   ├─→ Collecting all price ticks...
   │
3. WAITING FOR CANDLE CLOSE
   │
   ├─→ Time: 10:30:16... 10:30:17... 10:30:18...
   ├─→ Collecting ticks: 22,545, 22,547, 22,546...
   │
4. CANDLE CLOSES (at 10:31:00)
   │
   ├─→ Calculate High: max(all ticks) = 22,550
   ├─→ Calculate Low: min(all ticks) = 22,530
   ├─→ Display: "Entry Candle: High=22,550 | Low=22,530"
   │
5. BREAKOUT MONITORING
   │
   ├─→ Watch live price
   ├─→ If price > 22,550 → BUY CALL
   ├─→ If price < 22,530 → BUY PUT
   │
   └─→ Continue to TRADE EXECUTION...
```

## Key Points

1. **Entry Candle = Current Market Candle**
   - When you press ENTER at 10:30:15, the entry candle is the one that started at 10:30:00

2. **Wait Time Varies**
   - Depends on when you press ENTER within the minute
   - Could be 5 seconds (if pressed at 10:30:55) or 55 seconds (if pressed at 10:30:05)

3. **Always Aligned with Clock**
   - Candle always closes at the next minute boundary
   - Examples: 10:31:00, 10:32:00, 10:33:00, etc.

4. **Tick Collection**
   - System only uses ticks from when you press ENTER onwards
   - Does NOT retroactively fetch earlier data from the same candle
   - This is a design choice for simplicity and real-time operation

## ✅ Complete Candle Data Guarantee

The system now uses **Kite Connect Historical Data API** to ensure you get the complete candle data:

### How It Works:

1. You press ENTER at any time during the minute (e.g., 10:30:15)
2. System designates the current candle (10:30:00 to 10:31:00)
3. Waits for candle to close at 10:31:00
4. **Fetches the complete candle from Kite API** using `historical_data()`
5. Gets the true High and Low from the entire candle

### Key Benefits:

✅ **Captures ALL price action** - including before you pressed ENTER
✅ **Matches your charts exactly** - Same High/Low as TradingView, Kite, etc.
✅ **No data loss** - Even if low was at 10:30:07 and you pressed ENTER at 10:30:15
✅ **Reliable** - Uses official Kite API data, not just WebSocket ticks
✅ **Fallback protection** - Uses WebSocket ticks if API fails

### Example with Real Numbers:

```
Candle: 10:30:00 to 10:31:00

10:30:07 - Price touches 22,530 (ACTUAL LOW)
10:30:15 - You press ENTER
10:30:28 - Price reaches 22,550 (ACTUAL HIGH)
10:31:00 - Candle closes

System fetches historical data:
→ High: 22,550 ✓ (captured even though it was after ENTER)
→ Low: 22,530 ✓ (captured even though it was BEFORE ENTER)

Result: Perfect accuracy!
```

---

**In Summary**: When you press ENTER at any time, the system designates the current 1-minute candle (based on clock time) as the Entry Candle, waits for it to close at the next minute boundary, then starts monitoring for breakouts.
