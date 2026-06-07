"""
AbstractMenuBar subclasses 'QMenuBar' and 'MixinBase' and provides the base
for menu bars in the main window. A menu is to a menu bar as an action is to
a menu: menus are declared as 'MenuBox' fields that register their type on
the bar, and 'initUI' builds one menu per registered type, stores it back on
its box, adds it to the bar and initialises it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenuBar
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException, SubclassException

from ...mixin import MixinBase
from . import AbstractMenu

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias

  Menus: TypeAlias = dict[str, AbstractMenu]
  MaybeMenus: TypeAlias = Optional[Menus]
  MenuType: TypeAlias = type[AbstractMenu]
  MenuTypes: TypeAlias = dict[str, MenuType]
  MaybeMenuTypes: TypeAlias = Optional[MenuTypes]


class AbstractMenuBar(QMenuBar, MixinBase):
  """
  AbstractMenuBar subclasses 'QMenuBar' and 'MixinBase' and provides the
  base for menu bars in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __registered_menu_types__: MaybeMenuTypes = None

  #  Private Variables
  __menu_cache__: MaybeMenus = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _classCreateRegisteredMenuTypes(cls, ) -> None:
    regs = maybe(cls.__registered_menu_types__, dict())
    cls.__registered_menu_types__ = {**regs, }

  @classmethod
  def _classGetRegisteredMenuTypes(cls, **kwargs) -> MenuTypes:
    """
    This method returns the registered menu types for the menu bar.
    """
    if cls.__registered_menu_types__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      cls._classCreateRegisteredMenuTypes()
      return cls._classGetRegisteredMenuTypes(_recursion=True)
    if isinstance(cls.__registered_menu_types__, dict):
      for name, menuType in cls.__registered_menu_types__.items():
        if not isinstance(menuType, type):
          raise TypeException(f'menuType for {name}', menuType, type)
        if not issubclass(menuType, AbstractMenu):
          raise SubclassException(menuType, AbstractMenu)
      return cls.__registered_menu_types__
    name = '__registered_menu_types__'
    value = cls.__registered_menu_types__
    raise TypeException(name, value, dict)

  @classmethod
  def registerMenuType(cls, name: str, menuType: MenuType) -> None:
    """
    This method registers a menu type on the menu bar. The menu type must be
    a subclass of 'AbstractMenu'. Registered menu types are used by the bar
    to determine which menus to initialize and display.
    """
    existing = cls._classGetRegisteredMenuTypes()
    if name in existing:
      raise NotImplementedError("""lol we need a custom exception!""")
    if not isinstance(menuType, type):
      raise TypeException('menuType', menuType, type)
    if not issubclass(menuType, AbstractMenu):
      raise SubclassException(menuType, AbstractMenu)
    existing[name] = menuType
    cls.__registered_menu_types__ = existing

  def _createMenus(self, ) -> None:
    menus = dict()
    for name, menuType in self._classGetRegisteredMenuTypes().items():
      menu = menuType(self, )
      setattr(menu, '__field_name__', name)
      setattr(self, name, menu)
      menus[name] = menu
    self.__menu_cache__ = {**menus, }

  def getMenus(self, **kwargs) -> Menus:
    """
    This method returns the menus to be displayed in the bar. By default, it
    initializes and returns a menu for each registered menu type.
    """
    if self.__menu_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMenus()
      return self.getMenus(_recursion=True)
    if isinstance(self.__menu_cache__, dict):
      for name, menu in self.__menu_cache__.items():
        if not isinstance(menu, AbstractMenu):
          raise TypeException(f'menu for {name}', menu, AbstractMenu)
      return self.__menu_cache__
    name = '__menu_cache__'
    value = self.__menu_cache__
    raise TypeException(name, value, dict)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    This method initializes the bar visually and calls the 'initUI' method
    of the owned menus. It should be called by the general 'initUI' chain
    beginning from the main window class responsible for the menus.
    """
    for name, menu in self.getMenus().items():
      self.addMenu(menu)
      menu.initUI()
