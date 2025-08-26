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

from icecream import ic

from PySide6.QtCore import Signal, QEvent, Qt
from PySide6.QtGui import QMouseEvent, QPointerEvent, QEventPoint, \
  QFontMetrics
from PySide6.QtGui import QFont, QSinglePointEvent
from PySide6.QtWidgets import QWidget, QApplication
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute.dispatch import DispatchException

from ..core import RGBA
from ..desQt import StateFlag
from ..geometry import Rect, Point2D, Vector2D, Size
from ..nums import MouseButtonNum, KeyMod
from ..settings import MouseClickSettings

from . import LabelWidget, TimerBox, PRESS_TYPES, RELEASE_TYPES, Click

from typing import TYPE_CHECKING

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
  #  --- From '__set_name__' on the 'BetterBox' ---
  __field_name__ = None
  __field_owner__ = None
  #  --- Positions ---
  __press_position__ = None
  __release_position__ = None
  #  --- Timestamps ---
  __press_timestamp__ = None
  __release_timestamp__ = None
  #  --- Mouse buttons and keyboard modifiers ---
  __press_button__ = None
  __release_button__ = None
  __press_modifiers__ = None
  __release_modifiers__ = None
  #  --- Flags ---
  __is_checked__ = None
  _hasClicks = Field()
  #  --- Remaining Variables ---
  __event_point__ = None
  __click_stack__ = None

  #  Public Variables
  fieldName = Field()
  fieldOwner = Field()
  eventPoint = Field()
  pressPosition = Field()
  pressTimestamp = Field()
  releasePosition = Field()
  releaseTimestamp = Field()
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

  #  Signals
  cursorEnter = Signal()
  cursorLeave = Signal()
  badInputEvent = Signal(QEvent)
  badInput = Signal()
  compoundClick = Signal(tuple[Click, ...])
  click = Signal()
  compoundHeld = Signal(tuple[Click, ...])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @_hasClicks.GET
  def _getHasClicks(self) -> bool:
    for _ in self.clickStack:
      return True
    return False

  @hovered
  def _getHovered(self) -> bool:
    return True if self.cursorPoint in self.mouseArea else False

  @pressed
  def _getPressed(self) -> bool:
    noButton = Qt.MouseButton.NoButton
    return True if QApplication.mouseButtons() != noButton else False

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

  @pressTimestamp.GET
  def getPressTimestamp(self) -> float:
    return self.__press_timestamp__

  @releaseTimestamp.GET
  def getReleaseTimestamp(self) -> float:
    return self.__release_timestamp__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: Widget, name: str) -> None:
    self.__field_name__ = name
    self.__field_owner__ = owner

  def __contains__(self, item: Any) -> bool:
    """
    The 'AbstractButton' understands the 'in' operator to mean whether the
    given object can be considered as bound by the mouse area. Objects
    supported are either points or regions such as rectangles. The 'Rect'
    class facilitates both with its overloaded constructor.
    """
    try:
      value = True if item in self.mouseArea else False
    except DispatchException:
      return NotImplemented
    else:
      return value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def event(self, event_: QEvent) -> bool:
    if isinstance(event_, QSinglePointEvent):
      self._processMove(event_)
      type_ = QEvent.type(event_)
      if type_ in PRESS_TYPES:
        self._processPress(event_)
      elif type_ in RELEASE_TYPES:
        self._processRelease(event_)
    return LabelWidget.event(self, event_)

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

    This abstract base class uses the boundingRect of the current text as
    inherited from 'LabelWidget' to define the mouse area. Please note the
    change to how this area is calculated. Instead of relying on the
    'font' descriptor, it uses the super call. This escapes the recursion
    where the 'font' depends on whether the button is hovered,
    which depends on the mouse area.
    """
    font = LabelWidget._getFont(self, )
    font.__font_weight__ = QFont.Weight.Normal  # using normal weight
    return Rect(QFontMetrics(font.Q, ).boundingRect(self.text))

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
    LabelWidget.initLogic(self)
    self.pressTimer.timeout.connect(self._dispatchClicks)

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

  def _clear(self) -> None:
    """
    Clears all timers and resets the button state. This method is called
    when the user input is not recognized as a valid click or hold.
    """
    self.__press_position__ = None
    self.__release_position__ = None
    self.__press_timestamp__ = None
    self.__release_timestamp__ = None
    self.__press_button__ = MouseButtonNum.NULL
    self.__release_button__ = MouseButtonNum.NULL
    self.__press_modifiers__ = KeyMod.NONE
    self.__release_modifiers__ = KeyMod.NONE
    self.__click_stack__ = []
    self.pressTimer.stop()
    self.holdTimer.stop()

  def _appendClick(self, click: Click) -> None:
    self.__click_stack__ = [*self.clickStack, click]

  def _dispatchClicks(self) -> None:
    """
    This method is called when the user input is recognized as a valid
    click. It emits the 'compoundClick' signal with the click stack and
    clears the click stack.
    """
    if not self._hasClicks:
      return
    self.compoundClick.emit(self.clickStack)
    self.click.emit()
    self._clear()

  def _processBadInput(self, event_: QEvent) -> None:
    """
    This method is called when the user input is not recognized as a valid
    click or hold. It emits the 'badInput' and 'badInputEvent' signals.
    """
    self.badInput.emit()
    self.badInputEvent.emit(event_)
    self._clear()

  def _processMove(self, event_: QSinglePointEvent) -> None:
    """
    This method implements the cursor movement. It updates the hovered
    flag, the event point and dispatches the enter and leave methods when
    the cursor enters or leaves the mouse area.
    """
    oldHovered = self.hovered
    newPoint = QPointerEvent.points(event_)[0]
    newHovered = True if Point2D(newPoint) in self.mouseArea else False
    self.__event_point__ = newPoint
    if self._hasClicks:
      drift = Vector2D(self.releasePosition, self.cursorPoint)
      if abs(drift) > self.clickSettings.releaseRadius:
        self._dispatchClicks()
    if newHovered:
      if not oldHovered:
        return self.handleEnter(event_) and self.cursorEnter.emit()
    elif oldHovered:
      return self.handleLeave(event_) and self.cursorLeave.emit()

  def _processPress(self, event_: QSinglePointEvent) -> None:
    """
    This method processes the mouse button press.
    """
    self.__press_position__ = Point2D(QPointerEvent.points(event_)[0])
    self.__press_timestamp__ = event_.timestamp()
    self.__press_button__ = MouseButtonNum(event_.button())
    self.__press_modifiers__ = KeyMod.fromValue(event_.modifiers())
    self.holdTimer.start()

  def _processRelease(self, event_: QSinglePointEvent) -> None:
    """
    This method processes the mouse button release.
    """
    self.__release_position__ = Point2D(QPointerEvent.points(event_)[0])
    self.__release_timestamp__ = event_.timestamp()
    self.__release_button__ = MouseButtonNum(event_.button())
    self.__release_modifiers__ = KeyMod.fromValue(event_.modifiers())
    self._validateClick(event_)

  def _validateClick(self, event_: QSinglePointEvent, ) -> None:
    buttonCheck = self.__press_button__ != self.__release_button__
    modifierCheck = self.__press_modifiers__ != self.__release_modifiers__
    drift = abs(Vector2D(self.__press_position__, self.__release_position__))
    driftCheck = drift > self.clickSettings.pressRadius
    delay = self.__release_timestamp__ - self.__press_timestamp__
    delayCheck = delay > self.clickSettings.pressTime
    if any((buttonCheck, modifierCheck, driftCheck, delayCheck)):
      return self._processBadInput(event_)

    self.pressTimer.start()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def handleEnter(self, event_: QSinglePointEvent) -> None:
    """
    This method is called when the cursor enters the mouse area. It is not
    used by the base class functionality and is available for subclasses.
    """

  def handleLeave(self, event_: QSinglePointEvent) -> None:
    """
    This method is called when the cursor leaves the mouse area. It is not
    used by the base class functionality and is available for subclasses.
    """

  def handlePress(self, event_: QMouseEvent) -> None:
    """
    This method is called when the mouse button is pressed. It is not used
    by the base class functionality and is available for subclasses.
    """

  def handleRelease(self, event_: QMouseEvent) -> None:
    """
    This method is called when the mouse button is released. It is not used
    by the base class functionality and is available for subclasses.
    """

  def handleMove(self, event_: QSinglePointEvent) -> None:
    """
    This method is called when the mouse cursor moves. It is not used by
    the base class functionality and is available for subclasses.
    """
