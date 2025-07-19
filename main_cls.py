"""Tester classes"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QApplication


class App(QApplication):
  """Subclass of QApplication"""

  startUp = Signal()

  def exec(self) -> int:
    """Override exec() to emit startUp signal"""
    QTimer.singleShot(0, self.startUp.emit)
    return super().exec()
