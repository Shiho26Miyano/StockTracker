#!/bin/bash
set -e

# Default to port 8080 if not set
export PORT=${PORT:-8080}

# Print environment info
echo "=== Starting StockTracker on port: $PORT ==="
echo "Python: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files: $(ls -la)"

# Log Polygon.io API configuration
echo "=== Polygon.io Configuration ==="
echo "API KEY: ${POLYGON_API_KEY:0:4}... (hidden for security)"
echo "POLYGON_MAX_RETRIES: ${POLYGON_MAX_RETRIES:-3}"
echo "POLYGON_BACKOFF_FACTOR: ${POLYGON_BACKOFF_FACTOR:-2}"
echo "POLYGON_INITIAL_WAIT: ${POLYGON_INITIAL_WAIT:-1}"
echo "POLYGON_TIMEOUT: ${POLYGON_TIMEOUT:-30}"

# Test network connectivity to Polygon.io
echo "=== Testing Connection to Polygon.io ==="
curl -sI https://api.polygon.io > /dev/null || echo "WARNING: Could not connect to Polygon.io API"

# Test Python imports
echo "=== Testing Python Dependencies ==="
python -c "import pandas; import flask; import requests; print('All dependencies imported successfully')" || echo "WARNING: Could not import all required dependencies"

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