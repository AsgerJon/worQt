"""
MouseButtonState encapsulates the state of a mouse button. The event
system treats mouse buttons entirely independently, but aLso identically.
Thus, one class is sufficient to represent as many mouse buttons as needed.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtGui import QMouseEvent, QPointerEvent, QEventPoint
from worktoy.desc import Field, Alias
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from ...geometry import Point2D
from ...nums import MouseButtonNum, MouseButtonStateNum

from typing import TYPE_CHECKING

from ...settings import MouseClickSettings

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, Any, Self, Never, Type, TypeAlias

  from .. import BaseWidget

  Widget: TypeAlias = Type[BaseWidget]

_press = QEvent.Type.MouseButtonPress
_doubleClick = QEvent.Type.MouseButtonDblClick
PRESS_TYPES = frozenset({_press, _doubleClick})
RELEASE_TYPES = frozenset({QEvent.Type.MouseButtonRelease, })
MOVE_TYPES = frozenset({QEvent.Type.MouseMove, })


class _PrivateKey:
  __pvt_key__ = None

  def __init__(self, key: str) -> None:
    self.__pvt_key__ = key

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    return self.__pvt_key__


class MouseButtonState(BaseObject):
  """
  MouseButtonState encapsulates the state of a mouse button. The event
  system treats mouse buttons entirely independently, but also identically.
  Thus, one class is sufficient to represent as many mouse buttons as needed.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  settings = MouseClickSettings()
  _pressedKey = _PrivateKey('pressed_key')
  _posKey = _PrivateKey('pos_key')
  _whenKey = _PrivateKey('when_key')

  #  Fallback Variables
  __fallback_num__ = MouseButtonNum.NULL

  #  Private Variables
  __button_num__ = None
  __owning_instance__ = None

  #  Public Variables
  buttonNum = Field()
  pressed = Field()
  pos = Field()
  when = Field()
  instance = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # --  With private value at owning instance -- #
  @pos.GET
  def _getPos(self, ) -> Point2D:
    return getattr(self.instance, self._posKey, Point2D(-1, -1))

  @pressed.GET
  def _getPressed(self, ) -> bool:
    return getattr(self.instance, self._pressedKey, False)

  @when.GET
  def _getWhen(self, ) -> float:
    return getattr(self.instance, self._whenKey, -1.0)

  # --  With private value at 'self' -- #
  @buttonNum.GET
  def _getButtonNum(self) -> MouseButtonNum:
    return maybe(self.__button_num__, self.__fallback_num__)

  @instance.GET
  def _getInstance(self) -> Widget:
    return self.__owning_instance__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @pos.SET
  def _setPos(self, eventPoint: QEventPoint) -> None:
    rightHere = Point2D(QEventPoint.pressPosition(eventPoint))
    setattr(self.instance, self._posKey, rightHere)

  @pressed.SET
  def _setPressed(self, pressed: bool) -> None:
    setattr(self.instance, self._pressedKey, True if pressed else False)

  @when.SET
  def _setWhen(self, eventPoint: QEventPoint) -> None:
    rightNow = QEventPoint.pressTimestamp(eventPoint)
    setattr(self.instance, self._whenKey, rightNow)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: Widget, name: str) -> None:
    BaseObject.__set_name__(self, owner, name)
    raise NotImplementedError

  def __enter__(self, ) -> Self:
    return self

  def __exit__(self, _, exc: BaseException, __) -> None:
    if exc is not None:
      raise exc
    self.__owning_instance__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, buttonNum: MouseButtonNum, ) -> None:
    self.__button_num__ = buttonNum

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def reset(self, ) -> None:
    self.pos = Point2D(-1, -1)
    self.pressed = False
    self.when = None

  def _setContext(self, widget: BaseWidget, ) -> Self:
    self.__owning_instance__ = widget
    return self

  def _processPress(self, widget: BaseWidget, event_: QMouseEvent) -> None:
    """
    This method processes the event representing a mouse button press.

    It first validates that the event does refer to a press, otherwise it
    raises RuntimeError. Next it validates that the pressed button in the
    event matches the button enumeration of self. If not, it does not
    raise, but returns immediately.

    After successful validation, it retrieves the 'QEventPoint' from the
    event. This is assumed to be the first point found in the list
    returned from `QPointerEvent.points` method.

    Please note that the same applies as appropriate for the processing
    release and move events.
    """
    if QEvent.type(event_) not in PRESS_TYPES:
      raise RuntimeError
    if QMouseEvent.button(event_) != self.buttonNum.value:
      return
    eventPoint = QPointerEvent.points(event_)[0]
    p2D = Point2D(QEventPoint.pressPosition(eventPoint))
    rightNow = QEventPoint.pressTimestamp(eventPoint)
    setattr(widget, self._posKey, p2D)
    setattr(widget, self._pressedKey, True)
    setattr(widget, self._whenKey, rightNow)

  def _processRelease(self, widget: BaseWidget, event_: QMouseEvent) -> None:
    if QEvent.type(event_) not in RELEASE_TYPES:
      raise RuntimeError
    if QMouseEvent.button(event_) != self.buttonNum.value:
      return
    eventPoint = QPointerEvent.points(event_)[0]
    here = Point2D(QEventPoint.pressPosition(eventPoint))
    there = getattr(widget, self._posKey, )
    drift = here.dist(there)
    if drift > self.settings.pressRadius:
      return self.reset()
    if QEventPoint.timeHeld(eventPoint) > self.settings.pressTime:
      return self.reset()

  def _processMove(self, widget: BaseWidget, event_: QMouseEvent) -> None:
    if QEvent.type(event_) not in MOVE_TYPES:
      raise RuntimeError
    eventPoint = QPointerEvent.points(event_)[0]
    here = Point2D(QEventPoint.pressPosition(eventPoint))
    
    with self._setContext(widget) as self:
      drift = Point2D(QEventPoint.pressPosition(eventPoint)).dist(self.pos)
      duration = QEventPoint.timestamp(eventPoint) - self.when

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
