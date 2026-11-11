"""
DiagramsToolBar subclasses 'PaintedWidget' and is the row of buttons
above the frame.
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
from ...gui import ToolButton
from ...gui._paint_panel import PaintPanel

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent


class DiagramsToolBar(PaintedWidget):
  """
  DiagramsToolBar subclasses 'PaintedWidget' and is the row of buttons
  above the frame, each saying what it does: 'Add member', from the node
  selected, or joining the two nodes selected, 'Add support', on the
  node selected, 'Add point load', 'Add line load' and 'Add moment', on
  the member selected, and 'Remove', taking away what is selected; and
  apart, which diagram the frame shows, 'N', 'V', 'M' or its 'Shape' as
  it bends, the one shown lit.
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
  memberButton = AttriBox[ToolButton](THIS)
  supportButton = AttriBox[ToolButton](THIS)
  pointButton = AttriBox[ToolButton](THIS)
  lineButton = AttriBox[ToolButton](THIS)
  momentButton = AttriBox[ToolButton](THIS)
  removeButton = AttriBox[ToolButton](THIS)
  normalButton = AttriBox[ToolButton](THIS)
  shearButton = AttriBox[ToolButton](THIS)
  bendingButton = AttriBox[ToolButton](THIS)
  shapeButton = AttriBox[ToolButton](THIS)

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
      self.memberButton, self.supportButton, self.pointButton,
      self.lineButton, self.momentButton, self.removeButton,
      self.normalButton, self.shearButton, self.bendingButton,
      self.shapeButton
    )

  def diagramButtons(self, ) -> tuple[ToolButton, ...]:
    """The 'diagramButtons' method returns the buttons choosing the
    diagram shown: N, V, M and the shape."""
    return (self.normalButton, self.shearButton, self.bendingButton,
            self.shapeButton)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.memberButton.sizeHint().height() + 16
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
      'Add member', 'Add support', 'Add point load', 'Add line load',
      'Add moment', 'Remove', 'N', 'V', 'M', 'Shape'
    )
    for button, text in zip(self._buttons(), texts):
      button.text = text
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
    """Places the buttons left to right, the groups apart, the diagrams'
    buttons each as wide as the widest of them."""
    left = 12
    for index, button in enumerate(self._buttons()):
      if index == 6:
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      width = size.width()
      if any(button is other for other in self.diagramButtons()):
        width = max(b.sizeHint().width() for b in self.diagramButtons())
      button.setGeometry(left, 8, width, size.height())
      left += width + self.__fallback_spacing__
