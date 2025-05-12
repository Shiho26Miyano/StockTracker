#!/bin/bash
set -e

# Default to port 8080 if not set
export PORT=${PORT:-8080}

# Print environment info
echo "=== Starting StockTracker on port: $PORT ==="
echo "Python: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files: $(ls -la)"

# Log yfinance debug info
echo "=== YFinance Configuration ==="
echo "YF_MAX_RETRIES: ${YF_MAX_RETRIES:-5}"
echo "YF_BACKOFF_FACTOR: ${YF_BACKOFF_FACTOR:-2}"
echo "YF_INITIAL_WAIT: ${YF_INITIAL_WAIT:-2}"
echo "YF_TIMEOUT: ${YF_TIMEOUT:-30}"

# Test network connectivity to Yahoo Finance
echo "=== Testing Connection to Yahoo Finance ==="
curl -sI https://query2.finance.yahoo.com > /dev/null || echo "WARNING: Could not connect to Yahoo Finance API"

# Test Python imports
echo "=== Testing Python Dependencies ==="
python -c "import yfinance; import pandas; import flask; print('All dependencies imported successfully')" || echo "WARNING: Could not import all required dependencies"

# Execute gunicorn with proper binding
echo "=== Starting Gunicorn ==="
exec gunicorn --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app 