#!/bin/bash
set -e

echo "===== Starting Fly.io Deployment Process ====="

# Make sure start.sh is executable
chmod +x start.sh

# Ensure we're using the right app
APP_NAME="stocktracker-besttesttest222"
echo "Deploying to app: $APP_NAME"

# Check if the app exists
if ! flyctl apps list | grep -q "$APP_NAME"; then
  echo "App $APP_NAME doesn't exist, please create it first with:"
  echo "flyctl apps create --name $APP_NAME"
  exit 1
fi

# Set regions (try a few reliable ones)
echo "Setting regions..."
flyctl regions set sjc ord dfw

# Deploy with a longer timeout and verbose output
echo "Starting deployment (this may take a few minutes)..."
flyctl deploy --app "$APP_NAME" \
  --wait-timeout 300 \
  --strategy rolling \
  --remote-only \
  --verbose

# Check deployment status
echo "Checking deployment status..."
flyctl status --app "$APP_NAME"

echo "===== Deployment Complete ====="
echo "To view logs: flyctl logs --app $APP_NAME"
echo "To open app: flyctl open --app $APP_NAME" 