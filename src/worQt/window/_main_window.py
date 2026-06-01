"""
MainWindow is the concrete 'worQt' main window. It subclasses
'QMainWindow' and 'MixinBase', demonstrating that the metaclass fusion
generalises beyond 'QApplication' to any Qt type. Every widget and
layout is held in an 'AttriBox'; widgets receive 'THIS' as parent,
layouts never do.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
  QMainWindow,
  QWidget,
  QVBoxLayout,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QPushButton,
  QListWidget,
  QTextEdit,
  QMessageBox,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..mixin import MixinBase
from ..widgets import BaseWidget

if TYPE_CHECKING:  # pragma: no cover
  pass


class MainWindow(QMainWindow, MixinBase):
  """
  Concrete 'worQt' main window. Every widget and layout is a boxed
  'AttriBox' field; widgets take 'THIS' as parent, layouts never do.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  baseWidget = AttriBox[BaseWidget](THIS)
  baseLayout = AttriBox[QVBoxLayout]()
  inputWidget = AttriBox[BaseWidget](THIS)
  inputRow = AttriBox[QHBoxLayout]()
  header = AttriBox[QLabel]('worQt demo', THIS)
  inputField = AttriBox[QLineEdit](THIS)
  addButton = AttriBox[QPushButton]('Add', THIS)
  itemList = AttriBox[QListWidget](THIS)
  logView = AttriBox[QTextEdit](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """Build menus, central layout and status bar. Idempotent."""
    self.setWindowTitle('worQt')
    self.resize(640, 480)
    self._buildMenus()
    self._buildCentral()
    self._connectSignals()
    self.statusBar().showMessage('Ready')

  def _buildMenus(self, ) -> None:
    """Populate the menubar from the per-menu builders."""
    self._fileMenu()
    self._editMenu()
    self._viewMenu()
    self._helpMenu()

  def _fileMenu(self, ) -> None:
    """Build the File menu."""
    menu = self.menuBar().addMenu('&File')
    menu.addAction(self._action('&New', 'Ctrl+N', self._clearItems))
    menu.addAction(self._action('&Open', 'Ctrl+O', self._onOpen))
    menu.addSeparator()
    menu.addAction(self._action('&Quit', 'Ctrl+Q', self.close))

  def _editMenu(self, ) -> None:
    """Build the Edit menu."""
    menu = self.menuBar().addMenu('&Edit')
    menu.addAction(self._action('Add &item', 'Ctrl+Return', self._addItem))
    menu.addAction(self._action('&Clear', 'Ctrl+L', self._clearItems))

  def _viewMenu(self, ) -> None:
    """Build the View menu."""
    menu = self.menuBar().addMenu('&View')
    action = self._action('Toggle &log', 'Ctrl+G', self._toggleLog)
    action.setCheckable(True)
    action.setChecked(True)
    menu.addAction(action)

  def _helpMenu(self, ) -> None:
    """Build the Help menu."""
    menu = self.menuBar().addMenu('&Help')
    menu.addAction(self._action('&About', 'F1', self._onAbout))

  def _buildCentral(self, ) -> None:
    """Assemble the central widget from its boxed widgets."""
    self.inputField.setPlaceholderText('Type something and press Enter')
    self.logView.setReadOnly(True)
    self.inputRow.addWidget(self.inputField)
    self.inputRow.addWidget(self.addButton)
    self.inputWidget.setLayout(self.inputRow)
    self.baseLayout.addWidget(self.header)
    self.baseLayout.addWidget(self.inputWidget)
    self.baseLayout.addWidget(self.itemList)
    self.baseLayout.addWidget(self.logView)
    self.baseWidget.setLayout(self.baseLayout)
    self.setCentralWidget(self.baseWidget)

  def _connectSignals(self, ) -> None:
    """Wire the interactive widgets to their handlers."""
    self.addButton.clicked.connect(self._addItem)
    self.inputField.returnPressed.connect(self._addItem)

  def _action(self, text: str, shortcut: str, slot) -> QAction:
    """Build a 'QAction' with text, shortcut and triggered handler."""
    action = QAction(text, self)
    action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(slot)
    return action

  def _log(self, message: str) -> None:
    """Append a line to the read-only log view."""
    self.logView.append(message)

  def _addItem(self, *_) -> None:
    """Move the input text into the item list and clear the field."""
    text = self.inputField.text().strip()
    if not text:
      self.statusBar().showMessage('Nothing to add', 2000)
      return
    self.itemList.addItem(text)
    self.inputField.clear()
    self._log('Added: %s' % text)
    self.statusBar().showMessage('Added %s' % text, 2000)

  def _clearItems(self, *_) -> None:
    """Empty the item list."""
    self.itemList.clear()
    self._log('List cleared')
    self.statusBar().showMessage('List cleared', 2000)

  def _toggleLog(self, checked: bool) -> None:
    """Show or hide the log view from the View menu."""
    self.logView.setVisible(checked)

  def _onOpen(self, *_) -> None:
    """Placeholder File>Open handler."""
    self.statusBar().showMessage('Open is not implemented yet', 2000)

  def _onAbout(self, *_) -> None:
    """Show an About dialog from the Help menu."""
    QMessageBox.about(self, 'About worQt', 'worQt fuses worktoy with Qt.')

  def show(self, ) -> None:
    self.initUi()
    super().show()
