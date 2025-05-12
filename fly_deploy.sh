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

# Ask for Polygon.io API key
read -p "Enter your Polygon.io API key: " api_key
if [ -z "$api_key" ]; then
  echo "ERROR: Polygon.io API key is required for the application to function."
  echo "You can get a free API key at https://polygon.io/dashboard/signup"
  exit 1
else
  echo "Using provided API key"
fi

# Set the Polygon.io API key as a secret
echo "Setting Polygon.io API key as a secret..."
flyctl secrets set POLYGON_API_KEY="$api_key" --app "$APP_NAME"

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