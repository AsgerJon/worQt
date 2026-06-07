"""
TextWindow is the editor window for the 'words' larp. It subclasses
'AbstractWindow', so the build-once 'show()' lifecycle and the 'QAction'
helper come from the base; this class only builds its own contents in
'initUi' (a 'QPlainTextEdit' central widget and a File menu) and handles the
menu actions. The handlers are deliberately thin for now; the document
binding, the dirty-star title and the unsaved-changes guard are the next
abstractions to lift into 'AbstractWindow'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QPlainTextEdit
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..windows import AbstractWindow

if TYPE_CHECKING:  # pragma: no cover
  pass


class TextWindow(AbstractWindow):
  """The 'words' editor window: a plain-text editor with a File menu."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  editor = AttriBox[QPlainTextEdit](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """Build the central editor, the menu bar and the status bar."""
    self.setWindowTitle('words')
    self.resize(720, 540)
    self.setCentralWidget(self.editor)
    self._buildFileMenu()
    self.statusBar().showMessage('Ready')

  def _buildFileMenu(self, ) -> None:
    """Populate the File menu."""
    menu = self.menuBar().addMenu('&File')
    menu.addAction(self._action('&New', 'Ctrl+N', self._onNew))
    menu.addAction(self._action('&Open', 'Ctrl+O', self._onOpen))
    menu.addSeparator()
    menu.addAction(self._action('&Save', 'Ctrl+S', self._onSave))
    menu.addAction(self._action('Save &As', 'Ctrl+Shift+S', self._onSaveAs))
    menu.addSeparator()
    menu.addAction(self._action('&Quit', 'Ctrl+Q', self.close))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HANDLERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _onNew(self, *_) -> None:
    """Start a blank document."""
    self.editor.clear()
    self.statusBar().showMessage('New document', 2000)

  def _onOpen(self, *_) -> None:
    """Placeholder File>Open handler."""
    self.statusBar().showMessage('Open is not implemented yet', 2000)

  def _onSave(self, *_) -> None:
    """Placeholder File>Save handler."""
    self.statusBar().showMessage('Save is not implemented yet', 2000)

  def _onSaveAs(self, *_) -> None:
    """Placeholder File>Save As handler."""
    self.statusBar().showMessage('Save As is not implemented yet', 2000)
