#!/bin/bash

# PDF Bulk Converter Setup Script

echo "PDF Bulk Converter Setup Script"
echo "==============================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Detected: $python_version"

# Check if Python version is at least 3.11
if [[ ! $python_version =~ 3\.1[1-9]\. && ! $python_version =~ 3\.[2-9][0-9]\. ]]; then
    echo "Warning: This project requires Python 3.11+"
    echo "Current system Python version $python_version is not compatible."
    echo ""
    echo "Attempting to use setup_with_pyenv.sh to install the correct Python version..."
    
    # Make setup_with_pyenv.sh executable
    chmod +x setup_with_pyenv.sh
    
    # Run setup_with_pyenv.sh
    ./setup_with_pyenv.sh
    
    # Exit this script after setup_with_pyenv.sh is run
    exit $?
fi

echo "Python $python_version is compatible with this project."

# Check if venv directory exists and delete it
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create a new virtual environment
echo "Creating a new virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Add execute permissions to the requirements-fix.py script
chmod +x requirements-fix.py

# Use our custom requirements-fix.py script to install dependencies
echo "Installing project dependencies using requirements-fix.py..."
./requirements-fix.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    echo ""
    echo "Trying to install MuPDF system dependencies..."
    ./requirements-fix.py --mupdf-only
    echo "Now trying to install requirements again..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies after fixing MuPDF."
        echo ""
        echo "Possible solutions:"
        echo "1. For PyMuPDF issues:"
        echo "   - macOS: brew install mupdf"
        echo "   - Ubuntu: apt-get install libmupdf-dev"
        echo "   - Windows: Ensure Microsoft Visual C++ Redistributable is installed"
        echo "2. Try manually installing the problematic package:"
        echo "   - pip install PyMuPDF==1.23.26"
        echo "3. Check for Python version compatibility"
        echo ""
        exit 1
    fi
fi

# 環境変数ファイルをコピー
echo ""
echo "環境変数を設定しています..."
if [ -f ".env.local" ]; then
    cp .env.local .env
    echo ".env.localを.envにコピーしました"
else
    echo "WARNING: .env.localファイルが見つかりません。環境変数を手動で設定する必要があります。"
fi

# Setup successful
echo ""
echo "Setup completed successfully!"
echo ""
echo "To activate the virtual environment, run:"
echo "    source venv/bin/activate"
echo ""
echo "Then start the development server with:"
echo "    uvicorn app.main:app --reload"

# Exit the virtual environment
deactivate
