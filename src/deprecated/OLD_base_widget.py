"""
BaseWidget provides the basic widget functionality for the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QPen, QColor, QBrush, QMouseEvent, QPointerEvent
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QWidget

from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

from ..desQt import App, Etc
from ..geometry import Point2D
from ..geometry import Rect
from ..nums import resolveQtNum, MouseButtonNum

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseWidget(QWidget):
  """BaseWidget subclass QWidget and provides the basic widget functionality
  for the worQt framework."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  app = App()
  etc = Etc()
  # settings = Settings("""mouse click settings""")
  __waiting_for_press_time_limit__ = None
  __waiting_for_release_time_limit__ = None
  __waiting_for_hold_time_limit__ = None
  __waiting_for_press_radius__ = None
  __waiting_for_release_radius__ = None
  __waiting_for_hold_radius__ = None

  #  Fallback Variables
  __fallback_button__ = MouseButtonNum.NULL

  #  Private Variables
  __mouse_px__ = None
  __mouse_py__ = None
  __mouse_vx__ = None
  __mouse_vy__ = None
  __under_cursor__ = None
  #  Timers
  __waiting_for_press_timer__ = None
  __waiting_for_release_timer__ = None
  __waiting_for_hold_timer__ = None
  #  Positions
  __waiting_for_press_position__ = None
  __waiting_for_release_position__ = None
  __waiting_for_hold_position__ = None
  #  Mouse buttons
  __waiting_for_press_button__ = None
  __waiting_for_release_button__ = None
  __waiting_for_hold_button__ = None

  __button_stack__ = None

  #  Public Variables
  mouseX = Field()
  mouseY = Field()
  mouseVel = Field()
  underCursor = Field()
  #  Positions
  waitingForPressPosition = Field()
  waitingForReleasePosition = Field()
  waitingForHoldPosition = Field()
  #  Mouse buttons
  waitingForPressButton = Field()
  waitingForReleaseButton = Field()
  waitingForHoldButton = Field()

  #  Settings Variables
  # ---  Time Limits ---
  waitingForPressTimeLimit = Field()
  waitingForReleaseTimeLimit = Field()
  waitingForHoldTimeLimit = Field()
  # ---  Movement Radius Limits ---
  waitingForPressRadius = Field()
  waitingForReleaseRadius = Field()
  waitingForHoldRadius = Field()

  #  Timers
  waitingForPressTimer = Field()
  waitingForReleaseTimer = Field()
  waitingForHoldTimer = Field()

  #  Virtual Variables
  emptyPen = Field()
  emptyBrush = Field()
  mousePos = Field()

  #  Private Signals
  __resetButtons = Signal()

  #  Public Signals
  cursorEnter = Signal()
  cursorLeave = Signal()
  eventType = Signal(str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @waitingForPressTimeLimit.GET
  def _getWaitingForPressTimeLimit(self) -> int:
    return self.settings.waitingForPressTimeLimit

  @waitingForReleaseTimeLimit.GET
  def _getWaitingForReleaseTimeLimit(self) -> int:
    return self.settings.waitingForReleaseTimeLimit

  @waitingForHoldTimeLimit.GET
  def _getWaitingForHoldTimeLimit(self) -> int:
    return self.settings.waitingForHoldTimeLimit

  @waitingForPressRadius.GET
  def _getWaitingForPressRadius(self) -> float:
    return self.settings.waitingForPressRadius

  @waitingForReleaseRadius.GET
  def _getWaitingForReleaseRadius(self) -> float:
    return self.settings.waitingForReleaseRadius

  @waitingForHoldRadius.GET
  def _getWaitingForHoldRadius(self) -> float:
    return self.settings.waitingForHoldRadius

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

  @underCursor.GET
  def _getUnderCursor(self) -> bool:
    """Returns True if the cursor is inside the mouse area."""
    return True if self.__under_cursor__ else False

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

  @waitingForPressButton.GET
  def _getWaitingForPressButton(self) -> MouseButtonNum:
    return maybe(self.__waiting_for_press_button__, self.__fallback_button__)

  @waitingForReleaseButton.GET
  def _getWaitingForReleaseButton(self) -> MouseButtonNum:
    btn, fb = self.__waiting_for_release_button__, self.__fallback_button__
    return maybe(btn, fb)

  @waitingForHoldButton.GET
  def _getWaitingForHoldButton(self) -> MouseButtonNum:
    return maybe(self.__waiting_for_hold_button__, self.__fallback_button__)

  def _getMouseArea(self, ) -> Rect:
    """
    Returns the rectangle indicating the part of the region of the
    widget open to mouse interaction. The 'hovered' flag requires the
    cursor to be inside the mouse area. Please note that this is different
    from the QWidget provided 'underMouse' method, which considers counts
    when the cursor is inside any part of the widget geometry.

    By default, this mouse area defaults to the full geometry of the
    widget, meaning that the 'hovered' flag effectively reflects the
    'underMouse' method.
    """
    return Rect(self.geometry(), )

  def _createWaitingForPress(self, ) -> None:
    """
    Creates the QTimer waiting for a mouse press. It triggers on release
    of any mouse button. It waits for the user to provide further inputs,
    such as the second click in a double-click sequence. Any mouse press
    before timeout cancels the timer. On timeout, the input sequence
    executes. Please note that moving the cursor before the timeout,
    cancels the timeout and immediately executes the input sequence.

    Whenever a user has completed an input sequence, such as a double
    click, the user is likely to move the cursor to the next input action.
    The user may also leave the cursor after the input sequence,
    for example to move hands to the keyboard. The latter case is handled
    by the timeout of the 'waitingForRelease' timer. The first case is
    handled by the 'mouseAreaMoveEvent' method, which registers how far
    the cursor has moved from where it was when the 'waitingForPress'
    timer was last started.
    """
    self.__waiting_for_press_timer__ = QTimer()
    self.__waiting_for_press_timer__.setSingleShot(True)
    timeLimit = self.waitingForPressTimeLimit
    self.__waiting_for_press_timer__.setInterval(timeLimit)
    self.__waiting_for_press_timer__.setTimerType(Qt.TimerType.PreciseTimer)
    self.__waiting_for_press_timer__.timeout.connect(self._waitedForPress)

  @waitingForPressTimer.GET
  def _getWaitingForPress(self, **kwargs) -> QTimer:
    if self.__waiting_for_press_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWaitingForPress()
      return self._getWaitingForPress(_recursion=True)
    if isinstance(self.__waiting_for_press_timer__, QTimer):
      return self.__waiting_for_press_timer__
    name, value = '__waiting_for_press__', self.__waiting_for_press_timer__
    raise TypeException(name, value, QTimer, )

  @waitingForPressPosition.GET
  def _getWaitingForPressPosition(self, **kwargs) -> Point2D:
    return self.__waiting_for_press_position__

  def _createWaitingForRelease(self, ) -> None:
    """
    Creates the QTimer waiting for a mouse release. It starts on any mouse
    press. The user must release the mouse button before the timer times
    out for the 'click' to be registered. Upon release, if the cursor has
    remained stationary, the release is registered as a click action. If
    the 'waitingForPress' times out, it cancels the 'click'. The longer
    'waitingForHold' timer started at the same time, then lets the user
    hold longer to trigger a 'press and hold' action.

    Unlike the 'waitingForPress' timer, movement during the timer is not
    recognized as valid input. This allows the user to cancel an unwanted
    click by moving the cursor. This matches the user behaviour that
    expects the 'click' to occur upon release of the mouse button.

    Please note that the 'waitingForRelease' timer is not connected to any
    action on timeout. Instead, the 'mouseAreaReleaseEvent' method uses
    this timer to decide if the release is a click.
    """
    self.__waiting_for_release_timer__ = QTimer()
    self.__waiting_for_release_timer__.setSingleShot(True)
    time, type_ = self.waitingForReleaseTimeLimit, Qt.TimerType.PreciseTimer
    self.__waiting_for_release_timer__.setInterval(time)
    self.__waiting_for_release_timer__.setTimerType(type_)
    callback = self._waitedForRelease
    self.__waiting_for_release_timer__.timeout.connect(callback)

  @waitingForReleaseTimer.GET
  def _getWaitingForRelease(self, **kwargs) -> QTimer:
    if self.__waiting_for_release_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWaitingForRelease()
      return self._getWaitingForRelease(_recursion=True)
    if isinstance(self.__waiting_for_release_timer__, QTimer):
      return self.__waiting_for_release_timer__
    name = '__waiting_for_release__'
    value = self.__waiting_for_release_timer__
    raise TypeException(name, value, QTimer, )

  @waitingForReleasePosition.GET
  def _getWaitingForReleasePosition(self, **kwargs) -> Point2D:
    return self.__waiting_for_release_position__

  def _createWaitingForHold(self, ) -> None:
    """
    Creates the QTimer waiting for the user to hold long enough to trigger
    a 'press and hold' action. The timer starts on any mouse press. Upon
    timeout, if the cursor remained stationary, the 'press and hold' action
    is triggered.

    Input sequences including any 'press and hold' actions should end on
    it rather than requiring further clicks. For example, an input
    sequence might be a double click where the second click must be held.

    Please note the 'dead zone' between the 'waitingForRelease' and
    'waitingForHold'. If the user releases after 'waitingForRelease' has
    timed out, but before 'waitingForHold' has timed out, the input is
    unrecognized. The suggested time limits should make the 'press and
    hold' noticeably long. This makes them suitable for infrequently used
    or irreversible actions.

    Finally note, that the 'press and hold' triggers on the timeout,
    not on the release. A visual indication of the 'press and hold'
    waiting state is thus recommended to inform the user that something is
    about to happen. This achieves both a visual feedback of remaining
    waiting time and a visual warning against inadvertent actions.
    """
    self.__waiting_for_hold_timer__ = QTimer()
    self.__waiting_for_hold_timer__.setSingleShot(True)
    timeLimit = self.waitingForHoldTimeLimit
    self.__waiting_for_hold_timer__.setInterval(timeLimit)
    self.__waiting_for_hold_timer__.setTimerType(Qt.TimerType.PreciseTimer)
    self.__waiting_for_hold_timer__.timeout.connect(self._waitedForHold)

  @waitingForHoldTimer.GET
  def _getWaitingForHold(self, **kwargs) -> QTimer:
    if self.__waiting_for_hold_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWaitingForHold()
      return self._getWaitingForHold(_recursion=True)
    if isinstance(self.__waiting_for_hold_timer__, QTimer):
      return self.__waiting_for_hold_timer__
    name, value = '__waiting_for_hold__', self.__waiting_for_hold_timer__
    raise TypeException(name, value, QTimer, )

  @waitingForHoldPosition.GET
  def _getWaitingForHoldPosition(self, **kwargs) -> Point2D:
    return self.__waiting_for_hold_position__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

  def _waitedForPress(self) -> None:
    """
    Called when the waiting for press timer runs out. This dispatches the
    button stack and then resets it.
    """
    raise NotImplementedError

  def _waitedForRelease(self, ) -> None:
    """
    Called when the user has pressed the button long enough to cancel
    normal click action. By default, this method does nothing as the
    widget is still waiting for a potential 'press and hold' action. If a
    release occurs after this time but before the 'press and hold' action
    occurs, the 'mouseAreaReleaseEvent' method handles it.
    """

  def _waitedForHold(self, ) -> None:
    """
    Called when the user has held the mouse button long enough to trigger
    a 'press and hold' action.
    """
    raise NotImplementedError

  def mouseAreaPressEvent(self, event: QMouseEvent, ) -> None:
    """Called when the mouse button is pressed inside the mouse area."""
    self.__waiting_for_release_position__ = Point2D(event)
    self.__waiting_for_release_button__ = event.button()
    self.__waiting_for_hold_position__ = Point2D(event)
    self.__waiting_for_hold_button__ = event.button()
    if self.waitingForPressTimer.isActive():
      raise NotImplementedError
    self.waitingForReleaseTimer.start()
    self.waitingForHoldTimer.start()

  def mouseAreaReleaseEvent(self, event: QMouseEvent, ) -> None:
    """Called when the mouse button is released inside the mouse area."""
    self.__waiting_for_press_position__ = Point2D(event)
    self.__waiting_for_press_button__ = event.button()
    if self.waitingForReleaseTimer.isActive():
      raise NotImplementedError
    if self.waitingForHoldTimer.isActive():
      raise NotImplementedError
    self.waitingForPressTimer.start()

  def mouseAreaEnterEvent(self, event: QPointerEvent, ) -> None:
    """Called when the mouse cursor enters the mouse area."""

  def mouseAreaLeaveEvent(self, event: QPointerEvent, ) -> None:
    """Called when the mouse cursor leaves the mouse area."""

  def mouseAreaMoveEvent(self, event: QPointerEvent, ) -> None:
    """Called when the mouse cursor moves inside the mouse area."""
    if self.waitingForPressTimer.isActive():
      self.waitingForPressTimer.stop()

  def _dispatchButtonStack(self, ) -> None:
    """Dispatches the button stack. """
    raise NotImplementedError

  def _resetButtonStack(self, ) -> None:
    """
    Resets the button stack by emptying it and removes all existing
    timer objects. Also emits the private '_resetButtons' signal to
    notify any listeners that the button stack has been reset.
    """
    self.__button_stack__ = None
    self.__waiting_for_press_button__ = None
    self.__waiting_for_release_button__ = None
    self.__waiting_for_hold_button__ = None
    self.__waiting_for_press_position__ = None
    self.__waiting_for_release_position__ = None
    self.__waiting_for_hold_position__ = None
    self.__waiting_for_press_timer__ = None
    self.__waiting_for_release_timer__ = None
    self.__waiting_for_hold_timer__ = None
    self.__resetButtons.emit()

  def _undefinedInput(self, ) -> None:
    """
    Method invoked when user input is undefined. For example, when the
    user moves the cursor whilst pressing a mouse button. This example
    would be taken as the user wishing to cancel the 'click' that would
    result from releasing. After this method is invoked, the mouse input
    stack resets itself.

    Please note that this method is not expected to raise an exception,
    so subclasses may freely implement it. Perhaps to provide a subtle
    visual or even audible feedback to indicate that the input was not
    recognized. Subclasses wishing to raise an exception must explicitly
    interrupt the running application in this case.

    The default implementation does nothing.
    """

  def event_DEBUG(self, event_: QEvent) -> None:
    if isinstance(event_, (QMouseEvent, QWheelEvent)):
      typeName = resolveQtNum(QEvent.Type, event_.type())
      self.eventType.emit(typeName)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def event(self, event_: QEvent) -> bool:
    """Override the event method to handle custom events."""
    typeName = resolveQtNum(QEvent.Type, event_.type())
    self.event_DEBUG(event_)
    point = None
    if isinstance(event_, QMouseEvent):
      eventPoint = event_.points()[0]
      p = eventPoint.position()
      self.__mouse_px__, self.__mouse_py__ = p.x(), p.y()
      v = eventPoint.velocity()
      self.__mouse_vx__, self.__mouse_vy__ = v.x(), v.y()
      geom = Rect(self.geometry(), )
      point = Point2D(self.__mouse_px__, self.__mouse_py__)

      if point in geom:
        if not self.underCursor:
          self.__under_cursor__ = True
          self.cursorEnter.emit()
          self.mouseAreaEnterEvent(event_, )

        elif typeName in ['MouseButtonPress', 'MouseButtonDblClick']:
          self.mouseAreaPressEvent(event_)

        elif typeName == 'MouseButtonRelease':
          self.mouseAreaReleaseEvent(event_)

        elif typeName == 'MouseMove':
          self.mouseAreaMoveEvent(event_)

      elif self.underCursor:
        self.__under_cursor__ = False
        self.cursorLeave.emit()
        self.mouseAreaLeaveEvent(event_, )

    return QWidget.event(self, event_)
