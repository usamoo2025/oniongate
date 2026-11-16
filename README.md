# 🧅 OnionGate
![OnionGate banner](assets/oniongate-banner.png)
<p align="center">
  <strong>An Open-Source Tor Gateway for Linux</strong>
  <br>
  <em>Command-Line Interface + Modern Desktop GUI</em>
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

## 📖 About OnionGate

**OnionGate** is an independent open-source Tor gateway for Linux, designed to provide a convenient way to manage Tor-based network connections through a command-line interface and an optional graphical desktop application.

It combines a Bash networking backend with a modern PySide6 GUI, allowing users to manage connections, configure bridge preferences, inspect system status and access diagnostics.

OnionGate aims to support both Debian-based and Arch-based Linux distributions.

> **Disclaimer:** OnionGate is an independent project. It is not official Tor Project software and is not affiliated with the Tor Project.

---

## ✨ Features

- **Tor Gateway:** Manage Tor-based network connections through the existing Bash backend.
- **Modern Desktop GUI:** Optional PySide6 graphical interface.
- **CLI Support:** Start, stop and inspect OnionGate from the terminal.
- **Bridge Support:** Direct, obfs4, Snowflake and meek_lite modes.
- **Country Preferences:** Configure preferred Tor exit countries.
- **Connection Management:** Start and stop the gateway through the GUI with user confirmation.
- **Diagnostics:** Check Tor, dependencies, configuration and runtime status.
- **Dark and Light Themes:** Choose your preferred interface appearance.
- **Linux Compatibility:** Designed for Debian- and Arch-family distributions.

---

## 🐧 Supported Distributions

| Debian-based | Arch-based |
|---|---|
| Debian | Arch Linux |
| Ubuntu | Manjaro |
| Linux Mint | EndeavourOS |
| Kali Linux | |
| Pop!_OS | |

Compatibility targets are documented, but live runtime verification on Debian and Arch systems has not yet been completed. Package availability and behavior may vary.

---

## ⚙️ Requirements

**Gateway**
- Bash
- Tor
- curl
- iproute2
- iptables
- ca-certificates
- util-linux
- Root privileges for installation and gateway-changing operations

**Desktop GUI**
- Python 3
- PySide6
- Installed OnionGate CLI
- `pkexec` for GUI connection controls

---

## 📥 Installation

### 1. Clone the repository

```bash
git clone https://github.com/usamoo2025/oniongate.git
cd oniongate
```

### 2. Make the installer executable

```bash
chmod +x install.sh
```

### 3. Install OnionGate CLI

```bash
sudo ./install.sh
```

The installer detects the distribution family and uses the appropriate package manager.

### 4. Install the optional GUI

```bash
sudo ./install.sh --with-gui
```

This installs the PySide6 GUI dependencies in `/opt/oniongate/venv` and adds the desktop launcher.

### 5. Launch OnionGate

CLI:

```bash
oniongate help
```

GUI:

```bash
oniongate-gui
```

---

## 🖥️ Desktop GUI

OnionGate includes an optional modern desktop interface built with PySide6.

The GUI works alongside the existing Bash backend rather than implementing a separate networking engine.

### GUI Features

| Page | Description |
|---|---|
| Dashboard | Connection status and connection controls |
| Locations | Country exit preferences |
| Connection | Connection information and management |
| Bridges | Bridge selection and availability |
| Diagnostics | System and dependency checks |
| Settings | Theme and application preferences |
| About | OnionGate project information |

### Connection Status

The GUI distinguishes between:

- Disconnected
- Connecting
- Connected
- Disconnecting
- Error

It displays Connected only after the CLI reports an active connection and the Tor connectivity check succeeds.

Privileged connection operations require an explicit user action and confirmation through `pkexec`.

### Country Selection

Users can select Automatic or a preferred country.

Country preferences are applied through Tor's `ExitNodes` configuration.

For example, Germany:

```bash
sudo oniongate start --country de
```

A country preference does not guarantee that a working exit relay is available in that country.

### Bridge Selection

The GUI supports the existing bridge modes:

- Direct
- obfs4
- Snowflake
- meek_lite

Required transport binaries and configuration must be available.

---

## 💻 CLI Usage

### Start OnionGate

Direct connection:

```bash
sudo oniongate start
```

### Bridge Modes

obfs4:

```bash
sudo oniongate start -o
```

Snowflake:

```bash
sudo oniongate start -s
```

meek_lite:

```bash
sudo oniongate start -m
```

### Country Preference

Prefer German exits:

```bash
sudo oniongate start --country de
```

Prefer Netherlands exits with obfs4:

```bash
sudo oniongate start -o --country nl
```

### Other Commands

```bash
sudo oniongate start -v
sudo oniongate status
sudo oniongate stop
oniongate version
oniongate help
```

Optional MAC changes:

```bash
sudo oniongate start --spoof-mac
```

MAC changes are opt-in and are not enabled by default.

---

## 🔧 Configuration

OnionGate stores its configuration and application data in:

```text
/etc/oniongate/
```

Important files:

| File | Purpose |
|---|---|
| `oniongate.conf` | Bridge configuration |
| `torrc` | Generated Tor configuration |
| `oniongate.status` | Runtime status |
| `tor.log` | Tor log |

Edit the bridge configuration with:

```bash
sudo nano /etc/oniongate/oniongate.conf
```

Preserve the expected configuration format when adding bridge lines.

---

## 🔥 Firewall and Traffic Handling

OnionGate uses dedicated firewall chains:

```text
ONIONGATE_NAT
ONIONGATE_OUT
ONIONGATE6_OUT
```

These chains are intended to keep OnionGate's firewall rules separate from unrelated rules.

The backend handles DNS redirection, supported TCP traffic and restrictions on unsupported outbound traffic.

### Important Limitations

- Not every UDP application is supported through Tor.
- Private and local destinations may bypass Tor.
- Applications using independent encrypted DNS may not follow system DNS redirection.
- Other VPN software or custom routing rules may conflict.
- A successful Tor connection does not prove every application is using Tor.

OnionGate does not guarantee that all system traffic is routed through Tor.

---

## 🛡️ Security Considerations

- Tor does not guarantee complete anonymity.
- Keep Tor and your operating system updated.
- Use HTTPS when browsing websites.
- Do not assume every application automatically uses Tor.
- Review firewall and DNS behavior after installation.
- Test network changes in an environment where connectivity can be recovered.

Starting OnionGate makes privileged firewall and network changes. Incorrect configuration or conflicts with other network tools can interrupt connectivity.

Never blindly flush the system firewall to troubleshoot OnionGate, as this could remove rules belonging to other applications.

---

## 🛠️ Troubleshooting

**OnionGate command not found**

```bash
command -v oniongate
```

**GUI command not found**

```bash
command -v oniongate-gui
```

**Check dependencies**

```bash
command -v tor
command -v curl
command -v ip
command -v iptables
```

**Check connection status**

```bash
sudo oniongate status
```

**View Tor logs**

```bash
sudo tail -n 50 /etc/oniongate/tor.log
```

**Stop OnionGate**

```bash
sudo oniongate stop
```

---

## 🗑️ Uninstallation

Run:

```bash
sudo oniongate uninstall
```

The uninstaller preserves `/etc/oniongate/` configuration and application data. Dependencies such as Tor are not removed.

---

## 🤝 Contributing

Contributions, bug reports and distribution-specific compatibility reports are welcome.

If you encounter an issue, include:

- Linux distribution and version.
- OnionGate version.
- Whether the problem occurs in the CLI or GUI.
- Relevant error output.
- Steps to reproduce.

[Report an Issue on GitHub](https://github.com/usamoo2025/oniongate/issues)

---

## 📜 License

OnionGate is intended to be distributed under the **GNU General Public License v3.0 (GPL-3.0)**.

See the [LICENSE](LICENSE) file for the complete license text.

---

## 👨‍💻 Author

**Usama Iqbal**

- GitHub: [@usamoo2025](https://github.com/usamoo2025)
- Repository: [OnionGate](https://github.com/usamoo2025/oniongate)

---

<p align="center">
  <strong>🧅 OnionGate</strong>
  <br>
  Open-Source Tor Gateway for Linux
  <br><br>
  <sub>Independent open-source project. Not official Tor Project software.</sub>
</p>