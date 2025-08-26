"""
DebugWidget subclasses BaseWidget for the purpose of testing and debugging.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtGui import QMouseEvent
from worktoy.utilities import maybe

from . import BaseWidget, LabelWidget

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self


class DebugWidget(LabelWidget):
  """
  DebugWidget subclasses BaseWidget for the purpose of testing and debugging.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getText(self) -> str:
    infoSpec = """Pos: %10s | Drift: %.3f"""
    pos = str(self.cursorPosition)
    drift = maybe(self.cursorPosition.holdDrift, 0.0)
    return infoSpec % (pos, drift)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _notifyMove(self, event_: QMouseEvent) -> Self:
    """Inserts update before super call"""
    self.update()
    return LabelWidget._notifyMove(self, event_)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def leaveEvent(self, event_: QEvent) -> None:
    """Override to update the widget when the mouse leaves."""
    self.cursorPosition.clear()
    self.update()
    super().leaveEvent(event_)
