#!/bin/bash
# Quick Start Script for GuardianVault Demo

echo "======================================================================"
echo "  GuardianVault Practical Demo - Quick Start"
echo "======================================================================"
echo ""

# Check if running from correct directory
if [ ! -f "cli_share_generator.py" ]; then
    echo "❌ Error: Please run this script from the practical_demo directory"
    exit 1
fi

echo "Step 1: Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 found"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✓ Docker found"

# Check if Bitcoin regtest is running
if ! docker ps | grep -q bitcoin-regtest; then
    echo ""
    echo "⚠️  Bitcoin regtest is not running"
    echo "Starting Bitcoin regtest..."
    cd ..
    docker compose -f docker-compose.regtest.yml up -d
    cd practical_demo
    echo "✓ Bitcoin regtest started"
    sleep 5

    # Setup regtest environment
    echo ""
    echo "Setting up Bitcoin regtest environment..."
    python3 setup_regtest.py
else
    echo "✓ Bitcoin regtest is running"
fi

# Check if coordination server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo "⚠️  Coordination server is not running"
    echo ""
    echo "Please start the coordination server in a separate terminal:"
    echo "  cd ../coordination-server"
    echo "  poetry install"
    echo "  poetry run uvicorn app.main:app --reload"
    echo ""
    echo "Then run this script again."
    exit 1
fi
echo "✓ Coordination server is running"

echo ""
echo "Step 2: Installing Python dependencies..."
pip3 install -r requirements.txt -q
echo "✓ Dependencies installed"

echo ""
echo "======================================================================"
echo "  All prerequisites are ready!"
echo "======================================================================"
echo ""
echo "Choose how to run the demo:"
echo ""
echo "1. Automated Demo (recommended for first-time users)"
echo "   python3 demo_orchestrator.py"
echo ""
echo "2. Manual Step-by-Step Demo (for understanding the process)"
echo "   Follow the instructions in README.md"
echo ""
echo "3. Quick Test (generates shares only)"
echo "   python3 cli_share_generator.py --guardians 3 --threshold 3 --vault 'Test Vault' --output test_shares"
echo ""
echo "======================================================================"
echo ""

read -p "Press Enter to run the automated demo, or Ctrl+C to exit..."

echo ""
python3 demo_orchestrator.py
