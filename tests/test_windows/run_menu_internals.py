"""
RunMenuInternals covers the menu/action accessor branches that build
'QObject's: the default and guarded icon/title/shortcut accessors on
'AbstractAction' and 'AbstractMenu', the box-owned default-title path, the
'MenuSeparator', and the 'getActions'/'getMenus' guards.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon, QKeySequence
from worktoy.waitaminute import TypeException

from worQt.windows.menus import (AbstractMenu, AbstractMenuBar,
                                AbstractAction, MenuSeparator)
from worQt.windows.menus.file_menu import NewAction, File

from . import WindowsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunMenuInternals(WindowsAppTest):
  """Tests for the menu/action accessor branches."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT ACTION  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_action_defaults(self) -> None:
    """A bare action yields an empty icon and shortcut; a configured one
    resolves a themed icon."""
    bare = AbstractAction()
    self.assertIsInstance(bare.actionIcon, QIcon)
    self.assertIsInstance(bare.actionShortcut, QKeySequence)
    self.assertIsInstance(NewAction().actionIcon, QIcon)

  def run_action_icon_guards(self) -> None:
    """The icon accessor's recursion and type guards fire."""
    action = AbstractAction()
    with self.assertRaises(RecursionError):
      action._getActionIcon(_recursion=True)
    action.__icon_cache__ = 'bad'
    with self.assertRaises(TypeException):
      _ = action.actionIcon

  def run_action_title_guards(self) -> None:
    """The title accessor's recursion and type guards fire."""
    action = AbstractAction()
    with self.assertRaises(RecursionError):
      action._getActionTitle(_recursion=True)
    action.__title_cache__ = 123
    with self.assertRaises(TypeException):
      _ = action.actionTitle

  def run_action_shortcut_guards(self) -> None:
    """The shortcut accessor's recursion and type guards fire."""
    action = AbstractAction()
    with self.assertRaises(RecursionError):
      action._getActionShortcut(_recursion=True)
    action.__short_cut__ = 'bad'
    with self.assertRaises(TypeException):
      _ = action.actionShortcut

  def run_action_default_title_from_field(self) -> None:
    """An action with no declared title falls back to its field name."""
    action = AbstractAction()
    action.__field_owner__ = File
    action.__field_name__ = 'myAction'
    action.__field_box__ = object()
    self.assertEqual(action.actionTitle, 'myAction')

  def run_menu_separator(self) -> None:
    """A 'MenuSeparator' constructs as a separator action."""
    self.assertTrue(MenuSeparator().isSeparator())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT MENU  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_menu_icon_from_reference(self) -> None:
    """A menu declaring an icon reference resolves a themed icon (the
    non-default branch of the icon builder)."""
    menu = AbstractMenu()
    menu.__icon_reference__ = 'help-about'
    self.assertIsInstance(menu.menuIcon, QIcon)

  def run_menu_icon_guards(self) -> None:
    """The menu icon accessor's default, recursion and type guards fire."""
    self.assertIsInstance(AbstractMenu().menuIcon, QIcon)
    menu = AbstractMenu()
    with self.assertRaises(RecursionError):
      menu._getMenuIcon(_recursion=True)
    menu.__icon_cache__ = 'bad'
    with self.assertRaises(TypeException):
      _ = menu.menuIcon

  def run_menu_title_guards(self) -> None:
    """The menu title accessor's recursion and type guards fire."""
    menu = AbstractMenu()
    with self.assertRaises(RecursionError):
      menu._getMenuTitle(_recursion=True)
    menu.__title_cache__ = 123
    with self.assertRaises(TypeException):
      _ = menu.menuTitle

  def run_menu_default_title_from_field(self) -> None:
    """A menu with no declared title falls back to its field name."""
    menu = AbstractMenu()
    menu.__field_owner__ = File
    menu.__field_name__ = 'myMenu'
    menu.__field_box__ = object()
    self.assertEqual(menu.menuTitle, 'myMenu')

  def run_get_actions_guards(self) -> None:
    """The action cache's recursion and type guards fire."""
    menu = AbstractMenu()
    with self.assertRaises(RecursionError):
      menu.getActions(_recursion=True)
    menu.__action_cache__ = {'x': 123}
    with self.assertRaises(TypeException):
      menu.getActions()
    menu.__action_cache__ = 'bad'
    with self.assertRaises(TypeException):
      menu.getActions()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT MENU BAR  # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_get_menus_guards(self) -> None:
    """The menu cache's recursion and type guards fire."""
    bar = AbstractMenuBar()
    with self.assertRaises(RecursionError):
      bar.getMenus(_recursion=True)
    bar.__menu_cache__ = {'x': 123}
    with self.assertRaises(TypeException):
      bar.getMenus()
    bar.__menu_cache__ = 'bad'
    with self.assertRaises(TypeException):
      bar.getMenus()
