"""
MouseButtonState encapsulates the state of a mouse button. The event
system treats mouse buttons entirely independently, but aLso identically.
Thus, one class is sufficient to represent as many mouse buttons as needed.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from worktoy.desc import Field, Alias
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from worQt.geometry import Point2D
from worQt.nums import MouseButtonNum, MouseButtonStateNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


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
  __num_key__ = 'button_num'
  __state_key__ = 'button_state'

  #  Fallback Variables
  __fallback_num__ = MouseButtonNum.NULL
  __fallback_state__ = MouseButtonStateNum.RELEASED

  #  Private Variables
  __button_num__ = None  # Declare in __init__
  __button_state__ = None

  #  Public Variables
  numKey = Field()
  stateKey = Field()
  buttonNum = Field()
  buttonState = Field()

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

  @buttonNum.GET  # Shared across all instances
  def _getButtonNum(self, **kwargs, ) -> MouseButtonNum:
    key = self._getNumKey()
    if hasattr(self.instance, key):
      return getattr(self.instance, key)
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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
