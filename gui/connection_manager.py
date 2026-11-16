"""Explicit, asynchronous GUI controls for the existing OnionGate CLI."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

if __package__:
    from .backend import find_backend, parse_status_output
    from .country_manager import validate_country_code
else:
    from backend import find_backend, parse_status_output
    from country_manager import validate_country_code


BRIDGE_ARGUMENTS = {
    "": (),
    "obfs4": ("--obfs4",),
    "snowflake": ("--snowflake",),
    "meek": ("--meek",),
}


def build_start_arguments(
    backend_path: Path,
    bridge: str,
    country: str,
) -> tuple[str, ...]:
    if bridge not in BRIDGE_ARGUMENTS:
        raise ValueError("The selected bridge mode is not supported.")
    country_code = validate_country_code(country)
    arguments = [str(backend_path), "start", *BRIDGE_ARGUMENTS[bridge]]
    if country_code:
        arguments.extend(("--country", country_code))
    return tuple(arguments)


class ConnectionManager(QObject):
    operation_started = Signal(str)
    output_received = Signal(str)
    bootstrap_progress = Signal(int)
    status_verified = Signal(object)
    operation_error = Signal(str)
    circuit_refresh_finished = Signal(str, bool, int)

    def __init__(
        self,
        backend_path: Path | None = None,
        pkexec_path: str | None = None,
    ) -> None:
        super().__init__()
        self.backend_path = backend_path if backend_path is not None else find_backend()
        self.pkexec_path = pkexec_path if pkexec_path is not None else shutil.which("pkexec")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)
        self.kill_timer = QTimer(self)
        self.kill_timer.setSingleShot(True)
        self.kill_timer.timeout.connect(self._kill_if_running)
        self.operation: str | None = None
        self._timed_out = False
        self._output = ""
        self._progress_buffer = ""
        self._last_progress: int | None = None
        self.is_connected = False
        self.is_active = False

    @property
    def can_manage(self) -> bool:
        return (
            self.backend_path is not None
            and self.backend_path.is_file()
            and bool(self.pkexec_path)
        )

    def connect_to_tor(self, bridge: str, country: str) -> None:
        if not self._ensure_idle():
            return
        if not self.can_manage:
            self.operation_error.emit(
                "GUI controls require the OnionGate CLI and pkexec. "
                "Use the documented sudo oniongate command in a terminal instead."
            )
            return
        try:
            arguments = build_start_arguments(self.backend_path, bridge, country)
        except ValueError as exc:
            self.operation_error.emit(str(exc))
            return

        self._launch(
            "connect",
            self.pkexec_path or "pkexec",
            list(arguments),
            timeout_ms=210_000,
        )

    def disconnect(self) -> None:
        if not self._ensure_idle():
            return
        if not self.can_manage:
            self.operation_error.emit(
                "GUI controls require the OnionGate CLI and pkexec. "
                "Use 'sudo oniongate stop' in a terminal instead."
            )
            return
        self._launch(
            "disconnect",
            self.pkexec_path or "pkexec",
            [str(self.backend_path), "stop"],
            timeout_ms=45_000,
        )

    def refresh_circuit(self) -> None:
        if not self._ensure_idle():
            return
        if not self.is_active:
            self.circuit_refresh_finished.emit(
                "OnionGate is not running. Start the gateway before refreshing its circuit.",
                False,
                0,
            )
            return
        if not self.can_manage:
            self.circuit_refresh_finished.emit(
                "Circuit refresh requires the OnionGate CLI and pkexec.",
                False,
                0,
            )
            return
        self._launch(
            "refresh",
            self.pkexec_path or "pkexec",
            [str(self.backend_path), "refresh"],
            timeout_ms=20_000,
        )

    def _ensure_idle(self) -> bool:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.operation_error.emit("An OnionGate operation is already running.")
            return False
        return True

    def _launch(
        self,
        operation: str,
        program: str,
        arguments: list[str],
        *,
        timeout_ms: int,
    ) -> None:
        self.operation = operation
        self._timed_out = False
        self._output = ""
        self._progress_buffer = ""
        self._last_progress = None
        if operation in ("connect", "disconnect"):
            self.operation_started.emit(operation)
        self.process.setProgram(program)
        self.process.setArguments(arguments)
        self.timeout_timer.start(timeout_ms)
        self.process.start()

    def _read_output(self) -> None:
        text = bytes(self.process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        if not text:
            return
        self._output += text
        self._progress_buffer += text
        self.output_received.emit(text)
        matches = list(
            re.finditer(
                r"Bootstrapped\s+(\d{1,3})%",
                self._progress_buffer,
                re.IGNORECASE,
            )
        )
        if matches:
            percentage = min(100, int(matches[-1].group(1)))
            if percentage != self._last_progress:
                self._last_progress = percentage
                self.bootstrap_progress.emit(percentage)
        self._progress_buffer = self._progress_buffer[-256:]

    def _process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self.timeout_timer.stop()
        self.kill_timer.stop()
        self._read_output()
        operation = self.operation
        if operation is None:
            return
        self.operation = None
        if self._timed_out:
            message = (
                "The operation timed out. Check OnionGate status and logs before retrying."
            )
            if operation == "refresh":
                self.circuit_refresh_finished.emit(message, False, 0)
            else:
                self.operation_error.emit(message)
        elif operation == "refresh":
            succeeded = (
                exit_code == 0
                and exit_status == QProcess.ExitStatus.NormalExit
            )
            cooldown = self._refresh_cooldown(self._output)
            if succeeded:
                cooldown = max(10, cooldown)
            elif "cooldown" in self._output.lower():
                cooldown = max(10, cooldown)
            detail = self._output.strip() or (
                f"Circuit refresh command exited with status {exit_code}."
            )
            self.circuit_refresh_finished.emit(detail[-3000:], succeeded, cooldown)
        elif operation in ("verify_connect", "verify_disconnect"):
            if exit_status == QProcess.ExitStatus.CrashExit:
                self.operation_error.emit(
                    self._output.strip()[-3000:]
                    or f"Status verification process exited with status {exit_code}."
                )
            else:
                self._complete_verification(operation)
        elif (
            exit_code != 0
            or exit_status == QProcess.ExitStatus.CrashExit
        ):
            detail = self._output.strip() or (
                f"CLI process failed with exit status {exit_code} "
                f"({exit_status.name})."
            )
            self.operation_error.emit(detail[-3000:])
        elif operation in ("connect", "disconnect"):
            self._verify_runtime(operation)

    def _verify_runtime(self, operation: str) -> None:
        if self.backend_path is None:
            self.operation_error.emit("OnionGate CLI executable is no longer available.")
            return
        verification = "verify_connect" if operation == "connect" else "verify_disconnect"
        self._launch(
            verification,
            str(self.backend_path),
            ["status"],
            timeout_ms=45_000,
        )

    def _complete_verification(self, operation: str) -> None:
        runtime = parse_status_output(self._output)
        self.is_active = runtime.state.startswith("Active")
        if operation == "verify_connect":
            if runtime.state != "Active · Tor verified":
                self.operation_error.emit(
                    "OnionGate start finished, but the CLI did not verify a working "
                    f"Tor connection. {runtime.detail}"
                )
                return
            self.is_connected = True
            self.is_active = True
        else:
            if runtime.state != "Inactive":
                self.operation_error.emit(
                    "Stop finished, but the CLI did not confirm an inactive gateway. "
                    f"{runtime.detail}"
                )
                return
            self.is_connected = False
            self.is_active = False
        self.status_verified.emit(runtime)

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart and self.operation is not None:
            self.timeout_timer.stop()
            operation = self.operation
            self.operation = None
            message = (
                f"Could not start the {operation} command: {self.process.errorString()}"
            )
            if operation == "refresh":
                self.circuit_refresh_finished.emit(message, False, 0)
            else:
                self.operation_error.emit(message)

    @staticmethod
    def _refresh_cooldown(output: str) -> int:
        match = re.search(
            r"cooldown:[^0-9]*(\d+)\s*seconds?",
            output,
            re.IGNORECASE,
        )
        return int(match.group(1)) if match else 0

    def _on_timeout(self) -> None:
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        self._timed_out = True
        self.process.terminate()
        self.kill_timer.start(5000)

    def _kill_if_running(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
