"""WAction subclasses QAction providing a streamlined interface used by
the menu system.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QAction, QShortcut, QKeySequence, QIcon
from PySide6.QtWidgets import QWidget
from worktoy.attr import AttriBox
from worktoy.mcls import BaseObject
from worktoy.static import overload

from worQt.resources import IconRes, ShortcutRes

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class _Deps:
  """Dependencies for the module."""
  __imported_modules = [
      QAction,
      QIcon,
      QKeySequence,
      QShortcut,
      BaseObject,
      overload,
  ]


class _Parsed(BaseObject):
  """Parsed class for the module."""

  __action_name__ = None
  __action_parent__ = None

  @overload(str, QWidget)
  def __init__(self, name: str, parent: QWidget) -> None:
    """Initialize the action with a name and a parent widget."""
    self.__action_name__ = name
    self.__action_parent__ = parent

  @overload(str, )
  def __init__(self, name: str) -> None:
    """Initialize the action with a name."""
    self.__action_name__ = name
    self.__action_parent__ = None

  @overload(QAction, QWidget)
  def __init__(self, action: QAction, parent: QWidget) -> None:
    """Initialize the action with an existing QAction and a parent widget."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(action.text(), parent)

  @overload(QAction, )
  def __init__(self, action: QAction) -> None:
    """Initialize the action with an existing QAction."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(action.text(), QAction.parent(action))


class WAction(QAction):
  """WAction subclasses QAction providing a streamlined interface used by
  the menu system.
  """

  name = AttriBox[str]()
  icon = AttriBox[QIcon]()
  shortcut = AttriBox[QKeySequence]()

  def __init__(self, *args) -> None:
    """Initialize the AbstractAction with a name."""
    _parsed = _Parsed(*args)
    name = _parsed.__action_name__
    parent = _parsed.__action_parent__
    if parent is None:
      QAction.__init__(self, name)
    else:
      QAction.__init__(self, name, parent)
    self.icon = IconRes(name).value
    self.shortcut = ShortcutRes(name).value

  def initUi(self, ) -> None:
    """Initialize the UI."""
    if self.icon:
      self.setIcon(self.icon)
    if self.shortcut:
      self.setShortcut(self.shortcut)
