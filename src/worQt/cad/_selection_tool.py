"""
SelectionToolPanel is the contents of the drawing app's 'Selection' tool
window: four scrollable lists - the nodes, the elements (members), the guides
(module lines) and the dimensions already in the scene - each under a header
that pairs its label with a 'show' checkbox toggling that category on the
canvas, plus the 'Clear all' button. The window owns the wiring; this panel
only builds and exposes its widgets. The lists share the panel's flexible
space and scroll once they overflow.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
  QVBoxLayout,
  QHBoxLayout,
  QLabel,
  QCheckBox,
  QPushButton,
  QListWidget,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..widgets import BaseWidget
from ..widgets import Container

if TYPE_CHECKING:  # pragma: no cover
  pass


class SelectionToolPanel(BaseWidget):
  """Tool-window contents for selecting and clearing existing items."""

  #  Public Variables
  built = AttriBox[bool](False)
  vbox = AttriBox[QVBoxLayout]()
  #  nodes
  nodeHeader = AttriBox[Container](THIS)
  nodeHeaderRow = AttriBox[QHBoxLayout]()
  nodeLabel = AttriBox[QLabel]('Nodes', THIS)
  showNodesCheck = AttriBox[QCheckBox]('show', THIS)
  nodeList = AttriBox[QListWidget](THIS)
  #  elements (members)
  elementHeader = AttriBox[Container](THIS)
  elementHeaderRow = AttriBox[QHBoxLayout]()
  elementLabel = AttriBox[QLabel]('Elements', THIS)
  showElementsCheck = AttriBox[QCheckBox]('show', THIS)
  elementList = AttriBox[QListWidget](THIS)
  #  guides (module lines + the crossed-circle glyph on each node)
  guideHeader = AttriBox[Container](THIS)
  guideHeaderRow = AttriBox[QHBoxLayout]()
  guideLabel = AttriBox[QLabel]('Guides', THIS)
  showGuidesCheck = AttriBox[QCheckBox]('show', THIS)
  guideList = AttriBox[QListWidget](THIS)
  #  dimensions (linear + angular)
  dimensionHeader = AttriBox[Container](THIS)
  dimensionHeaderRow = AttriBox[QHBoxLayout]()
  dimensionLabel = AttriBox[QLabel]('Dimensions', THIS)
  showDimensionsCheck = AttriBox[QCheckBox]('show', THIS)
  dimensionList = AttriBox[QListWidget](THIS)
  #  shared
  clearButton = AttriBox[QPushButton]('Clear all', THIS)

  def build(self, ) -> None:
    """Assemble the four labelled lists, each with a 'show' checkbox, and the
    clear button. Idempotent."""
    if self.built:
      return
    sections = (
      (self.nodeHeader, self.nodeHeaderRow, self.nodeLabel,
       self.showNodesCheck, self.nodeList),
      (self.elementHeader, self.elementHeaderRow, self.elementLabel,
       self.showElementsCheck, self.elementList),
      (self.guideHeader, self.guideHeaderRow, self.guideLabel,
       self.showGuidesCheck, self.guideList),
      (self.dimensionHeader, self.dimensionHeaderRow, self.dimensionLabel,
       self.showDimensionsCheck, self.dimensionList),
    )
    for host, row, label, check, listWidget in sections:
      check.setChecked(True)  # everything visible by default
      row.addWidget(label)
      row.addStretch(1)
      row.addWidget(check)
      host.setLayout(row)
      self.vbox.addWidget(host)
      self.vbox.addWidget(listWidget, 1)  # stretch: scrolls on overflow
    self.vbox.addWidget(self.clearButton)
    self.setLayout(self.vbox)
    self.built = True
