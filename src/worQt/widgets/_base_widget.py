"""
BaseWidget provides the basic widget functionality for the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QPen, \
  QColor, \
  QBrush, \
  QEnterEvent, \
  QMouseEvent, \
  QPointerEvent, QEventPoint, QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.utilities import maybe

from ..geometry import Point2D

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseWidget(QWidget):
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
  __holding_point__ = None  #
  __mouse_px__ = None  # The x-coordinate of the mouse cursor
  __mouse_py__ = None  # The y-coordinate of the mouse cursor
  __mouse_vx__ = None
  __mouse_vy__ = None

  #  Public Variables

  #  Virtual Variables
  emptyPen = Field()
  emptyBrush = Field()
  hovered = Field()  # True when under cursor
  pressed = Field()  # True when under cursor and mouse button is pressed
  moving = Field()  # True when under moving cursor
  holding = Field()  # True when under resting cursor
  mouseButton = Field()  # The pressed button or 'NULL' if unpressed.
  mouseX = Field()  # The x-coordinate of the mouse cursor.
  mouseY = Field()  # The y-coordinate of the mouse cursor.
  mousePos = Field()  # The position of the mouse cursor as a 'Point'.
  mouseVel = Field()

  #  Overloaded Functions

  #  Timers
  wasMoving = Field()  # Unsets moving on timeout

  #  Signals
  moved = Signal()
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

  @mouseX.GET
  def _getMouseX(self) -> float:
    return maybe(self.__mouse_px__, -1.0)

  @mouseY.GET
  def _getMouseY(self) -> float:
    return maybe(self.__mouse_py__, -1.0)

  @mousePos.GET
  def _getMousePos(self) -> Point2D:
    return Point2D(self.mouseX, self.mouseY)

  @mouseVel.GET
  def _getMouseVel(self) -> float:
    """Returns the magnitude of the mouse velocity."""
    if self.__mouse_vx__ is None or self.__mouse_vy__ is None:
      return 0.0
    return (self.__mouse_vx__ ** 2 + self.__mouse_vy__ ** 2) ** 0.5

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

  def __init__(self, *args, **kwargs) -> None:
    for arg in args:
      if isinstance(arg, QWidget):
        QWidget.__init__(self, arg)
        break
    else:
      QWidget.__init__(self)
    self.setMouseTracking(True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _updatePoint(self, eventPoint: QEventPoint) -> None:
    """Updates from a QEventPoint."""
    p = eventPoint.position()
    self.__mouse_px__, self.__mouse_py__ = p.x(), p.y()
    v = eventPoint.velocity()
    self.__mouse_vx__, self.__mouse_vy__ = v.x(), v.y()
    eventState = eventPoint.state()
    if eventState is QEventPoint.State.Updated:
      self.moved.emit()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def event(self, event_: QEvent) -> bool:
    """Override the event method to handle custom events."""
    if isinstance(event_, QPointerEvent):
      eventPoints = event_.points()
      if eventPoints:
        self._updatePoint(eventPoints[0])
    return QWidget.event(self, event_)

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

  def paintEvent(self, event: QPaintEvent) -> None:
    """Override the paint event to handle custom painting."""
    QWidget.paintEvent(self, event)
    painter = QPainter()
    painter.begin(self)
    g = self.geometry()
    v = painter.viewport()
    print(g, ' | ', v)
