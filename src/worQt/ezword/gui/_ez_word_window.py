"""
EZWordWindow subclasses 'MainWindow' and is the window EZWord writes in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.waitaminute import TypeException

from ...browser import FileBrowser
from ...tabs import TabBar
from ...windows import MainWindow
from .. import Chapter
from . import PageWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

  from PySide6.QtGui import QKeyEvent

_SAVE = QMessageBox.StandardButton.Save
_DISCARD = QMessageBox.StandardButton.Discard
_CTRL = Qt.KeyboardModifier.ControlModifier


class EZWordWindow(MainWindow):
  """
  EZWordWindow subclasses 'MainWindow' and is the window EZWord writes
  in: a 'FileBrowser' of the EZWord files around it on the left, taking
  the room there is, and on the right a 'TabBar' over the pages, one
  'PageWidget' a tab, each a file open, never narrower than its 80
  columns.

  The File menu, the page's ':w' and a double click in the browser open
  and save EZWord files; a file already open is shown in its tab, and
  another opens in a tab of its own. 'New', ':tabnew' open a new tab;
  'gt', 'gT', ':tabn', ':tabp', Ctrl+PageDown and Ctrl+PageUp go from tab
  to tab. ':q', ':wq' and the like close the tab, not the window; closing
  the last starts over on an empty page. Closing a tab by its cross asks
  first when it holds unsaved changes. The title names the current file
  and carries Qt's '[*]' marker while its page holds unsaved changes.

  A file holds one 'Chapter', written as its text: a page is read into a
  'Chapter' when saved, so the file always holds the format's own
  rendering of it, and a file is read through a 'Chapter' when opened.
  For the current tab, 'page' is its page and 'filePath' its file.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'EZWord'
  __file_suffix__ = '.ezw'
  __file_filter__ = 'EZWord files (*.ezw)'
  __start_size__ = 1100, 800
  __tab_keys__ = {
    Qt.Key.Key_PageDown: 1,
    Qt.Key.Key_PageUp  : -1,
  }

  #  Private Variables
  __page_widgets__: Optional[list[PageWidget]] = None

  #  Public Variables
  browser = AttriBox[FileBrowser](THIS)
  tabBar = AttriBox[TabBar](THIS)

  #  Virtual Variables
  pages: Field[list] = Field()
  page: Field[PageWidget] = Field()
  filePath: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @pages.GET
  def _getPages(self, ) -> list[PageWidget]:
    """The 'pages' getter returns the pages, one a tab, in tab order;
    there is always at least one."""
    if not self.__page_widgets__:
      self.__page_widgets__ = []
      self._addPage()
    return self.__page_widgets__

  @page.GET
  def _getPage(self, ) -> PageWidget:
    """The 'page' getter returns the current tab's page."""
    pages = self.pages
    return pages[min(max(self.tabBar.currentIndex, 0), len(pages) - 1)]

  @filePath.GET
  def _getFilePath(self, ) -> Optional[str]:
    """
    The 'filePath' getter returns the file the current page was last
    opened from or saved to, or 'None' for a page never saved.
    """
    return self.page.filePath

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @filePath.SET
  def _setFilePath(self, path: Optional[str]) -> None:
    if path is not None and not isinstance(path, str):
      raise TypeException('filePath', path, str)
    self.page.filePath = path
    self._updateTitles()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    The 'initUI' method puts the browser left of the tab bar and the
    pages, the browser taking the room the pages leave, sizes the window
    and gives the current page the keyboard focus.
    """
    self.browser.suffixes = (self.__file_suffix__,)
    self.baseLayout.addWidget(self.browser, 0, 0, 2, 1)
    self.baseLayout.addWidget(self.tabBar, 0, 1)
    self.baseLayout.setColumnStretch(0, 1)
    self.baseLayout.setColumnStretch(1, 0)
    self.baseLayout.setRowStretch(1, 1)
    self.baseLayout.setVerticalSpacing(0)
    MainWindow.initUI(self)
    self.resize(*self.__start_size__)
    self.selectTab(self.tabBar.currentIndex)

  def initLogic(self, ) -> None:
    """
    The 'initLogic' method wires the File menu, the browser and the tab
    bar to the file and tab operations. Each page is wired as it is
    added.
    """
    fileMenu = self.mainMenuBar.fileMenu
    fileMenu.newAction.triggered.connect(self.newFile)
    fileMenu.openAction.triggered.connect(self.openFile)
    fileMenu.saveAction.triggered.connect(self.saveFile)
    fileMenu.exitAction.triggered.connect(self.close)
    self.browser.fileActivated.connect(self.openFileAt)
    self.tabBar.currentChanged.connect(self.selectTab)
    self.tabBar.closeRequested.connect(self.closeTab)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \_____________
  #  The tabs  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _addPage(self, ) -> PageWidget:
    """Add a tab with an empty, untitled page, its signals wired, and
    return the page. The tab is not made current."""
    page = PageWidget(self.baseWidget)
    self.__page_widgets__.append(page)
    self.baseLayout.addWidget(page, 1, 1)
    page.hide()
    page.writeRequested.connect(partial(self.saveTab, page))
    page.quitRequested.connect(partial(self.closePage, page))
    page.modifiedChanged.connect(partial(self._onModified, page))
    page.newTabRequested.connect(self.newFile)
    page.tabStepRequested.connect(self.stepTab)
    self.tabBar.addTab(page.title)
    return page

  def selectTab(self, index: int) -> None:
    """
    The 'selectTab' method makes tab 'index' the current one: its page
    shows, takes the focus and names the window, and the browser marks
    its file.
    """
    pages = self.pages
    index = min(max(index, 0), len(pages) - 1)
    self.tabBar.currentIndex = index
    for number, page in enumerate(pages):
      page.setVisible(True if number == index else False)
    self._updateTitles()
    self._showFile()
    pages[index].setFocus()

  def stepTab(self, steps: int) -> None:
    """The 'stepTab' method goes 'steps' tabs on, back when negative,
    round from the last to the first."""
    count = len(self.pages)
    self.selectTab((self.tabBar.currentIndex + steps) % count)

  def _updateTitles(self, ) -> None:
    """Every tab shows its page's title and unsaved changes; the window
    shows the current page's."""
    for index, page in enumerate(self.pages):
      self.tabBar.setTitle(index, page.title)
      self.tabBar.setModified(index, page.modified)
    self.setWindowTitle('%s[*] - %s' % (self.page.title, self.__app_name__))
    self.setWindowModified(self.page.modified)

  def _onModified(self, page: PageWidget, modified: bool) -> None:
    self._updateTitles()

  def _showFile(self, ) -> None:
    """The browser lists the folder again and marks the current file."""
    self.browser.refresh()
    self.browser.markedPath = self.filePath
    if self.filePath is not None:
      self.browser.reveal(self.filePath)

  def _askToSave(self, page: PageWidget) -> bool:
    """Ask whether to save 'page''s unsaved changes before it closes, and
    tell whether to go on closing it."""
    askToSave = getattr(self.app, 'askToSave', None)
    if askToSave is None:
      return True
    self.selectTab(self.pages.index(page))
    answer = askToSave()
    if answer == _SAVE:
      return self.saveTab(page)
    return True if answer == _DISCARD else False

  def closePage(self, page: PageWidget, *_) -> bool:
    """
    The 'closePage' method closes the tab of 'page', asking first when it
    holds unsaved changes, and tells whether it closed. Closing the last
    tab starts over on an empty one.
    """
    if page.modified and not self._askToSave(page):
      return False
    index = self.pages.index(page)
    self.__page_widgets__.remove(page)
    self.tabBar.removeTab(index)
    self.baseLayout.removeWidget(page)
    page.hide()
    page.deleteLater()
    if not self.__page_widgets__:
      self._addPage()
    self.selectTab(self.tabBar.currentIndex)
    return True

  def closeTab(self, index: int) -> bool:
    """The 'closeTab' method closes tab 'index', as its cross does."""
    return self.closePage(self.pages[index])

  def closeFile(self, *_) -> bool:
    """The 'closeFile' method closes the current tab."""
    return self.closePage(self.page)

  # \_____________
  #  The files ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _isBlank(self, page: PageWidget) -> bool:
    """Whether 'page' is an empty, untitled page nothing was written on,
    which a file may take over rather than open a tab of its own."""
    if page.filePath is not None or page.modified:
      return False
    return False if page.text else True

  def newFile(self, *_) -> None:
    """The 'newFile' method opens a new tab with an empty, untitled
    page."""
    self._addPage()
    self.selectTab(len(self.pages) - 1)

  def openFileAt(self, path: str) -> None:
    """
    The 'openFileAt' method opens the file at 'path': in its tab if it
    is open already, read again from the file unless it holds unsaved
    changes; otherwise in the current tab, if that is blank, or in a new
    one. A file the format cannot read is refused before any tab changes.
    """
    path = os.path.abspath(path)
    for index, page in enumerate(self.pages):
      if page.filePath == path:
        if not page.modified:
          self._fill(page, path, self._read(path))
        return self.selectTab(index)
    text = self._read(path)
    page = self.page
    if not self._isBlank(page):
      page = self._addPage()
    self._fill(page, path, text)
    self.selectTab(self.pages.index(page))

  def openFile(self, *_) -> None:
    """The 'openFile' method asks for a file and opens it."""
    path = self.askOpenPath()
    if path:
      self.openFileAt(path)

  def loadFrom(self, path: str) -> None:
    """The 'loadFrom' method opens the file at 'path', as 'openFileAt'
    does."""
    self.openFileAt(path)

  @staticmethod
  def _read(path: str) -> str:
    """The text of the file at 'path', read through a 'Chapter'."""
    with open(path) as file:
      return str(Chapter(file.read()))

  def _fill(self, page: PageWidget, path: str, text: str) -> None:
    page.text = text
    page.filePath = path
    page.modified = False
    self._updateTitles()

  def saveTab(self, page: PageWidget, *_) -> bool:
    """
    The 'saveTab' method saves 'page' to its file, asking for one the
    first time, and tells whether it saved.
    """
    path = page.filePath
    if path is None:
      path = self.askSavePath()
    if not path:
      return False
    self._write(page, path)
    return True

  def saveFile(self, *_) -> bool:
    """The 'saveFile' method saves the current page, as 'saveTab'
    does."""
    return self.saveTab(self.page)

  def saveTo(self, path: str) -> None:
    """The 'saveTo' method saves the current page to the file at
    'path'."""
    self._write(self.page, path)

  def _write(self, page: PageWidget, path: str) -> None:
    """
    Write 'page', read into a 'Chapter', to the file at 'path'. A
    temporary file beside it is written first and moved into place, so a
    failed save leaves the old file whole.
    """
    content = '%s\n' % str(Chapter(page.text))
    temporary = '%s.tmp' % path
    try:
      with open(temporary, 'w') as file:
        file.write(content)
      os.replace(temporary, path)
    except BaseException:
      if os.path.exists(temporary):
        os.remove(temporary)
      raise
    page.filePath = path
    page.modified = False
    self._updateTitles()
    self._showFile()

  def unsavedPages(self, ) -> list[PageWidget]:
    """The 'unsavedPages' method returns the pages holding unsaved
    changes."""
    return [page for page in self.pages if page.modified]

  def askOpenPath(self, ) -> str:  # pragma: no cover
    """
    The 'askOpenPath' method asks which file to open, and returns its
    path, or an empty string when cancelled. It is a hook of its own so a
    test, which must never open a modal dialog, can answer instead.
    """
    title, filters = 'Open', self.__file_filter__
    path, _ = QFileDialog.getOpenFileName(self, title, '', filters)
    return path

  def askSavePath(self, ) -> str:  # pragma: no cover
    """
    The 'askSavePath' method asks where to save, and returns the path,
    given the EZWord suffix, or an empty string when cancelled. Like
    'askOpenPath', it is a hook a test can answer instead.
    """
    title, filters = 'Save', self.__file_filter__
    path, _ = QFileDialog.getSaveFileName(self, title, '', filters)
    if path and not path.endswith(self.__file_suffix__):
      path = '%s%s' % (path, self.__file_suffix__)
    return path

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Ctrl+PageDown and Ctrl+PageUp go to the next and the previous
    tab, from wherever the focus is."""
    steps = self.__tab_keys__.get(event.key(), None)
    if steps is not None and event.modifiers() & _CTRL:
      self.stepTab(steps)
      return event.accept()
    MainWindow.keyPressEvent(self, event)
