from __future__ import annotations

import socket
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "tor_control.py"


class MockTorControl:
    def __init__(self, authentication_code: int = 250, signal_code: int = 250) -> None:
        self.authentication_code = authentication_code
        self.signal_code = signal_code
        self.cookie_hex: str | None = None
        self.signal: bytes | None = None
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self) -> MockTorControl:
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.listener.close()
        self.thread.join(timeout=2)

    def _serve(self) -> None:
        try:
            connection, _address = self.listener.accept()
        except OSError:
            return
        with connection:
            stream = connection.makefile("rwb", buffering=0)
            stream.write(b"250 OnionGate mock control\r\n")
            authentication = stream.readline().decode("ascii").strip()
            self.cookie_hex = authentication.removeprefix("AUTHENTICATE ")
            if self.authentication_code != 250:
                stream.write(b"515 Authentication failed\r\n")
                return
            stream.write(b"250 OK\r\n")
            self.signal = stream.readline().strip()
            if self.signal_code == 250:
                stream.write(b"250 OK\r\n")
            else:
                stream.write(b"552 Signal NEWNYM is too frequent\r\n")


class TorControlClientTests(unittest.TestCase):
    def test_authenticates_with_cookie_and_sends_newnym(self) -> None:
        cookie = bytes(range(32))
        with TemporaryDirectory() as directory:
            cookie_path = Path(directory) / "control_auth_cookie"
            cookie_path.write_bytes(cookie)
            with MockTorControl() as server:
                result = subprocess.run(
                    [sys.executable, str(CLIENT), str(cookie_path), str(server.port)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                server.thread.join(timeout=2)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(server.cookie_hex, cookie.hex())
            self.assertEqual(server.signal, b"SIGNAL NEWNYM")
            self.assertNotIn(cookie.hex(), result.stdout + result.stderr)

    def test_reports_authentication_failure_without_sending_signal(self) -> None:
        with TemporaryDirectory() as directory:
            cookie_path = Path(directory) / "control_auth_cookie"
            cookie_path.write_bytes(bytes(range(32)))
            with MockTorControl(authentication_code=515) as server:
                result = subprocess.run(
                    [sys.executable, str(CLIENT), str(cookie_path), str(server.port)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                server.thread.join(timeout=2)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cookie authentication failed", result.stderr)
            self.assertIsNone(server.signal)

    def test_reports_tor_newnym_cooldown(self) -> None:
        with TemporaryDirectory() as directory:
            cookie_path = Path(directory) / "control_auth_cookie"
            cookie_path.write_bytes(bytes(range(32)))
            with MockTorControl(signal_code=552) as server:
                result = subprocess.run(
                    [sys.executable, str(CLIENT), str(cookie_path), str(server.port)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NEWNYM cooldown", result.stderr)


if __name__ == "__main__":
    unittest.main()
