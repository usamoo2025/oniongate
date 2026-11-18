
#!/bin/bash

# ============================================
# OnionGate Uninstallation Script
# Supports Debian-based and Arch-based Linux
# ============================================

set -Eeuo pipefail

ONIONGATE_DIR="/etc/oniongate"
INSTALL_BIN="/usr/local/bin/oniongate"
UNINSTALL_BIN="/usr/local/sbin/oniongate-uninstall"
STATUS_FILE="$ONIONGATE_DIR/oniongate.status"

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
        echo "    Usage: sudo ./uninstall.sh"
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
    log_info "Package manager family: $DISTRO_FAMILY"
}

# ============================================
# Check OnionGate Status
# ============================================

is_running() {

    if [[ -f "$STATUS_FILE" ]] &&
       grep -qiE 'running|active' "$STATUS_FILE" 2>/dev/null; then
        return 0
    fi

    return 1
}

# ============================================
# Restore Firewall Backups
# ============================================

restore_firewall() {
    log_info "No full firewall snapshots are restored; OnionGate stop removes only its tagged rules."
}

# ============================================
# Restore Network Settings
# ============================================

restore_network_settings() {
    log_info "OnionGate does not modify /etc/resolv.conf, system Tor configuration, or IPv6 sysctls."
}

# ============================================
# Restore MAC Addresses
# ============================================

restore_mac_addresses() {
    log_info "MAC addresses are restored by the OnionGate stop command when a run enabled spoofing."
}

# ============================================
# Stop OnionGate
# ============================================

stop_oniongate() {
    if [[ -x "$INSTALL_BIN" ]]; then
        if grep -qE '^[[:space:]]*proxy\)' "$INSTALL_BIN"; then
            if "$INSTALL_BIN" proxy stop; then
                log_success "OnionGate proxy stop command completed."
            else
                log_error "OnionGate proxy stop command failed."
                die "Cannot safely continue uninstall while proxy firewall state may be active."
            fi
        else
            log_warning "Installed CLI predates proxy mode; no proxy-specific cleanup command is available."
        fi

        if "$INSTALL_BIN" stop; then
            log_success "OnionGate stop command completed."
        else
            log_error "OnionGate stop command failed."
            die "Cannot safely continue uninstall while network state may be active."
        fi

    elif is_running; then
        log_error "OnionGate executable is missing."
        die "Cannot safely restore network state without the application's stop command."
    else
        log_warning "OnionGate CLI is unavailable; no system-wide firewall or network restore will be attempted."
    fi

    if is_running; then
        die "OnionGate still reports that it is running. Resolve this before uninstalling."
    fi

    log_success "OnionGate stopped."
}

# ============================================
# Restore Backups
# ============================================

restore_backups() {
    restore_firewall
    restore_network_settings
    restore_mac_addresses
}

# ============================================
# Remove Binary
# ============================================

remove_binary() {

    log_info "Removing OnionGate executable..."

    if [[ -f "$INSTALL_BIN" ]]; then
        rm -f -- "$INSTALL_BIN"
        log_success "Executable removed: $INSTALL_BIN"
    else
        log_info "Executable not found. Skipping."
    fi
}

# ============================================
# Remove Uninstaller
# ============================================

remove_uninstaller() {

    if [[ -f "$UNINSTALL_BIN" ]]; then
        rm -f -- "$UNINSTALL_BIN"
        log_success "Uninstaller removed."
    fi
}

# ============================================
# Remove Configuration
# ============================================

preserve_config_dir() {

    if [[ -d "$ONIONGATE_DIR" ]]; then
        log_info "Preserving OnionGate configuration and data: $ONIONGATE_DIR"
    else
        log_info "Configuration directory not found. Skipping."
    fi
}

remove_gui() {
    log_info "Removing OnionGate GUI application files..."
    rm -f -- /usr/local/bin/oniongate-gui
    rm -f -- /usr/local/share/applications/oniongate.desktop
    rm -f -- /usr/local/lib/oniongate/tor_control.py
    rmdir /usr/local/lib/oniongate 2>/dev/null || true
    rm -rf -- /opt/oniongate/gui /opt/oniongate/venv /opt/oniongate/assets
    rmdir /opt/oniongate 2>/dev/null || true
    log_success "GUI application files removed."
}

# ============================================
# Restore Previous Tor Service State
# ============================================

restore_tor_service() {
    log_info "Tor system service state is left unchanged."
}

# ============================================
# Main
# ============================================

main() {

    show_banner

    check_root

    detect_distribution

    echo ""

    log_info "Starting OnionGate uninstallation..."

    echo ""

    stop_oniongate

    echo ""

    remove_binary

    echo ""

    remove_gui

    echo ""

    preserve_config_dir

    echo ""

    remove_uninstaller

    echo ""

    log_success "============================================"
    log_success "OnionGate has been uninstalled"
    log_success "============================================"

    echo ""

    log_info "The following packages were NOT removed:"
    echo "    - tor"
    echo "    - obfs4proxy (if installed)"
    echo "    - snowflake client (if installed)"
    echo "    - curl"
    echo ""

    log_info "To remove packages manually:"

    if [[ "$DISTRO_FAMILY" == "debian" ]]; then
        echo "    sudo apt remove tor obfs4proxy snowflake-client"
    else
        echo "    sudo pacman -R tor obfs4proxy snowflake"
    fi

    echo ""
}

main "$@"
