"""
SuspensionPanel sets the car's coilovers as it drives (user,
2026-11-13: "Is it possible for the app to have these stiffnesses be
adjustable with a settings window or something?"): the springs front and
rear as the ride they give (Hz: how fast a corner would bob on its own
spring), the damping front and rear (a share of critical: nought rings
on, one just stops), what that makes them in N/m and N s/m, and a
button back to the car as built. A change is told ('changed', the rides
and dampings) a moment after the sliders stop ('SETTLE'), so a drag is
one change. 'setupOf' and 'keptSetup' keep a setup between runs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from ...engineering.gui import QuantitySlider
from .._car import RIDE, RIDE_DAMPING

#  The springs' and the damping's ranges (rides, Hz; shares of
#  critical), and how long after the sliders stop a change is told, ms.
RIDES, DAMPINGS, SETTLE = (1.0, 5.0), (0.2, 1.2), 250
#  Where a setup is kept between runs (gitignored).
SETUP = 'previews/car-setup.json'


def setupOf(path: str) -> tuple:
  """The 'setupOf' function returns the setup kept at 'path' (rides,
  dampings: front, rear each), or the car as built's if none is (or it
  cannot be read)."""
  try:
    with open(path) as file:
      kept = json.load(file)
    return tuple(kept['rides']), tuple(kept['dampings'])
  except (OSError, ValueError, KeyError, TypeError):
    return (RIDE, RIDE), (RIDE_DAMPING, RIDE_DAMPING)


def keptSetup(path: str, rides: tuple, dampings: tuple) -> None:
  """The 'keptSetup' function writes the setup to 'path'."""
  with open(path, 'w') as file:
    json.dump({'rides': list(rides), 'dampings': list(dampings)}, file)


class SuspensionPanel(QWidget):
  """
  SuspensionPanel is a small window of four sliders (springs and
  damping, front and rear), the rates they make ('rated'), and 'As
  built'; 'changed' tells the rides and dampings a moment after a
  change. 'show' it beside the car's window; 'setSetup' sets the
  sliders without telling.
  """

  changed = Signal(tuple, tuple)

  def __init__(self, parent: QWidget = None) -> None:
    QWidget.__init__(self, parent, Qt.WindowType.Tool)
    self.setWindowTitle('Suspension')
    self.rated = None
    self.sliders = []
    layout = QGridLayout()
    for row, (name, low, high, unit, decimals, tip) in enumerate((
            ('Front springs', RIDES[0], RIDES[1], 'Hz', 1,
             'How stiff the front springs are: the ride they give, how '
             'fast a front corner would bob on its own spring'),
            ('Rear springs', RIDES[0], RIDES[1], 'Hz', 1,
             'How stiff the rear springs are, as the ride they give'),
            ('Front damping', DAMPINGS[0], DAMPINGS[1], '', 2,
             'How hard the front dampers hold the springs back: a share '
             'of critical (nought rings on, one just stops)'),
            ('Rear damping', DAMPINGS[0], DAMPINGS[1], '', 2,
             'How hard the rear dampers hold the springs back'))):
      slider = QuantitySlider()
      slider.text = name
      slider.setScale(low, high, unit, decimals)
      slider.setToolTip(tip)
      slider.setMinimumWidth(320)
      slider.quantityChanged.connect(self._moved)
      layout.addWidget(slider, row, 0, 1, 2)
      self.sliders.append(slider)
    self.rates = QLabel('')
    layout.addWidget(self.rates, 4, 0)
    built = QPushButton('As built')
    built.setToolTip('Back to the car as built: %.1f Hz, %.2f of '
                     'critical, front and rear' % (RIDE, RIDE_DAMPING))
    built.clicked.connect(self._asBuilt)
    layout.addWidget(built, 4, 1)
    self.setLayout(layout)
    self.timer = QTimer()
    self.timer.setSingleShot(True)
    self.timer.setInterval(SETTLE)
    self.timer.timeout.connect(self._told)

  @property
  def setup(self, ) -> tuple:
    """The rides and dampings the sliders say (front, rear each)."""
    values = [slider.quantity for slider in self.sliders]
    return (values[0], values[1]), (values[2], values[3])

  def setSetup(self, rides: tuple, dampings: tuple) -> None:
    """The 'setSetup' method sets the sliders, not telling."""
    for slider, value in zip(self.sliders, (*rides, *dampings)):
      slider.blockSignals(True)
      slider.quantity = value
      slider.blockSignals(False)
    self._showRates()

  def setRated(self, rated: object) -> None:
    """The 'setRated' method sets how the rates are worked out: a
    function of the rides and dampings returning (front spring, rear
    spring, front damper, rear damper), N/m and N s/m."""
    self.rated = rated
    self._showRates()

  def _moved(self, _: float) -> None:
    """Shows the rates and tells the change once the sliders stop."""
    self._showRates()
    self.timer.start()

  def _told(self, ) -> None:
    """Tells the change."""
    self.changed.emit(*self.setup)

  def _asBuilt(self, ) -> None:
    """Back to the car as built, told at once."""
    self.setSetup((RIDE, RIDE), (RIDE_DAMPING, RIDE_DAMPING))
    self._told()

  def _showRates(self, ) -> None:
    """Shows what the setup makes the coilovers."""
    if self.rated is None:
      return
    front, rear, frontDamper, rearDamper = self.rated(*self.setup)
    self.rates.setText('springs %.0f / %.0f kN/m,  dampers %.0f / %.0f '
                       'N s/m  (front / rear)' % (
                         front / 1000.0, rear / 1000.0, frontDamper,
                         rearDamper))
