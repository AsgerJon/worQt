"""
TextWindow is the 'new_words' editor: a 'QTextEdit' for the body plus a few
'QLineEdit's for the metadata (author editable, the two date stamps shown
read-only), all bound to a 'TextDocument'. File handling rides on
'worQt.document' - 'Save'/'Open' just call the document's 'save'/'load'.
Following
the worQt QObject rule, the widgets are 'AttriBox'es built lazily on the
first 'show' (via 'initUi'), never in the class body or before a
'QApplication' exists.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (QTextEdit,
                               QLineEdit,
                               QWidget,
                               QFormLayout,
                               QFileDialog,
                               QMessageBox)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from worQt.windows import AbstractWindow
from ._text_document import TextDocument

if TYPE_CHECKING:  # pragma: no cover
  pass


class TextWindow(AbstractWindow):
  """The 'new_words' editor window."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Model (a 'worQt.document' Document - not a 'QObject')
  document = AttriBox[TextDocument]()
  currentPath = AttriBox[str]('')  # empty until first saved/opened
  defaultDir = AttriBox[str]('')  # seeds the dialogs when there is no path

  #  Widgets (lazy; built on first 'show')
  bodyWidget = AttriBox[QWidget](THIS)
  formLayout = AttriBox[QFormLayout]()  # no THIS on layouts
  authorEdit = AttriBox[QLineEdit](THIS)
  creationEdit = AttriBox[QLineEdit](THIS)
  modifiedEdit = AttriBox[QLineEdit](THIS)
  editor = AttriBox[QTextEdit](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _stamp() -> str:
    """The current local time as a seconds-resolution ISO string."""
    return datetime.now().isoformat(timespec='seconds')

  def _dialogStart(self) -> str:
    """Where a file dialog should open: the current document's location if it
    has one, otherwise the configured 'defaultDir' (empty string -> the
    process working directory)."""
    return self.currentPath or self.defaultDir

  def _newDocument(self) -> TextDocument:
    """A fresh, stamped document that reads as clean (not dirty)."""
    document = TextDocument()
    stamp = self._stamp()
    document.creationDate = stamp
    document.modifiedDate = stamp
    document.markPristine()
    return document

  def _modelToView(self) -> None:
    """Push the document's values into the widgets. Signals are blocked so
    this programmatic fill is not mistaken for a user edit and does not
    dirty the document."""
    document = self.document
    self.authorEdit.blockSignals(True)
    self.authorEdit.setText(document.author)
    self.authorEdit.blockSignals(False)
    self.creationEdit.setText(document.creationDate)
    self.modifiedEdit.setText(document.modifiedDate)
    self.editor.blockSignals(True)
    self.editor.setPlainText(document.content)
    self.editor.blockSignals(False)

  def _viewToModel(self) -> None:
    """Pull the editable widgets into the document. An empty author falls
    back to 'unknown'."""
    document = self.document
    document.author = self.authorEdit.text() or 'unknown'
    document.content = self.editor.toPlainText()

  def _onContentEdited(self, *_) -> None:
    """The editor changed - push into the document so it tracks as dirty."""
    self.document.content = self.editor.toPlainText()

  def _onAuthorEdited(self, *_) -> None:
    """The author field changed - push into the document (blank ->
    'unknown')."""
    self.document.author = self.authorEdit.text() or 'unknown'

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HANDLERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _confirmDiscard(self) -> bool:
    """May the current document be abandoned? The single gate every action
    that replaces or closes it - New, Open, close - goes through. True when
    the document is clean, was saved, or the user chose Discard; False to
    abort (Cancel, or a cancelled save)."""
    if not self.document.isDirty():
      return True
    answer = QMessageBox.warning(
        self, 'Unsaved changes',
        'This document has unsaved changes. Save before continuing?',
        QMessageBox.StandardButton.Save
        | QMessageBox.StandardButton.Discard
        | QMessageBox.StandardButton.Cancel)
    if answer == QMessageBox.StandardButton.Save:
      self.saveDocument()
      return not self.document.isDirty()  # False if the save was cancelled
    if answer == QMessageBox.StandardButton.Discard:
      return True
    return False  # Cancel

  def _onNew(self, *_) -> None:
    if not self._confirmDiscard():
      return
    self.document = self._newDocument()
    self.currentPath = ''
    self._modelToView()

  def _onOpen(self, *_) -> None:
    if not self._confirmDiscard():
      return
    path, _filter = QFileDialog.getOpenFileName(
        self, 'Open', self._dialogStart(), 'worQt text (*.json)')
    if not path:
      return
    self.document = TextDocument.load(path)
    self.currentPath = path
    self._modelToView()

  def saveDocument(self, *_) -> None:
    """Save to the current path, or prompt for a name via Rename if the
    document has never been saved. Public: the action menu and the app's
    exit-guard 'saveChanges' both call it."""
    if not self.currentPath:
      return self._onRename()
    self._viewToModel()
    self.document.modifiedDate = self._stamp()
    self.document.save(self.currentPath)
    self.modifiedEdit.setText(self.document.modifiedDate)

  def _onRename(self, *_) -> None:
    """Move the document to a new path: save the current contents there and
    drop the old file. A never-saved document just gets its first name."""
    path, _filter = QFileDialog.getSaveFileName(
        self, 'Rename', self._dialogStart(), 'worQt text (*.json)')
    if not path:
      return
    if not path.lower().endswith('.json'):
      path = '%s.json' % path  # default the extension if the user omits it
    oldPath = self.currentPath
    self.currentPath = path
    self._viewToModel()
    self.document.modifiedDate = self._stamp()
    self.document.save(path)
    if oldPath and oldPath != path and os.path.exists(oldPath):
      os.remove(oldPath)  # a rename moves the file; the old name is gone
    self.modifiedEdit.setText(self.document.modifiedDate)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _buildMenu(self) -> None:
    fileMenu = self.menuBar().addMenu('&File')
    fileMenu.addAction(self._action('&New', 'Ctrl+N', self._onNew))
    fileMenu.addAction(self._action('&Open', 'Ctrl+O', self._onOpen))
    fileMenu.addAction(self._action('&Save', 'Ctrl+S', self.saveDocument))
    fileMenu.addAction(self._action('&Rename', 'F2', self._onRename))
    fileMenu.addSeparator()
    fileMenu.addAction(self._action('&Quit', 'Ctrl+Q', self.close))

  def initUi(self) -> None:
    """Build the editor, the metadata fields and the File menu. Invoked
    once, lazily, by 'AbstractWindow.show'."""
    self.setWindowTitle('new_words')
    self.resize(640, 480)
    self.creationEdit.setReadOnly(True)
    self.modifiedEdit.setReadOnly(True)
    self.formLayout.addRow('Author', self.authorEdit)
    self.formLayout.addRow('Created', self.creationEdit)
    self.formLayout.addRow('Modified', self.modifiedEdit)
    self.formLayout.addRow(self.editor)
    self.bodyWidget.setLayout(self.formLayout)
    self.setCentralWidget(self.bodyWidget)
    self._buildMenu()
    self.editor.textChanged.connect(self._onContentEdited)
    self.authorEdit.textChanged.connect(self._onAuthorEdited)
    self.document = self._newDocument()
    self._modelToView()
