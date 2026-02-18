#!/bin/bash
#
# Nightwatch Installer
#
# Installs Nightwatch epilepsy monitoring system on Raspberry Pi.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/.../install.sh | bash
#   # or
#   ./install.sh
#
# Options:
#   --uninstall    Remove Nightwatch
#   --update       Update existing installation
#   --no-dashboard Skip dashboard installation (Python only)
#

set -euo pipefail

# Configuration
INSTALL_DIR="/opt/nightwatch"
CONFIG_DIR="/etc/nightwatch"
DATA_DIR="/var/lib/nightwatch"
LOG_DIR="/var/log/nightwatch"
VENV_DIR="${INSTALL_DIR}/venv"
USER="nightwatch"
GROUP="nightwatch"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root: sudo ./install.sh"
        exit 1
    fi
}

# Check if running on Raspberry Pi
check_platform() {
    if [ ! -f /proc/device-tree/model ]; then
        log_warn "Not running on Raspberry Pi - some features may not work"
        return
    fi

    local model=$(cat /proc/device-tree/model)
    log_info "Detected: $model"
}

# Install system dependencies
install_dependencies() {
    log_step "Installing system dependencies..."

    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libzmq3-dev \
        libasound2-dev \
        portaudio19-dev \
        libsndfile1 \
        git \
        curl \
        nodejs \
        npm

    log_info "System dependencies installed"
}

# Create nightwatch user
create_user() {
    log_step "Creating nightwatch user..."

    if id "$USER" &>/dev/null; then
        log_info "User $USER already exists"
    else
        useradd --system --home-dir "$INSTALL_DIR" --shell /bin/false "$USER"
        log_info "Created user: $USER"
    fi

    # Add to required groups for hardware access
    usermod -aG dialout "$USER"  # Serial/UART access
    usermod -aG audio "$USER"    # Audio device access
    usermod -aG gpio "$USER" 2>/dev/null || true  # GPIO access (may not exist)
}

# Create directories
create_directories() {
    log_step "Creating directories..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "${INSTALL_DIR}/sounds"

    chown -R "$USER:$GROUP" "$INSTALL_DIR"
    chown -R "$USER:$GROUP" "$DATA_DIR"
    chown -R "$USER:$GROUP" "$LOG_DIR"

    log_info "Directories created"
}

# Install Python package
install_python() {
    log_step "Installing Python package..."

    # Create virtual environment
    python3 -m venv "$VENV_DIR"

    # Upgrade pip
    "$VENV_DIR/bin/pip" install --upgrade pip wheel

    # Install nightwatch
    if [ -f "pyproject.toml" ]; then
        # Installing from source
        "$VENV_DIR/bin/pip" install -e .
    else
        # Installing from git
        "$VENV_DIR/bin/pip" install git+https://github.com/YOUR_USERNAME/nightwatch.git
    fi

    chown -R "$USER:$GROUP" "$VENV_DIR"

    log_info "Python package installed"
}

# Install default configuration
install_config() {
    log_step "Installing configuration..."

    local config_file="${CONFIG_DIR}/config.yaml"

    if [ -f "$config_file" ]; then
        log_info "Config already exists, preserving: $config_file"
        return
    fi

    # Copy default config
    if [ -f "config/default.yaml" ]; then
        cp "config/default.yaml" "$config_file"
    else
        cat > "$config_file" << 'EOF'
# Nightwatch Configuration
# See documentation for all options

system:
  name: "nightwatch"
  log_level: "INFO"
  data_dir: "/var/lib/nightwatch"

detectors:
  radar:
    enabled: true
    device: "/dev/ttyUSB0"
    baud_rate: 256000
    model: "ld2450"

  audio:
    enabled: true
    device: "default"
    sample_rate: 16000

alert_engine:
  detector_timeout_seconds: 10
  alert_cooldown_seconds: 30

  rules:
    - name: "Respiration critical"
      conditions:
        - detector: radar
          field: value.respiration_rate
          operator: "<"
          value: 4
          duration_seconds: 10
      severity: critical
      message: "Respiration rate critically low"

    - name: "Respiration low"
      conditions:
        - detector: radar
          field: value.respiration_rate
          operator: "<"
          value: 8
          duration_seconds: 15
      severity: warning
      message: "Respiration rate low"

notifiers:
  audio:
    enabled: true
    sounds_dir: "/opt/nightwatch/sounds"
    initial_volume: 60

  push:
    enabled: false
    # provider: "pushover"
    # pushover_user_key: ""
    # pushover_api_token: ""
EOF
    fi

    chmod 640 "$config_file"
    chown root:$GROUP "$config_file"

    log_info "Configuration installed: $config_file"
}

# Install systemd services
install_services() {
    log_step "Installing systemd services..."

    # Main nightwatch service
    cat > /etc/systemd/system/nightwatch.service << EOF
[Unit]
Description=Nightwatch Epilepsy Monitor
After=network.target

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/bin"
ExecStart=${VENV_DIR}/bin/python -m nightwatch.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${LOG_DIR}
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Dashboard service (if installed)
    cat > /etc/systemd/system/nightwatch-dashboard.service << EOF
[Unit]
Description=Nightwatch Dashboard
After=network.target nightwatch.service

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${INSTALL_DIR}/dashboard
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Convex sync service
    cat > /etc/systemd/system/nightwatch-convex.service << EOF
[Unit]
Description=Nightwatch Convex Bridge
After=network.target nightwatch.service

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/bin"
ExecStart=${VENV_DIR}/bin/python -m nightwatch.bridge.convex
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload

    log_info "Systemd services installed"
}

# Install dashboard
install_dashboard() {
    if [ "${NO_DASHBOARD:-false}" == "true" ]; then
        log_info "Skipping dashboard installation"
        return
    fi

    log_step "Installing dashboard..."

    local dashboard_dir="${INSTALL_DIR}/dashboard"

    if [ -d "dashboard-ui" ]; then
        # Build from source
        cd dashboard-ui
        npm ci
        npm run build

        # Copy standalone build
        mkdir -p "$dashboard_dir"
        cp -r .next/standalone/* "$dashboard_dir/"
        cp -r .next/static "$dashboard_dir/.next/"
        cp -r public "$dashboard_dir/"

        cd ..
    fi

    chown -R "$USER:$GROUP" "$dashboard_dir"

    log_info "Dashboard installed"
}

# Copy sound files
install_sounds() {
    log_step "Installing sound files..."

    local sounds_dir="${INSTALL_DIR}/sounds"

    if [ -d "sounds" ]; then
        cp -r sounds/* "$sounds_dir/"
        chown -R "$USER:$GROUP" "$sounds_dir"
        log_info "Sound files installed"
    else
        log_warn "No sound files found, using system defaults"
    fi
}

# Enable and start services
start_services() {
    log_step "Starting services..."

    systemctl enable nightwatch.service
    systemctl start nightwatch.service

    if [ "${NO_DASHBOARD:-false}" != "true" ]; then
        systemctl enable nightwatch-dashboard.service
        systemctl start nightwatch-dashboard.service
    fi

    log_info "Services started"
}

# Print summary
print_summary() {
    local ip=$(hostname -I | awk '{print $1}')

    echo ""
    echo "=========================================="
    echo "  Nightwatch Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Services:"
    echo "  nightwatch.service           - Main monitor"
    echo "  nightwatch-dashboard.service - Web dashboard"
    echo ""
    echo "Commands:"
    echo "  sudo systemctl status nightwatch"
    echo "  sudo journalctl -u nightwatch -f"
    echo ""
    echo "Configuration:"
    echo "  ${CONFIG_DIR}/config.yaml"
    echo ""
    echo "Dashboard:"
    echo "  http://${ip}:9530"
    echo "  http://localhost:9530"
    echo ""
    echo "Next steps:"
    echo "  1. Edit ${CONFIG_DIR}/config.yaml"
    echo "  2. Connect radar to USB (should appear as /dev/ttyUSB0)"
    echo "  3. Restart: sudo systemctl restart nightwatch"
    echo ""
}

# Uninstall
uninstall() {
    log_step "Uninstalling Nightwatch..."

    # Stop services
    systemctl stop nightwatch.service 2>/dev/null || true
    systemctl stop nightwatch-dashboard.service 2>/dev/null || true
    systemctl stop nightwatch-convex.service 2>/dev/null || true

    # Disable services
    systemctl disable nightwatch.service 2>/dev/null || true
    systemctl disable nightwatch-dashboard.service 2>/dev/null || true
    systemctl disable nightwatch-convex.service 2>/dev/null || true

    # Remove service files
    rm -f /etc/systemd/system/nightwatch.service
    rm -f /etc/systemd/system/nightwatch-dashboard.service
    rm -f /etc/systemd/system/nightwatch-convex.service
    systemctl daemon-reload

    # Remove installation
    rm -rf "$INSTALL_DIR"

    # Optionally remove config and data
    read -p "Remove configuration and data? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        rm -rf "$DATA_DIR"
        rm -rf "$LOG_DIR"
    fi

    # Remove user
    userdel "$USER" 2>/dev/null || true

    log_info "Nightwatch uninstalled"
}

# Update existing installation
update() {
    log_step "Updating Nightwatch..."

    # Stop services
    systemctl stop nightwatch.service
    systemctl stop nightwatch-dashboard.service 2>/dev/null || true

    # Update Python package
    "$VENV_DIR/bin/pip" install --upgrade git+https://github.com/YOUR_USERNAME/nightwatch.git

    # Rebuild dashboard if present
    if [ -d "dashboard-ui" ]; then
        install_dashboard
    fi

    # Restart services
    systemctl start nightwatch.service
    systemctl start nightwatch-dashboard.service 2>/dev/null || true

    log_info "Nightwatch updated"
}

# Main
main() {
    echo ""
    echo "  _   _ _       _     _               _       _     "
    echo " | \ | (_) __ _| |__ | |___      ____ | |_ ___| |__  "
    echo " |  \| | |/ _\` | '_ \| __\ \ /\ / / _\` | __/ __| '_ \ "
    echo " | |\  | | (_| | | | | |_ \ V  V / (_| | || (__| | | |"
    echo " |_| \_|_|\__, |_| |_|\__| \_/\_/ \__,_|\__\___|_| |_|"
    echo "          |___/                                      "
    echo ""
    echo " Epilepsy Monitoring System Installer"
    echo ""

    # Parse arguments
    case "${1:-install}" in
        --uninstall|-u)
            check_root
            uninstall
            exit 0
            ;;
        --update)
            check_root
            update
            exit 0
            ;;
        --no-dashboard)
            NO_DASHBOARD=true
            ;;
    esac

    check_root
    check_platform
    install_dependencies
    create_user
    create_directories
    install_python
    install_config
    install_sounds
    install_services
    install_dashboard
    start_services
    print_summary
}

main "$@"
