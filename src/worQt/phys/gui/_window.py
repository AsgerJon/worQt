"""
PhysWindow runs the tower on the hexapod live: a 'PhysView' stepped by
a timer, buttons to play or pause and to hold, heave, surge or roll the
platform, or stack the tower anew (made and laid as by hand, a new
seed each time, turned as far off the axis the platform surges along
and rolls about as the slider beside says). PhysApp opens it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ...app import App
from ...engineering.gui import QuantitySlider
from .._books import Sleep
from .._hexapod import HeldPose, SwayingPose
from .._scenes import TABLE_MIDDLE, towerOnHexapod
from .._vectors import ORIGIN, UNTURNED
from .._world import World
from ._readings import readingsOf
from ._view import PhysView

_MIDDLE = TABLE_MIDDLE
MOTIONS = (('Hold', HeldPose(_MIDDLE)),
           ('Heave', SwayingPose(_MIDDLE, UNTURNED, (0.0, 0.0, 0.004),
                                 ORIGIN, 2.0)),
           ('Surge', SwayingPose(_MIDDLE, UNTURNED, (0.05, 0.0, 0.0), ORIGIN,
                                 2.5)),
           ('Roll', SwayingPose(_MIDDLE, UNTURNED, ORIGIN,
                                (math.radians(10.0), 0.0, 0.0), 1.5)))
FRAME = 1.0 / 60.0
#  How far, degrees, the tower may stand turned off the surge and roll
#  axis (x) either way, and how far it starts.
TURNS = 45.0
TURNED = 20.0


class PhysWindow(QMainWindow):
  """PhysWindow runs the tower on the hexapod live."""

  def __init__(self, ) -> None:
    QMainWindow.__init__(self)
    self.setWindowTitle('Tower on the hexapod')
    self.world = World((0.0, 0.0, -9.81), 1e-3, None, None, True, Sleep())
    self.view = PhysView()
    self.status = readingsOf(self)
    self.playButton = QPushButton('Pause')
    self.playButton.clicked.connect(self.togglePlay)
    stackButton = QPushButton('Stack anew')
    stackButton.clicked.connect(self.stack)
    self.turnSlider = QuantitySlider()
    self.turnSlider.text = 'Tower turned'
    self.turnSlider.setScale(-TURNS, TURNS, '\u00b0', 0)
    self.turnSlider.quantity = TURNED
    self.turnSlider.setToolTip('How far the next stack stands turned off '
                               'the surge and roll axis (0: not at all)')
    row = QHBoxLayout()
    row.addWidget(self.playButton)
    for name, motion in MOTIONS:
      button = QPushButton(name)
      button.clicked.connect(lambda _=None, m=motion: self.move(m))
      row.addWidget(button)
    row.addWidget(stackButton)
    row.addWidget(self.turnSlider)
    row.addStretch(1)
    column = QVBoxLayout()
    column.addLayout(row)
    column.addWidget(self.view, 1)
    holder = QWidget()
    holder.setLayout(column)
    self.setCentralWidget(holder)
    self.playing, self.clock, self.spent = True, 0.0, 0.0
    self.seed, self.heading = 0, 0.0
    self.stack()
    self.timer = QTimer()
    self.timer.setInterval(15)
    self.timer.timeout.connect(self.tick)
    self.timer.start()

  def stack(self, ) -> None:
    """Stacks the tower anew on the held platform, as by hand: no
    two stacks alike; turned off the x axis as the slider says, in
    whole degrees."""
    self.motion, self.seed = MOTIONS[0][1], self.seed + 1
    self.heading = math.radians(round(self.turnSlider.quantity))
    self.assembly, self.states = towerOnHexapod(self.motion, 18, 0.02,
                                                self.seed, self.heading)
    self.clock = 0.0
    floor = len(self.states) - 1
    self.view.floor, self.view.tiles = floor, {0: 0.02, floor: 0.1}
    self.view.show_(self.assembly, self.states, self.world.sleeping.settle)

  def move(self, motion: object) -> None:
    """Moves the platform as 'motion' says, from its start."""
    self.motion, self.clock = motion, 0.0
    self.assembly, _ = towerOnHexapod(motion, 18, 0.02, self.seed,
                                      self.heading)
    self.states = (motion.at(0.0).state(),) + self.states[1:]

  def togglePlay(self, ) -> None:
    """Plays or pauses."""
    self.playing = not self.playing
    self.playButton.setText('Pause' if self.playing else 'Play')

  def tick(self, ) -> None:
    """Steps a frame on and shows it."""
    if not self.playing:
      return
    began = time.perf_counter()
    self.states = self.world.advancedAll(self.assembly, self.states, FRAME,
                                         self.clock)
    self.clock += FRAME
    took = time.perf_counter() - began
    asleep = sum(1 for state in self.states[1:-1]
                 if state.rest >= self.world.sleeping.settle)
    self.status.setText('  stack %d at %+.0f\u00b0    %.2f s    %d of %d '
                        'asleep    %.1fx slower than real time'
                        % (self.seed, math.degrees(self.heading),
                           self.clock, asleep,
                           len(self.states) - 2, took / FRAME))
    self.view.show_(self.assembly, self.states, self.world.sleeping.settle)


class PhysApp(App):
  """PhysApp opens a 'PhysWindow'."""

  __window_class__ = PhysWindow
