"""
RunMainWindow subclasses 'WindowsAppTest' and tests the window chain
('AbstractWindow' -> 'BaseWindow' -> 'LayoutWindow' -> 'MainWindow') end to
end: showing the window runs the build-once lifecycle ('initMenus',
'initUI', 'initLogic'), installing the menu bar with its four menus and a
central widget.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.windows import MainWindow
from worQt.windows.menus import MainMenuBar

from . import WindowsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunMainWindow(WindowsAppTest):
  """Tests for the assembled main-window lifecycle."""

  def run_show_installs_menu_bar(self) -> None:
    """Showing the window builds the menu bar with its four menus. 'showLive'
    renders it as an exposed, painted window - the build-once lifecycle runs
    through the worQt 'show' override - and the harness disposes it on
    'tearDown', so no explicit close is needed."""
    window = MainWindow()
    window.resize(400, 300)
    self.showLive(window)
    self.assertTrue(window.isVisible())
    self.assertIsInstance(window.menuBar(), MainMenuBar)
    self.assertEqual(len(window.menuBar().actions()), 4)

  def run_show_sets_central_widget(self) -> None:
    """'initUI' installs a central widget carrying the base layout."""
    window = MainWindow()
    window.resize(400, 300)
    self.showLive(window)
    self.assertIsNotNone(window.centralWidget())
    self.assertIsNotNone(window.centralWidget().layout())
