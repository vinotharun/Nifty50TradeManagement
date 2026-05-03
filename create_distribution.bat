@echo off
REM Script to create a clean distribution package for sharing (Windows)

echo ============================================
echo Creating Distribution Package
echo ============================================
echo.

REM Set variables
set DIST_NAME=NIFTY50_Trading_System
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set DATESTAMP=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set TIMESTAMP=%%a%%b)
set DIST_FOLDER=%DIST_NAME%_%DATESTAMP%_%TIMESTAMP%

echo Creating distribution folder...
mkdir "..\%DIST_FOLDER%"

echo Copying Python files...
copy *.py "..\%DIST_FOLDER%\" >nul

echo Copying documentation...
copy *.md "..\%DIST_FOLDER%\" >nul

echo Copying configuration files...
copy requirements.txt "..\%DIST_FOLDER%\" >nul
copy requirements-latest.txt "..\%DIST_FOLDER%\" >nul
copy .env.example "..\%DIST_FOLDER%\" >nul
copy .gitignore "..\%DIST_FOLDER%\" >nul

echo Creating START_HERE.txt...
(
echo NIFTY50 ALGORITHMIC TRADING SYSTEM
echo ===================================
echo.
echo Thank you for receiving this trading system!
echo.
echo FIRST STEPS:
echo 1. Read SETUP_INSTRUCTIONS.md for complete setup guide
echo 2. For quick start, see QUICKSTART_WINDOWS.md
echo 3. Read README.md for full documentation
echo.
echo REQUIREMENTS:
echo - Python 3.8 or higher
echo - Zerodha trading account
echo - Kite Connect API subscription
echo - Stable internet connection
echo.
echo QUICK SETUP:
echo 1. Install Python dependencies: pip install -r requirements.txt
echo 2. Copy .env.example to .env
echo 3. Edit .env with your Kite API credentials
echo 4. Run: python main.py
echo.
echo IMPORTANT:
echo - This system trades REAL MONEY
echo - Test in paper trading mode first
echo - Start with minimum positions
echo - Monitor actively
echo - Read all documentation before using
echo.
echo SUPPORT:
echo - Check trading_system.log for errors
echo - See INSTALLATION_TROUBLESHOOTING.md
echo - Contact the person who shared this with you
echo.
echo DISCLAIMER:
echo Trading involves substantial risk. Use at your own risk.
echo.
echo Good luck and trade responsibly!
) > "..\%DIST_FOLDER%\START_HERE.txt"

echo.
echo ============================================
echo Distribution Folder Created!
echo ============================================
echo.
echo Folder: %DIST_FOLDER%
echo.
echo Next Steps:
echo 1. Compress the folder to ZIP (right-click ^> Send to ^> Compressed folder)
echo 2. Share the ZIP file
echo 3. Tell recipient to read START_HERE.txt first
echo.
echo Location: %CD%\..\%DIST_FOLDER%
echo.
echo Done!
echo.
pause
