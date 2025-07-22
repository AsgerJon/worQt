"""
ActionBox subclasses the 'AttriBox' from the 'worktoy' library, providing a
descriptor specifically for actions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QAction
from icecream import ic
from worktoy.desc import AttriBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias

  from . import AbstractMenu

  MenuClass: TypeAlias = Type[AbstractMenu]

ic.configureOutput(includeContext=True, )


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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _formatName(self, ) -> str:
    """
    Formats the name passed to __set_name__ into a public name.
    """
    name = []
    for i, char in enumerate(self.__field_name__):
      if i:
        if char.isupper():
          name.append(' ')
          name.append(char.upper())
        else:
          name.append(char)
      else:
        name.append(char.upper())
    return ''.join(name).replace('_', ' ').replace('Action', ' ').strip()

  def __instance_get__(self, *args, **kwargs) -> Any:
    out = super().__instance_get__(*args, **kwargs)
    QAction.setText(out, self._formatName())
    QAction.setObjectName(out, self.__field_name__)
    return out
