#!/bin/bash
#
# Create virtual serial port pairs for hardware simulation
#
# Creates PTY pairs using socat that can be used to simulate
# hardware devices (radar, etc) without physical hardware.
#
# Usage:
#   ./scripts/vm/virtual-serial.sh start    # Create virtual ports
#   ./scripts/vm/virtual-serial.sh stop     # Remove virtual ports
#   ./scripts/vm/virtual-serial.sh status   # Check status
#

set -euo pipefail

# Virtual port paths
RADAR_DEVICE="/tmp/ttyVRADAR"
RADAR_SIM="/tmp/ttyRADAR_SIM"
BCG_DEVICE="/tmp/ttyVBCG"
BCG_SIM="/tmp/ttyBCG_SIM"

PID_FILE="/tmp/nightwatch-virtual-serial.pid"

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

check_socat() {
    if ! command -v socat &> /dev/null; then
        log_error "socat is required but not installed"
        echo ""
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt install socat"
        echo "  macOS:         brew install socat"
        exit 1
    fi
}

start_virtual_ports() {
    check_socat

    if [ -f "$PID_FILE" ]; then
        log_info "Virtual ports may already be running. Stopping first..."
        stop_virtual_ports
    fi

    log_info "Creating virtual serial ports..."

    # Create radar port pair
    socat -d -d \
        pty,raw,echo=0,link="${RADAR_DEVICE}" \
        pty,raw,echo=0,link="${RADAR_SIM}" &
    RADAR_PID=$!

    # Create BCG port pair
    socat -d -d \
        pty,raw,echo=0,link="${BCG_DEVICE}" \
        pty,raw,echo=0,link="${BCG_SIM}" &
    BCG_PID=$!

    # Wait for ports to be created
    sleep 1

    # Save PIDs
    echo "${RADAR_PID} ${BCG_PID}" > "$PID_FILE"

    # Verify
    if [ -L "$RADAR_DEVICE" ] && [ -L "$RADAR_SIM" ]; then
        log_info "Radar ports created:"
        echo "  Device: $RADAR_DEVICE (connect Nightwatch here)"
        echo "  Simulator: $RADAR_SIM (send fake data here)"
    else
        log_error "Failed to create radar ports"
    fi

    if [ -L "$BCG_DEVICE" ] && [ -L "$BCG_SIM" ]; then
        log_info "BCG ports created:"
        echo "  Device: $BCG_DEVICE"
        echo "  Simulator: $BCG_SIM"
    else
        log_error "Failed to create BCG ports"
    fi

    echo ""
    log_info "Virtual ports running in background"
    log_info "Use './scripts/vm/virtual-serial.sh stop' to cleanup"
}

stop_virtual_ports() {
    if [ -f "$PID_FILE" ]; then
        log_info "Stopping virtual serial ports..."
        read -r PIDS < "$PID_FILE"
        for pid in $PIDS; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
        done
        rm -f "$PID_FILE"
    fi

    # Cleanup symlinks
    rm -f "$RADAR_DEVICE" "$RADAR_SIM" "$BCG_DEVICE" "$BCG_SIM" 2>/dev/null || true

    log_info "Virtual ports stopped"
}

show_status() {
    echo "Virtual Serial Port Status"
    echo "==========================="
    echo ""

    if [ -f "$PID_FILE" ]; then
        read -r PIDS < "$PID_FILE"
        running=0
        for pid in $PIDS; do
            if kill -0 "$pid" 2>/dev/null; then
                ((running++))
            fi
        done
        echo "Background processes: $running running"
    else
        echo "Background processes: None"
    fi

    echo ""
    echo "Port Status:"

    for port in "$RADAR_DEVICE" "$RADAR_SIM" "$BCG_DEVICE" "$BCG_SIM"; do
        if [ -L "$port" ]; then
            target=$(readlink "$port")
            echo "  $port -> $target [OK]"
        else
            echo "  $port [NOT FOUND]"
        fi
    done
}

# Main
case "${1:-status}" in
    start)
        start_virtual_ports
        ;;
    stop)
        stop_virtual_ports
        ;;
    status)
        show_status
        ;;
    restart)
        stop_virtual_ports
        sleep 1
        start_virtual_ports
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
