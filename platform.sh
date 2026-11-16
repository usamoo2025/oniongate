
#!/bin/bash
# OnionGate platform compatibility layer

detect_platform() {
    if [[ ! -r /etc/os-release ]]; then
        echo "Cannot identify Linux distribution."
        return 1
    fi

    . /etc/os-release

    local distro_info=" ${ID:-} ${ID_LIKE:-} "
    distro_info="${distro_info,,}"

    if [[ "$distro_info" == *" arch "* ]] ||
       [[ "$distro_info" == *"manjaro"* ]] ||
       [[ "$distro_info" == *"endeavouros"* ]]; then
        PKG_FAMILY="arch"
    elif [[ "$distro_info" == *"debian"* ]] ||
         [[ "$distro_info" == *"ubuntu"* ]]; then
        PKG_FAMILY="debian"
    else
        echo "Unsupported distribution: ${PRETTY_NAME:-unknown}"
        return 1
    fi

    export PKG_FAMILY
}

install_base_dependencies() {
    detect_platform || return 1

    case "$PKG_FAMILY" in
        debian)
            apt-get update
            apt-get install -y tor curl iptables
            ;;
        arch)
            pacman -Syu --needed --noconfirm tor curl iptables
            ;;
    esac
}

detect_tor_account() {
    if id debian-tor >/dev/null 2>&1; then
        TOR_USER="debian-tor"
    elif id tor >/dev/null 2>&1; then
        TOR_USER="tor"
    else
        echo "Tor service account was not found."
        return 1
    fi

    TOR_UID="$(id -u "$TOR_USER")"
    export TOR_USER TOR_UID
}

run_as_tor() {
    if ! id "$TOR_USER" >/dev/null 2>&1; then
        echo "Invalid Tor account: $TOR_USER"
        return 1
    fi

    runuser -u "$TOR_USER" -- "$@"
}

detect_torrc() {
    if [[ -f /etc/tor/torrc ]]; then
        TORRC_FILE="/etc/tor/torrc"
    else
        echo "Tor configuration file not found: /etc/tor/torrc"
        return 1
    fi

    export TORRC_FILE
}

