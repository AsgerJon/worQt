"""AbstractMenu subclasses QMenu and adds abstract methods for it. These
include:
- getMenuName: str -> returns the name of the menu
- initUI: None -> initializes the UI

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget
from worktoy.attr import AttriBox
from worktoy.text import monoSpace, typeMsg

from worQt.window.menus import WAction

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Self


class AbstractMenu(QMenu):
  """AbstractMenu subclasses QMenu and adds abstract methods for it. These
  include:
  - getMenuName: str -> returns the name of the menu
  - initUI: None -> initializes the UI
  """

  __iter_contents__ = None

  name = AttriBox[str]()

  @abstractmethod
  def initUi(self, ) -> None:
    """Initialize the UI. Subclasses must implement this method to set up
    the menu and actions. """

  def __iter__(self, ) -> Self:
    """Iterate over the contents of the menu."""
    self.__iter_contents__ = [*QMenu.actions(self), ]
    return self

  def __next__(self, ) -> Any:
    """Return the next item in the menu."""
    try:
      return self.__iter_contents__.pop(0)
    except IndexError:
      raise StopIteration
    finally:
      if not self.__iter_contents__:
        self.__iter_contents__ = None

  def __len__(self, ) -> int:
    """Return the number of items in the menu."""
    return len(QMenu.actions(self))

  def addAction(self, *args, ) -> None:
    """Add an action to the menu."""
    for arg in args:
      if isinstance(arg, QAction):
        return self.addAction(WAction(arg), self)
      if isinstance(arg, str):
        return self.addAction(WAction(arg), self)
      if isinstance(arg, WAction):
        arg.initUi()
        return QMenu.addAction(self, arg, )
      raise TypeError(typeMsg('arg', arg, WAction))

  def addActions(self, names: list) -> None:
    """Add actions to the menu."""
    for name in names:
      self.addAction(name)

  def __init__(self, *args) -> None:
    _title, _parent = None, None
    for arg in args:
      if isinstance(arg, str) and _title is None:
        _title = arg
      elif isinstance(arg, QWidget) and _parent is None:
        _parent = arg
      if _title and _parent:
        break
    else:
      if _title is None:
        raise ValueError(monoSpace('No title or parent provided!'))
    if _parent is None:
      QMenu.__init__(self, _title)
    else:
      QMenu.__init__(self, _title, _parent)
