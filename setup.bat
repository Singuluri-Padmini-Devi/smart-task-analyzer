@echo off
echo ========================================
echo  Smart Task Analyzer - Quick Setup
echo ========================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python 3.8+ is installed
    pause
    exit /b 1
)
echo ✓ Virtual environment created
echo.

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

echo [3/4] Installing dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [4/4] Setup complete!
echo.
echo ========================================
echo  To run the project:
echo ========================================
echo.
echo 1. Start backend:
echo    cd backend
echo    python manage.py runserver
echo.
echo 2. Open frontend:
echo    Double-click frontend/index.html
echo    OR run: python -m http.server 3000 (in frontend folder)
echo.
echo Read HOW_TO_RUN.md for detailed instructions
echo ========================================
pause

