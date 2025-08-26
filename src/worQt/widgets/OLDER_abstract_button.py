"""
AbstractButton subclasses LabelWidget and provides a base class for mouse
aware buttons. The base class provides comprehension of user inputs given
with a mouse cursor.

The base class provides the following functionalities (the mouse area
spoken of is the 'Rect' object returned by the 'getMouseArea' method):

From the parent widget classes, it inherits the following properties:
 - 'hovered': True when cursor inside mouse area
 - 'cursorPosition': Cursor position relative to mouse area
 - 'modifiers': The keyboard modifiers pressed when the mouse event
    occurred

It provides the following signals intended for further processing by
subclasses (i.e. push buttons and radio buttons).
 - 'hover': Emitted when the cursor enters the button area.
 - 'leave': Emitted when the cursor leaves the button area.
 - 'comboClick': Emits mouse button input. All mouse button inputs are
 emitted through this signal. Single click, double click and any other
 combination of mouse button clicks are stacked into a single user input
 emitted through this signal.
 - 'comboHeld': Same as above, except ending with holding the last button
 being held for the hold duration specified by the settings value.
 - 'shake': Emitted when the mouse cursor moves rapidly within the mouse
 area (WORK IN PROGRESS!).
 - 'spin': Emitted when the mouse cursor moves in a circular motion within
 the mouse area (WORK IN PROGRESS!).

Finally, it exposes the following properties in addition to those
inherited from parent classes:
 - 'clickStack': The clicks the user has pressed so far. For example,
 when the user intends to emit a triple left click, before the final click,
 this property will return an array of two left clicks.

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal, QEvent
from PySide6.QtGui import QMouseEvent, QPointerEvent, QEventPoint, \
  QEnterEvent
from PySide6.QtGui import QFont, QSinglePointEvent
from PySide6.QtWidgets import QWidget
from icecream import ic
from worktoy.desc import Field
from worktoy.utilities import maybe

from ..core import RGBA
from ..desQt import StateFlag
from ..geometry import Rect, Point2D, Vector2D
from ..nums import MouseButtonNum
from ..settings import MouseClickSettings
from . import PRESS_TYPES, RELEASE_TYPES, MOVE_TYPES
from . import LEAVE_TYPES, ENTER_TYPES
from . import LabelWidget, TimerBox, ButtonFlags

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias

  Widget: TypeAlias = Type[QWidget]

ic.configureOutput(includeContext=True, )


class AbstractButton(LabelWidget):
  """
  AbstractButton subclasses LabelWidget and provides a base class for mouse
  aware buttons. The base class provides comprehension of user inputs given
  with a mouse cursor.

  The base class provides the following functionalities (the mouse area
  spoken of is the 'Rect' object returned by the 'getMouseArea' method):

  From the parent widget classes, it inherits the following properties:
   - 'hovered': True when cursor inside mouse area
   - 'cursorPosition': Cursor position relative to mouse area
   - 'modifiers': The keyboard modifiers pressed when the mouse event
      occurred

  It provides the following signals intended for further processing by
  subclasses (i.e. push buttons and radio buttons).
   - 'hover': Emitted when the cursor enters the button area.
   - 'leave': Emitted when the cursor leaves the button area.
   - 'comboClick': Emits mouse button input. All mouse button inputs are
   emitted through this signal. Single click, double click and any other
   combination of mouse button clicks are stacked into a single user input
   emitted through this signal.
   - 'comboHeld': Same as above, except ending with holding the last button
   being held for the hold duration specified by the settings value.
   - 'shake': Emitted when the mouse cursor moves rapidly within the mouse
   area (WORK IN PROGRESS!).
   - 'spin': Emitted when the mouse cursor moves in a circular motion within
   the mouse area (WORK IN PROGRESS!).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  clickSettings = MouseClickSettings()

  #  Fallback Variables

  #  Private Variables
  __field_name__ = None
  __field_owner__ = None
  __event_point__ = None
  __is_hovered__ = None
  __is_pressed__ = None
  __is_checked__ = None
  __press_position__ = None
  __release_position__ = None
  __click_stack__ = None
  __press_button__ = None

  #  Public Variables
  fieldName = Field()
  fieldOwner = Field()
  eventPoint = Field()
  pressPosition = Field()
  releasePosition = Field()
  clickStack = Field()
  pressButton = Field()

  #  Timers
  pressTimer = TimerBox()
  releaseTimer = TimerBox()
  holdTimer = TimerBox()

  #  Virtual Variables
  mouseArea = Field()
  cursorX = Field()
  cursorY = Field()
  cursorSpeed = Field()
  cursorVelocity = Field()
  cursorPoint = Field()
  pressDrift = Field()  # vector from latest press to current point
  releaseDrift = Field()  # vector from latest release to current point

  #  Flags
  enabled = StateFlag(QWidget.isEnabled)
  hovered = StateFlag()
  pressed = StateFlag()
  checked = StateFlag()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @hovered
  def _getHovered(self) -> bool:
    return True if self.__is_hovered__ else False

  @pressed
  def _getPressed(self) -> bool:
    return True if self.__is_pressed__ else False

  @checked
  def _getChecked(self) -> bool:
    return True if self.__is_checked__ else False

  @eventPoint.GET
  def _getEventPoint(self) -> QEventPoint:
    return maybe(self.__event_point__, QEventPoint())

  @cursorPoint.GET
  def getCursorPoint(self) -> Point2D:
    return Point2D(self.eventPoint)

  @cursorX.GET
  def getCursorX(self) -> float:
    return self.cursorPoint.x

  @cursorY.GET
  def getCursorY(self) -> float:
    return self.cursorPoint.y

  @cursorVelocity.GET
  def getCursorVelocity(self) -> Vector2D:
    return Vector2D(QEventPoint.velocity(self.eventPoint))

  @cursorSpeed.GET
  def getCursorSpeed(self) -> float:
    return abs(self.cursorVelocity)

  @pressPosition.GET
  def getPressPosition(self) -> Point2D:
    return maybe(self.__press_position__, Point2D(-1, -1))

  @releasePosition.GET
  def getReleasePosition(self) -> Point2D:
    return maybe(self.__release_position__, Point2D(-1, -1))

  @clickStack.GET
  def getClickStack(self) -> list[MouseButtonNum]:
    return maybe(self.__click_stack__, [])

  @pressButton.GET
  def getPressButton(self) -> MouseButtonNum:
    """Get the mouse button that was pressed."""
    return maybe(self.__press_button__, MouseButtonNum.NULL)

  @pressDrift.GET
  def getPressDrift(self) -> Vector2D:
    if self.__press_position__ is None:
      return Vector2D(0, 0)
    return Vector2D(self.cursorPoint, self.pressPosition)

  @releaseDrift.GET
  def getReleaseDrift(self) -> Vector2D:
    if self.__release_position__ is None:
      return Vector2D(0, 0)
    return Vector2D(self.cursorPoint, self.releasePosition)

  @fieldName.GET
  def getFieldName(self) -> str:
    return self.__field_name__

  @fieldOwner.GET
  def getFieldOwner(self) -> Widget:
    return self.__field_owner__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  cursorEnter = Signal()
  cursorLeave = Signal()
  badInputEvent = Signal(QEvent)
  badInput = Signal()
  compoundClick = Signal(object)
  click = Signal()
  compoundHeld = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: Widget, name: str) -> None:
    self.__field_name__ = name
    self.__field_owner__ = owner

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    LabelWidget.__init__(self, *args, **kwargs)
    self.setMouseTracking(True)
    press = self.clickSettings.pressTime
    release = self.clickSettings.releaseTime
    hold = self.clickSettings.holdTime
    type(self).pressTimer.__timeout_interval__ = press
    type(self).releaseTimer.__timeout_interval__ = release
    type(self).holdTimer.__timeout_interval__ = hold
    self.holdTimer.timeout.connect(self._dispatchHeld)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def mouseMoveEvent(self, event_: QMouseEvent) -> None:
    self._processMouse(event_)
    self._processMove(event_)
    self._handleMove(event_)
    self.update()
    LabelWidget.mouseMoveEvent(self, event_)

  def mousePressEvent(self, event_: QMouseEvent) -> None:
    self._processMouse(event_)
    self._processPress(event_)
    self.update()
    LabelWidget.mousePressEvent(self, event_)

  def mouseReleaseEvent(self, event_: QMouseEvent) -> None:
    self._processMouse(event_)
    self._processRelease(event_)
    self.update()
    LabelWidget.mouseReleaseEvent(self, event_)

  def enterEvent(self, event_: QEnterEvent) -> None:
    self._processEnter(event_)
    self.update()
    LabelWidget.enterEvent(self, event_)

  def leaveEvent(self, event_: QEvent) -> None:
    self._processLeave(event_)
    self.update()
    LabelWidget.leaveEvent(self, event_)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mouseArea.GET
  def getMouseArea(self) -> Rect:
    """
    Subclasses must implement this method to specify the exact area inside
    the painted widget that should be considered the mouse area.
    By default, 'QWidget.underMouse()' considers the entire widget as
    mouse area. When the cursor is inside the mouse area, the button will
    be considered hovered and mouse button events will be processed.
    """
    return self.shadowRect

  def initLogic(self, ) -> None:
    """
    Subclasses that reimplement this method should include a super call to
    ensure the base class logic is initialized. If not, the click and hold
    will not be emitted as the timeout signals from the timers will not be
    connected. The precise function of the timers is provided below:

    - 'releaseTimer': This timer is started when the mouse button is
    pressed. To recognize a 'click', the button must be released while
    this timer is still running. When the button is released, if this
    timer is not running, the user input is not recognized and the
    'badInput' and 'badInputEvent' signals are emitted. Otherwise,
    the previously held button is appended to the click stack.

    - 'pressTimer': This timer is started when the mouse button is
    released. If a button is pressed while this timer is still running,
    it is taken to mean that the user intends to append another click to
    the stack, such as a double click. Otherwise, at timeout the timer
    dispatches the click stack. Please note click dispatches may also be
    triggered by the user moving the cursor away from the button,
    which also dispatches the click stack immediately. Only when the user
    keeps the cursor stationary after releasing, the click stack waits for
    'pressTimer' to allow for another click to be stacked.

    - 'holdTimer':  This timer starts along with 'releaseTimer' and upon
    timeout, it emits the 'compoundHeld' signal with the click stack. This
    allows the button to recognize user inputs that end with the button
    held for a prolonged period. This may be useful for situations where
    certain actions must not be triggered accidentally. The 'holdTimer'
    also explains why the timeout of 'releaseTimer' does not connect to
    anything. After 'releaseTimer' times out, the user may still reach a
    valid input by holding the button long enough for 'holdTimer' to time
    out.

    In summary:
    - 'releaseTimer.timeout' connects to nothing
    - 'pressTimer.timeout' connects to '_dispatchClicks'
    - 'holdTimer.timeout' connects to '_dispatchHeld'
    """
    print('initLogic of %s' % self.fieldName)
    # LabelWidget.initLogic(self)

  def _getFont(self, **kwargs) -> Any:
    font = LabelWidget._getFont(self, **kwargs)
    if self.pressed:
      font.__font_weight__ = QFont.Weight.Bold
    elif self.hovered:
      font.__font_weight__ = QFont.Weight.Medium
    return font

  def _getShadowColor(self) -> RGBA:
    """
    Returns the shadow color of the button. The shadow color is used to
    paint the button when it is hovered or pressed.
    """
    color = LabelWidget._getShadowColor(self)
    f = 0.25 if self.hovered else 0
    color = color.darker(f)
    return color if self.enabled else color.lighter(0.5)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _clear(self, ) -> None:
    """Clears timers, points and click stack."""
    self.pressTimer.stop()
    self.releaseTimer.stop()
    self.holdTimer.stop()
    self.__event_point__ = None
    self.__press_position__ = None
    self.__release_position__ = None
    self.__is_hovered__ = None
    self.__click_stack__ = None

  def _badInputFunc(self, event_: QEvent) -> None:
    self._clear()
    self.badInputEvent.emit(event_)
    self.badInput.emit()

  def _appendClick(self) -> None:
    print('appendClick of %s' % self.fieldName)
    button = self.pressButton
    if not button:
      raise RuntimeError("""clicked null button""")
    existing = self.clickStack
    self.__click_stack__ = [*existing, button, ]

  def _dispatchClicks(self, ) -> None:
    self.compoundClick.emit((*self.clickStack,), )
    self.click.emit()
    self._clear()

  def _dispatchHeld(self, ) -> None:
    self.compoundHeld.emit((*self.clickStack,), )
    self._clear()

  def _updatePoint(self, event_: QSinglePointEvent) -> None:
    """Updates the event point from the event. """
    point = QPointerEvent.points(event_)[0]
    self.__event_point__ = QPointerEvent.points(event_)[0]

  def _updateHovered(self, event_: QSinglePointEvent) -> None:
    point = Point2D(QPointerEvent.points(event_)[0])
    if point in self.mouseArea:
      if self.__is_hovered__:
        return
      self.__is_hovered__ = True
      return self._handleEnter(event_)
    if self.__is_hovered__:
      self.__is_hovered__ = False
      return self._handleLeave(event_)

  def _processEnter(self, event_: QSinglePointEvent) -> None:
    self._updatePoint(event_)

  def _processLeave(self, event_: QEvent) -> None:
    self._clear()

  def _processMouse(self, event_: QMouseEvent) -> None:
    """
    Calls the updates shared by all mouse events.
    """
    self._updatePoint(event_)
    self._updateHovered(event_)

  def _processMove(self, event_: QSinglePointEvent) -> None:
    if self.pressTimer.isActive():  # waiting for next click
      if abs(self.releaseDrift) > self.clickSettings.releaseRadius:
        return self._dispatchClicks()
    if self.releaseTimer.isActive():
      if abs(self.pressDrift) > self.clickSettings.pressRadius:
        return self._badInputFunc(event_)

  def _processPress(self, event_: QMouseEvent) -> None:
    print('processPress of %s' % self.fieldName)
    if not self.hovered:
      return
    self.__is_pressed__ = True
    self.__press_position__ = Point2D(event_.position())
    self.__press_button__ = MouseButtonNum(event_.button())
    self.pressTimer.stop()
    self.releaseTimer.start()
    self.holdTimer.start()

  def _processRelease(self, event_: QMouseEvent) -> None:
    print('processRelease of %s' % self.fieldName)
    if not self.hovered:
      return
    self.__is_pressed__ = False
    self.__release_position__ = Point2D(event_.position())
    if self.__event_point__ is None:
      return  # a bad input event triggered before release
    self._appendClick()
    self.holdTimer.stop()
    self.releaseTimer.stop()
    self.pressTimer.start()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _handleMove(self, event_: QMouseEvent) -> None:
    pass

  def _handleEnter(self, event_: QPointerEvent) -> None:
    pass

  def _handleLeave(self, event_: QEvent) -> None:
    pass

  def _handlePress(self, event_: QMouseEvent) -> None:
    pass

  def _handleRelease(self, event_: QMouseEvent) -> None:
    pass
