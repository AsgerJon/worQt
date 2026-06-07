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


class AbstractWindow(QMainWindow, MixinBase):
  """Shared base for top-level application windows."""
