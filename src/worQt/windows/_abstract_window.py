"""
AbstractWindow is the shared base for top-level application windows: a
'QMainWindow' fused with 'MixinBase'. Concrete windows (for example a text
editor's 'TextWindow') inherit it and implement 'initUi' to build their
contents. It is the place to lift behaviour every main window shares - the
build-once lifecycle, the menu-action helper, and later the document
controller, dirty-state title and close guard. Dialogs are NOT windows in
this sense and get their own base.

Per the QObject-construction constraint the UI is built lazily on the first
'show()', never in the class body or '__init__'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow
from worktoy.desc import AttriBox
from worktoy.utilities import textFmt

from ..mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable

  from PySide6.QtGui import QCloseEvent


class AbstractWindow(QMainWindow, MixinBase):
  """Shared base for top-level application windows."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __ui_built__ = None  # guards the build-once lifecycle in 'show'

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """Build the window contents. Invoked once, lazily, on the first
    'show()'. The default does nothing; concrete windows override it."""

  def _action(self, text: str, shortcut: str, slot: Callable) -> QAction:
    """Build a 'QAction' parented on this window, wired to 'slot'. An empty
    'shortcut' leaves the action unbound."""
    action = QAction(text, self)
    if shortcut:
      action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(slot)
    return action

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def show(self, ) -> None:
    """Build the UI once (via 'initUI') before the first show."""
    if not self.__ui_built__:
      self.initUI()
      self.__ui_built__ = True
    super().show()

  def closeEvent(self, event: QCloseEvent) -> None:
    """Consult the application's exit guard before closing. A 'worQt.app'
    application implements 'confirmExit' (which checks 'hasUnsavedChanges');
    under a plain 'QApplication' that method is absent and the window simply
    closes."""
    confirmExit = getattr(self.app, 'confirmExit', None)
    if confirmExit is not None and not confirmExit():
      return event.ignore()
    return event.accept()
