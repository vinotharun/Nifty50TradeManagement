#!/bin/bash
# Script to create a clean distribution package for sharing

echo "============================================"
echo "Creating Distribution Package"
echo "============================================"
echo ""

# Get the current directory name
DIST_NAME="NIFTY50_Trading_System"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIST_FOLDER="${DIST_NAME}_${TIMESTAMP}"
ZIP_FILE="${DIST_NAME}_${TIMESTAMP}.zip"

# Create distribution folder
echo "📁 Creating distribution folder..."
mkdir -p "../${DIST_FOLDER}"

# Copy Python files
echo "📄 Copying Python files..."
cp *.py "../${DIST_FOLDER}/"

# Copy documentation
echo "📚 Copying documentation..."
cp *.md "../${DIST_FOLDER}/"

# Copy configuration files
echo "⚙️  Copying configuration files..."
cp requirements.txt "../${DIST_FOLDER}/"
cp requirements-latest.txt "../${DIST_FOLDER}/"
cp .env.example "../${DIST_FOLDER}/"
cp .gitignore "../${DIST_FOLDER}/"

# Create a README for the distribution
echo "📝 Creating distribution README..."
cat > "../${DIST_FOLDER}/START_HERE.txt" << 'EOF'
NIFTY50 ALGORITHMIC TRADING SYSTEM
===================================

Thank you for receiving this trading system!

FIRST STEPS:
1. Read SETUP_INSTRUCTIONS.md for complete setup guide
2. For quick start, see QUICKSTART.md (Mac/Linux) or QUICKSTART_WINDOWS.md (Windows)
3. Read README.md for full documentation

REQUIREMENTS:
- Python 3.8 or higher
- Zerodha trading account
- Kite Connect API subscription (₹2000/month)
- Stable internet connection

QUICK SETUP:
1. Install Python dependencies: pip install -r requirements.txt
2. Copy .env.example to .env
3. Edit .env with your Kite API credentials
4. Run: python main.py

IMPORTANT:
⚠️  This system trades REAL MONEY
⚠️  Test in paper trading mode first
⚠️  Start with minimum positions
⚠️  Monitor actively - don't leave unattended
⚠️  Read all documentation before using

SUPPORT:
- Check trading_system.log for errors
- See INSTALLATION_TROUBLESHOOTING.md for common issues
- Contact the person who shared this with you

DISCLAIMER:
Trading involves substantial risk. Use at your own risk.
The creators are not responsible for any financial losses.

Good luck and trade responsibly!
EOF

# Create ZIP file
echo "🗜️  Creating ZIP archive..."
cd ..
zip -r "${ZIP_FILE}" "${DIST_FOLDER}" -q

# Show results
echo ""
echo "============================================"
echo "✅ Distribution Package Created!"
echo "============================================"
echo ""
echo "📦 Package: ${ZIP_FILE}"
echo "📁 Location: $(pwd)/${ZIP_FILE}"
echo "📊 Size: $(du -h ${ZIP_FILE} | cut -f1)"
echo ""
echo "🎯 What to share:"
echo "   - Share the ZIP file: ${ZIP_FILE}"
echo "   - Tell them to read START_HERE.txt first"
echo "   - Tell them to read SETUP_INSTRUCTIONS.md"
echo ""
echo "✅ The package is ready to share!"
echo ""

# Cleanup
read -p "❓ Delete the temporary folder? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    rm -rf "${DIST_FOLDER}"
    echo "✓ Temporary folder deleted"
fi

echo ""
echo "Done! 🎉"
