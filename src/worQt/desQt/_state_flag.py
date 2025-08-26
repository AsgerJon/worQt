"""
StateFlag provides a descriptor for boolean attributes reflecting live
widget states.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from icecream import ic
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException
from worktoy.waitaminute import VariableNotNone

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Callable

  Widget: TypeAlias = Type[QWidget]

ic.configureOutput(includeContext=True, )


class StateFlag:
  """
  StateFlag provides a descriptor for boolean attributes reflecting live
  widget states.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __getter_key__ = None

  #  Public Variables
  getterKey = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @getterKey.GET
  def _getGetterKey(self) -> str:
    if self.__getter_key__ is None:
      raise MissingVariable(self, '__getter_key__', str)
    if isinstance(self.__getter_key__, str):
      return self.__getter_key__
    raise TypeException('__getter_key__', self.__getter_key__, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @getterKey.SET
  def _setGetterKey(self, value: str) -> None:
    if self.__getter_key__ is not None:
      raise VariableNotNone('__getter_key__', self.__getter_key__)
    self.__getter_key__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, widget: Any, cls: Widget) -> Any:
    if widget is None:
      return self
    getterFunc = getattr(cls, self.getterKey, )
    if callable(getterFunc):
      return getterFunc(widget)
    raise TypeException(self.getterKey, getterFunc, callable)

  def __call__(self, callMeMaybe: Callable) -> Callable:
    """Sets the getter key to the name of the callable."""
    if not callable(callMeMaybe):
      try:
        from typing import Callable
      except ImportError:
        Callable = object  # noqa
      raise TypeException('callMeMaybe', callMeMaybe, Callable)
    self.getterKey = callMeMaybe.__name__
    return callMeMaybe

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, ) -> None:
    for arg in args:
      if isinstance(arg, str):
        self.getterKey = arg
        break
      if callable(arg):
        self.getterKey = arg.__name__
        break
