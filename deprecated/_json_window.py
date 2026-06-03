"""
JsonWindow is a generic main window for loading, editing and saving files
containing JSON data. It subclasses 'QMainWindow' and 'MixinBase'. Every
widget and layout is held in an 'AttriBox'; widgets receive 'THIS' as
parent, layouts never do. The pure 'JsonDocument' model is boxed too and
owns the file IO; the window only mediates between it and the editor.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QFont
from PySide6.QtWidgets import (
  QMainWindow,
  QPlainTextEdit,
  QLabel,
  QSplitter,
  QScrollArea,
  QFileDialog,
  QMessageBox,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..mixin import MixinBase
from ..widgets import JsonHighlighter, JsonFormWidget
from ..doc import JsonDocument

if TYPE_CHECKING:  # pragma: no cover
  pass


class JsonWindow(QMainWindow, MixinBase):
  """
  Generic JSON document window. Opens, edits and saves files containing
  JSON data, validating the text before every save. Every widget and
  layout is a boxed 'AttriBox' field; widgets take 'THIS' as parent,
  layouts never do.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __name_filter__ = 'JSON files (*.json);;All files (*)'

  #  Private Variables
  __json_highlighter__ = None  # JsonHighlighter, built once UI exists
  __form_base__ = None  # dict the form was last built from

  #  Public Variables
  document = AttriBox[JsonDocument]()
  dirty = AttriBox[bool](False)
  splitter = AttriBox[QSplitter](THIS)
  formScroll = AttriBox[QScrollArea](THIS)
  formWidget = AttriBox[JsonFormWidget](THIS)
  editor = AttriBox[QPlainTextEdit](THIS)
  validityLabel = AttriBox[QLabel](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """Build menus, central editor and status bar. Idempotent."""
    self.resize(640, 480)
    self._buildMenus()
    self._buildCentral()
    self._buildStatusBar()
    self._connectSignals()
    self._showText(self.document.text)
    self.dirty = False
    self._updateTitle()
    self.statusBar().showMessage('Ready')

  def _buildMenus(self, ) -> None:
    """Populate the menubar from the per-menu builders."""
    self._fileMenu()
    self._editMenu()
    self._helpMenu()

  def _fileMenu(self, ) -> None:
    """Build the File menu."""
    menu = self.menuBar().addMenu('&File')
    menu.addAction(self._action('&New', 'Ctrl+N', self._onNew))
    menu.addAction(self._action('&Open', 'Ctrl+O', self._onOpen))
    menu.addSeparator()
    menu.addAction(self._action('&Save', 'Ctrl+S', self._onSave))
    menu.addAction(self._action('Save &As', 'Ctrl+Shift+S', self._onSaveAs))
    menu.addSeparator()
    menu.addAction(self._action('&Quit', 'Ctrl+Q', self.close))

  def _editMenu(self, ) -> None:
    """Build the Edit menu."""
    menu = self.menuBar().addMenu('&Edit')
    menu.addAction(self._action('&Format', 'Ctrl+Shift+F', self._onFormat))
    menu.addAction(self._action('&Minify', 'Ctrl+M', self._onMinify))
    menu.addSeparator()
    menu.addAction(self._action('Sync &form', 'Ctrl+R', self._onSyncForm))

  def _helpMenu(self, ) -> None:
    """Build the Help menu."""
    menu = self.menuBar().addMenu('&Help')
    menu.addAction(self._action('&About', 'F1', self._onAbout))

  def _buildCentral(self, ) -> None:
    """
    Assemble the central widget: a splitter with the type-specific form
    on the left and the raw JSON text editor on the right.
    """
    self.editor.setPlaceholderText('{}')
    self._styleEditor()
    self.__json_highlighter__ = JsonHighlighter(self.editor.document())
    self.formScroll.setWidget(self.formWidget)
    self.formScroll.setWidgetResizable(True)
    self.splitter.setOrientation(Qt.Orientation.Horizontal)
    self.splitter.addWidget(self.formScroll)
    self.splitter.addWidget(self.editor)
    self.splitter.setSizes([260, 380])
    self.setCentralWidget(self.splitter)

  def _styleEditor(self, ) -> None:
    """Give the editor a monospace font and a dark code-editor theme."""
    font = QFont('monospace')
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSize(11)
    self.editor.setFont(font)
    self.editor.setTabStopDistance(2 * font.pointSizeF() * 2)
    style = (
      'QPlainTextEdit {'
      '  background-color: #282c34;'
      '  color: #abb2bf;'
      '  border: none;'
      '  padding: 8px;'
      '  selection-background-color: #3e4451;'
      '}'
    )
    self.editor.setStyleSheet(style)

  def _buildStatusBar(self, ) -> None:
    """Pin the live validity readout to the right of the status bar."""
    self.statusBar().addPermanentWidget(self.validityLabel)

  def _connectSignals(self, ) -> None:
    """Wire the editor to its handlers."""
    self.editor.textChanged.connect(self._onTextChanged)
    self.editor.textChanged.connect(self._refreshValidity)

  def _action(self, text: str, shortcut: str, slot) -> QAction:
    """Build a 'QAction' with text, shortcut and triggered handler."""
    action = QAction(text, self)
    action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(slot)
    return action

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HANDLERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _onNew(self, *_) -> None:
    """Discard the current document and start an empty JSON object."""
    if not self._confirmDiscard():
      return
    self.document.data = dict()
    self.document.path = ''
    self._showText(self.document.text)
    self._buildForm(self.document.data)
    self.dirty = False
    self._updateTitle()
    self.statusBar().showMessage('New document', 2000)

  def _onOpen(self, *_) -> None:
    """Pick a file, load it through the model and show the parsed text."""
    if not self._confirmDiscard():
      return
    filePath, _ = QFileDialog.getOpenFileName(
        self, 'Open JSON', '', self.__name_filter__)
    if not filePath:
      return
    try:
      self.document.loadFile(filePath)
    except (OSError, ValueError) as error:
      self._error('Could not open file', error)
      return
    self._showText(self.document.text)
    self._buildForm(self.document.data)
    self.dirty = False
    self._updateTitle()
    self.statusBar().showMessage('Opened %s' % filePath, 2000)

  def _onSave(self, *_) -> bool:
    """
    Validate the editor text as JSON and write it through the model.
    Routes to 'save as' when the document has no path yet. Returns True
    on a successful write, False on cancellation or error.
    """
    if not self.document.path:
      return self._onSaveAs()
    try:
      self.document.text = self.editor.toPlainText()
    except ValueError as error:
      self._error('Invalid JSON', error)
      return False
    try:
      self.document.saveFile()
    except OSError as error:
      self._error('Could not save file', error)
      return False
    self.dirty = False
    self._updateTitle()
    self.statusBar().showMessage('Saved %s' % self.document.path, 2000)
    return True

  def _onSaveAs(self, *_) -> bool:
    """Pick a destination path, then delegate to 'save'."""
    filePath, _ = QFileDialog.getSaveFileName(
        self, 'Save JSON', '', self.__name_filter__)
    if not filePath:
      return False
    self.document.path = filePath
    return self._onSave()

  def _onTextChanged(self, *_) -> None:
    """Mark the document dirty and refresh the title bar."""
    self.dirty = True
    self._updateTitle()

  def _onFormat(self, *_) -> None:
    """Re-indent the editor text. No-op (with a status note) if invalid."""
    try:
      self.document.text = self.editor.toPlainText()
    except ValueError:
      self.statusBar().showMessage('Cannot format: invalid JSON', 3000)
      return
    self.editor.setPlainText(self.document.text)

  def _onMinify(self, *_) -> None:
    """Collapse the editor text to one line. No-op if invalid."""
    try:
      self.document.text = self.editor.toPlainText()
    except ValueError:
      self.statusBar().showMessage('Cannot minify: invalid JSON', 3000)
      return
    self.editor.setPlainText(self.document.compact)

  def _onSyncForm(self, *_) -> None:
    """Rebuild the form from the current editor text. No-op if invalid."""
    try:
      self.document.text = self.editor.toPlainText()
    except ValueError:
      self.statusBar().showMessage('Cannot sync form: invalid JSON', 3000)
      return
    self._buildForm(self.document.data)
    self.statusBar().showMessage('Form synced from text', 2000)

  def _onFormChanged(self, *_) -> None:
    """
    Merge the form's scalar values back over the base object and push the
    result into the document and text editor. Non-scalar keys (nested
    objects, arrays) are preserved from the base untouched.
    """
    if self.__form_base__ is None:
      return
    merged = dict(self.__form_base__)
    merged.update(self.formWidget.currentValues())
    self.document.data = merged
    self.__form_base__ = merged
    self._showText(self.document.text)
    self.dirty = True
    self._updateTitle()

  def _onAbout(self, *_) -> None:
    """Show an About dialog from the Help menu."""
    info = 'A generic JSON document editor built with worQt.'
    QMessageBox.about(self, 'About worQt JSON', info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def loadData(self, data: object) -> None:
    """
    Replace the document content with 'data' and show it in the editor.
    The document is captured once and used for both the store and the
    render, so the editor always reflects exactly what was loaded. Safe
    to call before or after the window is shown.
    """
    document = self.document
    document.data = data
    self._showText(document.text)
    self._buildForm(document.data)
    self.dirty = False
    self._updateTitle()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HELPERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _buildForm(self, data: object) -> None:
    """
    Rebuild the type-specific form from 'data'. Only a top-level object
    contributes editable rows; anything else yields an empty form.
    """
    base = data if isinstance(data, dict) else dict()
    self.__form_base__ = base
    self.formWidget.loadFrom(base, self._onFormChanged)

  def _showText(self, text: str) -> None:
    """
    Replace the editor contents without tripping the dirty flag. Signals
    are blocked so the programmatic update is not seen as a user edit;
    the validity readout is refreshed explicitly afterwards.
    """
    self.editor.blockSignals(True)
    self.editor.setPlainText(text)
    self.editor.blockSignals(False)
    self._refreshValidity()

  def _refreshValidity(self, *_) -> None:
    """Update the status-bar readout from the current editor text."""
    ok, message = JsonDocument.validate(self.editor.toPlainText())
    if ok:
      self.validityLabel.setStyleSheet('color: green;')
      self.validityLabel.setText('● valid JSON')
    else:
      self.validityLabel.setStyleSheet('color: red;')
      self.validityLabel.setText('● invalid JSON')
    self.validityLabel.setToolTip(message)

  def _updateTitle(self, ) -> None:
    """Reflect the current path and dirty state in the window title."""
    name = self.document.path if self.document.path else 'untitled'
    star = '*' if self.dirty else ''
    self.setWindowTitle('worQt JSON - %s%s' % (name, star))

  def _confirmDiscard(self, ) -> bool:
    """
    Ask the user before discarding unsaved edits. Returns True when it is
    safe to proceed (no unsaved changes, or the user chose to discard).
    """
    if not self.dirty:
      return True
    yes = QMessageBox.StandardButton.Yes
    no = QMessageBox.StandardButton.No
    answer = QMessageBox.question(
        self, 'Unsaved changes', 'Discard unsaved changes?', yes | no)
    return True if answer == yes else False

  def _error(self, title: str, error: Exception) -> None:
    """Report an error in a modal dialog and on the status bar."""
    QMessageBox.critical(self, title, str(error))
    self.statusBar().showMessage(title, 4000)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def closeEvent(self, event) -> None:
    """Guard against losing unsaved edits when the window is closed."""
    if self._confirmDiscard():
      event.accept()
    else:
      event.ignore()

  def show(self, ) -> None:
    self.initUi()
    super().show()
