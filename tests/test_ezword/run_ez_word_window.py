"""
RunEZWordWindow covers 'EZWordWindow' and 'EZWordApp': the title and its
'[*]' marker, saving and opening EZWord files through the File menu, the
page's ex commands and the file browser beside it, the tabs a file each,
and the unsaved-changes guard before a page is thrown away.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os

from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QMessageBox
from worktoy.waitaminute.keenum import KeeResolveError

from . import EZWordWidgetTest

_DISCARD = QMessageBox.StandardButton.Discard
_SAVE = QMessageBox.StandardButton.Save


class RunEZWordWindow(EZWordWidgetTest):
  """Tests for 'EZWordWindow' and 'EZWordApp'."""

  def _write(self, name: str, content: str) -> str:
    path = self.path(name)
    with open(path, 'w') as file:
      file.write(content)
    return path

  @staticmethod
  def _read(path: str) -> str:
    with open(path) as file:
      return file.read()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TITLE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_untitled_until_saved(self) -> None:
    """A new window holds an untitled page, unmodified."""
    window = self.openWindow()
    self.assertEqual(window.windowTitle(), 'untitled[*] - EZWord')
    self.assertFalse(window.isWindowModified())
    self.assertIsNone(window.filePath)

  def run_typing_marks_the_title(self) -> None:
    """Typing shows the '[*]' marker; saving clears it and names the
    file in the title."""
    window = self.openWindow()
    self.insert(window.page, 'hello.')
    self.assertTrue(window.isWindowModified())
    window.savePath = self.path('note.ezw')
    window.saveFile()
    self.assertFalse(window.isWindowModified())
    self.assertEqual(window.windowTitle(), 'note.ezw[*] - EZWord')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SAVE   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_save_writes_the_format(self) -> None:
    """Saving writes the page as the format renders it: cased by the
    punctuation, whitespace tidied, paragraphs split by blank lines."""
    window = self.openWindow()
    window.page.text = 'hello ,  world. how are you?\n\n\nnext one'
    window.savePath = self.path('save.ezw')
    self.assertTrue(window.saveFile())
    expected = 'Hello, world. How are you?\n\nNext one\n'
    self.assertEqual(self._read(window.savePath), expected)
    self.assertFalse(os.path.exists('%s.tmp' % window.savePath))

  def run_save_reuses_the_file(self) -> None:
    """Once saved, saving again writes the same file without asking."""
    window = self.openWindow()
    path = window.savePath = self.path('again.ezw')
    window.saveFile()
    window.savePath = ''
    self.insert(window.page, 'more.')
    self.assertTrue(window.saveFile())
    self.assertEqual(self._read(path), 'More.\n')

  def run_cancelled_save(self) -> None:
    """Cancelling the file question saves nothing and keeps the page
    modified."""
    window = self.openWindow()
    self.insert(window.page, 'kept.')
    self.assertFalse(window.saveFile())
    self.assertTrue(window.page.modified)
    self.assertEqual(os.listdir(self.path('')), [])

  def run_failed_save_leaves_nothing(self) -> None:
    """A save that fails raises, and leaves neither a file nor a
    temporary file behind."""
    window = self.openWindow()
    path = self.path(os.path.join('missing', 'fail.ezw'))
    with self.assertRaises(OSError):
      window.saveTo(path)
    self.assertEqual(os.listdir(self.path('')), [])
    self.assertIsNone(window.filePath)

  def run_save_action(self) -> None:
    """The File menu's 'Save' saves."""
    window = self.openWindow()
    window.page.text = 'from the menu.'
    window.savePath = self.path('menu.ezw')
    window.mainMenuBar.fileMenu.saveAction.trigger()
    self.assertEqual(self._read(window.savePath), 'From the menu.\n')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPEN   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_open_reads_through_a_chapter(self) -> None:
    """Opening reads the file through a 'Chapter', so the page holds the
    format's rendering of it, unmodified."""
    window = self.openWindow()
    path = self._write('open.ezw', 'hello.   world\n\n\n\nnext\n')
    window.openPath = path
    window.openFile()
    self.assertEqual(window.page.text, 'Hello. World\n\nNext')
    self.assertEqual(window.filePath, path)
    self.assertFalse(window.page.modified)

  def run_open_refuses_a_foreign_file(self) -> None:
    """A file holding what the format cannot is refused, and the page
    keeps what it had."""
    window = self.openWindow()
    window.page.text = 'still here'
    window.openPath = self._write('bad.ezw', 'version 2.\n')
    with self.assertRaises(KeeResolveError):
      window.openFile()
    self.assertEqual(window.page.text, 'still here')
    self.assertIsNone(window.filePath)

  def run_open_round_trip(self) -> None:
    """What is saved opens again as it was saved."""
    window = self.openWindow()
    window.page.text = 'one, two. three?\n\nfour; five'
    window.savePath = self.path('trip.ezw')
    window.saveFile()
    saved = self._read(window.savePath)
    window.openPath = window.savePath
    window.openFile()
    self.assertEqual('%s\n' % window.page.text, saved)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  EX COMMANDS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_w_saves(self) -> None:
    """':w' on the page saves, as the File menu does."""
    window = self.openWindow()
    self.insert(window.page, 'written.')
    window.savePath = self.path('w.ezw')
    self.ex(window.page, 'w')
    self.assertEqual(self._read(window.savePath), 'Written.\n')
    self.assertFalse(window.page.modified)

  def run_wq_saves_and_starts_over(self) -> None:
    """':wq' saves, then closes the file, not the window: the page starts
    over, empty and untitled."""
    window = self.openWindow()
    self.insert(window.page, 'done.')
    window.savePath = self.path('wq.ezw')
    self.ex(window.page, 'wq')
    self.assertEqual(self._read(window.savePath), 'Done.\n')
    self.assertTrue(window.isVisible())
    self.assertEqual(window.page.text, '')
    self.assertIsNone(window.filePath)
    self.assertFalse(window.page.modified)

  def run_q_bang_starts_over_without_saving(self) -> None:
    """':q' refuses with unsaved changes; ':q!' throws them away and
    starts over, without saving or asking, the window still open."""
    window = self.openWindow()
    self.insert(window.page, 'lost')
    self.ex(window.page, 'q')
    self.assertEqual(window.page.text, 'lost')
    self.ex(window.page, 'q!')
    self.assertEqual(window.page.text, '')
    self.assertTrue(window.isVisible())
    self.assertEqual(self.app.askCount, 0)
    self.assertEqual(os.listdir(self.path('')), [])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  THE BROWSER  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_browser_beside_the_page(self) -> None:
    """The browser sits left of the page and takes the room the page,
    never narrower than its 80 columns, leaves; the window asks for room
    for both.

    The layout is laid out at given widths directly, rather than by
    resizing the window, which a desktop may refuse - fitting it to a
    screen narrower than it asks for, say."""
    window = self.openWindow()
    browser, page = window.browser, window.page
    least = page.minimumSizeHint().width()
    asked = window.minimumSizeHint().width()
    self.assertGreaterEqual(asked, least + browser.minimumSizeHint().width())
    widths = []
    for width in (asked + 100, asked + 300):
      window.baseLayout.setGeometry(QRect(0, 0, width, 600))
      self.assertLess(browser.geometry().right(), page.geometry().left())
      self.assertEqual(page.width(), least)
      widths.append(browser.width())
    self.assertEqual(widths[1] - widths[0], 200)

  def run_browser_lists_ezword_files(self) -> None:
    """The browser lists the folders and the EZWord files, nothing
    else."""
    window = self.openWindow()
    self._write('one.ezw', 'One.\n')
    self._write('other.txt', 'other')
    os.mkdir(self.path('folder'))
    window.browser.rootPath = self.path('')
    names = [node.name for node in window.browser.rows]
    self.assertEqual(names, ['folder', 'one.ezw'])

  def run_browser_opens_files(self) -> None:
    """Opening a file in the browser opens it on the page and marks it
    as the one open."""
    window = self.openWindow()
    path = self._write('open me.ezw', 'opened.\n')
    window.browser.rootPath = self.path('')
    window.browser.activate(window.browser.rows[0])
    self.assertEqual(window.page.text, 'Opened.')
    self.assertEqual(window.filePath, path)
    self.assertEqual(window.browser.markedPath, path)

  def run_saved_files_show_in_the_browser(self) -> None:
    """A file saved in the browser's folder shows in it, marked."""
    window = self.openWindow()
    window.browser.rootPath = self.path('')
    self.insert(window.page, 'fresh.')
    window.savePath = self.path('fresh.ezw')
    window.saveFile()
    names = [node.name for node in window.browser.rows]
    self.assertEqual(names, ['fresh.ezw'])
    self.assertEqual(window.browser.markedPath, window.savePath)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TABS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _titles(self, window) -> list[str]:
    bar = window.tabBar
    return [bar.titleAt(index) for index in range(bar.count)]

  def run_new_opens_a_tab(self) -> None:
    """'New' opens an empty, untitled tab, leaving the others as they
    are, without asking anything."""
    window = self.openWindow()
    self.insert(window.page, 'draft')
    window.newFile()
    self.assertEqual(window.tabBar.count, 2)
    self.assertEqual(window.page.text, '')
    self.assertEqual(window.pages[0].text, 'draft')
    self.assertEqual(self.app.askCount, 0)

  def run_files_open_in_tabs(self) -> None:
    """A file opens in the blank tab, the next in a tab of its own, and
    one open already is shown in its tab."""
    window = self.openWindow()
    one = self._write('one.ezw', 'One.\n')
    two = self._write('two.ezw', 'Two.\n')
    window.openFileAt(one)
    window.openFileAt(two)
    self.assertEqual(self._titles(window), ['one.ezw', 'two.ezw'])
    self.assertEqual(window.filePath, two)
    window.openFileAt(one)
    self.assertEqual(window.tabBar.count, 2)
    self.assertEqual((window.tabBar.currentIndex, window.page.text),
                     (0, 'One.'))

  def run_each_tab_keeps_its_own_page(self) -> None:
    """Each tab keeps its own text and shows its own changes; the
    window's title follows the current one."""
    window = self.openWindow()
    window.openFileAt(self._write('one.ezw', 'One.\n'))
    window.openFileAt(self._write('two.ezw', 'Two.\n'))
    self.insert(window.page, 'changed ')
    window.selectTab(0)
    self.assertEqual(window.page.text, 'One.')
    self.assertEqual(window.windowTitle(), 'one.ezw[*] - EZWord')
    self.assertFalse(window.tabBar.isModified(0))
    self.assertTrue(window.tabBar.isModified(1))
    self.assertEqual([page.isVisible() for page in window.pages],
                     [True, False])

  def run_tab_keys(self) -> None:
    """'gt', 'gT', ':tabnew', Ctrl+PageDown and Ctrl+PageUp go from tab
    to tab, round from the last to the first."""
    window = self.openWindow()
    self.ex(window.page, 'tabnew')
    self.ex(window.page, 'tabnew')
    self.assertEqual(window.tabBar.currentIndex, 2)
    self.typeText(window.page, 'gt')
    self.assertEqual(window.tabBar.currentIndex, 0)
    self.typeText(window.page, 'gT')
    self.assertEqual(window.tabBar.currentIndex, 2)
    ctrl = Qt.KeyboardModifier.ControlModifier
    self.key(window.page, Qt.Key.Key_PageDown, ctrl, '')
    self.assertEqual(window.tabBar.currentIndex, 0)
    self.key(window.page, Qt.Key.Key_PageUp, ctrl, '')
    self.assertEqual(window.tabBar.currentIndex, 2)

  def run_q_closes_the_tab(self) -> None:
    """':q' closes the current tab only; the next takes its place."""
    window = self.openWindow()
    window.openFileAt(self._write('one.ezw', 'One.\n'))
    window.openFileAt(self._write('two.ezw', 'Two.\n'))
    window.selectTab(0)
    self.ex(window.page, 'q')
    self.assertEqual(self._titles(window), ['two.ezw'])
    self.assertEqual(window.page.text, 'Two.')

  def run_closing_a_modified_tab_asks(self) -> None:
    """Closing a tab with unsaved changes asks: cancelled, it stays;
    saved, it is written and closes; discarded, it closes as it is."""
    window = self.openWindow()
    path = self._write('one.ezw', 'One.\n')
    window.openFileAt(path)
    self.insert(window.page, 'more ')
    self.assertFalse(window.closeTab(0))
    self.assertEqual(window.page.text, 'more One.')
    self.app.answer = _SAVE
    self.assertTrue(window.closeTab(0))
    self.assertEqual(self._read(path), 'More one.\n')
    window.openFileAt(path)
    self.insert(window.page, 'lost ')
    self.app.answer = _DISCARD
    self.assertTrue(window.closeTab(0))
    self.assertEqual(self._read(path), 'More one.\n')
    self.assertEqual(self.app.askCount, 3)

  def run_exit_guard_covers_every_tab(self) -> None:
    """Unsaved changes in any tab count; saving them saves every one."""
    window = self.openWindow()
    one = self._write('one.ezw', 'One.\n')
    two = self._write('two.ezw', 'Two.\n')
    window.openFileAt(one)
    self.insert(window.page, 'a ')
    window.openFileAt(two)
    self.insert(window.page, 'b ')
    window.selectTab(0)
    self.assertTrue(self.app.hasUnsavedChanges())
    self.assertTrue(self.app.saveChanges())
    self.assertEqual((self._read(one), self._read(two)),
                     ('A one.\n', 'B two.\n'))
    self.assertFalse(self.app.hasUnsavedChanges())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UNSAVED CHANGES  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_exit_guard_saves_the_page(self) -> None:
    """The application has unsaved changes while the page is modified,
    and saving them saves the page."""
    window = self.openWindow()
    self.assertFalse(self.app.hasUnsavedChanges())
    self.insert(window.page, 'unsaved.')
    self.assertTrue(self.app.hasUnsavedChanges())
    window.savePath = self.path('exit.ezw')
    self.app.answer = _SAVE
    self.assertTrue(self.app.confirmExit())
    self.assertEqual(self._read(window.savePath), 'Unsaved.\n')
    self.assertFalse(self.app.hasUnsavedChanges())
