"""
CursorPress subclasses AbstractEvent and encapsulates the cursor press
event in the custom event system. Instances respect the getMouseArea
method of the owning widget.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.waitaminute import VariableNotNone

from ..nums import MouseButtonNum

from . import CursorEvent

if TYPE_CHECKING:  # pragma: no cover
  pass


class CursorPress(CursorEvent):
  """
  CursorPress subclasses AbstractEvent and encapsulates the cursor press
  event in the custom event system. Instances respect the getMouseArea
  method of the owning widget.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __mouse_button__ = None

  #  Public Variables
  mouseButton = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mouseButton.GET
  def _getMouseButton(self, ) -> MouseButtonNum:
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(self.__mouse_button__, MouseButtonNum)
    return self.__mouse_button__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mouseButton.SET
  def _setMouseButton(self, value: MouseButtonNum) -> None:
    if self.__mouse_button__ is not None:
      raise VariableNotNone('mouseButton', self.__mouse_button__)
    self.__mouse_button__ = value
