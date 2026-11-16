# 🧅 OnionGate

![OnionGate Banner](assets/oniongate-banner.png)

**An open-source Tor gateway for Linux.**

Manage Tor connections, select exit countries, configure bridge transports, and control supported network traffic through a command-line interface or a modern desktop GUI.

[GitHub Profile](https://github.com/usamoo2025) • [Repository](https://github.com/usamoo2025/oniongate) • [Report an Issue](https://github.com/usamoo2025/oniongate/issues)

![Platform](https://img.shields.io/badge/Platform-Linux-blue)
![Network](https://img.shields.io/badge/Network-Tor-purple)
![GUI](https://img.shields.io/badge/GUI-PySide6-green)
![License](https://img.shields.io/badge/License-GPL--3.0-green)
![Status](https://img.shields.io/badge/Status-Development-orange)

---

## 📖 About OnionGate

**OnionGate** is an open-source Linux utility designed to configure a Tor-based network gateway.

It provides two ways to manage your connection:

- **CLI:** Manage OnionGate directly from the Linux terminal.
- **GUI:** Use a modern desktop application to manage connections, select exit countries, choose bridge transports, and view diagnostic information.

Originally based on TorGate, the project has been renamed and adapted as OnionGate, with the goal of preserving its existing functionality while improving distribution compatibility, maintainability, and system-safety checks.

## ✨ Features

### Network and Tor

- Tor gateway configuration.
- Dedicated firewall chain management.
- DNS redirection for supported traffic.
- Supported outbound traffic restrictions.
- obfs4, Snowflake, and meek_lite bridge modes.
- Country-based Tor exit-node preferences.
- Optional MAC address spoofing.
- IPv6 firewall restrictions.

### Desktop GUI

- Modern dark desktop interface.
- Connect and disconnect controls.
- Searchable country selector.
- ISO country and territory selection.
- Automatic Tor exit selection.
- Bridge transport selection.
- Connection status monitoring.
- Observed Tor exit IP information.
- Tor log viewer.
- GUI authentication through PolicyKit (`pkexec`).

### CLI and system management

- Original command-line workflow.
- Debian- and Arch-based distribution detection.
- Dependency detection.
- Separate OnionGate configuration.
- Configuration backup support.
- OnionGate-specific firewall chains.

> **Important:** OnionGate does not guarantee complete anonymity or complete traffic protection. Its gateway implementation focuses on TCP traffic and DNS redirection. Private/local destinations and unsupported protocols may not be routed through Tor. Applications using their own encrypted DNS, VPNs, or other network paths may behave differently.

## 🐧 Supported Linux Distributions

### Debian-based

- Debian
- Ubuntu
- Linux Mint
- Kali Linux
- Pop!_OS
- Zorin OS

### Arch-based

- Arch Linux
- Manjaro
- EndeavourOS
- Artix Linux

Compatibility depends on package availability, system configuration, firewall implementation, and installed Tor version.

**Note:** These are supported distribution targets. Test installation and runtime behavior on each distribution before treating it as fully verified.

## 📋 Requirements

### Backend requirements

- Supported Debian-based or Arch-based Linux distribution.
- Root privileges for installation and network configuration.
- Bash.
- Tor.
- iptables.
- iproute2.
- curl.
- util-linux.
- ca-certificates.

Bridge transports require their corresponding transport software.

### GUI requirements

- Python 3.
- Python virtual environment support.
- PySide6.
- PolicyKit (`pkexec`) for privileged GUI operations.
- Installed OnionGate CLI backend.

The GUI does not replace the Bash backend. It communicates with the existing `oniongate` command.

---

# 📥 Installation

## 1. Clone the repository

```bash
git clone https://github.com/usamoo2025/oniongate.git
```

## 2. Enter the project directory

```bash
cd oniongate
```

## 3. Make the installer executable

```bash
chmod +x install.sh
```

## 4. Install the OnionGate backend

```bash
sudo ./install.sh
```

The backend installer is intended to detect the supported distribution family, install required dependencies, and configure OnionGate.

Check that the CLI is available:

```bash
oniongate version
```

> Make sure `install.sh` is included in your repository. The backend must be installed before launching the desktop GUI.

---

# 🖥️ Running OnionGate GUI

OnionGate provides a graphical desktop interface built with **Python and PySide6**.

The GUI uses the existing OnionGate backend to manage Tor connections. You can continue using the terminal even if you install the GUI.

## 1. Install Python and virtual environment support

On Debian-based systems:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

On Arch-based systems:

```bash
sudo pacman -S python python-pip
```

## 2. Install PolicyKit

The GUI uses `pkexec` to request administrator privileges when starting or stopping the gateway.

Install the appropriate PolicyKit package for your distribution.

Check whether `pkexec` is available:

```bash
command -v pkexec
```

If the command is missing, install the package that provides `pkexec` using your distribution's package manager.

## 3. Create a Python virtual environment

From the OnionGate project directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

## 4. Install PySide6

```bash
python -m pip install --upgrade pip
python -m pip install PySide6
```

## 5. Check the GUI files

Your project should contain:

```text
oniongate/
├── oniongate.sh
├── install.sh
├── gui/
│   └── oniongate_gui.py
├── assets/
│   └── oniongate-banner.png
├── README.md
└── LICENSE
```

The backend should already be installed as:

```text
/usr/local/bin/oniongate
```

The GUI searches for the installed OnionGate command in the system PATH and standard installation locations.

## 6. Launch OnionGate GUI

With the virtual environment activated:

```bash
python gui/oniongate_gui.py
```

Alternatively:

```bash
.venv/bin/python gui/oniongate_gui.py
```

You should now see the OnionGate desktop dashboard.

**Important:** Run the GUI as your normal desktop user, not with `sudo`. It uses PolicyKit to request elevated privileges for administrative actions.

---

# 🌍 Selecting a Tor Exit Country

One of the main GUI features is the searchable country selector.

You can select a country before starting OnionGate.

### How to use it

1. Open OnionGate GUI.
2. Find the **Tor exit country** selector.
3. Click the country search field.
4. Type a country name.
5. Select the matching country from the suggestions.
6. Choose a bridge transport if needed.
7. Click **Connect**.

The selector includes an automatic option:

**Automatic (Tor chooses)**

When this option is selected, OnionGate does not pass a country preference to Tor.

### Example

Selecting Germany:

```bash
sudo oniongate start --country de
```

Selecting the Netherlands:

```bash
sudo oniongate start --country nl
```

Selecting Japan:

```bash
sudo oniongate start --country jp
```

The GUI sends the selected two-letter ISO country code to the existing backend.

### How country selection works

The backend uses Tor configuration preferences:

```text
ExitNodes {de}
StrictNodes 1
```

The country code `de` represents Germany.

`StrictNodes 1` makes the preference strict. If Tor cannot find a suitable exit relay in the selected country, the connection may fail.

**Important limitations:**

- Country selection refers to the Tor exit relay, not your physical location.
- Not every country has available Tor exit relays.
- Selecting a country does not guarantee that an IP geolocation service will report that country.
- A country preference can reduce the number of available exit relays.

---

# 🌉 Bridge Selection

The GUI also allows you to select a Tor transport.

Available options:

| Transport | Description |
|---|---|
| Direct connection | Connect using the normal Tor connection |
| obfs4 | Use an obfs4 bridge |
| Snowflake | Use the Snowflake transport |
| meek_lite | Use the meek_lite transport |

Bridge availability depends on the installed transport software and valid bridge configuration.

### CLI bridge commands

Direct connection:

```bash
sudo oniongate start
```

obfs4:

```bash
sudo oniongate start --obfs4
```

Snowflake:

```bash
sudo oniongate start --snowflake
```

meek_lite:

```bash
sudo oniongate start --meek
```

### Combine country and bridge selection

For example, obfs4 with a German exit preference:

```bash
sudo oniongate start --obfs4 --country de
```

Snowflake with a Netherlands exit preference:

```bash
sudo oniongate start --snowflake --country nl
```

---

# 🚀 CLI Quick Start

You can use OnionGate without opening the GUI.

Start OnionGate:

```bash
sudo oniongate start
```

Check status:

```bash
sudo oniongate status
```

Stop OnionGate:

```bash
sudo oniongate stop
```

Display version:

```bash
oniongate version
```

Display help:

```bash
oniongate help
```

## 🛠️ CLI Command Reference

| Command | Description |
|---|---|
| `sudo oniongate start` | Start OnionGate |
| `sudo oniongate start -o` | Start with obfs4 |
| `sudo oniongate start -s` | Start with Snowflake |
| `sudo oniongate start -m` | Start with meek_lite |
| `sudo oniongate start -v` | Start with verbose output |
| `sudo oniongate start --country de` | Prefer a German exit relay |
| `sudo oniongate start --spoof-mac` | Enable optional MAC spoofing |
| `sudo oniongate stop` | Stop OnionGate |
| `sudo oniongate status` | Display gateway status |
| `oniongate version` | Display version |
| `oniongate help` | Display help |
| `sudo oniongate uninstall` | Uninstall OnionGate |

---

# ⚙️ Configuration

OnionGate stores its configuration separately from the main system configuration.

| Component | Location |
|---|---|
| Main directory | `/etc/oniongate/` |
| Main configuration | `/etc/oniongate/oniongate.conf` |
| Tor configuration | `/etc/oniongate/torrc` |
| Status file | `/etc/oniongate/oniongate.status` |
| Runtime status | `/run/oniongate.status` |
| Log file | `/etc/oniongate/tor.log` |
| Backup directory | `/etc/oniongate/backup/` |
| Tor data directory | `/var/lib/oniongate/` |

---

# 🔐 How OnionGate Works

At a high level, OnionGate performs the following operations when started:

1. Checks root privileges and supported distribution.
2. Checks required dependencies.
3. Loads the OnionGate configuration.
4. Detects the available Tor service user.
5. Prepares the Tor configuration.
6. Creates or updates OnionGate-owned firewall rules.
7. Starts the managed Tor process.
8. Checks whether the Tor connection is available.
9. Reports the resulting gateway status.

When stopped, OnionGate attempts to stop its managed Tor process and remove its own firewall rules.

The GUI communicates with the CLI backend to perform administrative operations.

---

# 🧱 Firewall and Traffic Handling

OnionGate uses dedicated firewall chains:

```text
ONIONGATE_NAT
ONIONGATE_OUT
ONIONGATE6_OUT
```

These chains are intended to keep OnionGate's firewall rules separate from unrelated system rules.

The implementation uses supported firewall rules for DNS redirection, TCP traffic handling, and restrictions on unsupported outbound traffic.

### Traffic limitations

- Not every UDP application is supported through Tor.
- Private and local network destinations may bypass Tor.
- Applications using their own encrypted DNS may not follow system DNS redirection.
- Other VPN software or custom routing rules may conflict with OnionGate.
- A successful Tor connection does not prove that every application is using Tor.

Always verify application network behavior rather than assuming that starting OnionGate protects every connection.

---

# 🛡️ Security Considerations

OnionGate is a network configuration tool, not a substitute for good security practices.

- Tor does not make users completely anonymous.
- Avoid sharing personal information with untrusted services.
- HTTPS remains important when browsing websites.
- Do not assume every application automatically uses Tor.
- Keep Tor and your operating system updated.
- Review firewall and DNS behavior after installation.
- Test changes in an environment where you can recover network connectivity.

OnionGate aims to avoid broad firewall flushing and unnecessary changes to system resolver files. However, firewall and routing changes can still interrupt connectivity if configuration is incorrect.

---

# 🧰 Troubleshooting

## OnionGate command not found

```bash
command -v oniongate
```

If the command is missing, check the backend installation.

## GUI cannot find the backend

Check:

```bash
command -v oniongate
```

The GUI requires the OnionGate CLI to be installed.

## PySide6 module not found

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install PySide6:

```bash
python -m pip install PySide6
```

## pkexec not found

Check:

```bash
command -v pkexec
```

Install the PolicyKit package that provides `pkexec` for your distribution.

## GUI does not start

Run:

```bash
python gui/oniongate_gui.py
```

Check the terminal output for Python or Qt errors.

## Check Tor service

```bash
systemctl status tor
```

The service name can differ between distributions.

## Check OnionGate status

```bash
sudo oniongate status
```

## Check installed dependencies

```bash
command -v tor
command -v curl
command -v ip
command -v iptables
```

## Check OnionGate logs

```bash
sudo tail -n 50 /etc/oniongate/tor.log
```

## Network connectivity problems

If network connectivity is interrupted:

1. Check OnionGate's status.
2. Review the log file.
3. Check whether another VPN or firewall is managing the network.
4. Stop OnionGate using its normal stop command.
5. Review the system's firewall configuration before making further changes.

Do not blindly flush the system firewall. This may remove rules belonging to other applications.

---

# 🗑️ Uninstallation

To uninstall OnionGate:

```bash
sudo oniongate uninstall
```

The backend uninstaller is intended to remove OnionGate-managed components and its own firewall rules.

The GUI source and Python virtual environment are separate from the backend. If you want to remove the local GUI environment too:

```bash
rm -rf .venv
```

Review remaining configuration and backup files before deleting them manually. Avoid removing unrelated system packages or firewall rules.

---

# 🗺️ Roadmap

- [x] Rename TorGate to OnionGate.
- [x] Introduce Debian-based distribution detection.
- [x] Introduce Arch-based distribution detection.
- [x] Add distribution-specific dependency handling.
- [x] Preserve the original CLI command structure.
- [x] Retain bridge-mode options.
- [x] Introduce OnionGate-specific firewall chains.
- [x] Build a PySide6 desktop interface.
- [x] Add searchable country selection.
- [x] Connect GUI country selection to the CLI backend.
- [x] Add bridge selection to the GUI.
- [ ] Complete GUI/backend integration testing.
- [ ] Test installation on clean Debian systems.
- [ ] Test installation on clean Arch systems.
- [ ] Test country-based exit-node selection.
- [ ] Improve automated testing.
- [ ] Improve recovery and rollback testing.
- [ ] Expand documentation.
- [ ] Consider additional distribution support.

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test your changes on a supported Linux distribution.
5. Submit a pull request.

Please include details about the distribution and version used for testing.

# 🐛 Reporting Issues

If you encounter a problem, open an issue:

[**Report an Issue**](https://github.com/usamoo2025/oniongate/issues)

Please include:

- Linux distribution and version.
- OnionGate version.
- Whether the problem occurs in the CLI or GUI.
- Relevant error messages.
- Relevant log output.
- Steps to reproduce the issue.

Do not include passwords, private keys, personal information, or other sensitive configuration data in issue reports.

---

# 📜 License

OnionGate is intended to be distributed under the **GNU General Public License v3.0 (GPL-3.0)**.

See the `LICENSE` file in the repository for the complete license text.

---

# 👨‍💻 Author and Project

**Project:** OnionGate

**Author / Maintainer:** Usama Iqbal

**GitHub:** [usamoo2025](https://github.com/usamoo2025)

**Repository:** [github.com/usamoo2025/oniongate](https://github.com/usamoo2025/oniongate)

---

**ONIONGATE — YOUR NETWORK, YOUR CONTROL.**

*Open-Source Tor Gateway*

Built as an open-source project by Usama Iqbal.