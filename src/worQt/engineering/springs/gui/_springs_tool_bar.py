"""
SpringsToolBar subclasses 'PaintedWidget' and is the row of buttons
above the springs.
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


class SpringsToolBar(PaintedWidget):
  """
  SpringsToolBar subclasses 'PaintedWidget' and is the row of buttons
  above the springs, each saying what it does: 'Play', setting the
  system moving, which says 'Pause' while it moves, and 'Reset', back to
  how it was set up; and apart, 'Add mass', hanging a mass on a spring
  under the point selected, 'Add anchor', 'Add component', hanging a
  spring-mass-damper under it, 'Add spring' and 'Add damper', joining
  the two points selected, and 'Remove', taking away what is
  selected.
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
  playButton = AttriBox[ToolButton](THIS)
  resetButton = AttriBox[ToolButton](THIS)
  massButton = AttriBox[ToolButton](THIS)
  anchorButton = AttriBox[ToolButton](THIS)
  componentButton = AttriBox[ToolButton](THIS)
  springButton = AttriBox[ToolButton](THIS)
  damperButton = AttriBox[ToolButton](THIS)
  removeButton = AttriBox[ToolButton](THIS)

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
      self.playButton, self.resetButton, self.massButton,
      self.anchorButton, self.componentButton, self.springButton,
      self.damperButton, self.removeButton
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.playButton.sizeHint().height() + 16
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
      'Play', 'Reset', 'Add mass', 'Add anchor', 'Add component',
      'Add spring', 'Add damper', 'Remove'
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
    """Places the buttons left to right, the groups apart. 'Play' has
    the room 'Pause' needs, so nothing moves as it changes."""
    left = 12
    for index, button in enumerate(self._buttons()):
      if index == 2:
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      width = size.width()
      if button is self.playButton:
        metrics = button.font.metrics
        longer = metrics.horizontalAdvance('Pause')
        width += max(0, longer - metrics.horizontalAdvance(button.text))
      button.setGeometry(left, 8, width, size.height())
      left += width + self.__fallback_spacing__
