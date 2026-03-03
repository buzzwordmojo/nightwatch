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
CERTS_DIR="${CONFIG_DIR}/certs"
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
        npm \
        hostapd \
        dnsmasq \
        avahi-daemon \
        openssl

    # Disable hostapd and dnsmasq system services - Nightwatch manages them directly
    systemctl disable hostapd 2>/dev/null || true
    systemctl stop hostapd 2>/dev/null || true
    systemctl disable dnsmasq 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true

    # Enable avahi for mDNS discovery (nightwatch.local)
    systemctl enable avahi-daemon
    systemctl start avahi-daemon

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
    usermod -aG netdev "$USER"   # Network device management (for hotspot)
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

# Generate CA and server SSL certificates
# Creates a CA cert (for user to install) and a server cert signed by the CA
generate_certificates() {
    log_step "Generating SSL certificates..."

    mkdir -p "$CERTS_DIR"

    local ca_key="${CERTS_DIR}/nightwatch-ca.key"
    local ca_cert="${CERTS_DIR}/nightwatch-ca.crt"
    local server_key="${CERTS_DIR}/nightwatch.key"
    local server_cert="${CERTS_DIR}/nightwatch.crt"

    # Skip if certs already exist
    if [ -f "$ca_cert" ] && [ -f "$server_cert" ]; then
        log_info "SSL certificates already exist, skipping generation"
        return
    fi

    # 1. Generate CA key and certificate
    log_info "Generating CA certificate..."
    openssl genrsa -out "$ca_key" 2048 2>/dev/null
    openssl req -x509 -new -nodes -key "$ca_key" -sha256 -days 3650 \
        -out "$ca_cert" \
        -subj "/CN=Nightwatch CA/O=Nightwatch Monitor" \
        2>/dev/null

    # 2. Generate server key and CSR
    log_info "Generating server certificate..."
    openssl genrsa -out "$server_key" 2048 2>/dev/null
    openssl req -new -key "$server_key" \
        -out "${CERTS_DIR}/nightwatch.csr" \
        -subj "/CN=nightwatch.local/O=Nightwatch Monitor" \
        2>/dev/null

    # 3. Create extension file for SANs
    cat > "${CERTS_DIR}/san.ext" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage=digitalSignature, keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:nightwatch.local,DNS:localhost,IP:127.0.0.1,IP:192.168.4.1
EOF

    # 4. Sign server cert with CA
    openssl x509 -req -in "${CERTS_DIR}/nightwatch.csr" \
        -CA "$ca_cert" -CAkey "$ca_key" -CAcreateserial \
        -out "$server_cert" -days 3650 -sha256 \
        -extfile "${CERTS_DIR}/san.ext" \
        2>/dev/null

    # Cleanup temporary files
    rm -f "${CERTS_DIR}/nightwatch.csr" "${CERTS_DIR}/san.ext" "${CERTS_DIR}/nightwatch-ca.srl"

    # Set secure permissions
    chmod 600 "$ca_key" "$server_key"
    chmod 644 "$ca_cert" "$server_cert"
    chown "$USER:$GROUP" "$CERTS_DIR"/*

    log_info "CA certificate: $ca_cert (install this on devices)"
    log_info "Server certificate: $server_cert"
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
        # Installing from source (non-editable for ProtectHome compatibility)
        "$VENV_DIR/bin/pip" install .
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

# Install Convex backend (native binary, no Docker)
install_convex() {
    log_step "Installing Convex backend..."

    local convex_dir="${INSTALL_DIR}/convex"
    local convex_data="${convex_dir}/data"
    local convex_env="${CONFIG_DIR}/convex.env"

    mkdir -p "$convex_dir" "$convex_data"

    # Download native ARM64 binary if not present
    if [ ! -f "${convex_dir}/convex-local-backend" ]; then
        local arch=$(uname -m)
        local binary_name=""

        case "$arch" in
            aarch64) binary_name="convex-local-backend-aarch64-unknown-linux-gnu.zip" ;;
            x86_64)  binary_name="convex-local-backend-x86_64-unknown-linux-gnu.zip" ;;
            *)
                log_error "Unsupported architecture: $arch"
                log_warn "Skipping Convex installation"
                return
                ;;
        esac

        log_info "Downloading Convex backend for ${arch}..."

        # Get latest release URL
        local release_url=$(curl -sL -o /dev/null -w '%{url_effective}' \
            https://github.com/get-convex/convex-backend/releases/latest)
        local release_tag=$(basename "$release_url")

        local download_url="https://github.com/get-convex/convex-backend/releases/download/${release_tag}/${binary_name}"

        curl -L -o "/tmp/${binary_name}" "$download_url"
        cd /tmp && unzip -o "${binary_name}" convex-local-backend
        mv /tmp/convex-local-backend "${convex_dir}/convex-local-backend"
        rm -f "/tmp/${binary_name}"

        chmod +x "${convex_dir}/convex-local-backend"
        log_info "Convex binary installed"
    else
        log_info "Convex binary already exists, skipping download"
    fi

    # Generate instance secret if not already configured
    if [ ! -f "$convex_env" ]; then
        log_info "Generating Convex instance secret..."

        local instance_secret=$(openssl rand -hex 32)

        # Start backend temporarily to generate admin key
        local temp_pid=""
        su -s /bin/bash "$USER" -c \
            "${convex_dir}/convex-local-backend \
                --instance-name convex-self-hosted \
                --instance-secret ${instance_secret} \
                --local-storage ${convex_data} \
                --port 3210 \
                ${convex_data}/convex.sqlite3" &
        temp_pid=$!
        sleep 3

        # Try to generate admin key using the API
        # The generate_key binary requires the same Rust toolchain, so we
        # derive it from an API call or store the secret for later key generation
        local admin_key="convex-self-hosted|${instance_secret}"

        # Check if we can reach the backend and get a proper key
        if command -v python3 &>/dev/null; then
            # Use Python HMAC to generate proper admin key format
            admin_key=$(python3 -c "
import hmac, hashlib, struct, time, base64
# For now, store the raw secret - admin key will be generated by deploy script
print('convex-self-hosted|${instance_secret}')
" 2>/dev/null || echo "convex-self-hosted|${instance_secret}")
        fi

        kill $temp_pid 2>/dev/null || true
        wait $temp_pid 2>/dev/null || true

        cat > "$convex_env" << ENVEOF
# Convex backend configuration - generated by install.sh
# Do not edit manually unless you know what you're doing
CONVEX_INSTANCE_SECRET=${instance_secret}
CONVEX_ADMIN_KEY=${admin_key}
ENVEOF

        chmod 640 "$convex_env"
        chown root:${GROUP} "$convex_env"

        log_info "Convex credentials saved to $convex_env"
        log_warn "Run 'scripts/deploy-convex.sh --remote pi@nightwatch.local' to deploy functions"
    else
        log_info "Convex credentials already exist, preserving"
    fi

    chown -R "$USER:$GROUP" "$convex_dir"

    log_info "Convex backend installed"
}

# Install systemd services
install_services() {
    log_step "Installing systemd services..."

    # Convex backend service
    cat > /etc/systemd/system/convex-backend.service << EOF
[Unit]
Description=Convex Local Backend
After=network.target
Before=nightwatch.service nightwatch-dashboard.service

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${INSTALL_DIR}/convex
ExecStart=${INSTALL_DIR}/convex/convex-local-backend \\
    --instance-name convex-self-hosted \\
    --instance-secret \${CONVEX_INSTANCE_SECRET} \\
    --local-storage ${INSTALL_DIR}/convex/data \\
    --port 3210 \\
    ${INSTALL_DIR}/convex/data/convex.sqlite3
EnvironmentFile=${CONFIG_DIR}/convex.env
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR}/convex/data
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Main nightwatch service
    cat > /etc/systemd/system/nightwatch.service << EOF
[Unit]
Description=Nightwatch Epilepsy Monitor
After=network.target convex-backend.service
Wants=convex-backend.service

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="CONVEX_URL=http://localhost:3210"
ExecStart=${VENV_DIR}/bin/python -m nightwatch --convex
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${LOG_DIR} ${CONFIG_DIR} /var/lib/misc
PrivateTmp=true

# Network capabilities for hotspot management
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

    # Create dnsmasq lease file with correct ownership
    touch /var/lib/misc/dnsmasq.leases
    chown ${USER}:${GROUP} /var/lib/misc/dnsmasq.leases

    # Dashboard service (if installed)
    cat > /etc/systemd/system/nightwatch-dashboard.service << EOF
[Unit]
Description=Nightwatch Dashboard
After=network.target convex-backend.service
Wants=convex-backend.service

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

    systemctl enable convex-backend.service
    systemctl start convex-backend.service

    # Wait for Convex to be ready
    log_info "Waiting for Convex backend to start..."
    for i in $(seq 1 15); do
        if curl -s --max-time 2 http://localhost:3210/version > /dev/null 2>&1; then
            log_info "Convex backend ready"
            break
        fi
        sleep 2
    done

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
    echo "  convex-backend.service       - Real-time database"
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
    echo "  https://${ip}"
    echo "  https://nightwatch.local"
    echo ""
    echo "Note: You'll need to accept the self-signed certificate warning"
    echo "on first visit to the dashboard."
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
    systemctl stop convex-backend.service 2>/dev/null || true

    # Disable services
    systemctl disable nightwatch.service 2>/dev/null || true
    systemctl disable nightwatch-dashboard.service 2>/dev/null || true
    systemctl disable convex-backend.service 2>/dev/null || true

    # Remove service files
    rm -f /etc/systemd/system/nightwatch.service
    rm -f /etc/systemd/system/nightwatch-dashboard.service
    rm -f /etc/systemd/system/convex-backend.service
    # Clean up legacy service if present
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
    if [ -f "pyproject.toml" ]; then
        "$VENV_DIR/bin/pip" install --upgrade .
    else
        "$VENV_DIR/bin/pip" install --upgrade git+https://github.com/YOUR_USERNAME/nightwatch.git
    fi

    # Update Convex binary
    install_convex

    # Rebuild dashboard if present
    if [ -d "dashboard-ui" ]; then
        install_dashboard
    fi

    # Reinstall service files
    install_services

    # Restart services
    systemctl start convex-backend.service
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
    generate_certificates
    install_python
    install_config
    install_sounds
    install_convex
    install_services
    install_dashboard
    start_services
    print_summary
}

main "$@"
