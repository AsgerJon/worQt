"""
TunePanel is the tune-up menu (user, 2026-11-14: "a tune-up menu where
the tire pressure of each wheel can be adjusted. Along with camber,
toe"; then "do the tune-up menu"): a small window of each wheel's tyre
pressure, camber and toe ('_rig.WheelSetup'), 'As built', telling the
setups a moment after the sliders stop ('changed'), for the window to
set its car (now the tyre rig's corner) up anew with them, as a
mechanic sets a car up stopped.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from ...engineering.gui import QuantitySlider
from .._rig import WheelSetup

#  The sliders' ranges: tyre pressure, bar; camber, degrees (top out
#  positive); toe, degrees (front in positive); how long after the last
#  move the setups are told, ms (a rebuild each: not while dragging).
PRESSURES, CAMBERS, TOES = (1.5, 3.5), (-4.0, 2.0), (-1.0, 1.0)
SETTLE = 400


class TunePanel(QWidget):
  """
  TunePanel is a small window of each wheel's tune-up, its wheels named
  'names' (the car's corners, kept as 'names'; the rig's one): for
  each its tyre's
  pressure (bar), its camber and its toe (degrees), and 'As built';
  'changed' tells the setups (a tuple of 'WheelSetup', in the wheels'
  order) a moment after a change; 'setSetups' sets the sliders without
  telling.
  """

  changed = Signal(tuple)

  def __init__(self, names: tuple, parent: QWidget = None) -> None:
    QWidget.__init__(self, parent, Qt.WindowType.Tool)
    self.setWindowTitle('Tune-up')
    self.names, self.sliders = tuple(names), []
    layout = QGridLayout()
    for column, name in enumerate(names):
      layout.addWidget(QLabel(name), 0, column)
      row = []
      for at, (text, (low, high), unit, decimals, tip) in enumerate((
              ('Pressure', PRESSURES, 'bar', 2,
               'The tyre\'s air over the outside\'s: how stiff it stands '
               'on the road'),
              ('Camber', CAMBERS, '°', 1,
               'How far the wheel\'s top leans out (in: below nought), '
               'set by shims at the upper wishbone\'s pivots'),
              ('Toe', TOES, '°', 2,
               'How far the wheel\'s front turns in toward the car\'s '
               'middle (out: below nought), set by the tie rod\'s '
               'length'))):
        slider = QuantitySlider()
        slider.text = text
        slider.setScale(low, high, unit, decimals)
        slider.setToolTip(tip)
        slider.setMinimumWidth(280)
        slider.quantityChanged.connect(self._moved)
        layout.addWidget(slider, 1 + at, column)
        row.append(slider)
      self.sliders.append(row)
    built = QPushButton('As built')
    built.setToolTip('Every wheel back as built: 2.30 bar, no camber, '
                     'no toe')
    built.clicked.connect(self._asBuilt)
    layout.addWidget(built, 4, 0)
    self.setLayout(layout)
    self.timer = QTimer()
    self.timer.setSingleShot(True)
    self.timer.setInterval(SETTLE)
    self.timer.timeout.connect(self._told)
    self.setSetups(tuple(WheelSetup() for _ in names))

  @property
  def setups(self, ) -> tuple:
    """The wheels' setups the sliders say."""
    return tuple(WheelSetup(1e5 * row[0].quantity,
                            math.radians(row[1].quantity),
                            math.radians(row[2].quantity))
                 for row in self.sliders)

  def setSetups(self, setups: tuple) -> None:
    """The 'setSetups' method sets the sliders to 'setups', not
    telling."""
    for row, setup in zip(self.sliders, setups):
      for slider, value in zip(row, (setup.pressure / 1e5,
                                     math.degrees(setup.camber),
                                     math.degrees(setup.toe))):
        slider.blockSignals(True)
        slider.quantity = value
        slider.blockSignals(False)

  def _moved(self, _: float) -> None:
    """Tells the change once the sliders stop."""
    self.timer.start()

  def _told(self, ) -> None:
    """Tells the change."""
    self.changed.emit(self.setups)

  def _asBuilt(self, ) -> None:
    """Every wheel back as built, told at once."""
    self.setSetups(tuple(WheelSetup() for _ in self.sliders))
    self._told()
