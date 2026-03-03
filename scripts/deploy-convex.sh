#!/bin/bash
# Deploy Convex functions to self-hosted backend
#
# For local development:
#   ./scripts/deploy-convex.sh
#
# For remote Pi deployment:
#   ./scripts/deploy-convex.sh --remote pi@nightwatch.local
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$PROJECT_DIR/dashboard-ui"

CONVEX_PORT=3210
REMOTE_HOST=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --remote)
            REMOTE_HOST="$2"
            shift 2
            ;;
        --port)
            CONVEX_PORT="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--remote user@host] [--port PORT]"
            exit 1
            ;;
    esac
done

# Determine Convex URL
if [ -n "$REMOTE_HOST" ]; then
    # Extract hostname/IP from user@host
    CONVEX_HOST=$(echo "$REMOTE_HOST" | sed 's/.*@//')
    CONVEX_URL="http://${CONVEX_HOST}:${CONVEX_PORT}"
    echo "Deploying to remote Convex at $CONVEX_URL..."

    # Get admin key from remote
    ADMIN_KEY=$(ssh "$REMOTE_HOST" "cat /etc/nightwatch/convex.env 2>/dev/null | grep CONVEX_ADMIN_KEY | cut -d= -f2-")
else
    CONVEX_URL="http://localhost:${CONVEX_PORT}"
    echo "Deploying to local Convex at $CONVEX_URL..."

    # Get admin key from local env file
    if [ -f "/etc/nightwatch/convex.env" ]; then
        ADMIN_KEY=$(grep CONVEX_ADMIN_KEY /etc/nightwatch/convex.env | cut -d= -f2-)
    elif [ -f "$PROJECT_DIR/.convex.env" ]; then
        ADMIN_KEY=$(grep CONVEX_ADMIN_KEY "$PROJECT_DIR/.convex.env" | cut -d= -f2-)
    fi
fi

if [ -z "$ADMIN_KEY" ]; then
    echo "Error: Could not find CONVEX_ADMIN_KEY"
    echo "Check /etc/nightwatch/convex.env or set it manually:"
    echo "  CONVEX_SELF_HOSTED_ADMIN_KEY=... npx convex deploy --url $CONVEX_URL"
    exit 1
fi

echo "Admin key: ${ADMIN_KEY:0:30}..."

# Check Convex is reachable
if ! curl -s --max-time 5 "$CONVEX_URL/version" > /dev/null 2>&1; then
    echo "Error: Convex not reachable at $CONVEX_URL"
    echo "Make sure convex-backend service is running"
    exit 1
fi

echo "Convex is running, deploying functions..."

# Deploy functions
cd "$DASHBOARD_DIR"
npx convex deploy \
    --url "$CONVEX_URL" \
    --admin-key "$ADMIN_KEY"

echo "Convex functions deployed successfully!"
