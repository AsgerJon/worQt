"""
AbstractAction provides a base class for actions in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import typing

from PySide6.QtCore import QKeyCombination, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu

from moreworktoy.dispatch import Dispatcher

from ..app.desQt import App
from ..core import Parent, Shortcut
from ..nums import KeyNum, KeyMod

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Union, Any, TypeAlias, Type, Callable

  from ..menus import AbstractMenu

  MenuObject: TypeAlias = Optional[QMenu]
  MenuClass: TypeAlias = Union[Type[QMenu], Type[AbstractMenu]]


class AbstractAction(QAction):
  """
  AbstractAction provides a base class for actions in the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __field_name__: str = None
  __field_owner__: str = None

  #  Public Variables
  app = App()
  parent = Parent()

  #  Overload Functions
  setShortcut = Dispatcher(QAction.setShortcut)
  setIcon = Dispatcher(QAction.setIcon)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @setShortcut.overload(Shortcut)
  def setShortcut(self, shortcut: Shortcut) -> None:
    """Sets the shortcut for the action using a Shortcut instance. """
    QAction.setShortcut(self, shortcut.Q)

  @setShortcut.overload(str)
  def setShortcut(self, shortcut: str) -> None:
    """Sets the shortcut for the action using a string representation of
    the shortcut."""
    QAction.setShortcut(self, Shortcut(shortcut).Q)

  @setShortcut.overload(QKeyCombination)
  def setShortcut(self, shortcut: QKeyCombination) -> None:
    """Sets the shortcut for the action using a QKeyCombination."""
    QAction.setShortcut(self, Shortcut(shortcut).Q)

  @setShortcut.flex(Qt.Key, Qt.KeyboardModifier)
  def setShortcut(self, *args) -> None:
    """Sets the shortcut for the action using a Qt.Key and a
    Qt.KeyboardModifier."""
    key, modifier = None, None
    for arg in args:
      if isinstance(arg, Qt.Key) and key is None:
        key = arg
        continue
      if isinstance(arg, Qt.KeyboardModifier) and modifier is None:
        modifier = arg
        continue
    shortcut = Shortcut(key, modifier)
    QAction.setShortcut(self, shortcut.Q)

  @setShortcut.flex(KeyNum, KeyMod)
  def setShortcut(self, *args) -> None:
    """Sets the shortcut for the action using a KeyNum and a KeyMod."""
    key, modifier = None, None
    for arg in args:
      if isinstance(arg, KeyNum) and key is None:
        key = arg
        continue
      if isinstance(arg, KeyMod) and modifier is None:
        modifier = arg
        continue
    shortcut = Shortcut(key, modifier)
    QAction.setShortcut(self, shortcut.Q)

  @setShortcut.overload(KeyNum)
  def setShortcut(self, key: KeyNum) -> None:
    """Sets the shortcut for the action using a KeyNum."""
    QAction.setShortcut(self, Shortcut(key).Q)

  @setShortcut.overload(Qt.Key)
  def setShortcut(self, key: Qt.Key) -> None:
    """Sets the shortcut for the action using a Qt.Key."""
    QAction.setShortcut(self, Shortcut(key).Q)

  @setIcon.overload(str)
  def setIcon(self, icon: str) -> None:
    """Sets the icon for the action using a string representation of the
    icon."""
    icon = QIcon.fromTheme(icon)
    QAction.setIcon(self, icon)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    """
    Initializes the AbstractAction with the given arguments and keyword
    arguments. It sets the parent and initializes the QAction.
    """
    QAction.setShortcutVisibleInContextMenu(self, True)
    QAction.__init__(self, *args, **kwargs)
