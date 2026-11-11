"""
SpringsWindow subclasses 'MainWindow' and is a system of masses on
springs and dampers, set up and set swinging in space.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ....utils import Color
from ....windows import MainWindow
from ...gui import TestStatus, TimeCurve
from .. import Damper, Motion, Point, Spring, SpringMassDamper, System
from . import SceneView, SpringsPanel, SpringsToolBar
from ._springs_panel import counted

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QCloseEvent

#  The energies plotted: the name, the colour and the energy
_ENERGIES = (
  ('moving', Color(152, 195, 121), 'kinetic'),
  ('springs', Color(229, 192, 123), 'elastic'),
  ('height', Color(97, 175, 239), 'gravity'),
  ('heat', Color(224, 108, 117), 'dissipated'),
)
_TOTAL = Color(220, 220, 220)
_AXES = (Color(224, 108, 117), Color(152, 195, 121), Color(97, 175, 239))


class SpringsWindow(MainWindow):
  """
  SpringsWindow subclasses 'MainWindow' and is a system of masses on
  springs and dampers in space: the 'toolBar' above; below it the
  'panel' of the part selected, or of the system and its modes, the
  system in space, 'sceneView', over its energies against time,
  'energyCurve', and the point selected's place against time,
  'traceCurve'; along the bottom the 'status'.

  It opens on an anchor with two masses hanging from it on springs, set
  up. 'Add mass' hangs a mass on a spring under the point selected, or
  the lowest; 'Add anchor' puts an anchor beside it; 'Add component'
  hangs a spring-mass-damper under it, a rod rigid but for its length,
  fixed in direction, then set to turn on a hinge or freely; a point
  may move along any of x, y and z, an anchor none; with two points
  selected, Ctrl and a click, 'Add spring' and 'Add damper' join them,
  the spring at rest as far apart as they are; 'Remove' takes away what
  is selected. A point dragged goes where it is dragged; the panel's
  numbers set the rest. 'Play' sets it moving and says 'Pause' as it
  moves, a point dragged then held by the hand and flung; 'Reset' takes
  it back to how it was set up, to change it. A mode clicked sets it
  swinging in that mode alone, from rest.

  The window moves the system on every 16 ms by as long as has passed,
  at most 50 ms a frame; 'advance' moves it on so long at once.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Springs'
  __start_size__ = 1600, 960
  __frame_ms__ = 16  # between two frames
  __longest_frame__ = 0.05  # s a frame moves the system on at most
  __pluck_reach__ = 0.1  # m the point moving most in a mode is moved
  __new_spring__ = (50.0, 0.5)  # N/m and m: a mass hung on a spring
  __new_damper__ = 2.0  # N s/m
  __new_component__ = (50.0, 1.0, 0.5)  # N/m, N s/m and m

  #  Private Variables
  __frame_clock__: float | None = None

  #  Public Variables
  toolBar = AttriBox[SpringsToolBar](THIS)
  panel = AttriBox[SpringsPanel](THIS)
  sceneView = AttriBox[SceneView](THIS)
  energyCurve = AttriBox[TimeCurve](THIS)
  traceCurve = AttriBox[TimeCurve](THIS)
  status = AttriBox[TestStatus](THIS)
  frameTimer = AttriBox[QTimer](THIS)

  #  Virtual Variables
  system: Field[System] = Field()
  motion: Field[Motion] = Field()
  running: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @system.GET
  def _getSystem(self, ) -> System:
    """The 'system' getter returns the system as set up."""
    return self.sceneView.system

  @motion.GET
  def _getMotion(self, ) -> Motion | None:
    """The 'motion' getter returns the system moving, or 'None' as it is
    set up."""
    return self.sceneView.motion

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the system moves, not
    paused."""
    return True if self.frameTimer.isActive() else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the window out and sizes it."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 3)
    layout.addWidget(self.panel, 1, 0, 2, 1)
    layout.addWidget(self.sceneView, 1, 1, 1, 2)
    layout.addWidget(self.energyCurve, 2, 1)
    layout.addWidget(self.traceCurve, 2, 2)
    layout.addWidget(self.status, 3, 0, 1, 3)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    layout.setColumnStretch(2, 1)
    layout.setRowStretch(1, 3)
    layout.setRowStretch(2, 2)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.sceneView.setFocus()
    self.setSystem(self.sceneView.system)

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons, the edits and the
    timer."""
    bar = self.toolBar
    bar.playButton.clicked.connect(self.togglePlay)
    bar.resetButton.clicked.connect(self.reset)
    bar.massButton.clicked.connect(self.addMass)
    bar.anchorButton.clicked.connect(self.addAnchor)
    bar.componentButton.clicked.connect(self.addComponent)
    bar.springButton.clicked.connect(self.addSpring)
    bar.damperButton.clicked.connect(self.addDamper)
    bar.removeButton.clicked.connect(self.sceneView.removeSelected)
    self.sceneView.systemEdited.connect(self.setSystem)
    self.sceneView.selectionChanged.connect(self.selected)
    self.panel.systemEdited.connect(self.setSystem)
    self.panel.modePlucked.connect(self.pluck)
    self.frameTimer.timeout.connect(self.tick)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)

  def closeEvent(self, event: QCloseEvent) -> None:
    """Closing the window stops the motion."""
    MainWindow.closeEvent(self, event)
    if event.isAccepted():
      self.frameTimer.stop()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setSystem(self, system: System) -> None:
    """The 'setSystem' method shows 'system' as set up."""
    self.sceneView.system = system
    self.refresh()

  def selected(self, part: tuple[str, int] | None) -> None:
    """The 'selected' method shows the part selected in the panel."""
    self.panel.showNote('')
    self.refresh()

  def togglePlay(self, ) -> None:
    """The 'togglePlay' method sets the system moving, from where it is
    set up or where it was paused, or pauses it."""
    if self.running:
      self.frameTimer.stop()
    else:
      if self.motion is None:
        self.sceneView.motion = Motion(self.system)
      self._start()
    self.refresh()

  def reset(self, ) -> None:
    """The 'reset' method stops the motion and shows the system as set
    up, to change it."""
    self.frameTimer.stop()
    self.sceneView.motion = None
    self.refresh()

  def pluck(self, index: int) -> None:
    """The 'pluck' method sets the system swinging in its mode of
    'index' alone: from rest, the point moving most in it moved so far,
    let go."""
    modes = self.system.modes()
    if modes is None:
      return
    _, shapes = modes
    start = self.system.rest() + self.__pluck_reach__ * shapes[index]
    self.sceneView.motion = Motion(self.system, start)
    self._start()
    self.refresh()

  def tick(self, ) -> None:
    """The 'tick' method moves the system on by as long as has passed
    since the last frame, at most so long."""
    now = time.monotonic()
    passed = now - (self.__frame_clock__ or now)
    self.__frame_clock__ = now
    self.advance(min(passed, self.__longest_frame__))

  def advance(self, seconds: float) -> None:
    """The 'advance' method moves the system on 'seconds' and shows
    it."""
    motion = self.motion
    if motion is None:
      return
    motion.advance(seconds)
    self.sceneView.update()
    self._showCurves()
    self.status.showState(*self.statusOf())

  def addMass(self, ) -> None:
    """The 'addMass' method hangs a mass on a spring half a metre under
    the point selected, or the lowest point, selected; under an anchor
    if there is none."""
    if not self.sceneView.editable:
      return
    system = self.system
    if not system.points:
      system = system.withPoints(Point((0.0, 0.0, 2.0), 1.0, ''))
    parent = self._chosenPoint(system)
    x, y, z = system.points[parent].at
    stiffness, rest = self.__new_spring__
    system = system.withPoints(*system.points,
                               Point((x, y, z - rest), 1.0, 'xyz'))
    index = len(system.points) - 1
    system = system.withSprings(*system.springs,
                                Spring(parent, index, stiffness, rest))
    self._edited(system, ('point', index))

  def addAnchor(self, ) -> None:
    """The 'addAnchor' method puts an anchor 0.6 m beside the point
    selected, or the highest point, selected."""
    if not self.sceneView.editable:
      return
    system = self.system
    at = (0.0, 0.0, 2.0)
    if system.points:
      _, highest = max((p.at[2], i) for i, p in enumerate(system.points))
      chosen = self.sceneView.selectedPoints()
      x, y, z = system.points[chosen[-1] if chosen else highest].at
      at = (round(x + 0.6, 2), y, z)
    system = system.withPoints(*system.points, Point(at, 1.0, ''))
    self._edited(system, ('point', len(system.points) - 1))

  def addComponent(self, ) -> None:
    """The 'addComponent' method hangs a spring-mass-damper, fixed in
    its direction, half a metre under the point selected, or the lowest
    point, its mass of a kilogram at its tip, selected; under an anchor
    if there is none."""
    if not self.sceneView.editable:
      return
    system = self.system
    if not system.points:
      system = system.withPoints(Point((0.0, 0.0, 2.0), 1.0, ''))
    base = self._chosenPoint(system)
    x, y, z = system.points[base].at
    stiffness, damping, rest = self.__new_component__
    system = system.withPoints(*system.points,
                               Point((x, y, z - rest), 1.0, 'xyz'))
    tip = len(system.points) - 1
    rod = SpringMassDamper(base, tip, stiffness, damping, rest, 'fixed',
                           (0.0, 1.0, 0.0))
    system = system.withComponents(*system.components, rod)
    self._edited(system, ('component', len(system.components) - 1))

  def addSpring(self, ) -> None:
    """The 'addSpring' method joins the two points selected last by a
    spring, at rest as far apart as they are, selected."""
    pair = self._pair()
    if pair is None:
      return
    system = self.system
    places = system.positions()
    rest = round(float((places[pair[1]] - places[pair[0]]).norm()), 3)
    spring = Spring(*pair, self.__new_spring__[0], rest)
    system = system.withSprings(*system.springs, spring)
    self._edited(system, ('spring', len(system.springs) - 1))

  def addDamper(self, ) -> None:
    """The 'addDamper' method joins the two points selected last by a
    damper, selected."""
    pair = self._pair()
    if pair is None:
      return
    system = self.system
    damper = Damper(*pair, self.__new_damper__)
    system = system.withDampers(*system.dampers, damper)
    self._edited(system, ('damper', len(system.dampers) - 1))

  def refresh(self, ) -> None:
    """The 'refresh' method greys out what cannot be done now, lights
    'Play' while it moves, shows the panel and the curves, and says what
    is going on."""
    bar, view = self.toolBar, self.sceneView
    editable = view.editable
    view.live = self.running
    bar.playButton.text = 'Pause' if self.running else 'Play'
    bar.playButton.checked = self.running
    bar.playButton.setEnabled(True if self.system.points else False)
    bar.resetButton.setEnabled(not editable)
    for button in (bar.massButton, bar.anchorButton,
                   bar.componentButton):
      button.setEnabled(editable)
    joinable = editable and self._pair() is not None
    bar.springButton.setEnabled(joinable)
    bar.damperButton.setEnabled(joinable)
    bar.removeButton.setEnabled(editable and bool(view.selection))
    for button in (bar.playButton, bar.resetButton, bar.massButton,
                   bar.anchorButton, bar.componentButton,
                   bar.springButton, bar.damperButton,
                   bar.removeButton):
      button.update()
    self.panel.showSystem(self.system, view.selection, editable)
    self._showCurves()
    self.status.showState(*self.statusOf())

  def statusOf(self, ) -> tuple[str, str, str]:
    """The 'statusOf' method says what is going on: the state, in words,
    and the details."""
    system, motion = self.system, self.motion
    counts = counted(system)
    if motion is None:
      return 'idle', 'Set up', counts
    energies = motion.energies
    details = 't = %.2f s · energy %.4f J, of which %.4f J heat' % (
      motion.time, energies.total, energies.dissipated)
    if energies.hand:
      details += ' · the hand put in %.4f J' % energies.hand
    if motion.slowed:
      details += ' · slowed: too stiff to keep up'
    if self.running:
      return 'running', 'Moving', details
    return 'paused', 'Paused', details

  def _start(self, ) -> None:
    """Starts the frames."""
    self.__frame_clock__ = None
    self.frameTimer.start(self.__frame_ms__)

  def _edited(self, system: System, part: tuple[str, int]) -> None:
    """Shows 'system' with 'part' selected."""
    self.sceneView.system = system
    self.sceneView.select(part)
    if not self.sceneView.showsAll():
      self.sceneView.fit()
    self.refresh()

  def _chosenPoint(self, system: System) -> int:
    """The point selected last, or else the lowest."""
    chosen = self.sceneView.selectedPoints()
    if chosen and chosen[-1] < len(system.points):
      return chosen[-1]
    _, lowest = min((p.at[2], i) for i, p in enumerate(system.points))
    return lowest

  def _pair(self, ) -> tuple[int, int] | None:
    """The two points selected last, if two are."""
    chosen = self.sceneView.selectedPoints()
    if len(chosen) < 2 or chosen[-1] == chosen[-2]:
      return None
    return chosen[-2], chosen[-1]

  def _showCurves(self, ) -> None:
    """Plots the energies against time, and the place of the point
    selected."""
    motion = self.motion
    samples = self._recent()
    if motion is None:
      self.energyCurve.showSeries('Energy', 'J', (),
                                  'Play to see where the energy goes.')
    else:
      series = [(name, color, [(s.time, getattr(s.energies, key))
                               for s in samples])
                for name, color, key in _ENERGIES]
      series.append(('total', _TOTAL, [(s.time, s.energies.total)
                                       for s in samples]))
      self.energyCurve.showSeries('Energy', 'J', series, '')
    chosen = self.sceneView.selectedPoints()
    if motion is None or not chosen:
      self.traceCurve.showSeries('Where a point is', 'm', (),
                                 'Select a point to follow it.')
      return
    index = chosen[-1]
    rows = [(s.time, s.positions[index].tolist()) for s in samples]
    series = [(axis, color, [(t, row[k]) for t, row in rows])
              for k, (axis, color) in enumerate(zip('xyz', _AXES))]
    self.traceCurve.showSeries('Where P%d is' % (index + 1), 'm', series,
                               '')

  def _recent(self, ) -> list:
    """The motion's samples of the last twenty seconds, and a little
    more."""
    motion = self.motion
    if motion is None:
      return []
    samples = motion.samples
    since = motion.time - 21.0
    first = len(samples)
    while first > 0 and samples[first - 1].time >= since:
      first -= 1
    return [*samples[first:]]
