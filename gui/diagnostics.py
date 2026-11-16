"""Read-only, distribution-independent system diagnostics."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
from collections import deque
from dataclasses import dataclass
from pathlib import Path


CONFIG_FILE = Path("/etc/oniongate/oniongate.conf")
STATUS_FILE = Path("/etc/oniongate/oniongate.status")
LOG_FILE = Path("/etc/oniongate/tor.log")

REQUIRED_UTILITIES = (
    "tor",
    "curl",
    "ip",
    "iptables",
    "ip6tables",
    "runuser",
    "id",
)

OPTIONAL_TRANSPORTS = {
    "obfs4proxy": ("obfs4proxy",),
    "snowflake": ("snowflake-client", "snowflake"),
}

BRIDGE_CONFIG_PATTERNS = {
    "obfs4": r"^[ \t]*obfs4[ \t]+",
    "snowflake": r"^[ \t]*snowflake[ \t]+",
    "meek": r"^[ \t]*meek_lite[ \t]+",
}


@dataclass(frozen=True)
class Distribution:
    name: str
    distribution_id: str
    family: str
    package_managers: tuple[str, ...]


@dataclass(frozen=True)
class Diagnostic:
    name: str
    available: bool | None
    detail: str


def parse_os_release(contents: str) -> dict[str, str]:
    """Parse os-release assignments as data; never evaluate shell syntax."""
    values: dict[str, str] = {}
    for line in contents.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum():
            continue
        try:
            parsed = shlex.split(value, comments=False, posix=True)
        except ValueError:
            continue
        if len(parsed) == 1:
            values[key] = parsed[0]
        elif not parsed:
            values[key] = ""
    return values


def detect_distribution(
    os_release_path: Path = Path("/etc/os-release"),
    which=shutil.which,
) -> Distribution | None:
    try:
        contents = os_release_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    values = parse_os_release(contents)
    distro_id = values.get("ID", "").lower()
    id_like = values.get("ID_LIKE", "").lower().split()
    debian_ids = {
        "debian", "ubuntu", "linuxmint", "kali", "pop", "elementary",
        "zorin", "raspbian",
    }
    arch_ids = {"arch", "manjaro", "endeavouros", "garuda", "artix"}
    if distro_id in debian_ids or any(token in debian_ids for token in id_like):
        family = "Debian-based"
    elif distro_id in arch_ids or any(token in arch_ids for token in id_like):
        family = "Arch-based"
    else:
        family = "Unsupported or unknown"

    managers = tuple(
        manager for manager in ("apt", "pacman") if which(manager) is not None
    )
    return Distribution(
        name=values.get("PRETTY_NAME") or values.get("NAME") or distro_id or "Unknown",
        distribution_id=distro_id or "unknown",
        family=family,
        package_managers=managers,
    )


def inspect_path(path: Path, label: str, *, readable: bool = False) -> Diagnostic:
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            return Diagnostic(label, False, f"Not found: {path}")
        if readable:
            with path.open("rb"):
                pass
        return Diagnostic(label, True, str(path))
    except OSError as exc:
        return Diagnostic(label, False, f"{path}: {exc}")


def check_executable(name: str, which=shutil.which) -> Diagnostic:
    try:
        location = which(name)
    except OSError as exc:
        return Diagnostic(name, False, str(exc))
    return Diagnostic(
        name,
        location is not None,
        location or "Not found in PATH",
    )


def check_bridge_configuration(
    bridge: str,
    config_path: Path = CONFIG_FILE,
) -> Diagnostic:
    pattern = BRIDGE_CONFIG_PATTERNS.get(bridge)
    if pattern is None:
        return Diagnostic(f"{bridge} bridge configuration", False, "Unknown bridge mode")
    try:
        with config_path.open("r", encoding="utf-8", errors="replace") as stream:
            configured = any(
                re.search(pattern, line, re.IGNORECASE)
                for line in stream
            )
    except OSError as exc:
        return Diagnostic(f"{bridge} bridge configuration", False, str(exc))
    return Diagnostic(
        f"{bridge} bridge configuration",
        configured,
        "Bridge lines found" if configured else f"No {bridge} bridge lines in {config_path}",
    )


def check_tor_service_account(which=shutil.which) -> Diagnostic:
    id_executable = which("id")
    if id_executable is None:
        return Diagnostic("Tor service account", False, "The id utility was not found")
    for username in ("debian-tor", "tor"):
        try:
            result = subprocess.run(
                (id_executable, username),
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return Diagnostic(
                "Tor service account",
                False,
                "Timed out checking the Tor service account",
            )
        except OSError as exc:
            return Diagnostic("Tor service account", False, str(exc))
        if result.returncode == 0:
            return Diagnostic(
                "Tor service account",
                True,
                f"{username} is available",
            )
    return Diagnostic(
        "Tor service account",
        False,
        "Neither debian-tor nor tor account was found",
    )


def check_init_system(path: Path = Path("/proc/1/comm")) -> Diagnostic:
    try:
        name = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        return Diagnostic("Init system", None, f"Could not identify init system: {exc}")
    return Diagnostic(
        "Init system",
        True if name else None,
        name or "Init system name is empty",
    )


def collect_diagnostics(
    *,
    backend_path: Path | None,
    config_path: Path = CONFIG_FILE,
    status_path: Path = STATUS_FILE,
    log_path: Path = LOG_FILE,
    os_release_path: Path = Path("/etc/os-release"),
    which=shutil.which,
) -> list[Diagnostic]:
    distribution = detect_distribution(os_release_path, which)
    if distribution is None:
        results = [Diagnostic("Linux distribution", False, "/etc/os-release is unreadable or missing")]
    else:
        managers = ", ".join(distribution.package_managers) or "none detected"
        results = [
            Diagnostic(
                "Linux distribution",
                distribution.family != "Unsupported or unknown",
                f"{distribution.name} · {distribution.family} · package managers: {managers}",
            )
        ]

    if backend_path is None:
        results.append(Diagnostic("OnionGate CLI", False, "Executable not found"))
    else:
        results.append(
            Diagnostic(
                "OnionGate CLI",
                os.access(backend_path, os.X_OK),
                str(backend_path),
            )
        )

    results.extend(
        (
            inspect_path(config_path, "Configuration file", readable=True),
            inspect_path(status_path, "Status file", readable=True),
            inspect_path(log_path, "Log file", readable=True),
        )
    )
    results.extend(check_executable(name, which) for name in REQUIRED_UTILITIES)
    results.append(check_executable("pkexec", which))
    results.append(check_tor_service_account(which))
    results.append(check_init_system())
    results.append(
        Diagnostic(
            "Tor service model",
            True,
            "OnionGate starts and manages its own Tor process; no systemd service is assumed.",
        )
    )

    for display_name, candidates in OPTIONAL_TRANSPORTS.items():
        found = [(name, check_executable(name, which)) for name in candidates]
        available = next(
            (
                (name, result.detail)
                for name, result in found
                if result.available
            ),
            None,
        )
        results.append(
            Diagnostic(
                f"Optional transport: {display_name}",
                available is not None,
                f"{available[0]}: {available[1]}" if available else "No supported transport binary found",
            )
        )

    return results


def recent_log(path: Path = LOG_FILE, limit: int = 80) -> tuple[str, str | None]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            lines = deque(stream, maxlen=max(0, limit))
    except OSError as exc:
        return "", str(exc)
    return "".join(lines), None
