"""
ActionBox subclasses 'AttriBox' from 'worktoy.desc' and registers boxed
actions on the owning menu.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from worktoy.desc import AttriBox
from worktoy.waitaminute import TypeException, SubclassException

T = TypeVar('T')

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeAlias
  from . import AbstractAction as Action
  from . import AbstractMenu as Menu

  ActionType: TypeAlias = type[Action]
  MenuType: TypeAlias = type[Menu]


class ActionBox(AttriBox[T]):
  """
  ActionBox subclasses 'AttriBox' from 'worktoy.desc' and registers boxed
  actions on the owning menu.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __class_getitem__(cls, actionType: ActionType) -> Self:
    if not isinstance(actionType, type):
      raise TypeException('actionType', actionType, type)
    if actionType.__name__ != 'MenuSeparator':
      if not issubclass(actionType, QAction):
        raise SubclassException(actionType, QAction)
    return super().__class_getitem__(actionType)

  def __set_name__(self, menuType: MenuType, name: str, **kwargs) -> None:
    if not isinstance(menuType, type):
      raise TypeException('menuType', menuType, type)
    if not issubclass(menuType, QMenu):
      raise SubclassException(menuType, QMenu)
    AttriBox.__set_name__(self, menuType, name)
    menuType.registerActionType(name, self.fieldType)
