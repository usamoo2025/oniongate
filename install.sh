
#!/bin/bash

# ============================================
# OnionGate Installation Script
# Debian-based and Arch-based Linux
# ============================================

set -Eeuo pipefail

ONIONGATE_DIR="/etc/oniongate"
INSTALL_BIN="/usr/local/bin/oniongate"
UNINSTALL_BIN="/usr/local/sbin/oniongate-uninstall"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ============================================
# Colors
# ============================================

WHITE='\033[1;37m'
GREEN='\033[0;32m'
RED='\033[0;31m'
ORANGE='\033[0;33m'
NC='\033[0m'

# ============================================
# Logging
# ============================================

log_info() {
    echo -e "${WHITE}[*] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

log_error() {
    echo -e "${RED}[-] $1${NC}"
}

log_warning() {
    echo -e "${ORANGE}[!] $1${NC}"
}

die() {
    log_error "$1"
    exit 1
}

# ============================================
# Banner
# ============================================

show_banner() {
    cat << 'EOF'

╔═══════════════════════════════════════════════╗
║                  OnionGate                    ║
║           Anonymous Traffic Gateway           ║
╚═══════════════════════════════════════════════╝

EOF
}

# ============================================
# Root Check
# ============================================

check_root() {
    if [[ "$EUID" -ne 0 ]]; then
        log_error "This script must be run as root"
        echo "    Usage: sudo ./install.sh"
        exit 1
    fi
}

# ============================================
# Distribution Detection
# ============================================

detect_distribution() {

    [[ -r /etc/os-release ]] ||
        die "Cannot identify Linux distribution."

    # shellcheck disable=SC1091
    source /etc/os-release

    DISTRO_ID="${ID,,}"
    DISTRO_LIKE="${ID_LIKE:-}"

    case "$DISTRO_ID" in
        debian|ubuntu|linuxmint|kali|pop|elementary|zorin)
            DISTRO_FAMILY="debian"
            ;;
        arch|manjaro|endeavouros|garuda|artix)
            DISTRO_FAMILY="arch"
            ;;
        *)
            if [[ " $DISTRO_LIKE " == *" debian "* ]] ||
               [[ " $DISTRO_LIKE " == *" ubuntu "* ]]; then
                DISTRO_FAMILY="debian"
            elif [[ " $DISTRO_LIKE " == *" arch "* ]]; then
                DISTRO_FAMILY="arch"
            else
                die "Unsupported distribution: ${PRETTY_NAME:-$DISTRO_ID}"
            fi
            ;;
    esac

    log_success "Detected distribution: ${PRETTY_NAME:-$DISTRO_ID}"
    log_info "Package manager: $DISTRO_FAMILY"
}

# ============================================
# Package Manager Check
# ============================================

check_package_manager() {

    case "$DISTRO_FAMILY" in
        debian)
            command -v apt-get >/dev/null 2>&1 ||
                die "apt-get not found."
            ;;
        arch)
            command -v pacman >/dev/null 2>&1 ||
                die "pacman not found."
            ;;
    esac
}

# ============================================
# Core Dependencies
# ============================================

install_dependencies() {

    log_info "Installing core dependencies..."

    if [[ "$DISTRO_FAMILY" == "debian" ]]; then

        log_info "Updating package lists..."
        apt-get update

        DEBIAN_FRONTEND=noninteractive apt-get install -y \
            tor \
            curl \
            iptables \
            iproute2 \
            ca-certificates

    elif [[ "$DISTRO_FAMILY" == "arch" ]]; then

        log_info "Synchronizing package databases..."
        pacman -Sy --needed --noconfirm

        pacman -S --needed --noconfirm \
            tor \
            curl \
            iptables \
            iproute2 \
            ca-certificates
    fi

    log_success "Core dependencies installed."
}

# ============================================
# Optional Tor Dependencies
# ============================================

install_optional_dependencies() {

    log_info "Checking optional Tor bridge dependencies..."

    if [[ "$DISTRO_FAMILY" == "debian" ]]; then
        OPTIONAL_PACKAGES=(
            obfs4proxy
            snowflake-client
        )
    else
        OPTIONAL_PACKAGES=(
            obfs4proxy
            snowflake
        )
    fi

    for package in "${OPTIONAL_PACKAGES[@]}"; do

        if [[ "$DISTRO_FAMILY" == "debian" ]]; then

            if apt-cache show "$package" >/dev/null 2>&1; then
                log_info "Installing $package..."

                if ! DEBIAN_FRONTEND=noninteractive apt-get install -y "$package"; then
                    log_warning "Could not install $package."
                fi
            else
                log_warning "$package is unavailable in configured repositories."
            fi

        else

            if pacman -Si "$package" >/dev/null 2>&1; then
                log_info "Installing $package..."

                if ! pacman -S --needed --noconfirm "$package"; then
                    log_warning "Could not install $package."
                fi
            else
                log_warning "$package is unavailable in configured repositories."
            fi

        fi

    done

    log_success "Optional dependency check completed."
}

# ============================================
# Configuration Directory
# ============================================

create_config_dir() {

    log_info "Creating OnionGate configuration directory..."

    mkdir -p "$ONIONGATE_DIR"
    mkdir -p "$ONIONGATE_DIR/backup"

    chmod 755 "$ONIONGATE_DIR"
    chmod 700 "$ONIONGATE_DIR/backup"

    log_success "Configuration directory created: $ONIONGATE_DIR"
}

# ============================================
# Main Binary
# ============================================

install_binary() {

    log_info "Installing OnionGate executable..."

    local MAIN_FILE="$SCRIPT_DIR/oniongate"

    if [[ ! -f "$MAIN_FILE" ]]; then
        MAIN_FILE="$SCRIPT_DIR/torgate"
    fi

    [[ -f "$MAIN_FILE" ]] ||
        die "OnionGate executable not found in $SCRIPT_DIR"

    install -m 0755 "$MAIN_FILE" "$INSTALL_BIN"

    log_success "OnionGate binary installed to $INSTALL_BIN"
}

# ============================================
# Help Documentation
# ============================================

install_help() {

    log_info "Installing help documentation..."

    if [[ -f "$SCRIPT_DIR/help.txt" ]]; then

        install -m 0644 "$SCRIPT_DIR/help.txt" \
            "$ONIONGATE_DIR/help.txt"

        log_success "Help documentation installed."

    else
        log_warning "help.txt not found. Skipping."
    fi
}

# ============================================
# Configuration File
# ============================================

install_config() {

    log_info "Installing configuration file..."

    local CONFIG_SOURCE=""

    if [[ -f "$SCRIPT_DIR/oniongate.conf" ]]; then
        CONFIG_SOURCE="$SCRIPT_DIR/oniongate.conf"
    elif [[ -f "$SCRIPT_DIR/torgate.conf" ]]; then
        CONFIG_SOURCE="$SCRIPT_DIR/torgate.conf"
    else
        die "oniongate.conf or torgate.conf not found in $SCRIPT_DIR"
    fi

    local CONFIG_DEST="$ONIONGATE_DIR/oniongate.conf"

    if [[ -f "$CONFIG_DEST" ]]; then
        log_info "Existing configuration found. Preserving it."
        return
    fi

    install -m 0600 "$CONFIG_SOURCE" "$CONFIG_DEST"

    log_success "Configuration installed: $CONFIG_DEST"
}

# ============================================
# Install Uninstaller
# ============================================

install_uninstaller() {

    log_info "Installing OnionGate uninstaller..."

    if [[ -f "$SCRIPT_DIR/uninstall.sh" ]]; then

        install -d -m 0755 "$(dirname "$UNINSTALL_BIN")"

        install -m 0755 "$SCRIPT_DIR/uninstall.sh" \
            "$UNINSTALL_BIN"

        log_success "Uninstaller installed."

    else
        log_warning "uninstall.sh not found. Skipping."
    fi
}

# ============================================
# Tor Service Handling
# ============================================

disable_systemd_tor() {

    log_info "Checking existing Tor service..."

    if ! command -v systemctl >/dev/null 2>&1; then
        log_warning "systemctl not found. Skipping."
        return
    fi

    if ! systemctl is-system-running >/dev/null 2>&1; then
        log_warning "Systemd is not fully available. Skipping."
        return
    fi

    if systemctl is-active --quiet tor.service; then
        log_warning "tor.service is active."
        log_warning "Stopping it to avoid conflict with OnionGate."
        systemctl stop tor.service
    fi

    if systemctl is-enabled --quiet tor.service; then
        systemctl disable tor.service
    fi

    log_success "Tor service check completed."
}

# ============================================
# Verify Installation
# ============================================

verify_installation() {

    log_info "Verifying OnionGate installation..."

    [[ -x "$INSTALL_BIN" ]] ||
        die "OnionGate executable installation failed."

    command -v tor >/dev/null 2>&1 ||
        die "Tor executable was not found."

    [[ -f "$ONIONGATE_DIR/oniongate.conf" ]] ||
        die "OnionGate configuration is missing."

    log_success "Installation verification completed."
}

# ============================================
# Main Installation
# ============================================

main() {

    show_banner

    check_root

    detect_distribution

    check_package_manager

    echo ""

    log_info "Starting OnionGate installation..."

    echo ""

    install_dependencies

    echo ""

    install_optional_dependencies

    echo ""

    create_config_dir

    echo ""

    install_binary

    echo ""

    install_help

    echo ""

    install_config

    echo ""

    install_uninstaller

    echo ""

    disable_systemd_tor

    echo ""

    verify_installation
}

# ============================================
# Installation Completion
# ============================================

log_success "============================================"
log_success "       OnionGate installation complete!"
log_success "============================================"
echo ""
log_info "Configuration file: $ONIONGATE_DIR/oniongate.conf"
log_info "Add your bridges to the configuration file before using bridge options."
echo ""
log_info "Usage:"
echo "    sudo oniongate start           # Direct connection"
echo "    sudo oniongate start -o        # Use obfs4 bridge"
echo "    sudo oniongate start -s        # Use snowflake bridge"
echo "    sudo oniongate start -m        # Use meek_lite bridge"
echo "    sudo oniongate stop            # Stop and restore"
echo "    sudo oniongate help            # Show help"
echo ""

# ============================================
# Execute Installer
# ============================================

main "$@"
