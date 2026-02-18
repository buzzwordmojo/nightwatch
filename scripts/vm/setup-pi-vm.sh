#!/bin/bash
#
# Nightwatch Pi VM Setup Script
#
# Downloads and configures a Raspberry Pi OS image for QEMU testing.
# This enables testing the full setup flow without physical hardware.
#
# Usage:
#   ./scripts/vm/setup-pi-vm.sh [--force]
#
# Options:
#   --force    Re-download and reconfigure even if image exists
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VM_DIR="${PROJECT_ROOT}/.pi-vm"

# Pi OS image settings
PI_OS_VERSION="2024-03-15"
PI_OS_URL="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-${PI_OS_VERSION}/${PI_OS_VERSION}-raspios-bookworm-arm64-lite.img.xz"
IMAGE_NAME="pi-os.img"
IMAGE_SIZE="8G"

# Default credentials
PI_USER="pi"
PI_PASS="raspberry"
# Pre-hashed password for userconf.txt (raspberry)
PI_PASS_HASH='$6$rBoByrWRKMY1EHFy$ho.LISnfm83CLBWBE/yqJ6Lq1TinRlxw/ImMTPcvvMuUfhQYcMmFnpFXUPowjy2br1NA0IACwF9JKugSNuHoe0'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing=()

    if ! command -v qemu-system-aarch64 &> /dev/null; then
        missing+=("qemu-system-arm")
    fi

    if ! command -v qemu-img &> /dev/null; then
        missing+=("qemu-utils")
    fi

    if ! command -v xz &> /dev/null; then
        missing+=("xz-utils")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        echo ""
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt install ${missing[*]}"
        echo "  macOS:         brew install qemu"
        echo "  Fedora:        sudo dnf install qemu-system-arm qemu-img"
        exit 1
    fi

    log_info "All dependencies satisfied"
}

download_image() {
    local image_path="${VM_DIR}/${IMAGE_NAME}"
    local compressed_path="${VM_DIR}/pi-os.img.xz"

    if [ -f "$image_path" ] && [ "$FORCE" != "true" ]; then
        log_info "Image already exists: $image_path"
        return 0
    fi

    log_info "Downloading Raspberry Pi OS..."
    mkdir -p "$VM_DIR"

    if [ -f "$compressed_path" ] && [ "$FORCE" != "true" ]; then
        log_info "Using cached compressed image"
    else
        wget -O "$compressed_path" "$PI_OS_URL" || {
            log_error "Failed to download Pi OS image"
            exit 1
        }
    fi

    log_info "Extracting image (this may take a while)..."
    xz -dk "$compressed_path" || {
        log_error "Failed to extract image"
        exit 1
    }

    mv "${compressed_path%.xz}" "$image_path"

    log_info "Resizing image to $IMAGE_SIZE..."
    qemu-img resize "$image_path" "$IMAGE_SIZE"

    log_info "Image ready: $image_path"
}

extract_kernel() {
    local image_path="${VM_DIR}/${IMAGE_NAME}"
    local kernel_path="${VM_DIR}/kernel8.img"
    local dtb_path="${VM_DIR}/bcm2710-rpi-3-b-plus.dtb"

    if [ -f "$kernel_path" ] && [ -f "$dtb_path" ] && [ "$FORCE" != "true" ]; then
        log_info "Kernel and DTB already extracted"
        return 0
    fi

    log_info "Extracting kernel and device tree..."

    # Create mount point
    local mount_point=$(mktemp -d)

    # Find the boot partition offset
    local boot_offset=$(fdisk -l "$image_path" 2>/dev/null | grep "^${image_path}1" | awk '{print $2}')
    boot_offset=$((boot_offset * 512))

    # Mount boot partition
    sudo mount -o loop,offset=$boot_offset "$image_path" "$mount_point" || {
        log_error "Failed to mount boot partition"
        rmdir "$mount_point"
        exit 1
    }

    # Copy kernel and DTB
    sudo cp "$mount_point/kernel8.img" "$kernel_path"
    sudo cp "$mount_point/bcm2710-rpi-3-b-plus.dtb" "$dtb_path"
    sudo chown $USER:$USER "$kernel_path" "$dtb_path"

    # Unmount
    sudo umount "$mount_point"
    rmdir "$mount_point"

    log_info "Kernel extracted: $kernel_path"
    log_info "DTB extracted: $dtb_path"
}

configure_image() {
    local image_path="${VM_DIR}/${IMAGE_NAME}"

    log_info "Configuring image for headless boot..."

    # Create mount point
    local mount_point=$(mktemp -d)

    # Mount boot partition
    local boot_offset=$(fdisk -l "$image_path" 2>/dev/null | grep "^${image_path}1" | awk '{print $2}')
    boot_offset=$((boot_offset * 512))

    sudo mount -o loop,offset=$boot_offset "$image_path" "$mount_point" || {
        log_error "Failed to mount boot partition"
        rmdir "$mount_point"
        exit 1
    }

    # Enable SSH
    sudo touch "$mount_point/ssh"
    log_info "SSH enabled"

    # Set default user credentials
    echo "${PI_USER}:${PI_PASS_HASH}" | sudo tee "$mount_point/userconf.txt" > /dev/null
    log_info "Default user configured (${PI_USER}:${PI_PASS})"

    # Unmount
    sudo umount "$mount_point"
    rmdir "$mount_point"

    log_info "Image configured for headless boot"
}

create_launch_scripts() {
    log_info "Creating launch scripts..."

    # Accurate raspi3b emulation (slower)
    cat > "${VM_DIR}/start-pi.sh" << 'SCRIPT'
#!/bin/bash
#
# Start Pi VM with accurate raspi3b emulation
# This is slower but more accurate for hardware testing
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

qemu-system-aarch64 \
    -machine raspi3b \
    -cpu cortex-a72 \
    -m 1G \
    -smp 4 \
    -kernel "${SCRIPT_DIR}/kernel8.img" \
    -dtb "${SCRIPT_DIR}/bcm2710-rpi-3-b-plus.dtb" \
    -drive "file=${SCRIPT_DIR}/pi-os.img,format=raw,if=sd" \
    -append "root=/dev/mmcblk0p2 rootfstype=ext4 rw rootwait console=ttyAMA0,115200" \
    -netdev user,id=net0,hostfwd=tcp::9522-:22,hostfwd=tcp::9530-:9530,hostfwd=tcp::9531-:9531,hostfwd=tcp::9532-:80 \
    -device usb-net,netdev=net0 \
    -nographic

echo ""
echo "VM exited. Connect via: ssh -p 2222 pi@localhost"
SCRIPT
    chmod +x "${VM_DIR}/start-pi.sh"

    # Fast virt machine (less accurate but much faster)
    cat > "${VM_DIR}/start-pi-fast.sh" << 'SCRIPT'
#!/bin/bash
#
# Start Pi VM with fast virt machine type
# Use this for application testing (not hardware-specific tests)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Download UEFI firmware if needed
if [ ! -f "${SCRIPT_DIR}/QEMU_EFI.fd" ]; then
    echo "Downloading UEFI firmware..."
    wget -q -O "${SCRIPT_DIR}/QEMU_EFI.fd" \
        "http://snapshots.linaro.org/components/kernel/leg-virt-tianocore-edk2-upstream/latest/QEMU-AARCH64/RELEASE_GCC5/QEMU_EFI.fd" || {
        echo "Failed to download UEFI firmware"
        exit 1
    }
fi

qemu-system-aarch64 \
    -machine virt \
    -cpu cortex-a72 \
    -m 2G \
    -smp 4 \
    -bios "${SCRIPT_DIR}/QEMU_EFI.fd" \
    -drive "file=${SCRIPT_DIR}/pi-os.img,format=raw,if=virtio" \
    -netdev user,id=net0,hostfwd=tcp::9522-:22,hostfwd=tcp::9530-:9530,hostfwd=tcp::9531-:9531,hostfwd=tcp::9532-:80 \
    -device virtio-net-pci,netdev=net0 \
    -nographic

echo ""
echo "VM exited. Connect via: ssh -p 2222 pi@localhost"
SCRIPT
    chmod +x "${VM_DIR}/start-pi-fast.sh"

    log_info "Launch scripts created:"
    echo "  ${VM_DIR}/start-pi.sh       (accurate, slow)"
    echo "  ${VM_DIR}/start-pi-fast.sh  (fast, less accurate)"
}

create_helper_script() {
    # Create a convenience wrapper in bin/
    mkdir -p "${PROJECT_ROOT}/bin"

    cat > "${PROJECT_ROOT}/bin/vm" << 'SCRIPT'
#!/bin/bash
#
# Nightwatch VM management helper
#
# Usage:
#   ./bin/vm start [--fast]     Start the Pi VM
#   ./bin/vm ssh                SSH into running VM
#   ./bin/vm setup              Initial VM setup
#   ./bin/vm test               Run integration tests in VM
#   ./bin/vm simulate <scenario> Run a simulation scenario
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VM_DIR="${PROJECT_ROOT}/.pi-vm"

case "${1:-help}" in
    start)
        if [ "${2:-}" == "--fast" ]; then
            exec "${VM_DIR}/start-pi-fast.sh"
        else
            exec "${VM_DIR}/start-pi.sh"
        fi
        ;;
    ssh)
        exec ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null pi@localhost
        ;;
    setup)
        exec "${PROJECT_ROOT}/scripts/vm/setup-pi-vm.sh"
        ;;
    test)
        echo "Running integration tests in VM..."
        ssh -p 2222 pi@localhost "cd ~/nightwatch && pytest tests/integration/ -v"
        ;;
    simulate)
        scenario="${2:-normal}"
        echo "Running simulation: $scenario"
        python3 "${PROJECT_ROOT}/scripts/vm/radar-simulator.py" --scenario "$scenario"
        ;;
    help|--help|-h|*)
        echo "Nightwatch VM Management"
        echo ""
        echo "Usage: ./bin/vm <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start [--fast]        Start the Pi VM"
        echo "  ssh                   SSH into running VM"
        echo "  setup                 Initial VM setup (download image, etc)"
        echo "  test                  Run integration tests in VM"
        echo "  simulate <scenario>   Run a simulation (normal, apnea, seizure)"
        echo ""
        echo "Examples:"
        echo "  ./bin/vm setup        # First-time setup"
        echo "  ./bin/vm start        # Start with accurate Pi emulation"
        echo "  ./bin/vm start --fast # Start with fast emulation"
        echo "  ./bin/vm ssh          # Connect to running VM"
        ;;
esac
SCRIPT
    chmod +x "${PROJECT_ROOT}/bin/vm"

    log_info "Helper script created: bin/vm"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "  Pi VM Setup Complete"
    echo "=========================================="
    echo ""
    echo "Quick Start:"
    echo "  1. Start VM:    ./bin/vm start"
    echo "  2. SSH into VM: ./bin/vm ssh"
    echo "  3. Run tests:   ./bin/vm test"
    echo ""
    echo "Port Forwarding:"
    echo "  localhost:9522  -> VM SSH"
    echo "  localhost:9530  -> Dashboard UI"
    echo "  localhost:9531  -> API"
    echo "  localhost:9532  -> Captive Portal"
    echo ""
    echo "Default Credentials:"
    echo "  User: ${PI_USER}"
    echo "  Pass: ${PI_PASS}"
    echo ""
    echo "First boot takes 1-2 minutes. Be patient!"
    echo ""
}

# Parse arguments
FORCE="false"
if [ "${1:-}" == "--force" ]; then
    FORCE="true"
fi

# Main
main() {
    log_info "Setting up Nightwatch Pi VM..."
    echo ""

    check_dependencies
    download_image
    extract_kernel
    configure_image
    create_launch_scripts
    create_helper_script
    print_summary
}

main
