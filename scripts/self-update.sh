#!/bin/bash
# Self-update script for Nightwatch on Pi
# Pulls latest code, rebuilds all components, restarts services
#
# Usage: sudo /home/pi/nightwatch/scripts/self-update.sh
#
# This script is called by the Python backend via sudo.
# Progress is written to /var/log/nightwatch/update.log

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
    echo "$msg" >> "$LOG_FILE"
}

fail() {
    log "ERROR: $1"
    exit 1
}

# Ensure git trusts the repo directory (we run as root, repo owned by pi)
git config --global --add safe.directory "$REPO_DIR" 2>/dev/null

# Clear previous log
echo "" > "$LOG_FILE"
log "UPDATE STARTED"

# Step 1: Ensure git repo exists
log "STEP 1/7: Checking git repo..."
if [ ! -d "$REPO_DIR/.git" ]; then
    log "Cloning repo to $REPO_DIR..."
    git clone "$REPO_URL" "$REPO_DIR" >> "$LOG_FILE" 2>&1 || fail "git clone failed"
    chown -R pi:pi "$REPO_DIR"
fi
log "STEP 1/7: DONE"

# Step 2: Pull latest code
log "STEP 2/7: Pulling latest code..."
cd "$REPO_DIR"
git fetch origin main >> "$LOG_FILE" 2>&1 || fail "git fetch failed"
git reset --hard origin/main >> "$LOG_FILE" 2>&1 || fail "git reset failed"
chown -R pi:pi "$REPO_DIR"
COMMIT=$(git rev-parse --short HEAD)
log "STEP 2/7: DONE (commit: $COMMIT)"

# Step 3: Install Python package
log "STEP 3/7: Installing Python package..."
"$VENV/bin/pip" install --no-deps . >> "$LOG_FILE" 2>&1 || fail "pip install failed"
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
    fail "node not found"
fi

log "  Running npm ci..."
npm ci --production=false >> "$LOG_FILE" 2>&1 || fail "npm ci failed"
log "  Running npm run build..."
npm run build >> "$LOG_FILE" 2>&1 || fail "npm run build failed"
log "STEP 4/7: DONE"

# Step 5: Deploy dashboard build
log "STEP 5/7: Deploying dashboard..."
rsync -a --delete .next/standalone/ "$DASHBOARD_DEST/" || fail "rsync standalone failed"
rsync -a --delete .next/static/ "$DASHBOARD_DEST/.next/static/" || fail "rsync static failed"
log "STEP 5/7: DONE"

# Step 6: Deploy Convex functions
log "STEP 6/7: Deploying Convex functions..."
CONVEX_URL="http://localhost:3210"

# Read admin key
if [ -f "/etc/nightwatch/convex.env" ]; then
    ADMIN_KEY=$(grep CONVEX_ADMIN_KEY /etc/nightwatch/convex.env | cut -d= -f2-)
fi

if [ -n "$ADMIN_KEY" ]; then
    # Convex CLI needs Node 20+; check before attempting
    NODE_MAJOR=$(node --version | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 20 ] 2>/dev/null; then
        if curl -s --max-time 5 "$CONVEX_URL/version" > /dev/null 2>&1; then
            npx convex deploy --url "$CONVEX_URL" --admin-key "$ADMIN_KEY" >> "$LOG_FILE" 2>&1 || log "  Warning: convex deploy failed"
            log "STEP 6/7: DONE"
        else
            log "STEP 6/7: SKIPPED (Convex not reachable)"
        fi
    else
        log "STEP 6/7: SKIPPED (Node $NODE_VERSION too old for Convex CLI, deploy from dev machine)"
    fi
else
    log "STEP 6/7: SKIPPED (no admin key)"
fi

# Step 7: Restart services
log "STEP 7/7: Restarting services..."
systemctl restart convex-backend >> "$LOG_FILE" 2>&1 || true
systemctl restart nightwatch-dashboard >> "$LOG_FILE" 2>&1 || true
log "STEP 7/7: DONE"

log "UPDATE COMPLETE (commit: $COMMIT)"

# Restart the main nightwatch service last — this is the caller's parent
systemctl restart nightwatch >> "$LOG_FILE" 2>&1 || true
