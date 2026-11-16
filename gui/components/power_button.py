"""Custom painted connection control for the OnionGate dashboard."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QAbstractButton, QSizePolicy


class PowerButton(QAbstractButton):
    def __init__(self) -> None:
        super().__init__()
        self._state = "disconnected"
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAccessibleName("Connect to Tor")
        self.setToolTip("Start or stop OnionGate through the installed CLI")

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return self._size()

    def _size(self):
        from PySide6.QtCore import QSize

        return QSize(210, 210)

    def set_state(self, state: str) -> None:
        self._state = state
        self.setAccessibleName(
            "Disconnect OnionGate"
            if state == "connected"
            else "Connecting to Tor"
            if state == "connecting"
            else "Disconnecting from Tor"
            if state == "disconnecting"
            else "Stop active OnionGate gateway"
            if state == "active_unverified"
            else "Retry OnionGate connection"
            if state == "error"
            else "Connect to Tor"
        )
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        bounds = QRectF(
            (self.width() - side) / 2 + 9,
            (self.height() - side) / 2 + 9,
            side - 18,
            side - 18,
        )
        center = bounds.center()
        radius = bounds.width() / 2
        connected = self._state == "connected"
        accent = QColor("#ff7078" if connected else "#32e6ae")
        if self._state in ("connecting", "disconnecting"):
            accent = QColor("#f0bd64")

        for spread, alpha in ((1.24, 16), (1.13, 24), (1.04, 38)):
            glow = QRadialGradient(center, radius * spread)
            glow.setColorAt(0.68, QColor(accent.red(), accent.green(), accent.blue(), alpha))
            glow.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(center, radius * spread, radius * spread)

        fill = QRadialGradient(center.x(), center.y() - radius * 0.3, radius * 1.4)
        fill.setColorAt(0.0, QColor("#18372f"))
        fill.setColorAt(1.0, QColor("#101a21"))
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 210), 2.2))
        painter.drawEllipse(bounds)

        icon_radius = radius * 0.25
        power_path = QPainterPath()
        power_path.arcMoveTo(
            center.x() - icon_radius,
            center.y() - icon_radius,
            icon_radius * 2,
            icon_radius * 2,
            45,
        )
        power_path.arcTo(
            center.x() - icon_radius,
            center.y() - icon_radius,
            icon_radius * 2,
            icon_radius * 2,
            45,
            270,
        )
        painter.setPen(
            QPen(
                accent,
                max(3.0, radius * 0.045),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(power_path)
        painter.drawLine(
            center.x(),
            center.y() - icon_radius * 1.35,
            center.x(),
            center.y() - icon_radius * 0.05,
        )

        label = (
            "DISCONNECT"
            if connected
            else "CONNECTING"
            if self._state == "connecting"
            else "DISCONNECTING"
            if self._state == "disconnecting"
            else "STOP ACTIVE GATEWAY"
            if self._state == "active_unverified"
            else "RETRY"
            if self._state == "error"
            else "CONNECT TO TOR"
        )
        painter.setPen(QColor("#eaf5f1"))
        painter.drawText(
            QRectF(bounds.left(), center.y() + radius * 0.43, bounds.width(), radius * 0.32),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            label,
        )
