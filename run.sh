#!/bin/bash
set -e

echo "=========================================================="
echo "  AI Recruitment Agent Team — Launch Script"
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check virtual environment
if [ -d "backend/venv" ]; then
    echo "[1/4] Activating virtual environment..."
    source backend/venv/bin/activate
else
    echo "[1/4] Creating virtual environment..."
    python3 -m venv backend/venv
    source backend/venv/bin/activate
    pip install -r backend/requirements.txt
fi

# Run test verification
echo "[2/4] Running automated tests..."
PYTHONPATH="." pytest backend/tests -v

# Seed sample data if database doesn't exist
if [ ! -f "recruitment.db" ] && [ ! -f "backend/recruitment.db" ]; then
    echo "[3/4] Seeding initial recruitment pipeline data..."
    PYTHONPATH="." python backend/seed_data.py
else
    echo "[3/4] Database already initialized."
fi

# Start FastAPI server
echo "[4/4] Starting FastAPI backend and recruiter dashboard..."
echo "----------------------------------------------------------"
echo "  Recruiter Dashboard: http://localhost:8000"
echo "  Interactive API Docs: http://localhost:8000/docs"
echo "----------------------------------------------------------"

PYTHONPATH="." python backend/main.py
