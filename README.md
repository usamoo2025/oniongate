# 🧅 OnionGate

![OnionGate banner](assets/oniongate-banner.png)

<p align="center">
  <strong>An Open-Source Tor Gateway for Linux</strong><br>
  <em>One shared Bash backend with a command-line interface and optional desktop GUI</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
  <img src="https://img.shields.io/badge/Network-Tor-7D4698?style=for-the-badge&logo=torproject&logoColor=white" alt="Tor">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0">
</p>

<p align="center">
  <a href="https://github.com/usamoo2025/oniongate">GitHub Repository</a> •
  <a href="https://github.com/usamoo2025/oniongate/issues">Report an Issue</a> •
  <a href="https://github.com/usamoo2025">GitHub Profile</a>
</p>

---

## About

OnionGate is an independent Linux Tor gateway. Its CLI and PySide6 desktop GUI use the same Bash backend to manage Tor, inspect connection status, configure bridge and country preferences, and run diagnostics.

> **Disclaimer:** OnionGate is not official Tor Project software and is not affiliated with the Tor Project.

## Features

- Shared Bash backend for CLI and GUI operations.
- Direct Tor, obfs4, Snowflake, and meek_lite bridge modes.
- Optional preferred Tor exit country.
- SOCKS, DNSPort, and transparent TCP checks.
- Read-only Tor bootstrap and circuit diagnostics with one bounded SOCKS download measurement.
- Cookie-authenticated ControlPort circuit refresh.
- OnionGate-specific firewall chains that leave unrelated firewall rules in place.
- PySide6 GUI and desktop launcher, installed by the standard installer when its dependencies are available.

## Supported distributions

The installer detects Debian- and Arch-family distributions. Intended targets include Debian, Ubuntu, Linux Mint, Kali Linux, Pop!_OS, Arch Linux, Manjaro, and EndeavourOS. Compatibility and package availability can vary by release.

Do not treat this list as a claim that every distribution has been tested. Run installation and network tests on the target Linux machine before relying on the gateway.

## Install CLI and GUI

Clone the repository, enter its directory, and run the installer once:

```bash
git clone https://github.com/usamoo2025/oniongate.git
cd oniongate
sudo bash ./install.sh
```

This is the single standard install command for both the CLI and GUI; there is no separate GUI installer. The installer also attempts to install GUI dependencies, the `oniongate-gui` launcher, and a desktop application entry. If a distribution PySide6 package is unavailable, it tries an isolated virtual environment under `/opt/oniongate/venv`. GUI installation can fail when packages or Python dependencies cannot be obtained; in that case, the installer reports the limitation and the CLI remains available.

To explicitly install only the CLI:

```bash
sudo bash ./install.sh --without-gui
```

Check the installer's final output to confirm whether the GUI was installed. Start the GUI as your regular desktop user, **not as root**:

```bash
oniongate-gui
```

The application is also available from the desktop application menu when its entry was installed. GUI connection controls request permission through `pkexec`.

## CLI commands

Run gateway-changing commands with `sudo`:

| Command | Description |
|---|---|
| `sudo oniongate start` | Start the direct Tor gateway |
| `sudo oniongate stop` | Stop OnionGate and remove its managed rules |
| `sudo oniongate restart` | Restart the gateway |
| `sudo oniongate status` | Show runtime and connection checks |
| `sudo oniongate diagnostics` | Inspect Tor bootstrap, circuits, DNS, and measured SOCKS download |
| `sudo oniongate refresh` | Request a new Tor circuit using ControlPort |
| `sudo oniongate proxy start` | Start the separate GOST provider-proxy backend |
| `sudo oniongate proxy stop` | Stop proxy mode and remove only its tagged firewall rules |
| `sudo oniongate proxy status` | Check proxy process, listeners, and redirection rules |
| `sudo oniongate proxy reconnect` | Reconnect to the configured endpoint |
| `sudo oniongate proxy refresh` | Switch to the next configured endpoint and compare observed public IPs |
| `sudo oniongate proxy diagnostics` | Measure proxy throughput and compare with a direct baseline |
| `oniongate version` | Show the installed version |
| `oniongate help` | Show CLI help |
| `sudo oniongate uninstall` | Uninstall OnionGate while preserving its configuration and data |

### Connection options

Options are used with `start` and can be combined:

```bash
sudo oniongate start --country de
sudo oniongate start --obfs4 --country nl
sudo oniongate start --snowflake
sudo oniongate start --meek
sudo oniongate start --verbose
sudo oniongate start --spoof-mac
```

Short forms are also supported: `-o` for obfs4, `-s` for Snowflake, `-m` for meek_lite, and `-v` for verbose output. `--country CODE` sets an exit-country preference; it cannot guarantee that Tor can use an exit in that country. `--spoof-mac` is opt-in and may interrupt network connectivity.

Bridge modes require the corresponding transport software and valid bridge entries in `/etc/oniongate/oniongate.conf`. Do not add a bridge mode until its configuration is available.

### Refresh a Tor circuit

```bash
sudo oniongate refresh
```

This authenticates to OnionGate's loopback ControlPort using Tor's cookie and requests `NEWNYM`. It does not restart Tor or alter firewall rules. A new circuit does **not** guarantee a different public exit IP, and existing connections are not moved to the new circuit. Tor may enforce a cooldown.

### Tor performance diagnostics

```bash
sudo oniongate diagnostics
```

Diagnostics checks the OnionGate Tor process, SOCKS and ControlPort listeners, Tor bootstrap progress, authenticated circuit status, DNSPort resolution when `dig` is available, and recent circuit-building timeout messages in the Tor log. It makes read-only ControlPort queries and does not request or change circuits.

It also performs **one** HTTPS download through SOCKS to estimate request duration and average throughput. The default test is 1 MiB and has a 30-second timeout. The result is a measurement of that request, not guaranteed Tor capacity; network conditions, bridges, exits, and the test endpoint affect it. No repeated or parallel downloads run automatically.

You can override the test URL and size with environment variables. The URL must use HTTPS and the requested size must be from 65,536 bytes through 10,485,760 bytes:

```bash
sudo env ONIONGATE_DIAGNOSTICS_URL="https://example.test/download" \
  ONIONGATE_DIAGNOSTICS_BYTES=2097152 oniongate diagnostics
```

Use an HTTPS endpoint that supports byte-range requests for a representative bounded test.

## High-speed provider proxy mode

Proxy mode is a separate, optional backend that uses **GOST v3**; it does not send proxy traffic through Tor. Install a trusted [GOST v3 Linux binary/package](https://gost.run/en/) and ensure the `gost` executable is on `PATH`. The standard OnionGate installer does not install GOST. Proxy startup also requires `curl`, `python3`, `ss` (from `iproute2`), and `iptables`; IPv6 redirection requires `ip6tables` and will fail safely if IPv6 is enabled but that utility is unavailable.

The first proxy command creates a protected configuration template. Edit it with provider-supplied values:

```bash
sudo oniongate proxy start
sudo nano /etc/oniongate/proxy.conf
```

Set `PROXY_PROTOCOL` to `socks5` or `http` (HTTP CONNECT), and provide `PROXY_SERVER`, `PROXY_PORT`, and optional paired `PROXY_USERNAME`/`PROXY_PASSWORD`. Credentials stay in the root-owned, mode-600 configuration and generated GOST file. `PROXY_TIMEOUT` sets listener-readiness and OnionGate probe timeouts from 1 to 120 seconds. SOCKS5 and HTTP CONNECT do not necessarily encrypt the connection to the provider; use credentials only with a provider and network you trust. Optional comma-separated `PROXY_ENDPOINTS` entries allow `proxy refresh` to switch among provider-approved endpoints using the configured credentials. IPv6 endpoint entries use `[address]:port`.

Then manage and inspect proxy mode with:

```bash
sudo oniongate proxy start
sudo oniongate proxy status
sudo oniongate proxy diagnostics
sudo oniongate proxy refresh
sudo oniongate proxy stop
```

The backend exposes a loopback SOCKS5 listener on `127.0.0.1:9052` and redirects outbound TCP through OnionGate-specific IPv4 and, when enabled, IPv6 NAT chains. Tor and proxy modes are mutually exclusive. Local/private destinations are excluded from redirection. OnionGate does not change system DNS: DNS queries use the current system resolver and may bypass the provider proxy; UDP traffic other than connections inside the GOST tunnel is not transparently proxied. This is **not** a guarantee that all traffic is protected or proxied.

Startup verifies a public IP through the local SOCKS listener. `proxy refresh` compares the observed IP before and after switching; the IP may remain unchanged, and an endpoint switch is not claimed to change it unless verified. Diagnostics make one bounded download through the proxy and compare it with a single direct baseline captured before proxy startup. The direct baseline contacts the test endpoint without a proxy and can expose the direct IP to that endpoint. Both speeds are measurements of those requests, not guaranteed provider capacity.

## Desktop GUI

The GUI shares the CLI backend; it does not implement a separate Tor or firewall manager. It includes a dashboard, connection controls, country and bridge preferences, diagnostics, logs, and settings. The dashboard can request a circuit refresh and reports the actual CLI result. It does not claim that the exit IP changed.

The GUI only reports a verified connection after the backend status checks pass. Privileged actions require explicit user action and use `pkexec`; launch the application as your regular user.

## Configuration and logs

OnionGate stores its configuration and runtime files under:

```text
/etc/oniongate/
```

| File or directory | Purpose |
|---|---|
| `oniongate.conf` | Bridge configuration |
| `torrc` | Generated Tor configuration |
| `data/` | Tor data and ControlPort cookie |
| `oniongate.status` | Runtime status marker |
| `tor.log` | Tor process log |
| `backup/` | Temporary startup backups |

Edit the bridge configuration with:

```bash
sudo nano /etc/oniongate/oniongate.conf
```

Generated Tor configuration binds the ControlPort to `127.0.0.1:9051` and enables cookie authentication. Do not expose this port on a network interface or share the cookie.

## Network behavior and limitations

OnionGate uses dedicated firewall chains (`ONIONGATE_NAT`, `ONIONGATE_OUT`, and `ONIONGATE6_OUT`) and is designed to remove only its own tagged rules. It does not flush the firewall, overwrite `/etc/resolv.conf`, or globally disable IPv6.

- UDP DNS is redirected to Tor's DNSPort.
- TCP traffic, including DNS-over-TCP, is handled by Tor's transparent TCP proxy.
- Other UDP traffic is not routed through Tor and may be blocked while OnionGate is active.
- Private and local destinations may bypass Tor.
- Applications using independent encrypted DNS or other network paths may not follow OnionGate's system DNS redirection.
- Other VPNs, firewall managers, or custom routes can conflict.

OnionGate does not guarantee that all system traffic or every application is protected by Tor. A successful Tor connection does not prove that every application uses Tor.

## Troubleshooting

Check whether the commands are installed:

```bash
command -v oniongate
command -v oniongate-gui
```

Inspect status and diagnostics:

```bash
sudo oniongate status
sudo oniongate diagnostics
```

View recent Tor logs:

```bash
sudo tail -n 50 /etc/oniongate/tor.log
```

Stop OnionGate if needed:

```bash
sudo oniongate stop
```

Stop proxy mode separately with `sudo oniongate proxy stop`.

If a bridge fails, check that its transport is installed and that valid matching bridge lines are present in `/etc/oniongate/oniongate.conf`. Do not flush firewall rules to troubleshoot; doing so could remove rules owned by other applications.

## Tests

Run the mock Tor ControlPort tests from the repository directory:

```bash
python3 -m unittest discover -s tests -v
```

Tests that require a running Tor daemon, Linux firewall tools, Debian/Arch package managers, or real network paths must be performed on the relevant Linux system. Do not infer Debian or Arch compatibility from tests run on another operating system.

Proxy startup, endpoint authentication and switching, firewall rollback, and real throughput tests additionally require GOST v3, root access to Linux firewall tools, a working provider account, and a network connection.

## Uninstall

```bash
sudo oniongate uninstall
```

The uninstaller removes OnionGate's installed application files and preserves `/etc/oniongate/` configuration and data. It does not remove packages such as Tor; remove those separately with your distribution's package manager if desired.

## Contributing

Bug reports and distribution-specific compatibility reports are welcome. Include the Linux distribution and version, OnionGate version, command used, relevant error output, and steps to reproduce.

[Report an issue](https://github.com/usamoo2025/oniongate/issues).

## License

OnionGate is distributed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for the license text.

## Author

**Usama Iqbal**

- GitHub: [@usamoo2025](https://github.com/usamoo2025)
- Repository: [OnionGate](https://github.com/usamoo2025/oniongate)

<p align="center">
  <strong>🧅 OnionGate</strong><br>
  Open-Source Tor Gateway for Linux<br><br>
  <sub>Independent open-source project. Not official Tor Project software.</sub>
</p>
