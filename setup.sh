#!/bin/bash

echo "========================================"
echo " Smart Task Analyzer - Quick Setup"
echo "========================================"
echo ""

echo "[1/4] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    echo "Make sure Python 3.8+ is installed"
    exit 1
fi
echo "✓ Virtual environment created"
echo ""

echo "[2/4] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

echo "[3/4] Installing dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

echo "[4/4] Setup complete!"
echo ""
echo "========================================"
echo " To run the project:"
echo "========================================"
echo ""
echo "1. Start backend:"
echo "   cd backend"
echo "   python manage.py runserver"
echo ""
echo "2. Open frontend:"
echo "   Open frontend/index.html in browser"
echo "   OR run: python -m http.server 3000 (in frontend folder)"
echo ""
echo "Read HOW_TO_RUN.md for detailed instructions"
echo "========================================"

