
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

    log_info "Checking firewall backups..."

    local backup_dir="$ONIONGATE_DIR/backup"

    if command -v iptables-restore >/dev/null 2>&1 &&
       [[ -f "$backup_dir/iptables.rules.backup" ]]; then

        if iptables-restore < "$backup_dir/iptables.rules.backup"; then
            log_success "IPv4 firewall rules restored."
        else
            log_error "IPv4 firewall restoration failed."
        fi
    else
        log_warning "IPv4 firewall backup unavailable. Leaving current rules unchanged."
    fi

    if command -v ip6tables-restore >/dev/null 2>&1 &&
       [[ -f "$backup_dir/ip6tables.rules.backup" ]]; then

        if ip6tables-restore < "$backup_dir/ip6tables.rules.backup"; then
            log_success "IPv6 firewall rules restored."
        else
            log_error "IPv6 firewall restoration failed."
        fi
    else
        log_warning "IPv6 firewall backup unavailable. Leaving current rules unchanged."
    fi
}

# ============================================
# Restore Network Settings
# ============================================

restore_network_settings() {

    local backup_dir="$ONIONGATE_DIR/backup"

    log_info "Restoring network settings..."

    # Restore IPv6 only if OnionGate saved the original values.
    if [[ -f "$backup_dir/ipv6_all.backup" ]]; then
        local ipv6_all
        ipv6_all="$(<"$backup_dir/ipv6_all.backup")"

        sysctl -w "net.ipv6.conf.all.disable_ipv6=$ipv6_all" \
            >/dev/null 2>&1 ||
            log_warning "Could not restore IPv6 all setting."
    fi

    if [[ -f "$backup_dir/ipv6_default.backup" ]]; then
        local ipv6_default
        ipv6_default="$(<"$backup_dir/ipv6_default.backup")"

        sysctl -w "net.ipv6.conf.default.disable_ipv6=$ipv6_default" \
            >/dev/null 2>&1 ||
            log_warning "Could not restore IPv6 default setting."
    fi

    # Restore DNS configuration.
    if [[ -f "$backup_dir/resolv.conf.backup" ]]; then

        chattr -i /etc/resolv.conf 2>/dev/null || true

        if cp -a "$backup_dir/resolv.conf.backup" /etc/resolv.conf; then
            log_success "DNS configuration restored."
        else
            log_error "DNS configuration restoration failed."
        fi
    else
        log_warning "DNS backup unavailable. Leaving current DNS configuration unchanged."
    fi

    # Restore Tor configuration.
    if [[ -f "$backup_dir/torrc.backup" ]]; then

        local torrc_path="/etc/tor/torrc"

        if [[ -d /etc/tor ]]; then
            if cp -a "$backup_dir/torrc.backup" "$torrc_path"; then
                log_success "Tor configuration restored."
            else
                log_error "Tor configuration restoration failed."
            fi
        else
            log_warning "Tor configuration directory not found."
        fi
    fi
}

# ============================================
# Restore MAC Addresses
# ============================================

restore_mac_addresses() {

    local backup_file="$ONIONGATE_DIR/backup/mac_addresses.backup"

    if [[ ! -f "$backup_file" ]]; then
        log_warning "MAC address backup unavailable. Skipping."
        return
    fi

    log_info "Restoring network interface addresses..."

    while IFS=: read -r iface mac; do

        [[ -n "$iface" && -n "$mac" ]] || continue

        if ! ip link show dev "$iface" >/dev/null 2>&1; then
            log_warning "Interface $iface no longer exists."
            continue
        fi

        ip link set "$iface" down 2>/dev/null || true

        if ip link set "$iface" address "$mac"; then
            log_success "Restored interface: $iface"
        else
            log_warning "Could not restore interface: $iface"
        fi

        ip link set "$iface" up 2>/dev/null || true

    done < "$backup_file"
}

# ============================================
# Stop OnionGate
# ============================================

stop_oniongate() {

    if ! is_running; then
        log_info "OnionGate is not marked as running."
        return
    fi

    log_warning "OnionGate is currently running."
    log_info "Stopping OnionGate..."

    if [[ -x "$INSTALL_BIN" ]]; then

        if "$INSTALL_BIN" stop; then
            log_success "OnionGate stop command completed."
        else
            log_error "OnionGate stop command failed."
            die "Cannot safely continue uninstall while network state may be active."
        fi

    else
        log_error "OnionGate executable is missing."
        die "Cannot safely restore network state without the application's stop command."
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

    log_info "Restoring saved system settings..."

    restore_firewall
    restore_network_settings
    restore_mac_addresses

    log_success "Backup restoration process completed."
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

remove_config_dir() {

    log_info "Removing OnionGate configuration directory..."

    if [[ -d "$ONIONGATE_DIR" ]]; then

        rm -rf -- "$ONIONGATE_DIR"

        log_success "Configuration directory removed: $ONIONGATE_DIR"

    else
        log_info "Configuration directory not found. Skipping."
    fi
}

# ============================================
# Restore Previous Tor Service State
# ============================================

restore_tor_service() {

    log_info "Checking Tor system service..."

    if ! command -v systemctl >/dev/null 2>&1; then
        log_warning "systemctl unavailable. Skipping."
        return
    fi

    if ! systemctl is-system-running >/dev/null 2>&1; then
        log_warning "Systemd is not fully available. Skipping."
        return
    fi

    # Only restore the service if the installer saved its original state.
    local service_backup="$ONIONGATE_DIR/backup/tor_service_state.backup"

    if [[ ! -f "$service_backup" ]]; then
        log_warning "Original Tor service state was not saved."
        log_info "Not enabling or starting Tor automatically."
        return
    fi

    local original_state
    original_state="$(<"$service_backup")"

    case "$original_state" in
        enabled)
            systemctl enable tor.service ||
                log_warning "Could not enable tor.service."
            ;;
        disabled)
            systemctl disable tor.service ||
                log_warning "Could not disable tor.service."
            ;;
        *)
            log_warning "Unknown previous Tor service state."
            ;;
    esac

    log_success "Tor service state restoration completed."
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

    # Restore only when backups exist.
    if [[ -d "$ONIONGATE_DIR/backup" ]]; then
        restore_backups
    else
        log_warning "No OnionGate backups found."
    fi

    echo ""

    remove_binary

    echo ""

    remove_config_dir

    echo ""

    # Service state backup is inside the config directory.
    # Therefore, restore it before deleting that directory.
    # See the note below about moving this operation.

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
