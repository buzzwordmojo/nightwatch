#!/bin/bash
#
# Test the Nightwatch setup phase manually
#
# Usage:
#   ./scripts/test-setup.sh           # Full portal test in dev mode
#   ./scripts/test-setup.sh --portal  # Just the portal UI
#   ./scripts/test-setup.sh --vm      # Show VM instructions
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Nightwatch Setup Testing ===${NC}"
echo

case "${1:-}" in
    --portal)
        echo -e "${GREEN}Starting portal-only mode...${NC}"
        echo "Access at: http://localhost:9532/setup"
        echo
        cd "$PROJECT_DIR"
        python -m nightwatch.setup.portal --dev
        ;;

    --vm)
        echo -e "${YELLOW}VM Testing Instructions:${NC}"
        echo
        echo "1. Setup VM (one-time):"
        echo "   ./bin/vm setup"
        echo
        echo "2. Start VM:"
        echo "   ./bin/vm start --fast"
        echo
        echo "3. SSH into VM:"
        echo "   ./bin/vm ssh"
        echo "   # or: ssh -p 2222 pi@localhost (password: raspberry)"
        echo
        echo "4. Inside VM, trigger setup mode:"
        echo "   sudo rm -f /etc/nightwatch/.configured"
        echo "   sudo rm -f /etc/nightwatch/wifi.conf"
        echo
        echo "5. Run nightwatch in setup mode:"
        echo "   cd ~/nightwatch"
        echo "   sudo python -m nightwatch --force-setup --mock-sensors"
        echo
        echo "6. From host, access portal at:"
        echo "   http://localhost:9532/setup"
        echo
        ;;

    --help|-h)
        echo "Usage: $0 [OPTION]"
        echo
        echo "Options:"
        echo "  (none)      Run full setup test in dev mode"
        echo "  --portal    Run just the captive portal UI"
        echo "  --vm        Show VM testing instructions"
        echo "  --help      Show this help"
        echo
        echo "Environment:"
        echo "  NIGHTWATCH_FORCE_SETUP=1  Force setup mode"
        echo "  NIGHTWATCH_MOCK=1         Use mock sensors"
        echo
        ;;

    *)
        echo -e "${GREEN}Running full setup in dev mode...${NC}"
        echo
        echo "This will:"
        echo "  - Start the captive portal on port 9532"
        echo "  - Use mock WiFi scan data"
        echo "  - Save config to a temp directory"
        echo
        echo "Access the setup wizard at:"
        echo -e "  ${BLUE}http://localhost:9532/setup${NC}"
        echo

        cd "$PROJECT_DIR"

        # Check if venv exists
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        fi

        # Run setup portal in dev mode
        python -m nightwatch --force-setup --mock-sensors
        ;;
esac
