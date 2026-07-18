"""
ClickDemoWindow places a 'DemoButton' (which shades on hover and depresses
on press) amid a grid of 'GestureLight' indicators - clicks above, holds
and rejections below. Each light flashes when its gesture fires and names
the mouse button that triggered it, so every recognised gesture and every
rejection is visible at a glance.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from worQt.widgets import AbstractWidget
from worQt.windows import AbstractWindow

from ._demo_button import DemoButton
from ._gesture_light import GestureLight

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class ClickDemoWindow(AbstractWindow):
  """A 'DemoButton' surrounded by flashing per-gesture indicator lights."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_width__ = 620  # opens at a usable size, no manual resizing
  __window_height__ = 520

  #  Public Variables
  base = AttriBox[AbstractWidget](THIS)  # host for the layout
  layout = AttriBox[QGridLayout]()  # no THIS on layouts
  button = AttriBox[DemoButton](THIS)

  clickSingle = AttriBox[GestureLight](THIS)
  clickDouble = AttriBox[GestureLight](THIS)
  clickTriple = AttriBox[GestureLight](THIS)
  clickMulti = AttriBox[GestureLight](THIS)

  holdSingle = AttriBox[GestureLight](THIS)
  holdDouble = AttriBox[GestureLight](THIS)
  holdTriple = AttriBox[GestureLight](THIS)
  holdMulti = AttriBox[GestureLight](THIS)

  holdArmedLight = AttriBox[GestureLight](THIS)
  rejectPress = AttriBox[GestureLight](THIS)
  rejectTooLong = AttriBox[GestureLight](THIS)
  rejectRegret = AttriBox[GestureLight](THIS)
  rejectMismatch = AttriBox[GestureLight](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _buttonName(seq) -> str:
    """The mouse button that drove the sequence, or '?' if empty."""
    return seq[0].name if seq else '?'

  def _onClick(self, seq) -> None:
    n = len(seq)
    light = {
      1: self.clickSingle,
      2: self.clickDouble,
      3: self.clickTriple,
    }.get(n, self.clickMulti)
    print('click x%d: %s' % (n, self._buttonName(seq)))
    light.light(self._buttonName(seq))

  def _onHold(self, seq) -> None:
    n = len(seq)
    light = {
      1: self.holdSingle,
      2: self.holdDouble,
      3: self.holdTriple,
    }.get(n, self.holdMulti)
    print('hold x%d: %s' % (n, self._buttonName(seq)))
    light.light(self._buttonName(seq))

  def _onArmed(self, seq) -> None:
    self.holdArmedLight.light(self._buttonName(seq))

  def _onReject(self, light: GestureLight, seq) -> None:
    print('reject %s: %s' % (light, self._buttonName(seq)))
    light.light(self._buttonName(seq))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    self.setWindowTitle('worQt - click / hold demo')
    self.resize(self.__window_width__, self.__window_height__)
    button = self.button
    button.text = 'Click me'
    button.setMinimumSize(240, 140)
    #  (light, title, row, col); the button spans row 1, the armed light
    #  spans its own row.
    lights = [
      (self.clickSingle, 'Single Click', 0, 0),
      (self.clickDouble, 'Double Click', 0, 1),
      (self.clickTriple, 'Triple Click', 0, 2),
      (self.clickMulti, 'Multi Click', 0, 3),
      (self.holdSingle, 'Single Hold', 2, 0),
      (self.holdDouble, 'Double Hold', 2, 1),
      (self.holdTriple, 'Triple Hold', 2, 2),
      (self.holdMulti, 'Multi Hold', 2, 3),
      (self.holdArmedLight, 'Hold Armed', 3, 0),
      (self.rejectPress, 'Press Rejected', 4, 0),
      (self.rejectTooLong, 'Hold Too Long', 4, 1),
      (self.rejectRegret, 'Move Regret', 4, 2),
      (self.rejectMismatch, 'Button Mismatch', 4, 3),
    ]
    for light, title, row, col in lights:
      light.setGesture(title)
      light.setMinimumSize(130, 40)
      if light is self.holdArmedLight:
        self.layout.addWidget(light, row, col, 1, 4)
      else:
        self.layout.addWidget(light, row, col)
    self.layout.addWidget(button, 1, 0, 1, 4)
    self.layout.setSpacing(6)
    for col in range(4):
      self.layout.setColumnStretch(col, 1)
    self.layout.setRowStretch(1, 2)  # the button row takes the extra height
    self.base.setLayout(self.layout)
    self.setCentralWidget(self.base)
    button.multiClick.connect(self._onClick)
    button.multiHold.connect(self._onHold)
    button._holdArmed.connect(self._onArmed)
    button.pressRejected.connect(
        lambda seq: self._onReject(self.rejectPress, seq))
    button.holdTooLong.connect(
        lambda seq: self._onReject(self.rejectTooLong, seq))
    button.moveRegret.connect(
        lambda seq: self._onReject(self.rejectRegret, seq))
    button.buttonMismatch.connect(
        lambda seq: self._onReject(self.rejectMismatch, seq))
    button.initUI()
