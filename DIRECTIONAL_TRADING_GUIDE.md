# Directional Trading Guide

## 🎯 Overview

The system now supports **directional trading control**, allowing you to choose whether to monitor for CALL or PUT breakouts only.

---

## 📊 How It Works

### Step-by-Step Flow

#### **Step 1: IDLE State**
```
════════════════════════════════════════════════════════
         NIFTY50 OPTIONS TRADING DASHBOARD
════════════════════════════════════════════════════════

Current NIFTY 50: 22,545.30

📊 System is monitoring market prices
⏳ Press ENTER to designate Entry Candle...
```

Press **ENTER**

---

#### **Step 2: Choose Direction**
```
════════════════════════════════════════════════════════
         ENTRY CANDLE SETUP
════════════════════════════════════════════════════════

Choose trading direction:
  [C] CALL - Monitor for breakout ABOVE entry candle high
  [P] PUT  - Monitor for breakout BELOW entry candle low

Enter your choice (C/P): _
```

Type **C** (for CALL) or **P** (for PUT) and press ENTER

---

#### **Step 3: Entry Candle Designated**
```
✓ Entry candle designated: 10:30:00 to 10:31:00
✓ Direction chosen: CALL
  Current time: 10:30:15
  Waiting 45 seconds for candle to close...
```

System waits for current 1-minute candle to close

---

#### **Step 4: Monitoring for Breakout**
```
════════════════════════════════════════════════════════
         MONITORING CALL BREAKOUT
════════════════════════════════════════════════════════

Entry Candle (10:30:00 - 10:31:00):
  High: 22,550.00
  Low:  22,530.00

Direction: CALL
Breakout Trigger: Price > 22,550.00
Current NIFTY: 22,547.25

⏳ Waiting for CALL breakout...
Press 'Q' to cancel and return to IDLE
════════════════════════════════════════════════════════
```

Dashboard updates every second with current price

**Note:** You can type 'Q' and press ENTER at any time during monitoring. A background thread is listening for your input, so the dashboard refresh won't clear what you type!

---

## 🔀 Three Possible Outcomes

### **Outcome 1: Correct Direction Breakout ✅**

```
Current NIFTY: 22,551.50 ✓ BREAKOUT!

🚀 CALL BREAKOUT DETECTED!
📊 Finding ITM Call option...
```

→ **Trade is executed**

---

### **Outcome 2: Wrong Direction Breakout (Ignored) ⚠️**

```
Chosen: CALL
Entry Candle: High = 22,550 | Low = 22,530

Price moves to: 22,528 (below Low - PUT direction)
```

→ **IGNORED** - System continues monitoring for CALL breakout
→ No message displayed (silent ignore)
→ Continues waiting for price > 22,550

**Key Point:** Even if PUT breakout happens, it's ignored because you chose CALL.

---

### **Outcome 3: Manual Cancellation 🛑**

```
[User presses 'Q']

❌ Monitoring cancelled by user
   Returning to IDLE state...
```

→ **No trade executed**
→ Returns to IDLE state

---

### **Outcome 4: EOD Auto-Return ⏰**

```
⏰ EOD TIME REACHED (3:15 PM)
   No breakout occurred
   Returning to IDLE state...

Press ENTER to continue...
```

→ **No trade executed**
→ Auto-returns to IDLE

---

## 💡 Use Cases

### **When to Use CALL Direction**

Choose **C** when:
- You expect upward movement
- Market sentiment is bullish
- You want to trade only if price breaks above resistance
- You want to avoid PUT trades even if support breaks

### **When to Use PUT Direction**

Choose **P** when:
- You expect downward movement
- Market sentiment is bearish
- You want to trade only if price breaks below support
- You want to avoid CALL trades even if resistance breaks

---

## 🎓 Example Scenarios

### **Scenario 1: Bullish Setup (Choose CALL)**

```
Time: 10:30 AM
Sentiment: Bullish, expecting upside

Action:
1. Press ENTER
2. Choose: C (CALL)
3. Entry Candle: High = 22,550 | Low = 22,530

Possible Outcomes:
- Price → 22,552 ✅ CALL trade executed (ITM 22500CE)
- Price → 22,528 ⚠️  Ignored (PUT direction)
- Press Q 🛑 Cancelled, no trade
```

---

### **Scenario 2: Bearish Setup (Choose PUT)**

```
Time: 2:00 PM
Sentiment: Bearish, expecting downside

Action:
1. Press ENTER
2. Choose: P (PUT)
3. Entry Candle: High = 22,550 | Low = 22,530

Possible Outcomes:
- Price → 22,529 ✅ PUT trade executed (ITM 22600PE)
- Price → 22,551 ⚠️  Ignored (CALL direction)
- Press Q 🛑 Cancelled, no trade
```

---

## ⚖️ Key Differences

### **Old System (Automatic Both Directions)**
```
Press ENTER → Wait → Trade whichever direction breaks first
- No control
- Could trade against your view
```

### **New System (User Choice)**
```
Press ENTER → Choose C or P → Wait → Trade only if chosen direction breaks
- Full control
- Only trade in your expected direction
- Can cancel anytime
```

---

## 📝 Trading Journal

The journal now includes both:
- **Chosen Direction**: What you selected (CALL or PUT)
- **Breakout Direction**: Actual trade direction (always matches chosen)

This helps you analyze:
- How often you chose correctly
- Win rate by direction
- Time to breakout after setup

---

## ✅ Best Practices

1. **Have a bias** - Don't choose randomly, have a directional view
2. **Use technical levels** - Choose based on support/resistance
3. **Monitor actively** - Don't set and forget
4. **Cancel if wrong** - If setup invalidates, press Q
5. **Respect EOD** - System auto-cancels at 3:15 PM
6. **Review journal** - Track which direction works best

---

## 🚫 What's NOT Allowed

❌ **Cannot change direction** after choosing
   → Cancel with Q and start fresh

❌ **Cannot trade both directions** from same entry candle  
   → Choose one or the other

❌ **Cannot wait indefinitely**
   → System auto-returns to idle at EOD (3:15 PM)

---

## 🎯 Summary

**Directional trading gives you:**
✅ Full control over trade direction
✅ Avoid unwanted opposite-direction trades  
✅ Flexibility to cancel and wait
✅ Better alignment with your market view
✅ Professional discretionary trading approach

**Remember:** The system executes automatically once breakout occurs in YOUR chosen direction!

---

**Happy Directional Trading! 📈📉**
