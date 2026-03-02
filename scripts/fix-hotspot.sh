#!/bin/bash
#
# Fix script to enable hotspot functionality on Nightwatch device
#
# Run as root: sudo ./fix-hotspot.sh
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root: sudo $0"
    exit 1
fi

log_info "Installing hotspot dependencies..."
apt-get update
apt-get install -y hostapd dnsmasq avahi-daemon

log_info "Disabling hostapd/dnsmasq system services (Nightwatch manages them)..."
systemctl disable hostapd 2>/dev/null || true
systemctl stop hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

log_info "Enabling avahi for mDNS (nightwatch.local)..."
systemctl enable avahi-daemon
systemctl start avahi-daemon

log_info "Adding nightwatch user to netdev group..."
usermod -aG netdev nightwatch 2>/dev/null || true

log_info "Creating dnsmasq lease file..."
touch /var/lib/misc/dnsmasq.leases
chown nightwatch:nightwatch /var/lib/misc/dnsmasq.leases

log_info "Updating systemd service..."
cat > /etc/systemd/system/nightwatch.service << 'EOF'
[Unit]
Description=Nightwatch Epilepsy Monitor
After=network.target

[Service]
Type=simple
User=nightwatch
Group=nightwatch
WorkingDirectory=/opt/nightwatch
Environment="PATH=/opt/nightwatch/venv/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/nightwatch/venv/bin/python -m nightwatch
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/nightwatch /var/log/nightwatch /etc/nightwatch /var/lib/misc
PrivateTmp=true

# Network capabilities for hotspot management
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

log_info "Reloading systemd..."
systemctl daemon-reload

log_info "Clearing configured flag to trigger setup mode..."
rm -f /etc/nightwatch/.configured
rm -f /etc/nightwatch/wifi.conf

log_info "Restarting nightwatch service..."
systemctl restart nightwatch

echo ""
log_info "Done! The hotspot should start shortly."
log_info "Look for WiFi network: Nightwatch-XXXX"
echo ""
log_info "To monitor: sudo journalctl -u nightwatch -f"
