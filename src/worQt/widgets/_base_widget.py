"""
BaseWidget provides the basic widget functionality for the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QPaintEvent, \
  QPen, \
  QColor, \
  QBrush, \
  QEnterEvent, \
  QMouseEvent
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import Dispatcher

from ..nums import MouseButtonNum as Mouse

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class _QWidget(QWidget):
  def __init__(self, parent: QWidget = None) -> None:
    if parent is None:
      QWidget.__init__(self, )
    else:
      QWidget.__init__(self, parent)
    self.setMouseTracking(True)


class BaseWidget(_QWidget):
  """BaseWidget subclass QWidget and provides the basic widget functionality
  for the worQt framework."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __under_cursor__ = None
  __cursor_moving__ = None
  __was_moving__ = None  # Timer to track if the cursor was moving

  #  Public Variables

  #  Virtual Variables
  emptyPen = Field()
  emptyBrush = Field()
  hovered = Field()  # True when under cursor
  pressed = Field()  # True when under cursor and mouse button is pressed
  moving = Field()  # True when under moving cursor
  holding = Field()  # True when under resting cursor
  mouseButton = Field()  # The pressed button or 'NULL' if unpressed.

  #  Overloaded Functions
  
  #  Timers
  wasMoving = Field()  # Unsets moving on timeout

  #  Signals
  cursorEnter = Signal()
  cursorLeave = Signal()
  startedHolding = Signal()
  stoppedHolding = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @emptyPen.GET
  def _getEmptyPen(self) -> QPen:
    pen = QPen()
    pen.setStyle(Qt.PenStyle.NoPen)
    pen.setColor(QColor(0, 0, 0, 0))
    return pen

  @emptyBrush.GET
  def _getEmptyBrush(self) -> QBrush:
    brush = QBrush()
    brush.setStyle(Qt.BrushStyle.NoBrush)
    brush.setColor(QColor(0, 0, 0, 0))
    return brush

  @hovered.GET
  def _getHovered(self) -> bool:
    return True if self.__under_cursor__ else False

  @moving.GET
  def _getMoving(self) -> bool:
    return True if self.__cursor_moving__ else False

  @holding.GET
  def _getHolding(self) -> bool:
    return False if self.__cursor_moving__ else True

  def _createWasMoving(self, ) -> None:
    """Creates the wasMoving timer."""
    self.__was_moving__ = QTimer()
    self.__was_moving__.setSingleShot(False)
    self.__was_moving__.setInterval(200)
    self.__was_moving__.setTimerType(Qt.TimerType.PreciseTimer)
    self.__was_moving__.timeout.connect(self._stopMoving)

  @wasMoving.GET
  def _getWasMoving(self, **kwargs) -> QTimer:
    if self.__was_moving__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWasMoving()
      return self._getWasMoving(_recursion=True)
    if isinstance(self.__was_moving__, QTimer):
      return self.__was_moving__
    raise TypeError('__was_moving__', self.__was_moving__, QTimer, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _stopMoving(self, ) -> None:
    if self.__cursor_moving__:
      self.__cursor_moving__ = False
      self.startedHolding.emit()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def enterEvent(self, event: QEnterEvent) -> None:
    QWidget.enterEvent(self, event)
    self.__under_cursor__ = True
    self.__cursor_moving__ = True
    self.cursorEnter.emit()
    self.wasMoving.start()  # Start the timer to track cursor movement

  def leaveEvent(self, event: QEvent) -> None:
    QWidget.leaveEvent(self, event)
    self.__under_cursor__ = False
    self.__cursor_moving__ = False
    self.cursorLeave.emit()
    self.wasMoving.stop()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    QWidget.mouseMoveEvent(self, event)
    self.__under_cursor__ = True
    self.wasMoving.start()  # Start the timer to track cursor movement
    if not self.__cursor_moving__:
      self.__cursor_moving__ = True
      self.stoppedHolding.emit()
