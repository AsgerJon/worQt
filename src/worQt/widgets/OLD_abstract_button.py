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

from PySide6.QtCore import Signal, QEvent, Slot
from PySide6.QtGui import QMouseEvent, QWheelEvent, QPointerEvent
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

from ..desQt import App, Etc
from ..desQt.pens import EmptyPen, EmptyBrush
from ..geometry import Rect, Point2D
from ..nums import resolveQtNum, MouseButtonNum
from ..settings import MouseClickSettings
from ..events import CursorMove, CursorRelease, CursorPress
from .states import PRESS_TYPES, RELEASE_TYPES, MOVE_TYPES, MouseButton, \
  ReleaseTimer, HoldTimer, ButtonPressed
from .states import CursorPosition, CursorHover
from . import Layout, LabelWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable


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

  #  Fallback Variables

  #  Private Variables
  __click_stack__ = None
  __press_position__ = None
  __release_position__ = None
  __hold_position__ = None

  #  Public Variables
  clickStack = Field()
  leftPressed = ButtonPressed(MouseButtonNum.LEFT)
  rightPressed = ButtonPressed(MouseButtonNum.RIGHT)
  middlePressed = ButtonPressed(MouseButtonNum.MIDDLE)
  forwardPressed = ButtonPressed(MouseButtonNum.FORWARD)
  backPressed = ButtonPressed(MouseButtonNum.BACK)

  #  Flags

  #  Virtual Variables

  #  Timers
  releaseTimer = ReleaseTimer()
  pressTimer = ReleaseTimer()
  holdTimer = HoldTimer()

  #  Positions
  pressPosition = Field()
  releasePosition = Field()
  holdPosition = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @clickStack.GET
  def _getClickStack(self) -> list[MouseButtonNum]:
    return maybe(self.__click_stack__, [])

  @pressPosition.GET
  def _getPressPosition(self) -> Point2D:
    return maybe(self.__press_position__, Point2D(-1, -1))

  @releasePosition.GET
  def _getReleasePosition(self) -> Point2D:
    return maybe(self.__release_position__, Point2D(-1, -1))

  @holdPosition.GET
  def _getHoldPosition(self) -> Point2D:
    return maybe(self.__hold_position__, Point2D(-1, -1))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setPressPosition(self, pos: Point2D) -> None:
    """
    Sets the position of the mouse cursor when the button was pressed.
    """
    if not isinstance(pos, Point2D):
      raise TypeException('pos', pos, Point2D, )
    self.__press_position__ = pos

  def _setReleasePosition(self, pos: Point2D) -> None:
    """
    Sets the position of the mouse cursor when the button was released.
    """
    if not isinstance(pos, Point2D):
      raise TypeException('pos', pos, Point2D, )
    self.__release_position__ = pos

  def _setHoldPosition(self, pos: Point2D) -> None:
    """
    Sets the position of the mouse cursor when the button was held.
    """
    if not isinstance(pos, Point2D):
      raise TypeException('pos', pos, Point2D, )
    self.__hold_position__ = pos

  def _addClick(self, btn: MouseButtonNum) -> None:
    """
    Adds a mouse button click to the click stack. This is used to
    accumulate clicks for combo clicks.
    """
    self.__click_stack__ = [*self.clickStack, btn]

  def _clearClickStack(self) -> None:
    self.__click_stack__ = []

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  hover = Signal()
  leave = Signal()
  comboClick = Signal(MouseButtonNum, int)
  comboHeld = Signal(MouseButtonNum, int)
  shake = Signal()
  spin = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _notifyPress(self, event_: QMouseEvent) -> None:
    point = QPointerEvent.points(event_)[0]
    if point in self.getMouseArea():
      self._buttonPress(event_)
    LabelWidget._notifyPress(self, event_)

  def _notifyRelease(self, event_: QMouseEvent) -> None:
    point = QPointerEvent.points(event_)[0]
    if point in self.getMouseArea():
      self._buttonRelease(event_)
    LabelWidget._notifyRelease(self, event_)

  def _notifyMove(self, event_: QMouseEvent) -> None:
    point = QPointerEvent.points(event_)
    if point in self.getMouseArea():
      self._buttonMove(event_)
    LabelWidget._notifyMove(self, event_)

  def _updateButtonState(self, event_: QMouseEvent) -> None:
    if event_.type() in PRESS_TYPES:
      state = True
    elif event_.type() in RELEASE_TYPES:
      state = False
    else:
      return  # Not a button event
    num = MouseButtonNum.fromValue(event_.buttons())
    self.leftPressed = True if num is MouseButtonNum.LEFT else False
    self.rightPressed = True if num is MouseButtonNum.RIGHT else False
    self.middlePressed = True if num is MouseButtonNum.MIDDLE else False
    self.forwardPressed = True if num is MouseButtonNum.FORWARD else False
    self.backPressed = True if num is MouseButtonNum.BACK else False

  def _buttonPress(self, event_: QMouseEvent) -> None:
    self._updateButtonState(event_)
    self.pressTimer.stop()
    self.releaseTimer.start()
    self.holdTimer.start()

  def _buttonRelease(self, event_: QMouseEvent) -> None:
    self._updateButtonState(event_)
    self.releaseTimer.stop()
    self.holdTimer.stop()
    self.pressTimer.start()

  def _buttonMove(self, event_: QMouseEvent) -> None:
    pass

  def pressTimeoutFunc(self, ) -> None:
    pass

  def releaseTimeoutFunc(self, ) -> None:
    pass

  def holdTimeoutFunc(self, ) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
