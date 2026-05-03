#!/bin/bash
# Script to upload NIFTY50 Trading System to GitHub
# Repository: https://github.com/vinotharun/Nifty50TradeManagement

echo "=============================================="
echo "  NIFTY50 Trading System - GitHub Upload"
echo "=============================================="
echo ""

# Step 1: Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: Please run this script from the StopLossTrading directory"
    echo "   cd /Users/varunmathialagan/Documents/augment-projects/StopLossTrading"
    exit 1
fi

echo "✓ Directory verified"
echo ""

# Step 2: Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✓ Git initialized"
else
    echo "✓ Git already initialized"
fi
echo ""

# Step 3: Configure remote (if not already configured)
echo "🔗 Configuring remote repository..."
if git remote | grep -q origin; then
    echo "⚠️  Remote 'origin' already exists. Updating URL..."
    git remote set-url origin https://github.com/vinotharun/Nifty50TradeManagement.git
else
    git remote add origin https://github.com/vinotharun/Nifty50TradeManagement.git
fi

echo "✓ Remote configured:"
git remote -v
echo ""

# Step 4: Check what files will be uploaded
echo "📋 Files to be uploaded (respecting .gitignore):"
echo ""
git status --short

echo ""
echo "⚠️  Files being IGNORED (will NOT be uploaded):"
echo "   - .env (API credentials)"
echo "   - access_token.txt (access token)"
echo "   - __pycache__/ (Python cache)"
echo "   - *.log (log files)"
echo "   - trading_journal.xlsx (trading data)"
echo ""

# Step 5: Ask for confirmation
read -p "Continue with upload? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Upload cancelled"
    exit 1
fi

# Step 6: Stage all files
echo ""
echo "📦 Staging files..."
git add .
echo "✓ Files staged"
echo ""

# Step 7: Create commit
echo "💬 Creating commit..."
git commit -m "v4.1: Production-ready with thread safety, risk controls, and comprehensive documentation

Features:
- Thread safety: Added locks for all shared state (price_lock, position_lock)
- Risk controls: Max capital ₹10Cr, max lots 100 per order
- API timeout: 30-second protection for all network calls
- Validation: Capital (₹1L-₹10Cr) and position size limits
- Documentation: Added comprehensive Code Quality & Security section
- Smart expiry: Automatically skip same-day expiry
- Entry candle: Choose between current or previous candle
- Directional trading: CALL/PUT selection with monitoring
- Target modification: Full control over stop-loss and target
- Risk-Reward: 1:3 ratio with manual override capability
- Capital management: Auto-scaling quantities based on capital
- Non-blocking UI: M/T/Q commands during active positions

Files:
- Core: main.py, strategy.py, order_manager.py, data_stream.py
- Config: config.py, auth.py, utils.py, dashboard.py
- Docs: README.md, CHANGELOG.md, IMPLEMENTATION_PROMPT.md
- Guides: SETUP_INSTRUCTIONS.md, QUICKSTART.md, DIRECTIONAL_TRADING_GUIDE.md"

echo "✓ Commit created"
echo ""

# Step 8: Push to GitHub
echo "🚀 Pushing to GitHub..."
echo ""

# Set main branch and push
git branch -M main

echo "Pushing to: https://github.com/vinotharun/Nifty50TradeManagement"
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================="
    echo "  ✅ SUCCESS! Code uploaded to GitHub"
    echo "=============================================="
    echo ""
    echo "🌐 View your repository:"
    echo "   https://github.com/vinotharun/Nifty50TradeManagement"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Visit the repository URL above"
    echo "   2. Verify all files are present"
    echo "   3. Check that README.md is displayed"
    echo "   4. Review .gitignore is working (no .env or access_token.txt)"
    echo ""
else
    echo ""
    echo "❌ ERROR: Push failed"
    echo ""
    echo "Common issues:"
    echo "   1. Authentication required - GitHub may ask for username/password"
    echo "   2. Use Personal Access Token instead of password"
    echo "   3. Or use GitHub CLI: gh auth login"
    echo ""
fi
