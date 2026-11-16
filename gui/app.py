#!/usr/bin/env python3
"""Primary OnionGate GUI entry point."""

from __future__ import annotations

import sys

if __package__:
    from .oniongate_gui import main
else:
    from oniongate_gui import main


if __name__ == "__main__":
    raise SystemExit(main())
