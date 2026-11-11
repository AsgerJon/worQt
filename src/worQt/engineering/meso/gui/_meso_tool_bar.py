"""
MesoToolBar subclasses 'PaintedWidget' and is the row of buttons above
the section and the curve.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QSize
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import PaintBoxModel
from ....utils import Color
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import ToolButton, Slider, CheckBox
from ...gui._paint_panel import PaintPanel

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent


class MesoToolBar(PaintedWidget):
  """
  MesoToolBar subclasses 'PaintedWidget' and is the row of buttons above
  the section and the curve, each saying what it does: 'New cylinder';
  a little apart, 'Compression test' and 'Tension test'; and apart
  again, 'Pause', which says 'Resume' while a test is paused, and
  'Export PDF', writing the test's report. Then the
  'Paste' slider, how opaque the paste is drawn, solid at first, and
  last 'Use GPU', ticked to reckon a test on the graphics card.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_panel_color__ = Color(37, 38, 42)
  __fallback_divider_color__ = Color(58, 61, 65)
  __fallback_spacing__ = 8  # pixels between buttons
  __fallback_group_gap__ = 24  # pixels between the groups of buttons

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  newButton = AttriBox[ToolButton](THIS)
  compressionButton = AttriBox[ToolButton](THIS)
  tensionButton = AttriBox[ToolButton](THIS)
  pauseButton = AttriBox[ToolButton](THIS)
  exportButton = AttriBox[ToolButton](THIS)
  pasteSlider = AttriBox[Slider](THIS)
  gpuBox = AttriBox[CheckBox](THIS)

  #  Virtual Variables
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @panelColor.GET
  def _getPanelColor(self, ) -> Color:
    return self.__fallback_panel_color__

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  def _buttons(self, ) -> tuple[ToolButton, ...]:
    return (
      self.newButton, self.compressionButton, self.tensionButton,
      self.pauseButton, self.exportButton
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.newButton.sizeHint().height() + 16
    return QSize(480, height)

  def minimumSizeHint(self, ) -> QSize:
    return self.sizeHint()

  def resizeEvent(self, event: QResizeEvent) -> None:
    PaintedWidget.resizeEvent(self, event)
    self._place()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    texts = (
      'New cylinder', 'Compression test', 'Tension test', 'Pause',
      'Export PDF'
    )
    for button, text in zip(self._buttons(), texts):
      button.text = text
    self.pasteSlider.text = 'Paste'
    self.pasteSlider.value = 1.0
    self.gpuBox.text = 'Use GPU'
    self._place()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the bottom,
    facing the views."""
    bottom = self.height() - 0.5
    return QPointF(0.0, bottom), QPointF(float(self.width()), bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _place(self, ) -> None:
    """Places the buttons left to right, the groups apart. 'Pause' has
    the room 'Resume' needs, so it does not move as it changes."""
    left = 12
    for index, button in enumerate(self._buttons()):
      if index in (1, 3):
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      width = size.width()
      if button is self.pauseButton:
        metrics = button.font.metrics
        longer = metrics.horizontalAdvance('Resume')
        width += max(0, longer - metrics.horizontalAdvance(button.text))
      button.setGeometry(left, 8, width, size.height())
      left += width + self.__fallback_spacing__
    left += self.__fallback_group_gap__ - self.__fallback_spacing__
    height = self.newButton.sizeHint().height()
    width = self.pasteSlider.sizeHint().width()
    self.pasteSlider.setGeometry(left, 8, width, height)
    left += width + self.__fallback_group_gap__
    box = self.gpuBox.sizeHint()
    self.gpuBox.setGeometry(left, 8, box.width(), height)
