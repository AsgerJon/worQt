"""
BilliardsToolBar subclasses 'PaintedWidget' and is the row of buttons
above the table.
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

from ....engineering.gui import CheckBox, QuantitySlider, ToolButton
from ....engineering.gui._paint_panel import PaintPanel
from ....paint_ops import PaintBoxModel
from ....utils import Color
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent


class BilliardsToolBar(PaintedWidget):
  """
  BilliardsToolBar subclasses 'PaintedWidget' and is the row of buttons
  above the table: the game, 'Three-cushion' or 'Kegler', keglebillard,
  the one played lit; the mode, 'Game' or 'Sandbox', the one on lit;
  'New game', or in the sandbox 'Reset', the balls as a game opens;
  'Replay', the last shot shown again; 'Top view', lit while the table
  is seen from straight above, the camera's view in the corner;
  'Unfolded', lit while the map of the table unfolded shows beside it,
  the arc of the English across its mirrored copies; 'Full map', lit
  while the full map, 7 by 7 tables, shows instead of the table; and, in
  the sandbox only, 'Mulligan', the last shot taken back: the balls as
  they were before it, and its mark; and 'Move balls', lit while a drag
  on the cloth moves balls.
  Last, 'Field of view', 'viewSlider', how much the camera takes in, top
  to bottom, 20 to 90 degrees; and 'Aim step', 'stepSlider', how far the
  keys A and D turn the aim, and W and S tilt the camera, 0.01 to 1
  degree a press, on a log scale; and 'Hand', 'handBox', ticked while a
  gloved hand holding the cue is drawn behind ball 1 with the last
  shot's trails, seen from above; and 'Sound', 'soundBox', ticked while
  the shots are heard; and 'Shadow', 'shadowBox', ticked while the
  shadow both eyes see of the cue ball shows along the aim, as trenches
  to where ball 1 and ball 2 touch or stop. Shots are
  set up and taken in the 'ShotPanel' beside the table.
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
  __fallback_view__ = 36.0  # degrees the camera takes in at first
  __fallback_step__ = 0.1  # degrees a key turns the aim at first
  __slider_width__ = 260  # pixels the field of view's slider takes

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  caromButton = AttriBox[ToolButton](THIS)
  kegleButton = AttriBox[ToolButton](THIS)
  gameButton = AttriBox[ToolButton](THIS)
  sandboxButton = AttriBox[ToolButton](THIS)
  resetButton = AttriBox[ToolButton](THIS)
  replayButton = AttriBox[ToolButton](THIS)
  topButton = AttriBox[ToolButton](THIS)
  mapButton = AttriBox[ToolButton](THIS)
  fullButton = AttriBox[ToolButton](THIS)
  mulliganButton = AttriBox[ToolButton](THIS)
  moveButton = AttriBox[ToolButton](THIS)
  viewSlider = AttriBox[QuantitySlider](THIS)
  stepSlider = AttriBox[QuantitySlider](THIS)
  handBox = AttriBox[CheckBox](THIS)
  soundBox = AttriBox[CheckBox](THIS)
  shadowBox = AttriBox[CheckBox](THIS)

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.resetButton.sizeHint().height() + 16
    return QSize(420, height)

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
    self.caromButton.text = 'Three-cushion'
    self.kegleButton.text = 'Kegler'
    self.caromButton.checked = True
    self.gameButton.text = 'Game'
    self.sandboxButton.text = 'Sandbox'
    self.resetButton.text = 'New game'
    self.replayButton.text = 'Replay'
    self.replayButton.setEnabled(False)
    self.topButton.text = 'Top view'
    self.mapButton.text = 'Unfolded'
    self.fullButton.text = 'Full map'
    self.mulliganButton.text = 'Mulligan'
    self.moveButton.text = 'Move balls'
    self.viewSlider.text = 'Field of view'
    self.viewSlider.setScale(20.0, 90.0, '°', 0)
    self.viewSlider.quantity = self.__fallback_view__
    self.stepSlider.text = 'Aim step'
    self.stepSlider.setLogScale(0.01, 1.0, '°', 3)
    self.stepSlider.quantity = self.__fallback_step__
    self.handBox.text = 'Hand'
    self.handBox.checked = True
    self.soundBox.text = 'Sound'
    self.soundBox.checked = True
    self.shadowBox.text = 'Shadow'
    self.shadowBox.checked = True
    self._place()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def buttons(self, ) -> tuple[ToolButton, ...]:
    """The 'buttons' method returns the buttons, left to right."""
    return (self.caromButton, self.kegleButton, self.gameButton,
            self.sandboxButton, self.resetButton,
            self.replayButton, self.topButton, self.mapButton,
            self.fullButton, self.mulliganButton, self.moveButton)

  def showKind(self, kind: str) -> None:
    """The 'showKind' method shows the game played, 'carom' for
    three-cushion or 'kegler' for keglebillard, its button lit."""
    self.caromButton.checked = kind != 'kegler'
    self.kegleButton.checked = kind == 'kegler'
    self.caromButton.update()
    self.kegleButton.update()

  def showMode(self, mode: str) -> None:
    """The 'showMode' method shows 'mode', 'game' or 'sandbox': its
    button lit, 'New game' or 'Reset', and 'Mulligan' and 'Move balls' only
    in the sandbox."""
    sandbox = mode == 'sandbox'
    self.gameButton.checked = not sandbox
    self.sandboxButton.checked = sandbox
    self.resetButton.text = 'Reset' if sandbox else 'New game'
    self.mulliganButton.setEnabled(sandbox)
    self.moveButton.setEnabled(sandbox)
    if not sandbox:
      self.moveButton.checked = False
    for button in self.buttons():
      button.update()
    self._place()

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the bottom,
    facing the table."""
    bottom = self.height() - 0.5
    return QPointF(0.0, bottom), QPointF(float(self.width()), bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _place(self, ) -> None:
    """Places the buttons left to right, the field of view's slider,
    the aim step's and the hand's box after them, a little apart."""
    left, height = 12, self.resetButton.sizeHint().height()
    for button in self.buttons():
      size = button.sizeHint()
      button.setGeometry(left, 8, size.width(), size.height())
      left += size.width() + self.__fallback_spacing__
    slider = self.viewSlider.sizeHint().height()
    top = 8 + (height - slider) // 2
    width = self.__slider_width__
    self.viewSlider.setGeometry(left + 16, top, width, slider)
    self.stepSlider.setGeometry(left + 32 + width, top, width, slider)
    box = self.handBox.sizeHint()
    self.handBox.setGeometry(left + 56 + 2 * width,
                             8 + (height - box.height()) // 2,
                             box.width(), box.height())
    sound = self.soundBox.sizeHint()
    self.soundBox.setGeometry(left + 72 + 2 * width + box.width(),
                              8 + (height - sound.height()) // 2,
                              sound.width(), sound.height())
    shadow = self.shadowBox.sizeHint()
    self.shadowBox.setGeometry(
      left + 88 + 2 * width + box.width() + sound.width(),
      8 + (height - shadow.height()) // 2, shadow.width(), shadow.height())
