"""
SelectionToolPanel is the contents of the drawing app's 'Selection' tool
window: a label, the scrollable list of items already in the scene, and the
'Clear all' button. The window owns the wiring; this panel only builds and
exposes its widgets. The list takes the panel's flexible space and scrolls
once it overflows.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
  QVBoxLayout,
  QLabel,
  QPushButton,
  QListWidget,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..widgets import BaseWidget

if TYPE_CHECKING:  # pragma: no cover
  pass


class SelectionToolPanel(BaseWidget):
  """Tool-window contents for selecting and clearing existing items."""

  #  Public Variables
  built = AttriBox[bool](False)
  vbox = AttriBox[QVBoxLayout]()
  listLabel = AttriBox[QLabel]('Scene items', THIS)
  itemList = AttriBox[QListWidget](THIS)
  clearButton = AttriBox[QPushButton]('Clear all', THIS)

  def build(self, ) -> None:
    """Assemble the label, list and clear button. Idempotent."""
    if self.built:
      return
    self.vbox.addWidget(self.listLabel)
    self.vbox.addWidget(self.itemList, 1)  # stretch: list scrolls on overflow
    self.vbox.addWidget(self.clearButton)
    self.setLayout(self.vbox)
    self.built = True
