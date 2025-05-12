#!/bin/bash
set -e

# Default to port 8080 if not set
export PORT=${PORT:-8080}

# Print environment info
echo "Starting StockTracker on port: $PORT"
echo "Python: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files: $(ls -la)"

# Execute gunicorn with proper binding
exec gunicorn --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    app:app 