"""Background work that must not block the Qt event loop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

if __package__:
    from .backend import BackendClient, CommandResult, find_backend
    from .diagnostics import Diagnostic, collect_diagnostics, recent_log
else:
    from backend import BackendClient, CommandResult, find_backend
    from diagnostics import Diagnostic, collect_diagnostics, recent_log


@dataclass(frozen=True)
class RefreshSnapshot:
    backend_path: Path | None
    version: CommandResult
    help_result: CommandResult
    status_result: CommandResult
    runtime_state: str
    runtime_detail: str
    diagnostics: list[Diagnostic]
    log_text: str
    log_error: str | None


class RefreshWorker(QThread):
    completed = Signal(object)

    def run(self) -> None:
        backend_path = find_backend()
        client = BackendClient(backend_path)
        version = client.version()
        help_result = client.help()
        status_result, runtime = client.status()
        diagnostics = collect_diagnostics(backend_path=backend_path)
        log_text, log_error = recent_log()
        self.completed.emit(
            RefreshSnapshot(
                backend_path,
                version,
                help_result,
                status_result,
                runtime.state,
                runtime.detail,
                diagnostics,
                log_text,
                log_error,
            )
        )


def connection_duration(started: datetime | None) -> str:
    if started is None:
        return "Unknown"
    seconds = max(0, int((datetime.now().astimezone() - started).total_seconds()))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
