"""Safe, read-only communication with the existing OnionGate CLI."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_BACKEND_PATHS = (
    Path("/usr/local/bin/oniongate"),
    Path("/usr/bin/oniongate"),
)


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None

    @property
    def output(self) -> str:
        return (self.stdout.strip() or self.stderr.strip()).strip()

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0 and self.error is None


@dataclass(frozen=True)
class RuntimeStatus:
    state: str
    detail: str


def find_backend(
    search_path: str | None = None,
    known_paths: Sequence[Path] = DEFAULT_BACKEND_PATHS,
) -> Path | None:
    """Find an executable OnionGate CLI without invoking a shell."""
    for candidate in known_paths:
        try:
            if candidate.is_file() and candidate.stat().st_mode & 0o111:
                return candidate
        except OSError:
            continue

    executable = shutil.which("oniongate", path=search_path)
    return Path(executable) if executable else None


def run_command(
    command: Sequence[str],
    timeout: float = 5,
) -> CommandResult:
    args = tuple(str(arg) for arg in command)
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            args,
            None,
            _as_text(exc.stdout),
            _as_text(exc.stderr),
            f"Command timed out after {timeout:g} seconds",
        )
    except OSError as exc:
        return CommandResult(args, None, error=str(exc))

    return CommandResult(
        args,
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )


def _as_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def parse_status_output(output: str) -> RuntimeStatus:
    """Parse only explicit states emitted by the current CLI."""
    if re.search(r"OnionGate Status:\s*INACTIVE\b", output, re.IGNORECASE):
        return RuntimeStatus("Inactive", "CLI reports OnionGate as inactive.")

    if re.search(r"OnionGate Status:\s*ACTIVE\b", output, re.IGNORECASE):
        if re.search(r"Tor Connection:\s*FAILED\b", output, re.IGNORECASE):
            return RuntimeStatus(
                "Active · Tor check failed",
                "CLI reports active, but its Tor connectivity check failed.",
            )
        if re.search(r"Tor Connection:\s*OK\b", output, re.IGNORECASE):
            return RuntimeStatus(
                "Active · Tor verified",
                "CLI reports active and its Tor connectivity check succeeded.",
            )
        return RuntimeStatus(
            "Active · connection unverified",
            "CLI reports active; no explicit Tor connectivity result was found.",
        )

    return RuntimeStatus(
        "Unknown",
        "The CLI output did not contain a recognized OnionGate status.",
    )


def parse_version_output(output: str) -> str | None:
    match = re.search(
        r"\bOnionGate\s+V?([0-9][A-Za-z0-9._+-]*)\b",
        output,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


class BackendClient:
    """Read-only adapter for the supported OnionGate CLI commands."""

    def __init__(self, executable: Path | None = None) -> None:
        self.executable = executable if executable is not None else find_backend()

    def _invoke(self, *arguments: str, timeout: float = 5) -> CommandResult:
        if self.executable is None:
            return CommandResult(
                (),
                None,
                error="OnionGate CLI executable was not found.",
            )
        return run_command((str(self.executable), *arguments), timeout=timeout)

    def version(self) -> CommandResult:
        return self._invoke("version")

    def help(self) -> CommandResult:
        return self._invoke("help")

    def status(self, timeout: float = 12) -> tuple[CommandResult, RuntimeStatus]:
        result = self._invoke("status", timeout=timeout)
        if not result.succeeded:
            return result, RuntimeStatus(
                "Unknown",
                result.error or result.output or "Status command failed.",
            )
        return result, parse_status_output(result.output)
