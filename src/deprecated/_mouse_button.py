"""
MouseButton provides functionality for managing mouse buttons
independently allowing each mouse button to be tracked independently.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QMouseEvent, QPointerEvent
from worktoy.core import Object
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from ...desQt import Etc
from ...geometry import Point2D
from ...nums import MouseButtonNum

from ...settings import MouseClickSettings

from . import ReleaseTimer, PressTimer
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias, Any

  from .. import BaseWidget as Widget
  from . import MouseButton

  WidgetType: TypeAlias = Type[Widget]

  BtnType: TypeAlias = Type[MouseButton]


class _ProxyKey:
  """
  _ProxyKey provides a private key for the proxy variables of the
  MouseButton class.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __proxy_key__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, mouseButton: MouseButton, owner) -> Any:
    if mouseButton is None:
      return self
    pvtName = mouseButton.getPrivateName()
    out = '%s_%s' % (pvtName, self.__proxy_key__)
    while '__' in out[2:-2]:
      out = out.replace('__', '_')
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, key: str) -> None:
    self.__proxy_key__ = key


class MouseButton(BaseObject):
  """
  This public class provides the descriptor protocol for the '_Button'
  class.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()
  settings = MouseClickSettings()
  _releaseTimerKey = _ProxyKey('__release_timer__')
  _pressTimerKey = _ProxyKey('__press_timer__')
  _holdTimerKey = _ProxyKey('__hold_timer__')
  _clickCountKey = _ProxyKey('__click_count__')
  _holdCountKey = _ProxyKey('__hold_count__')
  _pressedKey = _ProxyKey('__button_pressed__')
  _pressPosKey = _ProxyKey('__press_pos__')
  _releasePosKey = _ProxyKey('__release_pos__')

  #  Fallback Variables
  __fallback_num__ = MouseButtonNum.NULL

  #  Private Variables
  __button_num__ = None
  __current_widget__ = None

  #  Public Variables
  buttonNum = Field()
  widget = Field()

  #  Virtual Variables

  #  Proxy Variables - Manages attributes on the owning widget
  releaseTimer = Field()  # Holding longer cancels click
  pressTimer = Field()  # Time limit to issue next click in combo
  holdTimer = Field()  # Hold until timeout to trigger press-hold
  clickCount = Field()  # Number of clicks in a row
  holdCount = Field()  # Number of holds in a row
  pressed = Field()  # True if the button is pressed on the current widget
  pressPos = Field()  # Position of the press event
  releasePos = Field()  # Position of the release event

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @widget.GET
  def _getWidget(self) -> Widget:
    return self.__current_widget__

  @buttonNum.GET
  def _getButtonNum(self) -> MouseButtonNum:
    return maybe(self.__button_num__, self.__fallback_num__)

  @clickCount.GET
  def _getClickCount(self, **kwargs) -> int:
    if hasattr(self.widget, self._clickCountKey):
      return getattr(self.widget, self._clickCountKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.widget, self._clickCountKey, 0)
    return self._getClickCount(_recursion=True, )

  @holdCount.GET
  def _getHoldCount(self, **kwargs) -> int:
    if hasattr(self.widget, self._holdCountKey):
      return getattr(self.widget, self._holdCountKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.widget, self._holdCountKey, 0)
    return self._getHoldCount(_recursion=True, )

  @releaseTimer.GET
  def _getReleaseTimer(self, **kwargs) -> ReleaseTimer:
    if hasattr(self.widget, self._releaseTimerKey):
      return getattr(self.widget, self._releaseTimerKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    key = self._releaseTimerKey
    timer = ReleaseTimer(self.widget, self.buttonNum, )
    setattr(self.widget, key, timer)
    return self._getReleaseTimer(_recursion=True, )

  @pressTimer.GET
  def _getPressTimer(self, **kwargs) -> PressTimer:
    if hasattr(self.widget, self._pressTimerKey):
      return getattr(self.widget, self._pressTimerKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    key = self._pressTimerKey
    timer = PressTimer(self.widget, self.buttonNum, )
    setattr(self.widget, key, timer)
    return self._getPressTimer(_recursion=True, )

  @holdTimer.GET
  def _getHoldTimer(self, **kwargs) -> QTimer:
    if hasattr(self.widget, self._holdTimerKey):
      return getattr(self.widget, self._holdTimerKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    key = self._holdTimerKey
    timer = QTimer(self.widget)
    timer.setSingleShot(True)
    timer.setInterval(self.settings.holdTime)
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    setattr(self.widget, key, timer)
    return self._getHoldTimer(_recursion=True, )

  @pressed.GET
  def _getPressed(self, **kwargs) -> bool:
    if hasattr(self.widget, self._pressedKey):
      return True if getattr(self.widget, self._pressedKey) else False
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.widget, self._pressedKey, False)  # Falls back to False
    return self._getPressed(_recursion=True, )

  @pressPos.GET
  def _getPressPos(self, **kwargs) -> Point2D:
    if hasattr(self.widget, self._pressPosKey):
      return getattr(self.widget, self._pressPosKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.widget, self._pressPosKey, Point2D(-1, -1))
    return self._getPressPos(_recursion=True, )

  @releasePos.GET
  def _getReleasePos(self, **kwargs) -> Point2D:
    if hasattr(self.widget, self._releasePosKey):
      return getattr(self.widget, self._releasePosKey)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.widget, self._releasePosKey, Point2D(-1, -1))
    return self._getReleasePos(_recursion=True, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def incrementClickCount(self, widget: Widget) -> None:
    with self.createContext(widget, type(widget)) as self:
      existing = self.clickCount
      setattr(self.instance, self._clickCountKey, existing + 1)

  @widget.SET
  def _setWidget(self, widget: Widget) -> None:
    self.__current_widget__ = widget

  @holdCount.SET
  def _setHoldCount(self, count: int) -> None:
    setattr(self.instance, self._holdCountKey, count)

  @pressed.SET
  def _setPressed(self, pressed: bool) -> None:
    if pressed == self.pressed:
      return
    setattr(self.instance, self._pressedKey, True if pressed else False)

  @pressPos.SET
  def _setPressPos(self, event_: QMouseEvent) -> None:
    point = QPointerEvent.points(event_)[0]
    rightHere = Point2D(point.pressPosition())
    setattr(self.instance, self._pressPosKey, rightHere)

  @releasePos.SET
  def _setReleasePos(self, event_: QMouseEvent) -> None:
    point = QPointerEvent.points(event_)[0]
    rightHere = Point2D(point.pressPosition())
    setattr(self.instance, self._releasePosKey, rightHere)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: WidgetType, name: str) -> None:
    Object.__set_name__(self, owner, name)
    owner.registerMoveCallback(self._updateMove)
    owner.registerPressCallback(self._updatePress)
    owner.registerReleaseCallback(self._updateRelease)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, mouseButtonNum: MouseButtonNum) -> None:
    self.__button_num__ = mouseButtonNum

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _updateMove(self, widget: Widget, event_: QMouseEvent) -> None:
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(self.pressPos, Point2D)
    drift = self.pressPos.dist(Point2D(event_))
    if self.pressed:
      if drift > self.settings.pressRadius:
        self.releaseTimer.stop()
        self.holdTimer.stop()
        self.resetClickCount(widget)
    else:
      if drift > self.settings.releaseRadius:
        self.releaseTimer.stop()
        self.holdTimer.stop()

  def _updatePress(self, widget: Widget, event_: QMouseEvent) -> None:
    if not event_.buttons() & self.buttonNum.value:
      return  #
    self.pressed = True
    self.incrementClickCount(widget)
    self.pressTimer.stop()
    self.releaseTimer.start()
    self.pressPos = event_

  def _updateRelease(self, widget: Widget, event_: QMouseEvent) -> None:
    if not event_.buttons() & self.buttonNum.value:
      return  #
    self.pressed = False
    self.resetHoldCount(widget)
    self.releaseTimer.stop()
    self.holdTimer.stop()
    self.pressTimer.start()

  def resetClickCount(self, widget: Widget) -> None:
    self.holdCount = self.clickCount
    setattr(self.instance, self._clickCountKey, 0)

  def resetHoldCount(self, widget: Widget, ) -> None:
    self.holdCount = 0

  def dispatchClicks(self) -> None:
    """This method dispatches the clicks to the owning widget."""
    raise NotImplementedError

  def dispatchHold(self) -> None:
    """This method dispatches the hold event to the owning widget."""
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
