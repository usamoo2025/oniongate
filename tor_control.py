#!/usr/bin/env python3
"""Minimal cookie-authenticated Tor ControlPort client for OnionGate."""

from __future__ import annotations

import re
import socket
import sys
from pathlib import Path


class TorControlError(Exception):
    pass


def _read_reply(stream) -> tuple[int, str]:
    lines: list[str] = []
    while True:
        raw_line = stream.readline(4097)
        if not raw_line:
            raise TorControlError("Tor closed the ControlPort connection.")
        if len(raw_line) > 4096:
            raise TorControlError("Tor returned an oversized ControlPort response.")
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if not re.match(r"^\d{3}[ -]", line):
            raise TorControlError("Tor returned an invalid ControlPort response.")
        code = int(line[:3])
        lines.append(line[4:])
        if line[3] == " ":
            return code, "\n".join(lines)


def request_newnym(cookie_path: Path, port: int = 9051) -> None:
    if cookie_path.is_symlink():
        raise TorControlError("Tor control authentication cookie is a symbolic link.")
    try:
        cookie = cookie_path.read_bytes()
    except OSError as exc:
        raise TorControlError(
            f"Cannot read Tor control authentication cookie: {exc.strerror or exc}"
        ) from exc
    if len(cookie) != 32:
        raise TorControlError(
            "Tor control authentication cookie is missing or has an invalid length."
        )

    try:
        connection = socket.create_connection(("127.0.0.1", port), timeout=5)
    except OSError as exc:
        raise TorControlError(
            f"Cannot connect to Tor ControlPort at 127.0.0.1:{port}: {exc}"
        ) from exc

    with connection:
        connection.settimeout(5)
        with connection.makefile("rwb", buffering=0) as stream:
            code, reply = _read_reply(stream)
            if code != 250:
                raise TorControlError(f"Tor ControlPort greeting failed: {reply}")

            stream.write(f"AUTHENTICATE {cookie.hex()}\r\n".encode("ascii"))
            code, reply = _read_reply(stream)
            if code != 250:
                raise TorControlError(
                    "Tor ControlPort cookie authentication failed. "
                    f"Tor replied: {reply}"
                )

            stream.write(b"SIGNAL NEWNYM\r\n")
            code, reply = _read_reply(stream)
            if code == 552 and re.search(
                r"too (?:frequent|recently)|cooldown", reply, re.IGNORECASE
            ):
                raise TorControlError(
                    "Tor is enforcing the NEWNYM cooldown. Wait before retrying."
                )
            if code != 250:
                raise TorControlError(
                    f"Tor rejected the NEWNYM signal: {reply}"
                )


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        print("Usage: tor_control.py COOKIE_PATH PORT", file=sys.stderr)
        return 2
    try:
        port = int(arguments[1])
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print("Tor ControlPort must be a valid TCP port.", file=sys.stderr)
        return 2
    try:
        request_newnym(Path(arguments[0]), port)
    except (TorControlError, OSError, TimeoutError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
