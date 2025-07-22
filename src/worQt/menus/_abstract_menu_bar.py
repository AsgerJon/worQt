"""
AbstractMenuBar subclasses QMenuBar providing the menubar used by the main
window of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenuBar, QWidget
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

from ..desQt import App
from ..core import Parent

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Iterator, TypeAlias, Union, Any

  from PySide6.QtWidgets import QMenu
  from . import AbstractMenu

  Menu: TypeAlias = Union[QMenu, AbstractMenu]
  Menus: TypeAlias = Union[Menu, tuple[Menu, ...]]

  from . import MenuBox

  Boxes: TypeAlias = Union[MenuBox, tuple[MenuBox, ...]]


class AbstractMenuBar(QMenuBar):
  """
  AbstractMenuBar subclasses QMenuBar providing the menubar used by the main
  window of the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __owned_menus__ = None
  __boxed_menus__ = None

  #  Public Variables
  app = App()
  parent = Parent()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def getBoxedMenus(cls) -> Menus:
    """
    Returns a tuple of all menus in the menubar. This method is used to
    retrieve all menus that have been added to the menubar.
    """
    return maybe(cls.__boxed_menus__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def boxMenu(cls, box: MenuBox) -> None:
    """
    Boxes a menu in the menubar. This method is used to add a menu to the
    boxed menus list, allowing for easy retrieval later.
    """
    existing = maybe(cls.__boxed_menus__, [])
    cls.__boxed_menus__ = [*existing, box]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    for arg in args:
      if isinstance(arg, QWidget):
        QMenuBar.__init__(self, arg, )
        break
    else:
      QMenuBar.__init__(self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """
    Subclasses must implement this method. Menus should be defined as
    LabelBox descriptors in the class body. This method should then add
    each menu using `self.addMenu(self.menuName)`. This method runs before
    the 'initLogic' method defined below.
    """

  def initLogic(self) -> None:
    """
    Subclasses may implement this method to connect any particular menu
    to a specific logic. By default, menus are already added by the
    'initUi' defined above making them available externally.
    """

  def resolveKey(self, key: str) -> Menu:
    """
    Resolves a key to a menu in the menubar. This method searches through
    the menus and returns the first one that matches the key based on
    object name, text, or icon text.
    """
    for menu in self:
      if menu.objectName().lower() == key.lower():
        return menu
      if menu.title().lower() == key.lower():
        return menu
    else:
      infoSpec = """No menu with key '%s' found in '%s' object having 
      menus: <br><tab>%s"""
      clsName = type(self).__name__
      menuStr = '<br><tab>'.join([m.title() for m in self])
      info = infoSpec % (key, clsName, menuStr)
      raise KeyError(info)

  def resolveIndex(self, index: int) -> Menu:
    """
    Resolves an index to a menu in the menubar. This method returns the
    menu at the specified index, allowing for negative indexing.
    """
    if index < 0:
      return self.resolveIndex(len(self) + index)
    if index < len(self):
      return maybe(self.__owned_menus__, [])[index]
    infoSpec = """Index '%d' is out of range for '%s' object having '%d' 
    menus. """
    info = infoSpec % (index, type(self).__name__, len(self))
    raise IndexError(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addMenu(self, menu: QMenu, **kwargs) -> Self:
    """
    Adds a menu to the menubar. This method is overridden to ensure that
    the menus are stored in the `__owned_menus__` variable for later
    retrieval.
    """
    existing = maybe(self.__owned_menus__, [])
    menu = QMenuBar.addMenu(self, menu)
    self.__owned_menus__ = [*existing, menu]
    return menu

  def addMenus(self, *menus, **kwargs) -> None:
    """
    Adds multiple menus to the menubar. This method is overridden to ensure
    that the menus are stored in the `__owned_menus__` variable for later
    retrieval.
    """
    if len(menus) == 1 and isinstance(menus[0], (list, tuple)):
      return self.addMenus(*menus[0], **kwargs)
    for menu in menus:
      self.addMenu(menu, **kwargs)

  def show(self, ) -> None:
    """Runs the 'initUi' and 'initLogic' methods before the super call."""
    self.initUi()
    self.initLogic()
    QMenuBar.show(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[QMenu]:
    """
    Returns an iterator over the menus in the menubar. This allows for easy
    iteration over the menus.
    """
    yield from maybe(self.__owned_menus__, [])

  def __len__(self, ) -> int:
    """
    Returns the number of menus in the menubar. This allows for easy
    length checking of the menubar.
    """
    return len(maybe(self.__owned_menus__, []))

  def __getitem__(self, identifier: Any) -> Menus:
    """
    Returns a menu based on the provided identifier. The identifier can be
    a key (string) or an index (integer). If the identifier is a string,
    it resolves to a menu by key. If it is an integer, it resolves to a
    menu by index.
    """
    if isinstance(identifier, str):
      return self.resolveKey(identifier)
    elif isinstance(identifier, int):
      return self.resolveIndex(identifier)
    elif isinstance(identifier, slice):
      indices = range(*identifier.indices(len(self)))
      return (*[self.resolveIndex(i) for i in indices],)
    raise TypeException('identifier', identifier, str, int)
