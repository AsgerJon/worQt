"""
ViewToolPanel is the contents of the drawing app's 'Viewer' tool window:
the controls that govern how the canvas is viewed rather than what it holds.
It offers show-grid and snap-to-grid checkboxes, a grid-fineness control (a
slider paired with a line edit for a precise value, in target pixels per
cell), and a reset-view button. The panel only builds and exposes its
widgets and the slider/edit sync; the window wires them to the canvas.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
  QVBoxLayout,
  QHBoxLayout,
  QLabel,
  QCheckBox,
  QSlider,
  QLineEdit,
  QPushButton,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..widgets import BaseWidget
from ..widgets import Container

if TYPE_CHECKING:  # pragma: no cover
  pass


class ViewToolPanel(BaseWidget):
  """Tool-window contents for the canvas view controls (grid, snap, zoom)."""

  #  Fallback Variables
  __min_spacing__ = 8
  __max_spacing__ = 160
  __default_spacing__ = 24

  #  Public Variables
  built = AttriBox[bool](False)
  vbox = AttriBox[QVBoxLayout]()
  showGridCheck = AttriBox[QCheckBox]('Show grid', THIS)
  snapCheck = AttriBox[QCheckBox]('Snap to grid', THIS)
  gridLabel = AttriBox[QLabel]('Grid spacing (px)', THIS)
  sliderHost = AttriBox[Container](THIS)
  sliderRow = AttriBox[QHBoxLayout]()
  gridSlider = AttriBox[QSlider](THIS)
  gridEdit = AttriBox[QLineEdit]('24', THIS)
  factorLabel = AttriBox[QLabel]('', THIS)
  resetButton = AttriBox[QPushButton]('Reset view', THIS)

  def build(self, ) -> None:
    """Assemble the view controls into a vertical layout. Idempotent."""
    if self.built:
      return
    self.showGridCheck.setChecked(True)
    self.snapCheck.setChecked(True)
    self.gridSlider.setOrientation(Qt.Orientation.Horizontal)
    self.gridSlider.setRange(self.__min_spacing__, self.__max_spacing__)
    self.gridSlider.setValue(self.__default_spacing__)
    self.gridSlider.setMinimumWidth(120)
    self.gridEdit.setValidator(
        QIntValidator(self.__min_spacing__, self.__max_spacing__, self))
    self.gridEdit.setText(str(self.__default_spacing__))
    self.gridEdit.setMaximumWidth(56)
    self.sliderRow.setContentsMargins(0, 0, 0, 0)
    self.sliderRow.addWidget(self.gridSlider)
    self.sliderRow.addWidget(self.gridEdit)
    self.sliderHost.setLayout(self.sliderRow)
    self.vbox.addWidget(self.showGridCheck)
    self.vbox.addWidget(self.snapCheck)
    self.vbox.addWidget(self.gridLabel)
    self.vbox.addWidget(self.sliderHost)
    self.vbox.addWidget(self.factorLabel)
    self.vbox.addWidget(self.resetButton)
    self.vbox.addStretch(1)
    self.setLayout(self.vbox)
    self.setMinimumWidth(220)
    self.built = True

  def setFactor(self, value: float, mmPerPx: bool) -> None:
    """
    Show the integer view factor. Zoomed out it reads as millimetres per
    pixel; zoomed in past 1:1 it swaps to pixels per millimetre.
    """
    unit = 'mm/px' if mmPerPx else 'px/mm'
    self.factorLabel.setText('factor = %g %s' % (round(value), unit))

  def spacingRange(self, ) -> tuple:
    """The '(min, max)' allowed grid spacing in pixels."""
    return (self.__min_spacing__, self.__max_spacing__)

  def setSpacing(self, pixels: int) -> None:
    """
    Reflect 'pixels' on both the slider and the line edit without emitting
    their change signals (used to keep the two in step).
    """
    self.gridSlider.blockSignals(True)
    self.gridSlider.setValue(pixels)
    self.gridSlider.blockSignals(False)
    self.gridEdit.setText(str(pixels))
