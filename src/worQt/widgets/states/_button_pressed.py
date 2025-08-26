"""
ButtonPressed provides a flag descriptor indicating whether the
cursor presently presses a mouse button over the owning widget. Each mouse
button should have its own instance of this descriptor.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core import Object
from worktoy.desc import Field

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias
  from ...nums import MouseButtonNum


class ButtonPressed(Object):
  """
  ButtonPressed provides a flag descriptor indicating whether the
  cursor presently presses a mouse button over the owning widget. Each mouse
  button should have its own instance of this descriptor.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __button_num__ = None

  #  Public Variables
  buttonNum = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @buttonNum.GET
  def _getButtonNum(self) -> MouseButtonNum:
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(self.__button_num__, MouseButtonNum)
    return self.__button_num__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, btn: MouseButtonNum) -> None:
    self.__button_num__ = btn

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> bool:
    """
    Returns the current state of the button pressed.
    """
    pvtName = self.getPrivateName()
    if hasattr(self.instance, pvtName):
      return getattr(self.instance, pvtName)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, pvtName, False)
    return self.__instance_get__(*args, _recursion=True, )

  def __instance_set__(self, value: bool, *args, **kwargs) -> None:
    pvtName = self.getPrivateName()
    if hasattr(self.instance, pvtName):
      if value == getattr(self.instance, pvtName):
        return
    return setattr(self.instance, pvtName, value)
