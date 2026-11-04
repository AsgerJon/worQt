"""
RunMenus subclasses 'WindowsAppTest' and tests the declarative menu system
once it is built against a live 'QApplication': 'MainMenuBar' materialises
its four menus, 'initUI' assembles them onto the bar, a menu materialises
and lays out its actions, and an action carries its declared title, icon
and shortcut.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon

from worQt.windows.menus import MainMenuBar, AbstractMenu, AbstractAction
from worQt.windows.menus.file_menu import File, NewAction

from . import WindowsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunMenus(WindowsAppTest):
  """Tests for materialising the menu bar, menus and actions."""

  def run_bar_builds_four_menus(self) -> None:
    """The bar materialises one menu per registered type."""
    bar = MainMenuBar()
    menus = bar.getMenus()
    self.assertEqual(set(menus),
                     {'fileMenu', 'editMenu', 'viewMenu', 'helpMenu'})
    for menu in menus.values():
      self.assertIsInstance(menu, AbstractMenu)

  def run_bar_init_ui_assembles_menus(self) -> None:
    """'initUI' adds each menu onto the bar and titles the File menu."""
    bar = MainMenuBar()
    bar.initUI()
    self.assertEqual(len(bar.actions()), 4)
    self.assertEqual(bar.getMenus()['fileMenu'].title(), 'File')

  def run_file_menu_builds_actions(self) -> None:
    """The File menu materialises its five actions and lays them out."""
    fileMenu = File()
    actions = fileMenu.getActions()
    self.assertEqual(len(actions), 5)
    for action in actions.values():
      self.assertIsInstance(action, AbstractAction)
    fileMenu.initUI()
    self.assertEqual(fileMenu.title(), 'File')
    self.assertEqual(len(fileMenu.actions()), 5)

  def run_action_title_icon_shortcut(self) -> None:
    """An action exposes its declared title, icon and shortcut."""
    action = NewAction()
    self.assertEqual(action.actionTitle, 'New')
    self.assertEqual(action.actionShortcut.toString(), 'Ctrl+N')
    self.assertIsInstance(action.actionIcon, QIcon)

  def run_action_init_ui_applies(self) -> None:
    """'initUI' applies the title and shortcut onto the 'QAction'."""
    action = NewAction()
    action.initUI()
    self.assertEqual(action.text(), 'New')
    self.assertEqual(action.shortcut().toString(), 'Ctrl+N')
