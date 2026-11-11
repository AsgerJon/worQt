"""
BusToolBar subclasses 'PaintedWidget' and is the row of buttons adding
the parts of buses and of a little computer.
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
from ...circuits import BusIn, BusProbe
from ...gui import ToolButton
from ...gui._paint_panel import PaintPanel

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent

#  What each button adds, in order: a bus part, or a chip by its name
BUS_KINDS = (BusIn, BusProbe, 'SPLIT', 'JOIN', 'ADDB', 'ALU', 'REG', 'MUX',
             'PC', 'DEC', 'ROM', 'CPU', 'RF', 'STACK', 'ACC', 'MPU')
_TEXTS = ('Bus input', 'Bus probe', 'Split', 'Join', 'Bus adder', 'ALU',
          'Register', 'Bus switch', 'Counter', 'Decoder', 'ROM', 'CPU',
          'Registers', 'Stack', 'Accumulator', 'Microprocessor')
_GROUPS = (4, 12)  # the buttons the groups start at


class BusToolBar(PaintedWidget):
  """
  BusToolBar subclasses 'PaintedWidget' and is the row of buttons adding
  buses: 'Bus input', a number on four bits, 'Bus probe', reading one,
  'Split' and 'Join', between a bus and its bits; the chips of a
  little computer; and apart, those of a microprocessor after the
  4004, each greyed out until it is granted. 'buttons' returns them in
  the order of 'BUS_KINDS'.
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
  busInButton = AttriBox[ToolButton](THIS)
  busProbeButton = AttriBox[ToolButton](THIS)
  splitButton = AttriBox[ToolButton](THIS)
  joinButton = AttriBox[ToolButton](THIS)
  busAdderButton = AttriBox[ToolButton](THIS)
  aluButton = AttriBox[ToolButton](THIS)
  registerButton = AttriBox[ToolButton](THIS)
  switchButton = AttriBox[ToolButton](THIS)
  counterButton = AttriBox[ToolButton](THIS)
  decoderButton = AttriBox[ToolButton](THIS)
  romButton = AttriBox[ToolButton](THIS)
  cpuButton = AttriBox[ToolButton](THIS)
  filesButton = AttriBox[ToolButton](THIS)
  stackButton = AttriBox[ToolButton](THIS)
  accumulatorButton = AttriBox[ToolButton](THIS)
  mpuButton = AttriBox[ToolButton](THIS)

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
    'BUS_KINDS'."""
    return (self.busInButton, self.busProbeButton, self.splitButton,
            self.joinButton, self.busAdderButton, self.aluButton,
            self.registerButton, self.switchButton, self.counterButton,
            self.decoderButton, self.romButton, self.cpuButton,
            self.filesButton, self.stackButton, self.accumulatorButton,
            self.mpuButton)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.busInButton.sizeHint().height() + 16
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
    """Places the buttons left to right, the chips apart from the bus
    parts, the microprocessor's apart from the rest."""
    left = 12
    for index, button in enumerate(self.buttons()):
      if index in _GROUPS:
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      button.setGeometry(left, 8, size.width(), size.height())
      left += size.width() + self.__fallback_spacing__
