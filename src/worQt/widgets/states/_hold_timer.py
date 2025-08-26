"""
HoldTimer subclasses QTimer and provides the hold timer.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt

from . import MouseTimer


class HoldTimer(MouseTimer):
  """
  HoldTimer subclasses QTimer and provides the press timer.
  It is used to manage the press of mouse buttons in widgets.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createTimer(self, ) -> QTimer:
    """
    Subclasses must implement this method to specify how to instantiate
    QTimer.
    """
    timer = QTimer(self.instance)
    timer.setSingleShot(True)
    timer.setInterval(self.settings.holdTime)
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.timeout.connect(self.instance.holdTimeoutFunc)
    return timer
