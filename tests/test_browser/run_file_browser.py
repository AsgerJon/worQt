"""
RunFileBrowser covers 'FileBrowser': its rows, selecting and opening by
the keys and the mouse, revealing a path, marking the open file,
scrolling and painting.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPoint
from worktoy.waitaminute import TypeException

from worQt.browser import FileBrowser

from . import BrowserWidgetTest


class RunFileBrowser(BrowserWidgetTest):
  """Tests for 'FileBrowser'."""

  def _browser(self, live: bool = False) -> FileBrowser:
    browser = FileBrowser()
    browser.suffixes = ('.ezw',)
    browser.rootPath = self.path()
    if live:
      browser.resize(240, 400)
      self.showLive(browser)
      browser.repaint()
    return browser

  def _names(self, browser: FileBrowser) -> list[str]:
    return [node.name for node in browser.rows]

  def _rowPoint(self, browser: FileBrowser, row: int, x: int) -> QPoint:
    """A point in row 'row', counted from 0 below the header, 'x' pixels
    right of the left of the rows."""
    view = browser.paintView
    y = view.top + browser.rowHeight * (row + 1) + browser.rowHeight // 2
    return QPoint(view.left + x, int(y))

  def run_root_and_rows(self) -> None:
    """The browser shows its root folder's name and the files and
    folders in it, of its suffixes only."""
    browser = self._browser()
    self.assertEqual(browser.rootName, browser.rootPath.split('/')[-1])
    self.assertEqual(self._names(browser), ['notes', 'alpha.ezw',
                                            'Beta.ezw'])
    with self.assertRaises(TypeException):
      browser.suffixes = '.ezw'

  def run_keys_move_and_open(self) -> None:
    """'j' and 'k' move the selection, 'l' opens a folder and steps
    into it, 'h' steps out and closes it."""
    browser = self._browser()
    self.typeText(browser, 'j')
    self.assertEqual(browser.selectedPath, self.path('notes'))
    self.typeText(browser, 'l')
    self.assertIn('inner.ezw', self._names(browser))
    self.typeText(browser, 'l')
    self.assertEqual(browser.selectedPath, self.path('notes', 'old'))
    self.typeText(browser, 'hh')
    self.assertEqual(self._names(browser), ['notes', 'alpha.ezw',
                                            'Beta.ezw'])
    self.typeText(browser, 'jjjjk')
    self.assertEqual(browser.selectedPath, self.path('alpha.ezw'))

  def run_opening_a_file(self) -> None:
    """Opening a file announces it through 'fileActivated'; opening a
    folder opens or closes it instead."""
    browser = self._browser()
    spy = self.spy(browser.fileActivated)
    self.typeText(browser, 'jo')
    self.assertEqual(spy.count, 0)
    self.assertIn('inner.ezw', self._names(browser))
    browser.selectedPath = self.path('alpha.ezw')
    self.typeText(browser, 'o')
    self.assertEqual(spy.count, 1)
    self.assertEqual(spy.args, (self.path('alpha.ezw'),))

  def run_clicks(self) -> None:
    """A click selects a row; a click on a folder's arrow opens it; a
    double click on a file opens it."""
    browser = self._browser(True)
    spy = self.spy(browser.fileActivated)
    self.click(browser, self._rowPoint(browser, 1, 40))
    self.assertEqual(browser.selectedPath, self.path('alpha.ezw'))
    self.click(browser, self._rowPoint(browser, 0, 4))
    self.assertIn('inner.ezw', self._names(browser))
    self.doubleClick(browser, self._rowPoint(browser, 3, 40))
    self.assertEqual(spy.args, (self.path('alpha.ezw'),))

  def run_reveal_and_mark(self) -> None:
    """Revealing a path opens the folders down to it and selects it;
    the marked path is the file open."""
    browser = self._browser()
    deep = self.path('notes', 'old', 'deep.ezw')
    self.assertTrue(browser.reveal(deep))
    self.assertEqual(browser.selectedPath, deep)
    self.assertIn('deep.ezw', self._names(browser))
    self.assertFalse(browser.reveal(self.path('nowhere.ezw')))
    browser.markedPath = deep
    self.assertEqual(browser.markedPath, deep)

  def run_refresh(self) -> None:
    """A folder is listed once, when first shown; refreshing shows a
    file made since."""
    browser = self._browser()
    self.assertNotIn('gamma.ezw', self._names(browser))
    with open(self.path('gamma.ezw'), 'w') as file:
      file.write('Gamma.\n')
    self.assertNotIn('gamma.ezw', self._names(browser))
    browser.refresh()
    self.assertIn('gamma.ezw', self._names(browser))

  def run_slim(self) -> None:
    """The browser is slim but never squeezed to nothing."""
    browser = self._browser()
    least = browser.minimumSizeHint().width()
    self.assertGreater(least, 0)
    self.assertGreater(browser.sizeHint().width(), least)

  def run_paints(self) -> None:
    """The browser paints, header, arrows and all."""
    browser = self._browser(True)
    browser.reveal(self.path('notes', 'old', 'deep.ezw'))
    self.assertFalse(browser.grab().isNull())
