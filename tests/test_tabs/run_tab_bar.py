"""
RunTabBar covers 'TabBar': adding and removing tabs, their titles and
marks, which tab is current, and what a click on a tab or its cross
asks for.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.waitaminute import TypeException

from worQt.qtest import WidgetTest
from worQt.tabs import TabBar


class RunTabBar(WidgetTest):
  """Tests for 'TabBar'."""

  def _bar(self, *titles: str) -> TabBar:
    bar = TabBar()
    for title in titles:
      bar.addTab(title)
    return bar

  def _liveBar(self, *titles: str) -> TabBar:
    bar = self._bar(*titles)
    bar.resize(600, bar.sizeHint().height())
    self.showLive(bar)
    bar.repaint()
    return bar

  def run_tabs_and_titles(self) -> None:
    """Tabs are added at the end, each with a title and no mark."""
    bar = self._bar('one', 'two')
    self.assertEqual(bar.count, 2)
    self.assertEqual(bar.addTab('three'), 2)
    self.assertEqual(bar.titleAt(2), 'three')
    bar.setTitle(0, 'first')
    bar.setModified(1, True)
    self.assertEqual(bar.titleAt(0), 'first')
    self.assertTrue(bar.isModified(1))
    self.assertFalse(bar.isModified(0))

  def run_current_index(self) -> None:
    """The first tab is current until another is made so; with no tabs
    the current index is -1."""
    self.assertEqual(TabBar().currentIndex, -1)
    bar = self._bar('one', 'two', 'three')
    self.assertEqual(bar.currentIndex, 0)
    bar.currentIndex = 2
    self.assertEqual(bar.currentIndex, 2)
    with self.assertRaises(TypeException):
      bar.currentIndex = 'two'

  def run_removing_keeps_the_current_tab(self) -> None:
    """Removing a tab keeps the current one current; removing the current
    one gives its place to the next, or the last if it was the last."""
    bar = self._bar('one', 'two', 'three')
    bar.currentIndex = 2
    bar.removeTab(0)
    self.assertEqual(bar.titleAt(bar.currentIndex), 'three')
    bar.removeTab(1)
    self.assertEqual(bar.titleAt(bar.currentIndex), 'two')
    bar = self._bar('one', 'two', 'three')
    bar.currentIndex = 1
    bar.removeTab(1)
    self.assertEqual(bar.titleAt(bar.currentIndex), 'three')

  def run_click_selects(self) -> None:
    """A click on a tab makes it current and says so."""
    bar = self._liveBar('one', 'two')
    spy = self.spy(bar.currentChanged)
    self.click(bar, bar.tabRect(1).center().toPoint())
    self.assertEqual(bar.currentIndex, 1)
    self.assertEqual(spy.args, (1,))

  def run_cross_and_middle_click_ask_to_close(self) -> None:
    """A click on a tab's cross, or a middle click on it, asks to close
    it, and leaves the current tab alone."""
    bar = self._liveBar('one', 'two')
    spy = self.spy(bar.closeRequested)
    cross = bar.closeRect(bar.tabRect(1)).center().toPoint()
    self.click(bar, cross)
    self.assertEqual(spy.args, (1,))
    middle = Qt.MouseButton.MiddleButton
    self.click(bar, bar.tabRect(0).center().toPoint(), middle)
    self.assertEqual(spy.args, (0,))
    self.assertEqual(bar.currentIndex, 0)

  def run_takes_no_focus(self) -> None:
    """Clicking a tab is for choosing: the bar never takes the focus."""
    self.assertEqual(TabBar().focusPolicy(), Qt.FocusPolicy.NoFocus)

  def run_paints(self) -> None:
    """The bar paints its tabs, dots and crosses."""
    bar = self._liveBar('one', 'two', 'a rather long title indeed')
    bar.setModified(1, True)
    self.assertFalse(bar.grab().isNull())
