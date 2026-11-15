"""
RingWindow runs the giant hjulleje's outer ring standing upright, held
still, with steel balls in its groove, live: a click pushes whatever it
lands on, square into its surface, as hard as the 'Push' slider says.
RingApp opens it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ...app import App
from ...engineering.gui import QuantitySlider
from .._poke import poked
from .._scenes import RING_GROUND, outerRingWithBalls
from .._vectors import scaled
from .._world import World
from ._readings import readingsOf
from ._view import PhysView

FRAME = 1.0 / 60.0
#  How many balls, and how hard a click pushes at first, N s (a 263 kg
#  ball set going at about 2 m/s).
COUNT = 5
PUSH = 500.0


class RingWindow(QMainWindow):
  """RingWindow runs the outer ring and its balls live."""

  def __init__(self, ) -> None:
    QMainWindow.__init__(self)
    self.setWindowTitle('The outer ring')
    self.world = World((0.0, 0.0, -9.81), 1e-3, RING_GROUND, None, True)
    self.view = PhysView()
    self.view.groundSize, self.view.tiles = 14.0, {'ground': 1.0}
    self.view.target, self.view.distance = (0.0, 0.0, 0.6), 6.0
    self.view.pitch, self.view.yaw = 0.55, 2.6
    self.view.hiddenLegs = {0}
    self.view.poked.connect(self.poke)
    self.status = readingsOf(self)
    self.playButton = QPushButton('Pause')
    self.playButton.clicked.connect(self.togglePlay)
    backButton = QPushButton('Put the balls back')
    backButton.clicked.connect(self.reset)
    self.pushSlider = QuantitySlider()
    self.pushSlider.text = 'Push'
    self.pushSlider.setLogScale(20.0, 5000.0, 'N s', 0)
    self.pushSlider.quantity = PUSH
    self.pushSlider.setToolTip('How hard a click pushes what it lands on')
    row = QHBoxLayout()
    for widget in (self.playButton, backButton, self.pushSlider):
      row.addWidget(widget)
    row.addStretch(1)
    column = QVBoxLayout()
    column.addLayout(row)
    column.addWidget(self.view, 1)
    holder = QWidget()
    holder.setLayout(column)
    self.setCentralWidget(holder)
    self.playing, self.clock, self.pokes = True, 0.0, 0
    self.reset()
    self.timer = QTimer()
    self.timer.setInterval(15)
    self.timer.timeout.connect(self.tick)
    self.timer.start()

  def reset(self, ) -> None:
    """Puts the balls back at the bottom of the groove, still."""
    self.assembly, self.states = outerRingWithBalls(COUNT)
    self.clock = 0.0
    self.view.show_(self.assembly, self.states, 0.2)

  def poke(self, index: int, point: tuple, normal: tuple) -> None:
    """Pushes the body 'index' at 'point', square into its surface, as
    hard as the slider says; the ring is held, so pushing it does
    nothing."""
    if index == 0:
      return
    body, state = self.assembly.bodies[index], self.states[index]
    impulse = scaled(normal, -self.pushSlider.quantity)
    states = list(self.states)
    states[index] = poked(body, state, point, impulse)
    self.states = tuple(states)
    self.pokes += 1
    self.view.show_(self.assembly, self.states, 0.2)

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
    self.status.setText('  %.2f s    %.1f ms a frame of %.1f    click a '
                        'ball to push it along the groove (%d so far)'
                        % (self.clock, 1000.0 * took, 1000.0 * FRAME,
                           self.pokes))
    self.view.show_(self.assembly, self.states, 0.2)


class RingApp(App):
  """RingApp opens a 'RingWindow'."""

  __window_class__ = RingWindow
