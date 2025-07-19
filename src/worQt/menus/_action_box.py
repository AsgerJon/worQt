"""
ActionBox subclasses the 'AttriBox' from the 'worktoy' library, providing a
descriptor specifically for actions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias

  from . import AbstractMenu

  MenuClass: TypeAlias = Type[AbstractMenu]


class ActionBox(AttriBox):
  """
  ActionBox subclasses the 'AttriBox' from the 'worktoy' library, providing a
  descriptor specifically for actions.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, menuClass: MenuClass, name: str) -> None:
    """
    Set the name of the action in the menu class.

    Args:
      menuClass (MenuClass): The class where the action is defined.
      name (str): The name of the action.
    """
    super().__set_name__(menuClass, name)
    menuClass.boxAction(self, )
