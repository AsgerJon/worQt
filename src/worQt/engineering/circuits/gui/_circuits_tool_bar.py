"""
CircuitsToolBar subclasses 'PaintedWidget' and is the row of buttons
above the circuit.
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
from ._speed_slider import SpeedSlider

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent


class CircuitsToolBar(PaintedWidget):
  """
  CircuitsToolBar subclasses 'PaintedWidget' and is the row of buttons
  above the circuit, each saying what it does: 'Play', which says
  'Pause' while the circuit runs, and 'Reset', switching it on anew;
  'Examples', opening a menu of small circuits to start from; a button
  for each kind of part, 'Wire', 'Source', 'Resistor', 'Lamp',
  'Capacitor', 'Coil', 'Switch', 'Ammeter', 'Voltmeter', 'Diode',
  'LED' and 'Transistor', adding one, and 'Remove', taking away what is
  selected; and apart, 'speedSlider', how fast the circuit runs, from
  a thousandth of real time to ten times it. A subclass without
  examples sets '__fallback_examples__' false, its groups starting
  earlier.
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
  __fallback_groups__ = (2, 3)  # the buttons groups start at
  __fallback_slider_width__ = 330  # pixels the speed slider takes
  __fallback_examples__ = True  # whether there is an 'Examples' button

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  playButton = AttriBox[ToolButton](THIS)
  resetButton = AttriBox[ToolButton](THIS)
  examplesButton = AttriBox[ToolButton](THIS)
  wireButton = AttriBox[ToolButton](THIS)
  sourceButton = AttriBox[ToolButton](THIS)
  resistorButton = AttriBox[ToolButton](THIS)
  lampButton = AttriBox[ToolButton](THIS)
  capacitorButton = AttriBox[ToolButton](THIS)
  coilButton = AttriBox[ToolButton](THIS)
  switchButton = AttriBox[ToolButton](THIS)
  ammeterButton = AttriBox[ToolButton](THIS)
  voltmeterButton = AttriBox[ToolButton](THIS)
  diodeButton = AttriBox[ToolButton](THIS)
  ledButton = AttriBox[ToolButton](THIS)
  transistorButton = AttriBox[ToolButton](THIS)
  removeButton = AttriBox[ToolButton](THIS)
  speedSlider = AttriBox[SpeedSlider](THIS)

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
    examples = (self.examplesButton,) if self.__fallback_examples__ else ()
    return (
      self.playButton, self.resetButton, *examples,
      *self.partButtons(),
      self.removeButton,
    )

  def partButtons(self, ) -> tuple[ToolButton, ...]:
    """The 'partButtons' method returns the buttons adding a part, in
    the order of the kinds of part."""
    return (self.wireButton, self.sourceButton, self.resistorButton,
            self.lampButton, self.capacitorButton, self.coilButton,
            self.switchButton, self.ammeterButton, self.voltmeterButton,
            self.diodeButton, self.ledButton, self.transistorButton)

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
      'Play', 'Reset', 'Examples', 'Wire', 'Source', 'Resistor', 'Lamp',
      'Capacitor', 'Coil', 'Switch', 'Ammeter', 'Voltmeter', 'Diode',
      'LED', 'Transistor', 'Remove'
    )
    buttons = (self.playButton, self.resetButton, self.examplesButton,
               *self.partButtons(), self.removeButton)
    for button, text in zip(buttons, texts):
      button.text = text
    if not self.__fallback_examples__:
      self.examplesButton.setVisible(False)
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
    """Places the buttons left to right, the groups apart, 'Play' as
    wide as 'Pause' would be, and the speed slider apart after them."""
    left, height = 12, 0
    for index, button in enumerate(self._buttons()):
      if index in self.__fallback_groups__:
        left += self.__fallback_group_gap__ - self.__fallback_spacing__
      size = button.sizeHint()
      width = size.width()
      if button is self.playButton:
        width = max(width, 64)
      button.setGeometry(left, 8, width, size.height())
      left += width + self.__fallback_spacing__
      height = size.height()
    left += self.__fallback_group_gap__ - self.__fallback_spacing__
    slider = self.speedSlider
    tall = max(slider.sizeHint().height(), height)
    slider.setGeometry(left, 8 + (height - tall) // 2,
                       self.__fallback_slider_width__, tall)
