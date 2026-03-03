#!/bin/bash
# Self-update script for Nightwatch on Pi
# Pulls latest code, rebuilds all components, restarts services
#
# Usage: sudo /home/pi/nightwatch/scripts/self-update.sh
#
# This script is called by the Python backend via sudo.
# Progress is written to /var/log/nightwatch/update.log

set -e

REPO_DIR="/home/pi/nightwatch"
VENV="/opt/nightwatch/venv"
DASHBOARD_DEST="/opt/nightwatch/dashboard"
LOG_DIR="/var/log/nightwatch"
LOG_FILE="$LOG_DIR/update.log"
REPO_URL="https://github.com/buzzwordmojo/nightwatch.git"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

log() {
    local msg="$(date '+%Y-%m-%d %H:%M:%S') $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

# Clear previous log
echo "" > "$LOG_FILE"
log "UPDATE STARTED"

# Step 1: Ensure git repo exists
log "STEP 1/7: Checking git repo..."
if [ ! -d "$REPO_DIR/.git" ]; then
    log "Cloning repo to $REPO_DIR..."
    git clone "$REPO_URL" "$REPO_DIR"
    chown -R pi:pi "$REPO_DIR"
fi
log "STEP 1/7: DONE"

# Step 2: Pull latest code
log "STEP 2/7: Pulling latest code..."
cd "$REPO_DIR"
git fetch origin main
git reset --hard origin/main
chown -R pi:pi "$REPO_DIR"
COMMIT=$(git rev-parse --short HEAD)
log "STEP 2/7: DONE (commit: $COMMIT)"

# Step 3: Install Python package
log "STEP 3/7: Installing Python package..."
"$VENV/bin/pip" install --no-deps . 2>&1 | tail -5 | while read line; do log "  pip: $line"; done
log "STEP 3/7: DONE"

# Step 4: Build dashboard
log "STEP 4/7: Building dashboard..."
cd "$REPO_DIR/dashboard-ui"
cp .env.pi .env.local

# Use node from standard locations
export PATH="/usr/local/bin:/usr/bin:$PATH"
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    log "  Using node $NODE_VERSION"
else
    log "ERROR: node not found"
    exit 1
fi

npm ci --production=false 2>&1 | tail -3 | while read line; do log "  npm: $line"; done
npm run build 2>&1 | tail -5 | while read line; do log "  build: $line"; done
log "STEP 4/7: DONE"

# Step 5: Deploy dashboard build
log "STEP 5/7: Deploying dashboard..."
rsync -a --delete .next/standalone/ "$DASHBOARD_DEST/"
rsync -a --delete .next/static/ "$DASHBOARD_DEST/.next/static/"
log "STEP 5/7: DONE"

# Step 6: Deploy Convex functions
log "STEP 6/7: Deploying Convex functions..."
CONVEX_URL="http://localhost:3210"

# Read admin key
if [ -f "/etc/nightwatch/convex.env" ]; then
    ADMIN_KEY=$(grep CONVEX_ADMIN_KEY /etc/nightwatch/convex.env | cut -d= -f2-)
fi

if [ -n "$ADMIN_KEY" ]; then
    # Check if Convex is reachable
    if curl -s --max-time 5 "$CONVEX_URL/version" > /dev/null 2>&1; then
        npx convex deploy --url "$CONVEX_URL" --admin-key "$ADMIN_KEY" 2>&1 | tail -5 | while read line; do log "  convex: $line"; done
        log "STEP 6/7: DONE"
    else
        log "STEP 6/7: SKIPPED (Convex not reachable)"
    fi
else
    log "STEP 6/7: SKIPPED (no admin key)"
fi

# Step 7: Restart services
log "STEP 7/7: Restarting services..."
systemctl restart nightwatch-convex 2>/dev/null || log "  Warning: nightwatch-convex restart failed"
systemctl restart nightwatch-dashboard 2>/dev/null || log "  Warning: nightwatch-dashboard restart failed"
systemctl restart nightwatch 2>/dev/null || log "  Warning: nightwatch restart failed"
log "STEP 7/7: DONE"

log "UPDATE COMPLETE (commit: $COMMIT)"
