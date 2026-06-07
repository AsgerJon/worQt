"""
MenuBox subclasses 'AttriBox' from 'worktoy.desc' and registers boxed menus
on the owning menu bar. It is to a menu bar what 'ActionBox' is to a menu.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from PySide6.QtWidgets import QMenu, QMenuBar
from worktoy.desc import AttriBox
from worktoy.waitaminute import TypeException, SubclassException

T = TypeVar('T')

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeAlias
  from . import AbstractMenu as Menu
  from . import AbstractMenuBar as MenuBar

  MenuType: TypeAlias = type[Menu]
  MenuBarType: TypeAlias = type[MenuBar]


class MenuBox(AttriBox[T]):
  """
  MenuBox subclasses 'AttriBox' from 'worktoy.desc' and registers boxed
  menus on the owning menu bar.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __class_getitem__(cls, menuType: MenuType) -> Self:
    if not isinstance(menuType, type):
      raise TypeException('menuType', menuType, type)
    if not issubclass(menuType, QMenu):
      raise SubclassException(menuType, QMenu)
    return super().__class_getitem__(menuType)

  def __set_name__(self, menuBarType: MenuBarType, name: str, **kw) -> None:
    if not isinstance(menuBarType, type):
      raise TypeException('menuBarType', menuBarType, type)
    if not issubclass(menuBarType, QMenuBar):
      raise SubclassException(menuBarType, QMenuBar)
    AttriBox.__set_name__(self, menuBarType, name)
    menuBarType.registerMenuType(name, self.fieldType)
