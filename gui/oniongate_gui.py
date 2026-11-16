#!/usr/bin/env python3
"""OnionGate desktop interface. The existing oniongate CLI remains the backend."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QCompleter, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout,
    QWidget,
)

APP_NAME = "OnionGate"
BACKEND_CANDIDATES = [Path("/usr/local/bin/oniongate"), Path("/usr/bin/oniongate")]
STATUS_FILE = Path("/run/oniongate.status")
LOG_FILE = Path("/etc/oniongate/tor.log")
SOCKS_PORT = "9050"

COUNTRIES = [
    ("Automatic (Tor chooses)", ""),
    ('Afghanistan', 'af'),
    ('Albania', 'al'),
    ('Algeria', 'dz'),
    ('American Samoa', 'as'),
    ('Andorra', 'ad'),
    ('Angola', 'ao'),
    ('Anguilla', 'ai'),
    ('Antarctica', 'aq'),
    ('Antigua and Barbuda', 'ag'),
    ('Argentina', 'ar'),
    ('Armenia', 'am'),
    ('Aruba', 'aw'),
    ('Australia', 'au'),
    ('Austria', 'at'),
    ('Azerbaijan', 'az'),
    ('Bahamas', 'bs'),
    ('Bahrain', 'bh'),
    ('Bangladesh', 'bd'),
    ('Barbados', 'bb'),
    ('Belarus', 'by'),
    ('Belgium', 'be'),
    ('Belize', 'bz'),
    ('Benin', 'bj'),
    ('Bermuda', 'bm'),
    ('Bhutan', 'bt'),
    ('Bolivia, Plurinational State of', 'bo'),
    ('Bonaire, Sint Eustatius and Saba', 'bq'),
    ('Bosnia and Herzegovina', 'ba'),
    ('Botswana', 'bw'),
    ('Bouvet Island', 'bv'),
    ('Brazil', 'br'),
    ('British Indian Ocean Territory', 'io'),
    ('Brunei Darussalam', 'bn'),
    ('Bulgaria', 'bg'),
    ('Burkina Faso', 'bf'),
    ('Burundi', 'bi'),
    ('Cabo Verde', 'cv'),
    ('Cambodia', 'kh'),
    ('Cameroon', 'cm'),
    ('Canada', 'ca'),
    ('Cayman Islands', 'ky'),
    ('Central African Republic', 'cf'),
    ('Chad', 'td'),
    ('Chile', 'cl'),
    ('China', 'cn'),
    ('Christmas Island', 'cx'),
    ('Cocos (Keeling) Islands', 'cc'),
    ('Colombia', 'co'),
    ('Comoros', 'km'),
    ('Congo', 'cg'),
    ('Congo, The Democratic Republic of the', 'cd'),
    ('Cook Islands', 'ck'),
    ('Costa Rica', 'cr'),
    ('Croatia', 'hr'),
    ('Cuba', 'cu'),
    ('Curaçao', 'cw'),
    ('Cyprus', 'cy'),
    ('Czechia', 'cz'),
    ("Côte d'Ivoire", 'ci'),
    ('Denmark', 'dk'),
    ('Djibouti', 'dj'),
    ('Dominica', 'dm'),
    ('Dominican Republic', 'do'),
    ('Ecuador', 'ec'),
    ('Egypt', 'eg'),
    ('El Salvador', 'sv'),
    ('Equatorial Guinea', 'gq'),
    ('Eritrea', 'er'),
    ('Estonia', 'ee'),]