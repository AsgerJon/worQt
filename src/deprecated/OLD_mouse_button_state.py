"""
MouseButtonState encapsulates the state of a mouse button. The event
system treats mouse buttons entirely independently, but aLso identically.
Thus, one class is sufficient to represent as many mouse buttons as needed.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QMouseEvent
from worktoy.desc import Field, Alias
from worktoy.mcls import BaseObject

from ...geometry import Point2D
from ...nums import MouseButtonNum, MouseButtonStateNum

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from . import MouseClick


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
  # --  Keys to private variables on owning widget --
  __num_key__ = 'button_num'
  __state_key__ = 'button_state'
  __press_position_key__ = 'press_position_key'
  __release_position_key__ = 'release_position_key'
  __hold_position_key__ = 'hold_position_key'
  __press_dur_key__ = 'press_dur_key'
  __release_dur_key__ = 'release_dur_key'
  # --  Values read from settings --

  #  Fallback Variables
  __fallback_num__ = MouseButtonNum.NULL
  __fallback_state__ = MouseButtonStateNum.RELEASED

  #  Private Variables
  __button_num__ = None  # Declare in __init__
  __button_state__ = None

  #  Public Variables
  # -- Keys to private variables on owning widget --
  numKey = Field()
  stateKey = Field()
  pressPositionKey = Field()
  releasePositionKey = Field()
  holdPositionKey = Field()
  pressDurKey = Field()
  releaseDurKey = Field()
  #  -- Attributes retrieved from owning widget --
  buttonNum = Field()
  buttonState = Field()
  pressPosition = Field()
  releasePosition = Field()
  holdPosition = Field()
  pressDur = Field()
  releaseDur = Field()

  #  Virtual Variables
  widget = Alias('instance')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @numKey.GET
  def _getNumKey(self) -> str:
    return """%s%s__""" % (self.getPrivateName()[:-1], self.__num_key__)

  @stateKey.GET
  def _getStateKey(self) -> str:
    return """%s%s__""" % (self.getPrivateName()[:-1], self.__state_key__)

  @pressPositionKey.GET
  def _getPressPositionKey(self) -> str:
    spec, key = '%s%s__', self.__press_position_key__
    return spec % (self.getPrivateName()[:-1], key)

  @releasePositionKey.GET
  def _getReleasePositionKey(self) -> str:
    spec, key = '%s%s__', self.__release_position_key__
    return spec % (self.getPrivateName()[:-1], key)

  @holdPositionKey.GET
  def _getHoldPositionKey(self) -> str:
    spec, key = '%s%s__', self.__hold_position_key__
    return spec % (self.getPrivateName()[:-1], key)

  @pressDurKey.GET
  def _getPressDurKey(self) -> str:
    spec, key = '%s%s__', self.__press_dur_key__
    return spec % (self.getPrivateName()[:-1], key)

  @releaseDurKey.GET
  def _getReleaseDurKey(self) -> str:
    spec, key = '%s%s__', self.__release_dur_key__
    return spec % (self.getPrivateName()[:-1], key)

  @buttonNum.GET  # Shared across all instances
  def _getButtonNum(self, **kwargs, ) -> MouseButtonNum:
    key = self._getNumKey()
    if hasattr(self.owner, key):
      return getattr(self.owner, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, self.__fallback_num__)
    return self._getButtonNum(_recursion=True)

  @buttonState.GET
  def _getButtonState(self, **kwargs, ) -> MouseButtonStateNum:
    key = self._getStateKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, self.__fallback_state__)
    return self._getButtonState(_recursion=True)

  @pressPosition.GET
  def _getPressPosition(self, **kwargs, ) -> tuple[float, float]:
    key = self._getPressPositionKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, (0.0, 0.0))  # Default position
    return self._getPressPosition(_recursion=True)

  @releasePosition.GET
  def _getReleasePosition(self, **kwargs, ) -> tuple[float, float]:
    key = self._getReleasePositionKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, (0.0, 0.0))  # Default position
    return self._getReleasePosition(_recursion=True)

  @holdPosition.GET
  def _getHoldPosition(self, **kwargs, ) -> tuple[float, float]:
    key = self._getHoldPositionKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, (0.0, 0.0))  # Default position
    return self._getHoldPosition(_recursion=True)

  @pressDur.GET
  def _getPressDur(self, **kwargs, ) -> int:
    key = self._getPressDurKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, 0)  # Default time
    return self._getPressDur(_recursion=True)

  @releaseDur.GET
  def _getReleaseDur(self, **kwargs, ) -> int:
    key = self._getReleaseDurKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, key, 0)
    return self._getReleaseDur(_recursion=True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @buttonNum.SET
  def _setButtonNum(self, value: MouseButtonNum, **kwargs) -> None:
    setattr(self.instance, self.numKey, value)

  @buttonState.SET
  def _setButtonState(self, value: MouseButtonStateNum, **kwargs) -> None:
    setattr(self.instance, self.stateKey, value)

  @pressPosition.SET
  def _setPressPosition(self, *args) -> None:
    setattr(self.instance, self.pressPositionKey, Point2D(*args))

  @releasePosition.SET
  def _setReleasePosition(self, *args) -> None:
    setattr(self.instance, self.releasePositionKey, Point2D(*args))

  @holdPosition.SET
  def _setHoldPosition(self, *args) -> None:
    setattr(self.instance, self.holdPositionKey, Point2D(*args))

  @pressDur.SET
  def _setPressDur(self, value: int, **kwargs) -> None:
    setattr(self.instance, self.pressDurKey, value)

  @releaseDur.SET
  def _setReleaseDur(self, value: int, **kwargs) -> None:
    setattr(self.instance, self.releaseDurKey, value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, button: MouseButtonNum) -> None:
    self.__button_num__ = button

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def reset(self, ) -> None:
    """
    Resets the state back to 'None' for all private instance variables.
    """
    
  def update(self, event_: QMouseEvent) -> None:
    """
    Updates self from the given QMouseEvent.

    This method first ensures that the button relates to a mouse button,
    meaning that the event type is one of press, double click or release.
    Next, it compares the button in the event with the button enumeration
    managed by this instance. Finally, if both match, forwards to the
    relevant private methods.
    """
    raise NotImplementedError

  def sendClick(self, ) -> MouseClick:
    """
    Sends a click event to the owning widget. This method is used to
    simulate a click event based on the current state of the mouse button.
    It returns a 'MouseClick' object that encapsulates the click event.
    """
    raise NotImplementedError

  def _updatePress(self, event_: QMouseEvent) -> None:
    """
    Handles the update of a press or double click event. Please note that
    this method performs that caller has performed necessary validation
    checks. 
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
