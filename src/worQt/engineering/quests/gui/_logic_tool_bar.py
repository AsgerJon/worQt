"""
LogicToolBar subclasses 'PaintedWidget' and is the row of buttons
adding logic parts and chips, under the circuits' own.
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
from ...circuits import Bit, Clock, Probe
from ...gui import ToolButton
from ...gui._paint_panel import PaintPanel

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent

#  What each button adds, in order: a logic part, or a chip by its name
LOGIC_KINDS = (Bit, Probe, Clock, 'NOT', 'AND', 'OR', 'NAND', 'NOR', 'XOR',
               'FA', 'ADD4', 'SR', 'DFF', 'JKFF', 'SRAM')
_TEXTS = ('Input', 'Probe', 'Clock', 'NOT', 'AND', 'OR', 'NAND', 'NOR',
          'XOR', 'Full adder', 'Adder 4', 'SR latch', 'D flip-flop',
          'JK flip-flop', 'SRAM')


class LogicToolBar(PaintedWidget):
  """
  LogicToolBar subclasses 'PaintedWidget' and is the row of buttons
  adding logic: 'Input', a logic input set low or high, 'Probe', a logic
  output, 'Clock', and a button for each kind of chip, the gates, the
  adders, the latch and the flip-flops and the memory; each greyed out
  until it is granted. 'buttons' returns them in the order of
  'LOGIC_KINDS'.
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
  inputButton = AttriBox[ToolButton](THIS)
  probeButton = AttriBox[ToolButton](THIS)
  clockButton = AttriBox[ToolButton](THIS)
  notButton = AttriBox[ToolButton](THIS)
  andButton = AttriBox[ToolButton](THIS)
  orButton = AttriBox[ToolButton](THIS)
  nandButton = AttriBox[ToolButton](THIS)
  norButton = AttriBox[ToolButton](THIS)
  xorButton = AttriBox[ToolButton](THIS)
  adderButton = AttriBox[ToolButton](THIS)
  adder4Button = AttriBox[ToolButton](THIS)
  latchButton = AttriBox[ToolButton](THIS)
  flipButton = AttriBox[ToolButton](THIS)
  jkButton = AttriBox[ToolButton](THIS)
  ramButton = AttriBox[ToolButton](THIS)

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

  def buttons(self, ) -> tuple[ToolButton, ...]:
    """The 'buttons' method returns the buttons, in the order of
    'LOGIC_KINDS'."""
    return (self.inputButton, self.probeButton, self.clockButton,
            self.notButton, self.andButton, self.orButton, self.nandButton,
            self.norButton, self.xorButton, self.adderButton,
            self.adder4Button, self.latchButton, self.flipButton,
            self.jkButton, self.ramButton)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.inputButton.sizeHint().height() + 16
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
    for button, text in zip(self.buttons(), _TEXTS):
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
    """Places the buttons left to right, the chips apart from the logic
    parts."""
    left = 12
    for index, button in enumerate(self.buttons()):
      if index == 3:
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      button.setGeometry(left, 8, size.width(), size.height())
      left += size.width() + self.__fallback_spacing__
