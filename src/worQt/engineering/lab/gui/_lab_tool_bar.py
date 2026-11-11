"""
LabToolBar subclasses 'PaintedWidget' and is the row of buttons above
the beam.
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


class LabToolBar(PaintedWidget):
  """
  LabToolBar subclasses 'PaintedWidget' and is the row of buttons above
  the beam, each saying what it does: 'Start test' and 'Pause', which
  says 'Resume' while the test is paused; a little apart, 'New beam',
  casting the beam afresh, untested, 'Open…', setting up a beam on its
  rig as a '.beam' file holds them, and 'Save…', writing the setup to
  one; and apart again, 'Add support', 'Add actuator', 'Add
  transducer', 'Add stirrup gap', a stretch of the beam left without
  stirrups, and 'Remove', taking away the part selected.
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
  startButton = AttriBox[ToolButton](THIS)
  pauseButton = AttriBox[ToolButton](THIS)
  newButton = AttriBox[ToolButton](THIS)
  openButton = AttriBox[ToolButton](THIS)
  saveButton = AttriBox[ToolButton](THIS)
  supportButton = AttriBox[ToolButton](THIS)
  actuatorButton = AttriBox[ToolButton](THIS)
  transducerButton = AttriBox[ToolButton](THIS)
  gapButton = AttriBox[ToolButton](THIS)
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
      self.startButton, self.pauseButton, self.newButton,
      self.openButton, self.saveButton, self.supportButton,
      self.actuatorButton, self.transducerButton, self.gapButton,
      self.removeButton
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.startButton.sizeHint().height() + 16
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
      'Start test', 'Pause', 'New beam', 'Open…', 'Save…', 'Add support',
      'Add actuator', 'Add transducer', 'Add stirrup gap', 'Remove'
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
    """Places the buttons left to right, the groups apart. 'Pause' has
    the room 'Resume' needs, so it does not move as it changes."""
    left = 12
    for index, button in enumerate(self._buttons()):
      if index in (2, 5):
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      width = size.width()
      if button is self.pauseButton:
        metrics = button.font.metrics
        longer = metrics.horizontalAdvance('Resume')
        width += max(0, longer - metrics.horizontalAdvance(button.text))
      button.setGeometry(left, 8, width, size.height())
      left += width + self.__fallback_spacing__
