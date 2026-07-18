"""
GestureLight is a labelled indicator: it flashes a lit colour when its
gesture fires - showing which mouse button triggered it - then fades back
to its idle colour after a short delay.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

from worQt.utils import Color
from worQt.widgets import LabelWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class GestureLight(LabelWidget):
  """A labelled indicator that flashes when its gesture fires."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DEFAULT VALUES   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  __idle_color__ = Color(206, 206, 210)  # dim, at rest
  __lit_color__ = Color(120, 224, 140)  # bright, just fired
  __rest_delay__ = 500  # ms lit before fading back

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __gesture_name__: Optional[str] = None  # the persistent title
  __rest_timer__: Optional[QTimer] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setGesture(self, name: str) -> None:
    """Set the persistent title and reset to the idle colour."""
    self.__gesture_name__ = name
    self.text = name
    self.paddingsColor = self.__idle_color__

  def _createRestTimer(self) -> None:
    timer: QTimer = QTimer(self)
    QTimer.setSingleShot(timer, True)
    QTimer.setInterval(timer, self.__rest_delay__)
    QTimer.timeout.__get__(timer, QTimer).connect(self._fade)
    self.__rest_timer__ = timer

  def _restTimer(self) -> QTimer:
    if self.__rest_timer__ is None:
      self._createRestTimer()
    return self.__rest_timer__

  def _fade(self) -> None:
    """Return to the idle colour and the plain title."""
    self.text = self.__gesture_name__ or ''
    self.paddingsColor = self.__idle_color__

  def light(self, button: str) -> None:
    """Flash the lit colour and show 'button', then fade back."""
    self.text = '%s: %s' % (self.__gesture_name__ or '', button)
    self.paddingsColor = self.__lit_color__
    QTimer.start(self._restTimer())
