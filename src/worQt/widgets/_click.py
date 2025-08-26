"""
Click encapsulates a single mouse button click. Double and triple clicks
for example, would consist of 2 and 3 Click objects respectively.

Attributes:
  - mouseButton (MouseButtonNum): The mouse button that was clicked.
  - keyMod (KeyMod): The keyboard modifiers pressed during the click.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from worQt.nums import MouseButtonNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, TypeAlias, Type


class Click(BaseObject):
  """Click encapsulates a single mouse button click."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_button__ = MouseButtonNum.NULL
  __fallback_mod__ = KeyMod.NULL

  #  Private Variables
  __mouse_button__ = None
  __key_mod__ = None

  #  Public Variables
  mouseButton = Field()
  keyMod = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mouseButton.GET
  def _getMouseButton(self, **kwargs) -> MouseButtonNum:
    return maybe(self.__mouse_button__, self.__fallback_button__)

  @keyMod.GET
  def _getKeyMod(self, **kwargs) -> KeyMod:
    return maybe(self.__key_mod__, self.__fallback_mod__)
