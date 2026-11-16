#!/bin/bash

# ============================================
# OnionGate Installation Script
# Debian-based and Arch-based Linux
# ============================================

set -Eeuo pipefail

ONIONGATE_DIR="/etc/oniongate"
TOR_USER=""
TOR_GROUP=""
INSTALL_BIN="/usr/local/bin/oniongate"
UNINSTALL_BIN="/usr/local/sbin/oniongate-uninstall"
GUI_ROOT="/opt/oniongate"
GUI_INSTALL_DIR="$GUI_ROOT/gui"
GUI_VENV="$GUI_ROOT/venv"
GUI_LAUNCHER="/usr/local/bin/oniongate-gui"
DESKTOP_FILE="/usr/local/share/applications/oniongate.desktop"
TOR_CONTROL_HELPER="/usr/local/lib/oniongate/tor_control.py"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_GUI=true
GUI_INSTALLED=false

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

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                echo "Usage: sudo ./install.sh [--without-gui]"
                echo "  --without-gui  Install only the CLI"
                exit 0
                ;;
            --with-gui)
                INSTALL_GUI=true
                ;;
            --without-gui)
                INSTALL_GUI=false
                ;;
            *)
                die "Unknown installer option: $1"
                ;;
        esac
        shift
    done
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
    DISTRO_LIKE="${DISTRO_LIKE,,}"

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
            dnsutils \
            python3 \
            iptables \
            iproute2 \
            ca-certificates \
            util-linux

    elif [[ "$DISTRO_FAMILY" == "arch" ]]; then

        log_info "Synchronizing package databases..."
        pacman -Sy --needed --noconfirm

        pacman -S --needed --noconfirm \
            tor \
            curl \
            bind-tools \
            python \
            iptables \
            iproute2 \
            ca-certificates \
            util-linux
    fi

    log_success "Core dependencies installed."
}

install_gui() {
    log_info "Installing the optional OnionGate desktop GUI..."
    local required_file
    local python_command
    local gui_python
    local system_pyside6=false
    local gui_files=(
        app.py
        oniongate_gui.py
        backend.py
        diagnostics.py
        connection_manager.py
        country_manager.py
        theme.py
        workers.py
        components/__init__.py
        components/about.py
        components/bridge_selector.py
        components/connection.py
        components/connection_button.py
        components/country_selector.py
        components/dashboard.py
        components/diagnostics.py
        components/power_button.py
        components/settings.py
        components/sidebar.py
        components/status_cards.py
    )
    for required_file in "${gui_files[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/gui/$required_file" ]]; then
            log_warning "GUI source is incomplete ($required_file); continuing with CLI only."
            return 1
        fi
    done

    if [[ "$DISTRO_FAMILY" == "debian" ]]; then
        python_command="python3"
        if ! DEBIAN_FRONTEND=noninteractive apt-get install -y \
            python3 python3-venv python3-pip policykit-1; then
            log_warning "Could not install Python GUI prerequisites; the CLI remains available."
            return 1
        fi
        if apt-cache show python3-pyside6.qtwidgets >/dev/null 2>&1; then
            if DEBIAN_FRONTEND=noninteractive apt-get install -y \
                python3-pyside6.qtwidgets; then
                if python3 -c 'import PySide6.QtWidgets' >/dev/null 2>&1; then
                    system_pyside6=true
                    gui_python="$(command -v python3)"
                fi
            fi
        fi
    else
        python_command="python"
        if ! pacman -S --needed --noconfirm python python-pip polkit; then
            log_warning "Could not install Python GUI prerequisites; the CLI remains available."
            return 1
        fi
        if pacman -Si pyside6 >/dev/null 2>&1; then
            if pacman -S --needed --noconfirm pyside6; then
                if python -c 'import PySide6.QtWidgets' >/dev/null 2>&1; then
                    system_pyside6=true
                    gui_python="$(command -v python)"
                fi
            fi
        fi
    fi

    if [[ "$system_pyside6" != "true" ]]; then
        log_info "A usable distribution PySide6 package was not found; trying an isolated virtual environment."
        if ! install -d -m 0755 "$GUI_ROOT"; then
            log_warning "Could not create the GUI installation directory; the CLI remains available."
            return 1
        fi
        if ! "$python_command" -m venv "$GUI_VENV"; then
            log_warning "Could not create the GUI virtual environment; the CLI remains available."
            return 1
        fi
        if ! "$GUI_VENV/bin/python" -m pip install --upgrade pip PySide6; then
            log_warning "Could not install PySide6 in the virtual environment; the CLI remains available."
            return 1
        fi
        gui_python="$GUI_VENV/bin/python"
    fi

    if ! "$gui_python" -c 'import PySide6.QtWidgets'; then
        log_warning "PySide6 is not importable; the CLI remains available."
        return 1
    fi

    if [[ ! -f "$SCRIPT_DIR/assets/oniongate-banner.png" ]]; then
        log_warning "GUI branding asset is missing; the CLI remains available."
        return 1
    fi
    if ! install -d -m 0755 "$GUI_ROOT" "$GUI_INSTALL_DIR"; then
        log_warning "Could not create the GUI installation directories; the CLI remains available."
        return 1
    fi

    while IFS= read -r -d '' source_file; do
        local relative_path="${source_file#"$SCRIPT_DIR/gui/"}"
        if ! install -D -m 0644 "$source_file" "$GUI_INSTALL_DIR/$relative_path"; then
            log_warning "Could not install GUI source $relative_path; the CLI remains available."
            return 1
        fi
    done < <(find "$SCRIPT_DIR/gui" -type f -name '*.py' -print0)

    if ! install -d -m 0755 "$GUI_ROOT/assets"; then
        log_warning "Could not install GUI assets; the CLI remains available."
        return 1
    fi
    if ! install -m 0644 "$SCRIPT_DIR/assets/oniongate-banner.png" \
        "$GUI_ROOT/assets/oniongate-banner.png"; then
        log_warning "Could not install the GUI banner; the CLI remains available."
        return 1
    fi
    if ! install -d -m 0755 "$(dirname "$GUI_LAUNCHER")"; then
        log_warning "Could not install the GUI launcher; the CLI remains available."
        return 1
    fi
    if ! cat > "$GUI_LAUNCHER" <<EOF
#!/bin/sh
if [ "\$(id -u)" -eq 0 ]; then
    echo "Do not launch the OnionGate graphical application as root." >&2
    exit 1
fi
exec "$gui_python" "$GUI_INSTALL_DIR/app.py" "\$@"
EOF
    then
        log_warning "Could not create the GUI launcher; the CLI remains available."
        return 1
    fi
    if ! chmod 0755 "$GUI_LAUNCHER"; then
        log_warning "Could not make the GUI launcher executable; the CLI remains available."
        return 1
    fi

    if ! install -d -m 0755 "$(dirname "$DESKTOP_FILE")"; then
        log_warning "Could not install the desktop application entry; the CLI remains available."
        return 1
    fi
    if ! cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=OnionGate
Comment=Manage and diagnose the OnionGate Tor gateway
Exec=$GUI_LAUNCHER
Icon=$GUI_ROOT/assets/oniongate-banner.png
Terminal=false
Categories=Network;System;
EOF
    then
        log_warning "Could not create the desktop application entry; the CLI remains available."
        return 1
    fi
    if ! chmod 0644 "$DESKTOP_FILE"; then
        log_warning "Could not set desktop entry permissions; the CLI remains available."
        return 1
    fi

    for required_file in "${gui_files[@]}"; do
        if [[ ! -f "$GUI_INSTALL_DIR/$required_file" ]]; then
            log_warning "GUI source installation is incomplete; the CLI remains available."
            return 1
        fi
    done
    if [[ ! -x "$GUI_LAUNCHER" || ! -f "$DESKTOP_FILE" ]]; then
        log_warning "GUI launcher setup was incomplete; the CLI remains available."
        return 1
    fi
    GUI_INSTALLED=true
    if [[ "$system_pyside6" == "true" ]]; then
        log_success "GUI installed using distribution PySide6 packages."
    else
        log_success "GUI installed in an isolated Python virtual environment."
    fi
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

    [[ ! -L "$ONIONGATE_DIR" && ! -L "$ONIONGATE_DIR/backup" &&
       ! -L "$ONIONGATE_DIR/data" ]] ||
        die "OnionGate configuration paths must not be symbolic links."

    if id debian-tor >/dev/null 2>&1; then
        TOR_USER="debian-tor"
    elif id tor >/dev/null 2>&1; then
        TOR_USER="tor"
    else
        die "Tor service account was not created by the package installation."
    fi
    TOR_GROUP="$(id -gn "$TOR_USER")"

    install -d -o root -g "$TOR_GROUP" -m 0755 "$ONIONGATE_DIR"
    install -d -o root -g root -m 0700 "$ONIONGATE_DIR/backup"
    install -d -o "$TOR_USER" -g "$TOR_GROUP" -m 0700 "$ONIONGATE_DIR/data"

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

install_control_helper() {
    [[ -f "$SCRIPT_DIR/tor_control.py" ]] ||
        die "Tor ControlPort helper is missing from $SCRIPT_DIR"
    install -D -m 0644 "$SCRIPT_DIR/tor_control.py" "$TOR_CONTROL_HELPER"
    log_success "Tor circuit-control helper installed."
}

# ============================================
# Help Documentation
# ============================================

install_help() {

    log_info "Installing help documentation..."

    if [[ -f "$SCRIPT_DIR/help.txt" && ! -e "$ONIONGATE_DIR/help.txt" ]]; then

        install -m 0644 "$SCRIPT_DIR/help.txt" \
            "$ONIONGATE_DIR/help.txt"

        log_success "Help documentation installed."

    elif [[ -f "$ONIONGATE_DIR/help.txt" ]]; then
        log_info "Existing help file found. Preserving it."
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

# ============================================
# Verify Installation
# ============================================

verify_installation() {

    log_info "Verifying OnionGate installation..."

    [[ -x "$INSTALL_BIN" ]] ||
        die "OnionGate executable installation failed."

    [[ -r "$TOR_CONTROL_HELPER" ]] ||
        die "Tor circuit-control helper installation failed."

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

    parse_arguments "$@"
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

    if [[ "$INSTALL_GUI" == "true" ]]; then
        echo ""
        if ! install_gui; then
            log_warning "The optional GUI could not be installed; the CLI installation will continue."
        fi
    fi

    echo ""

    create_config_dir

    echo ""

    install_binary

    echo ""

    install_control_helper

    echo ""

    install_help

    echo ""

    install_config

    echo ""

    install_uninstaller

    echo ""

    verify_installation
    log_success "OnionGate installed successfully."
    echo ""
    log_info "Configuration file: $ONIONGATE_DIR/oniongate.conf"
    log_info "Add your bridges to the configuration file before using bridge options."
    echo ""
    echo "CLI:"
    echo "    sudo oniongate start"
    if [[ "$INSTALL_GUI" == "true" ]]; then
        echo ""
        echo "GUI:"
        if [[ "$GUI_INSTALLED" == "true" ]]; then
            echo "    oniongate-gui"
        else
            echo "    GUI dependencies were unavailable; the CLI is ready to use."
        fi
    else
        echo ""
        log_info "GUI installation was disabled with --without-gui."
    fi
}

# ============================================
# Execute Installer
# ============================================

main "$@"
