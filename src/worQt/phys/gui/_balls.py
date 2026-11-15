"""
BallsWindow runs steel balls on the ground with an oak prism launched
across them, live: a click pushes whatever it lands on, square into
its surface, as hard as the 'Push' slider says. BallsApp opens it.
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
from .._books import Sleep
from .._poke import poked
from .._scenes import BALL_GROUND, ballsUnderPrism, prismLaunched
from .._vectors import scaled
from .._world import World
from ._readings import readingsOf
from ._view import PhysView

FRAME = 1.0 / 60.0
#  How many balls, and how hard a click pushes at first, N s.
COUNT = 18
PUSH = 2.0


class BallsWindow(QMainWindow):
  """BallsWindow runs the balls and the prism live."""

  def __init__(self, ) -> None:
    QMainWindow.__init__(self)
    self.setWindowTitle('Balls and a prism')
    self.world = World((0.0, 0.0, -9.81), 1e-3, BALL_GROUND, None, True,
                       Sleep())
    self.view = PhysView()
    self.view.groundSize, self.view.tiles = 1.2, {'ground': 0.1}
    self.view.target, self.view.distance = (0.0, 0.0, 0.05), 1.7
    self.view.pitch, self.view.yaw = 0.62, -1.1
    self.view.poked.connect(self.poke)
    self.status = readingsOf(self)
    self.playButton = QPushButton('Pause')
    self.playButton.clicked.connect(self.togglePlay)
    launchButton = QPushButton('Launch the prism')
    launchButton.clicked.connect(self.launch)
    scatterButton = QPushButton('Scatter anew')
    scatterButton.clicked.connect(self.scatter)
    self.pushSlider = QuantitySlider()
    self.pushSlider.text = 'Push'
    self.pushSlider.setLogScale(0.2, 20.0, 'N s', 1)
    self.pushSlider.quantity = PUSH
    self.pushSlider.setToolTip('How hard a click pushes what it lands on')
    row = QHBoxLayout()
    for widget in (self.playButton, launchButton, scatterButton,
                   self.pushSlider):
      row.addWidget(widget)
    row.addStretch(1)
    column = QVBoxLayout()
    column.addLayout(row)
    column.addWidget(self.view, 1)
    holder = QWidget()
    holder.setLayout(column)
    self.setCentralWidget(holder)
    self.playing, self.clock, self.seed, self.pokes = True, 0.0, 0, 0
    self.scatter()
    self.timer = QTimer()
    self.timer.setInterval(15)
    self.timer.timeout.connect(self.tick)
    self.timer.start()

  def scatter(self, ) -> None:
    """Scatters the balls anew and launches the prism across them."""
    self.seed += 1
    self.assembly, self.states = ballsUnderPrism(COUNT, self.seed)
    self.clock = 0.0
    self.view.show_(self.assembly, self.states, self.world.sleeping.settle)

  def launch(self, ) -> None:
    """Launches the prism across the balls again, as they lie."""
    self.states = self.states[:-1] + (prismLaunched(),)
    self.view.show_(self.assembly, self.states, self.world.sleeping.settle)

  def poke(self, index: int, point: tuple, normal: tuple) -> None:
    """Pushes the body 'index' at 'point', square into its surface
    (against its outward 'normal'), as hard as the slider says."""
    body, state = self.assembly.bodies[index], self.states[index]
    impulse = scaled(normal, -self.pushSlider.quantity)
    states = list(self.states)
    states[index] = poked(body, state, point, impulse)
    self.states = tuple(states)
    self.pokes += 1
    self.view.show_(self.assembly, self.states, self.world.sleeping.settle)

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
    asleep = sum(1 for state in self.states
                 if state.rest >= self.world.sleeping.settle)
    self.status.setText('  scatter %d    %.2f s    %d of %d asleep    '
                        '%.1f ms a frame of %.1f    click a ball or the '
                        'prism to push it (%d so far)'
                        % (self.seed, self.clock, asleep, len(self.states),
                           1000.0 * took, 1000.0 * FRAME, self.pokes))
    self.view.show_(self.assembly, self.states, self.world.sleeping.settle)


class BallsApp(App):
  """BallsApp opens a 'BallsWindow'."""

  __window_class__ = BallsWindow
