"""
MenuBox subclasses the 'AttriBox' from the 'worktoy' library, providing a
descriptor specifically for menus.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias

  from . import AbstractMenuBar

  BarClass: TypeAlias = Type[AbstractMenuBar]


class MenuBox(AttriBox):
  """
  MenuBox subclasses the 'AttriBox' from the 'worktoy' library, providing a
  descriptor specifically for menus.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, barClass: BarClass, name: str) -> None:
    """
    Set the name of the action in the menu class.

    Args:
      barClass (MenuClass): The class where the action is defined.
      name (str): The name of the action.
    """
    super().__set_name__(barClass, name)
    barClass.boxMenu(self, )
