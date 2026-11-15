"""
CarWindow drives the car ('carBuilt': four wheels, each on a suspension
of its own, the front ones steered through a column, a rack and tie
rods, the rear two driven through a differential and halfshafts) on the
road, watched from behind, its suspension drawn big and bright
('CarDress'). The steering keys turn a steering wheel
('SteeringWheel': held, a key pushes it its way, as far as 135 degrees;
let go, it comes back to straight), shown on a dial ('WheelDial'); the
hands turn the column to the wheel's share of its lock. The throttle,
the brakes and the handbrake go to the car as the keys say (its own
traction control and anti-lock in 'drive'). The ground is dirt, the
tyres leaving tracks on it ('TyreTracks', drawn by the GPU). The world
is stepped at 'LIVE' fidelity (what Qt can afford: half the steps, the
ground met at the hull's corners; tests and recordings keep 'FULL').
The toggles say whether they are on and are lit while on; the pause
button is lit while paused. W or Up drives, S or Down brakes and,
stopped, backs; A and D, or Left and Right, turn the wheel; Space
pulls the handbrake; a click takes the mouse to steer with (Esc lets
it go), a right drag swings the camera round the car, the mouse wheel
brings it nearer; R sets it up anew, P pauses; the box picks the
ground: the hill track (a hill, a dip, speed humps ahead, washboard
behind, rolling ground), the oval (a mile of concrete, banked 24
degrees in its turns, after a famous one) or flat ground. On the oval
a lap timer ('LapTimer') shows the lap running, the last and the best,
and B hands the car to a robot that races it and learns to go faster
('LearningRacer', its brain kept between runs in 'BRAIN'), a panel
beside showing what it has learnt and its laps this session; stranded
(no way made: rolled over, or stuck), it is set on the start line
again, its brain kept.
'GPU' draws it with the GPU ('GpuView', Qt Quick 3D: depth, smooth
shading, the sun's shadows; on at first) or with Qt's painter
('CarView'); should the GPU's scene not load, the painter takes over and
the status says why. The engine is heard ('EngineSound', its own
process: the gearbox's revolutions and load, as they drive the car; M
or 'Sound' turns it off and on); the status shows the gear and
revolutions. 'Suspension' opens a small window setting the coilovers
as it drives ('SuspensionPanel': springs and damping, front and rear;
kept between runs). CarApp opens the window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMainWindow
from PySide6.QtWidgets import QPushButton, QStackedWidget, QVBoxLayout
from PySide6.QtWidgets import QWidget

from ...app import App
from .._car import CORNERS, STEER_LOCK, TYRE, carBuilt, carWorld, drive
from .._car import chassisPieces, columnPieces, handbrake, knucklePieces
from .._car import carPlaced, ovalWorld, speedOf, steer, steeringOf
from .._car import retuned, toeOf, trackWorld
from .._laps import LapTimer, lapText
from .._robot import BRAIN, LearningRacer, brainOf, keptBrain
from .._steering import WHEEL_LOCK, SteeringWheel
from .._world import LIVE
from .._vectors import rotated
from ._dress import COARSE, FINE, CarDress
from ._engine_sound import EngineSound
from ._readings import readingsOf
from ._tracks import TyreTracks
from ._gpu import GpuView
from ._setup import SETUP, SuspensionPanel, keptSetup, setupOf
from ._toggle import Toggle
from ._view import PhysView
from ._wheel import MOUSE_STEER, MouseHands, WheelDial

#  A frame steps the world on as long as it took since the last, but no
#  less than half of 'FRAME' (s) nor more than two.
FRAME = 1.0 / 60.0
#  How long the car is let settle as it is built, s.
SETTLE = 0.5
#  The road's checker, m, and how far it is drawn about the car, m: flat,
#  and on the track (a metre at a time: its shape drawn).
TILE, GROUND, TRACK_DRAWN = 3.0, 30.0, 16.0
#  The grounds to drive on: each its name, its world (as faithful as a
#  Qt window affords) and where the car is set down on it (or None: as
#  built, at the origin); the hill track first.
GROUNDS = (('Hill track', lambda: trackWorld(LIVE), None),
           ('Oval', lambda: ovalWorld(LIVE), (0.0, 0.0)),
           ('Flat', lambda: carWorld(LIVE), None))
#  How quickly the camera swings round behind the car as it turns, 1/s.
FOLLOW = 3.0
#  How the parts look, by their keys ('chassisPieces', 'knucklePieces',
#  'CarDress'): colour, and, drawn by the GPU, metalness and roughness.
#  The frame dark, so the suspension stands out: blue wishbones, a red
#  spring on a yellow damper, chrome joints and links, black rubber, the
#  wishbones' hinge brackets orange; the tyres' tracks on the dirt, the
#  more they slid the darker (blended, casting no shadow).
PALETTE = {'frame': (QColor(58, 62, 70), 0.3, 0.55),
           'seat': (QColor(140, 32, 30), 0.0, 0.8),
           'engine': (QColor(44, 45, 50), 0.4, 0.6),
           'tank': (QColor(70, 140, 82), 0.0, 0.4),
           'diff': (QColor(150, 155, 165), 0.7, 0.4),
           'shaft': (QColor(170, 175, 185), 0.9, 0.3),
           'knuckle': (QColor(120, 125, 135), 0.6, 0.45),
           'caliper': (QColor(215, 45, 35), 0.1, 0.4),
           'bracket': (QColor(255, 140, 20), 0.2, 0.4),
           'steering': (QColor(60, 62, 66), 0.5, 0.45),
           'spoke': (QColor(195, 200, 208), 0.9, 0.25),
           'grip': (QColor(30, 28, 26), 0.0, 0.7),
           'horn': (QColor(245, 200, 40), 0.1, 0.35),
           'arm': (QColor(40, 110, 225), 0.2, 0.35),
           'spring': (QColor(235, 70, 40), 0.2, 0.35),
           'damper': (QColor(245, 200, 40), 0.1, 0.4),
           'chrome': (QColor(210, 214, 220), 0.95, 0.18),
           'rubber': (QColor(28, 28, 30), 0.0, 0.9),
           'print': (QColor(52, 38, 26, 70), 0.0, 1.0, False),
           'scrub': (QColor(42, 31, 22, 140), 0.0, 1.0, False),
           'skid': (QColor(26, 20, 15, 215), 0.0, 1.0, False)}
#  The dirt's tone where the painter draws it (the GPU draws it from a
#  picture).
_DIRT_TONE = QColor(128, 102, 74)
#  The tones of the steering's parts, the wheels' rims, their tyres'
#  rubber (from the rim's flange out, m), and how they look (metalness,
#  roughness). The rims painted gold (user, 2026-11-13: "give it some
#  rims at a different color than black": as bare steel, metalness
#  0.85, the GPU drew them black, a metal showing what it reflects and
#  the scene having nothing for it to reflect).
_STEERING_TONE = QColor(60, 62, 66)
_RIM_TONE = QColor(206, 164, 62)
_RUBBER_TONE = QColor(36, 36, 40)
_RUBBER_FROM = 0.5 * TYRE.bead + 0.015
_STEERING_LOOK, _RIM_LOOK = (0.2, 0.6), (0.3, 0.35)
#  How a toggle looks: lit green while on, dim while off; the pause
#  button lit amber while paused.
_PAUSE_STYLE = ('QPushButton { padding: 4px 12px; border-radius: 4px; } '
                'QPushButton:checked { background: #d08a1c; '
                'border: 1px solid #f0b050; color: black; }')
#  How the lap timer looks: big, fixed-width figures on a dark panel.
_LAP_STYLE = ('QLabel { background: #1e2125; color: #ebeef2; '
              'border-radius: 6px; padding: 8px 14px; '
              'font-family: monospace; font-size: 15pt; }')
#  How the robot's panel looks: the lap timer's, smaller.
_ROBOT_STYLE = _LAP_STYLE.replace('15pt', '11pt')
#  How many of the robot's laps its panel shows, the last.
_ROBOT_LAPS = 5
_KEYS = ('W/Up drive, S/Down brake (stopped: back), A/D or Left/Right '
         'steer; click the view to steer with the mouse (Esc lets go); '
         'Space handbrake, R anew, P pause, B robot (on the oval), M '
         'sound; right drag to look round the car, wheel nearer')
#  How loud the engine plays (0 to 1), and the recording it plays (user,
#  2026-11-13: "found a royalty free engine sound"; gitignored: without
#  it, the engine made from what it does).
_VOLUME, ENGINE_RECORDING = 0.8, 'previews/v12_engine_sound.mp3'


class CarView(PhysView):
  """CarView watches the car from behind it: the keys held ('keys'); a
  left click takes the mouse to steer with ('hands', 'MouseHands'; Esc
  lets it go); a right drag swings the camera 'around' the car (rad
  from straight behind) and up or down, the mouse wheel brings it
  nearer."""

  def __init__(self, ) -> None:
    PhysView.__init__(self)
    self.keys, self.around, self.heading = set(), 0.0, None
    self.distance, self.pitch = 6.5, 0.28
    self.hands = MouseHands(self)
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.setMouseTracking(True)

  def follow(self, place: tuple, heading: float, seconds: float) -> None:
    """Puts the camera behind the car at 'place' heading 'heading' (rad),
    swinging round after it as it turns over 'seconds', and the road
    drawn about it (its checker fixed to the road)."""
    if self.heading is None:
      self.heading = heading
    turn = (heading - self.heading + math.pi) % (2.0 * math.pi) - math.pi
    self.heading += turn * min(1.0, FOLLOW * seconds)
    self.yaw = self.heading + math.pi + self.around
    self.target = (place[0], place[1], place[2] + 0.4)
    self.groundMiddle = (TILE * round(place[0] / TILE),
                         TILE * round(place[1] / TILE))

  def keyPressEvent(self, event: object) -> None:
    """Notes a key held; Esc lets the mouse go."""
    if event.key() == Qt.Key.Key_Escape:
      self.hands.letGo()
    elif not event.isAutoRepeat():
      self.keys.add(event.key())

  def keyReleaseEvent(self, event: object) -> None:
    """Notes a key let go."""
    if not event.isAutoRepeat():
      self.keys.discard(event.key())

  def focusOutEvent(self, event: object) -> None:
    """Lets every key and the mouse go (they would be held for ever)."""
    self.keys.clear()
    self.hands.letGo()
    PhysView.focusOutEvent(self, event)

  def leaveEvent(self, event: object) -> None:
    """Forgets where the pointer was (coming back in steers nothing)."""
    self.hands.forget()
    PhysView.leaveEvent(self, event)

  def mousePressEvent(self, event: object) -> None:
    """A left click takes the mouse to steer with; a right one starts a
    drag to look round (not while the mouse steers)."""
    event.accept()
    if self.hands.taken:
      return
    if event.button() == Qt.MouseButton.LeftButton:
      self.setFocus()
      self.hands.take()
      return
    self.grabbed = event.position()

  def mouseMoveEvent(self, event: object) -> None:
    """Steers while the mouse is taken; else swings the camera round the
    car and up or down as the pointer drags."""
    if self.hands.taken:
      self.hands.movedTo(event.globalPosition(), event.position())
      return
    if self.grabbed is None:
      return
    moved = event.position() - self.grabbed
    self.grabbed = event.position()
    self.dragged = True
    self.around -= 0.01 * moved.x()
    self.pitch = min(1.4, max(0.02, self.pitch + 0.01 * moved.y()))

  def mouseReleaseEvent(self, event: object) -> None:
    """Lets the view go (a click pokes nothing here)."""
    self.grabbed = None


class CarWindow(QMainWindow):
  """CarWindow drives the car live."""

  def __init__(self, ) -> None:
    QMainWindow.__init__(self)
    self.setWindowTitle('The car')
    self.painter, self.gpu = CarView(), GpuView()
    self.stack = QStackedWidget()
    self.stack.addWidget(self.gpu)
    self.stack.addWidget(self.painter)
    self.status = readingsOf(self)
    self.playButton = QPushButton('Pause (P)')
    self.playButton.setCheckable(True)
    self.playButton.setStyleSheet(_PAUSE_STYLE)
    self.playButton.clicked.connect(self.togglePlay)
    backButton = QPushButton('Set it up anew (R)')
    backButton.clicked.connect(self.reset)
    self.groundBox = QComboBox()
    for name, _, _ in GROUNDS:
      self.groundBox.addItem(name)
    self.groundBox.setToolTip('Where to drive: the hill track (a hill, a '
                              'dip, humps, washboard), the oval (a mile, '
                              'banked 24 degrees in its turns) or flat '
                              'ground')
    self.groundBox.currentIndexChanged.connect(self.reset)
    self.gpuButton = Toggle('GPU', "Drawn by the GPU (Qt Quick 3D), or by "
                                   "Qt's painter", True)
    self.gpuButton.clicked.connect(self._chooseView)
    self.robotButton = Toggle('Robot driver (B)', 'On the oval: a robot '
                              'races it and learns, lap by lap, to go '
                              'faster (its column and pedals only)',
                              False)
    self.robotButton.clicked.connect(self._chooseRobot)
    self.soundButton = Toggle('Sound (M)', "The engine's sound (its own "
                              'process: the revolutions and load the '
                              'gearbox drives with)', True)
    self.soundButton.clicked.connect(self._chooseSound)
    self.engineSound = EngineSound()
    self.rides, self.dampings = setupOf(SETUP)
    self.panel = SuspensionPanel(self)
    self.panel.setRated(self._ratesOf)
    self.panel.setSetup(self.rides, self.dampings)
    self.panel.changed.connect(self._retuned)
    setupButton = QPushButton('Suspension')
    setupButton.setToolTip('Springs and damping, front and rear, set as '
                           'it drives')
    setupButton.clicked.connect(self._showPanel)
    self.dial = WheelDial()
    self.lapLabel = QLabel('')
    self.lapLabel.setStyleSheet(_LAP_STYLE)
    self.robotLabel = QLabel('')
    self.robotLabel.setStyleSheet(_ROBOT_STYLE)
    keys = QLabel(_KEYS)
    keys.setWordWrap(True)
    row = QHBoxLayout()
    for widget in (self.playButton, backButton, self.groundBox,
                   self.gpuButton, self.robotButton, self.soundButton,
                   setupButton):
      widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
      row.addWidget(widget)
    row.addStretch(1)
    column = QVBoxLayout()
    column.addLayout(row)
    column.addWidget(self.stack, 1)
    bottom = QHBoxLayout()
    bottom.addWidget(self.dial)
    bottom.addWidget(self.lapLabel)
    bottom.addWidget(self.robotLabel)
    bottom.addWidget(keys, 1)
    column.addLayout(bottom)
    holder = QWidget()
    holder.setLayout(column)
    self.setCentralWidget(holder)
    self.playing, self.fallen = True, ''
    self.lastTick = time.perf_counter()
    self.robot, self.robotTimes, self.rescues = None, [], 0
    self.robotApron, self.laps, self.lapsGround = 0.0, [], None
    self.reset()
    self._chooseView()
    self._chooseSound()
    self.timer = QTimer()
    self.timer.setInterval(15)
    self.timer.timeout.connect(self.tick)
    self.timer.start()

  def reset(self, ) -> None:
    """Sets the car up anew, standing still, steering straight, on the
    ground the box says (set down where that ground starts); the robot
    anew from its brain (kept first, should it be driving); the laps
    done kept (forgotten on another ground)."""
    name, world, start = GROUNDS[self.groundBox.currentIndex()]
    self.world = world()
    onTrack = self.world.ground.terrain is not None
    self.car = retuned(carBuilt(SETTLE, LIVE), self.rides, self.dampings)
    self.states, self.clock = self.car.states, 0.0
    self.wheel = SteeringWheel()
    self.dial.setAngle(0.0)
    if self.robot is not None and self.robotDriving:
      keptBrain(self.robot, BRAIN)
    self.robot = LearningRacer(self.car, brainOf(BRAIN))
    self.lapsSeen = 0
    if name != self.lapsGround:
      self.laps, self.lapsGround = [], name
    self.robotButton.setEnabled(name == 'Oval')
    self.lapTimer, self.robotApron = LapTimer(0.0), 0.0
    self.lapLabel.setVisible(name == 'Oval')
    self.robotLabel.setVisible(name == 'Oval')
    self._showLaps()
    if name != 'Oval':
      self.robotButton.setChecked(False)
    if start is not None:
      terrain = self.world.ground.terrain
      self.states = carPlaced(self.states, (start[0], start[1],
                                            terrain.heightAt(*start)),
                              terrain.normalAt(*start))
    car = self.car
    tones = {car.rack: _STEERING_TONE}
    looks = {car.rack: _STEERING_LOOK}
    pieces = {car.chassis: chassisPieces(), car.column: columnPieces()}
    for knuckle, (_, side) in zip(car.knuckles, CORNERS):
      pieces[knuckle] = knucklePieces(side)
    bands = {}
    for wheel in car.wheels:
      tones[wheel], looks[wheel] = _RIM_TONE, _RIM_LOOK
      bands[wheel] = (_RUBBER_FROM, _RUBBER_TONE)
    for view in (self.painter, self.gpu):
      view.tones, view.bands = dict(tones), dict(bands)
      view.pieces = dict(pieces)
      view.terrain = self.world.ground.terrain
      view.wall = self.world.ground.wall
      view.heading = None
      view.tiles = {'ground': TILE}
    self.gpu.oval = name == 'Oval'
    self.painter.groundSize = TRACK_DRAWN if onTrack else GROUND
    colours = {key: look[0] for key, look in PALETTE.items()}
    self.painter.palette = colours
    self.painter.skins = [(CarDress(car, COARSE), colours)]
    self.painter.groundTone = _DIRT_TONE
    self.tracks = TyreTracks(car, self.world.ground)
    self.gpu.looks, self.gpu.palette = looks, dict(PALETTE)
    self.gpu.dresses = [CarDress(car, FINE), self.tracks]
    self.gpu.regrounded()
    self._showNow(FRAME)

  @property
  def view(self, ) -> PhysView | GpuView:
    """The view shown: the GPU's or the painter's."""
    return self.stack.currentWidget()

  def _chooseView(self, ) -> None:
    """Shows the view 'GPU' says, its camera where the other's was, the
    keys given to it."""
    gpu = self.gpuButton.isChecked() and not self.fallen
    shown, hidden = (self.gpu, self.painter) if gpu else (self.painter,
                                                         self.gpu)
    shown.around, shown.pitch = hidden.around, hidden.pitch
    shown.distance, shown.heading = hidden.distance, hidden.heading
    hidden.keys.clear()
    hidden.hands.letGo()
    self.stack.setCurrentWidget(shown)
    if gpu:
      self.gpu.box.setFocus()
    else:
      self.painter.setFocus()
    self._showNow(FRAME)

  @property
  def robotDriving(self, ) -> bool:
    """Whether the robot drives (on the oval, its toggle on)."""
    return self.robotButton.isEnabled() and self.robotButton.isChecked()

  def _chooseRobot(self, ) -> None:
    """Hands the column to the robot, or back to the wheel, where it
    is (the robot's brain kept)."""
    if self.robotDriving:
      self.robot.column = self.wheel.column
    else:
      self.wheel.angle = self.robot.column * WHEEL_LOCK / STEER_LOCK
      keptBrain(self.robot, BRAIN)

  def togglePlay(self, ) -> None:
    """Pauses or plays, the button lit and saying so while paused."""
    self.playing = not self.playing
    self.playButton.setChecked(not self.playing)
    self.playButton.setText('Paused (P)' if not self.playing
                            else 'Pause (P)')

  def tick(self, ) -> None:
    """Reads the keys, turns the wheel (the hands turning the column
    after it), sets the motors, steps the world on
    as long as passed since the last frame (within reason) and shows
    it."""
    began = time.perf_counter()
    passed, self.lastTick = began - self.lastTick, began
    self._watchGpu()
    keys = self.view.keys
    if Qt.Key.Key_R in keys:
      keys.discard(Qt.Key.Key_R)
      self.reset()
    if Qt.Key.Key_P in keys:
      keys.discard(Qt.Key.Key_P)
      self.togglePlay()
    if Qt.Key.Key_B in keys:
      keys.discard(Qt.Key.Key_B)
      if self.robotButton.isEnabled():
        self.robotButton.toggle()
        self._chooseRobot()
    if Qt.Key.Key_M in keys:
      keys.discard(Qt.Key.Key_M)
      self.soundButton.toggle()
      self._chooseSound()
    gearbox = self.car.gearbox
    if not self.playing:
      self.engineSound.heard(gearbox.rpm, 0.0, 0.0)
      self.status.setText('  paused')
      return
    seconds = min(max(passed, 0.5 * FRAME), 2.0 * FRAME)
    pulled = Qt.Key.Key_Space in keys
    if self.robotDriving:
      self.robot.take(self.states, seconds)
      throttle = self.robot.throttle
      self.dial.setAngle(self.robot.column * WHEEL_LOCK / STEER_LOCK)
    else:
      throttle = self._throttle(keys)
      self._steer(keys, seconds)
      self.dial.setAngle(self.wheel.angle)
      steer(self.car, self.wheel.column)
      drive(self.car, self.states, throttle, seconds)
    handbrake(self.car, pulled)
    self.engineSound.heard(gearbox.rpm, gearbox.load, _VOLUME
                           if self.soundButton.isChecked() else 0.0)
    self.states = self.world.advancedAll(self.car.assembly, self.states,
                                         seconds, self.clock)
    self.tracks.update(self.states)
    place = self.states[self.car.chassis].place
    self.lapTimer.seen(place[0], place[1], self.clock + seconds)
    if len(self.lapTimer.laps) > self.lapsSeen:
      self.lapsSeen = len(self.lapTimer.laps)
      self.laps.append(self.lapTimer.last)
      if self.robotDriving:
        self.robotTimes.append((self.lapTimer.last, self.robotApron))
        self.robotApron = 0.0
        keptBrain(self.robot, BRAIN)
    if self.robotDriving and self.robot.onApron(self.states):
      self.robotApron += seconds
    if self.robotDriving and self.robot.stranded:
      self.rescues += 1
      self.robot.gaveUp()
      self.reset()
      return
    self.clock += seconds
    took = time.perf_counter() - began
    self._showNow(seconds)
    self._showLaps()
    states = self.states
    toes = (math.degrees(toeOf(self.car, states, 0)),
            math.degrees(toeOf(self.car, states, 1)))
    self.status.setText(
      '  %.1f s    %.0f frames a second, physics %.1f ms    %.0f km/h, '
      'gear %d, %.0f rpm    column %+.0f deg, wheels %+.1f %+.1f deg    %s'
      % (self.clock, 1.0 / max(passed, 1e-3), 1000.0 * took,
         3.6 * speedOf(self.car, states), gearbox.gear, gearbox.rpm,
         math.degrees(steeringOf(self.car, states)), toes[0], toes[1],
         'drive' if throttle > 0.0 else 'brake' if throttle < 0.0
         else 'coast') + self._robotNow() + self._soundNow()
      + self._gpuNow())

  def _showLaps(self, ) -> None:
    """Shows the lap timer (the lap running and its time, the last and
    the best of the laps done on this ground, set up anew or not) and
    the robot's panel (how far it has learnt, how often it was set back
    on the start line, its last laps this session and how long a wheel
    was on the apron in each)."""
    laps = self.laps
    self.lapLabel.setText('LAP %d  %s\nlast %s  best %s' % (
      len(laps) + 1, lapText(self.lapTimer.now(self.clock)),
      lapText(laps[-1] if laps else None),
      lapText(min(laps) if laps else None)))
    robot, laps = self.robot, self.robotTimes[-_ROBOT_LAPS:]
    pace = 100.0 * (robot.paceLearnt - 1.0)
    self.robotLabel.setText(
      'ROBOT %s  pace %+.1f %%  rescued %d\nlaps  %s\napron %s' % (
        'driving' if self.robotDriving else 'off (B)', pace, self.rescues,
        ''.join('%8s' % lapText(took) for took, _ in laps) or '  -',
        ''.join('%7.1fs' % apron for _, apron in laps) or '  -'))

  def _watchGpu(self, ) -> None:
    """Hands the view to the painter should the GPU's scene not load."""
    if self.view is self.gpu and self.gpu.problems and not self.fallen:
      self.fallen = self.gpu.problems[0]
      print('GPU view failed: %s' % '\n'.join(self.gpu.problems))
      self._chooseView()

  def _robotNow(self, ) -> str:
    """Returns how the robot is doing, for the status (nothing unless
    it drives)."""
    if not self.robotDriving:
      return ''
    robot = self.robot
    pace = 100.0 * (robot.paceLearnt - 1.0)
    doing = ('braking' if robot.throttle < 0.0 else 'lifting'
             if robot.throttle < 0.95 else 'flat out')
    return ('    robot learning (%d passes, pace %+.1f %%): %.1f m off its '
            'line, %s' % (robot.learnt, pace, robot.off, doing))

  def _showPanel(self, ) -> None:
    """Shows the suspension's window beside this one."""
    self.panel.show()
    self.panel.raise_()

  def _retuned(self, rides: tuple, dampings: tuple) -> None:
    """Sets the coilovers anew as the car drives (and keeps the setup):
    the car where it is, its springs and dampers as told."""
    self.rides, self.dampings = tuple(rides), tuple(dampings)
    keptSetup(SETUP, self.rides, self.dampings)
    self.car = retuned(carBuilt(SETTLE, LIVE), self.rides, self.dampings)
    self.robot.car = self.car

  def _ratesOf(self, rides: tuple, dampings: tuple) -> tuple:
    """Returns what 'rides' and 'dampings' make the front's and the
    rear's spring, N/m, and damper, N s/m (along the coilover)."""
    car = retuned(carBuilt(SETTLE, LIVE), rides, dampings)
    front, rear = (car.assembly.connections[car.links.coilovers[k]]
                   for k in (0, 2))
    return front.stiffness, rear.stiffness, front.damping, rear.damping

  def _chooseSound(self, ) -> None:
    """Starts the engine's sound, or ends it, as 'Sound' says."""
    if self.soundButton.isChecked():
      self.engineSound.start(ENGINE_RECORDING
                             if os.path.exists(ENGINE_RECORDING) else None)
    else:
      self.engineSound.close()

  def _soundNow(self, ) -> str:
    """Returns what went wrong with the sound, for the status (nothing
    while it plays, or is off)."""
    sound = self.engineSound
    if not self.soundButton.isChecked():
      return ''
    if sound.trouble:
      return '    no sound: %s' % sound.trouble[:60]
    if not sound.running:
      return '    no sound: its process ended'
    return '' if sound.ready else '    sound starting'

  def closeEvent(self, event: object) -> None:
    """Ends the engine's sound with the window."""
    self.engineSound.close()
    QMainWindow.closeEvent(self, event)

  def _gpuNow(self, ) -> str:
    """Returns how the GPU's view is doing, for the status: loading (and
    for how long: the first time Qt Quick 3D builds its shaders), or why
    the painter took over; nothing once it draws."""
    if self.fallen:
      return '    GPU view failed, painting instead: %s' % self.fallen[:80]
    gpu = self.gpu
    if self.view is gpu and not gpu.drawn:
      return ('    3D view loading, %.0f s (the first time, Qt Quick 3D '
              'builds its shaders)' % gpu.loadingFor())
    return ''

  def _steer(self, keys: set, seconds: float) -> None:
    """Turns the wheel as the hands on it do: the mouse, while taken,
    turns it where it is and it stays ('MOUSE_STEER' a px), the keys
    pushing it too; else the keys alone, letting it come back."""
    hands = self.view.hands
    steering = self._steeringKey(keys)
    moved = hands.steered()
    self.dial.setMouse(hands.taken)
    if not hands.taken:
      self.wheel.turned(steering, seconds)
      return
    if steering:
      self.wheel.turned(steering, seconds)
    self.wheel.moved(-MOUSE_STEER * moved)

  def _steeringKey(self, keys: set) -> int:
    """Returns which way the steering keys ask: left 1, right -1, else
    (neither, or both) nought."""
    left = Qt.Key.Key_A in keys or Qt.Key.Key_Left in keys
    right = Qt.Key.Key_D in keys or Qt.Key.Key_Right in keys
    return int(left) - int(right)

  def _throttle(self, keys: set) -> float:
    """Returns the throttle the keys ask: forward 1, back -1, else
    nought."""
    if Qt.Key.Key_W in keys or Qt.Key.Key_Up in keys:
      return 1.0
    if Qt.Key.Key_S in keys or Qt.Key.Key_Down in keys:
      return -1.0
    return 0.0

  def _showNow(self, seconds: float) -> None:
    """Shows the car where it is, the camera behind it."""
    chassis = self.states[self.car.chassis]
    ahead = rotated(chassis.turn, (1.0, 0.0, 0.0))
    self.view.follow(chassis.place, math.atan2(ahead[1], ahead[0]),
                     seconds)
    self.view.show_(self.car.assembly, self.states, 0.2)


class CarApp(App):
  """CarApp opens a 'CarWindow'."""

  __window_class__ = CarWindow
