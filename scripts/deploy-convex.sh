#!/bin/bash
# Deploy Convex functions to self-hosted backend
# Run this after `docker compose up -d convex` or when functions change

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$PROJECT_DIR/dashboard-ui"

# Check if Convex is running
if ! docker ps | grep -q nightwatch-convex; then
    echo "Starting Convex backend..."
    docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d convex
    sleep 3
fi

# Get admin key from Convex container
echo "Getting admin key from Convex container..."
ADMIN_KEY=$(docker exec nightwatch-convex /convex/generate_admin_key.sh 2>/dev/null | grep "convex-self-hosted" || true)

if [ -z "$ADMIN_KEY" ]; then
    echo "Error: Could not get admin key from Convex container"
    exit 1
fi

echo "Admin key: ${ADMIN_KEY:0:30}..."

# Deploy functions
echo "Deploying Convex functions..."
cd "$DASHBOARD_DIR"

export CONVEX_SELF_HOSTED_URL=http://localhost:3210
export CONVEX_SELF_HOSTED_ADMIN_KEY="$ADMIN_KEY"

npx convex dev --once

echo "Convex functions deployed successfully!"
