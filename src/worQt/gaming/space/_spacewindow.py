"""
SpaceWindow flies the creative rocket (user, 2026-11-16: "let's start
with a 'creative' rocket with inf fuel"): the keys and the mouse, time
and its warp, the ascent guidance, the flight each frame, the flight
view with its artificial horizon and control board, or the map.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import threading
import time
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtWidgets import QMainWindow

from worQt.gaming.sandbox._pointer import Pointer

from ._ascentguidance import AscentGuidance
from ._chasecamera import ChaseCamera
from ._navball import Navball
from ._orrery import Orrery, lengthText, timeText
from ._planets import PAD, julianOf, solarSystemOn
from ._scenery import Scenery
from ._spaceviewport import SpaceViewport
from ._timekeeper import Timekeeper
from ._turns import dot, norm, unit
from ._vessel import Vessel

#  A frame, ms; the longest step a frame takes, s.
TICK = 16
LONGEST_REAL = 0.1
#  The throttle's keys: how fast Shift and Ctrl open and close it, a s.
THROTTLE_RATE = 0.6
#  The aim's keys (user, 2026-11-16: "roll-insensitive controls that
#  work only in the parallel of travel"): W S up and down over the
#  horizon, D A right and left off the path; a tap moves it 'AIM_STEP',
#  held past 'REPEAT_AFTER' s it moves on 'AIM_RATE' a s (rad).
AIMING = {Qt.Key.Key_W: (1.0, 0.0), Qt.Key.Key_S: (-1.0, 0.0),
          Qt.Key.Key_D: (0.0, 1.0), Qt.Key.Key_A: (0.0, -1.0)}
AIM_STEP = math.radians(5.0)
AIM_RATE = math.radians(20.0)
REPEAT_AFTER = 0.35
#  Q E roll the vessel about its nose, the wheels straight.
ROLLING = {Qt.Key.Key_Q: 1.0, Qt.Key.Key_E: -1.0}
#  Warping to the apoapsis stops this long before it, s.
APOAPSIS_LEAD = 30.0
#  A note on screen stays this long, s; a key tapped shows lit this
#  long, s.
NOTE_LASTS = 3.0
FLASH = 0.25
#  A click on the map picks the mark within this many pixels.
PICKED = 22.0
#  The artificial horizon's radius, pixels (the scene's 'navRadius').
NAV_RADIUS = 104.0
#  The keys as their caps on the board name them.
CAPS = {Qt.Key.Key_Shift: 'Shift', Qt.Key.Key_Control: 'Ctrl',
        Qt.Key.Key_Z: 'Z', Qt.Key.Key_X: 'X', Qt.Key.Key_T: 'T',
        Qt.Key.Key_F: 'F', Qt.Key.Key_R: 'R', Qt.Key.Key_W: 'W',
        Qt.Key.Key_S: 'S', Qt.Key.Key_A: 'A', Qt.Key.Key_D: 'D',
        Qt.Key.Key_Q: 'Q', Qt.Key.Key_E: 'E', Qt.Key.Key_Comma: ',',
        Qt.Key.Key_Period: '.', Qt.Key.Key_Slash: '/', Qt.Key.Key_G: 'G',
        Qt.Key.Key_J: 'J', Qt.Key.Key_BracketLeft: '[',
        Qt.Key.Key_BracketRight: ']', Qt.Key.Key_M: 'M',
        Qt.Key.Key_Backspace: '⌫'}
#  A click on a lamp of the board does what its key does.
ACTIONS = {'full': Qt.Key.Key_Z, 'cut': Qt.Key.Key_X,
           'hold': Qt.Key.Key_T, 'prograde': Qt.Key.Key_F,
           'retrograde': Qt.Key.Key_R, 'faster': Qt.Key.Key_Period,
           'stop': Qt.Key.Key_Slash, 'toAp': Qt.Key.Key_G,
           'ascent': Qt.Key.Key_J, 'higher': Qt.Key.Key_BracketRight,
           'map': Qt.Key.Key_M, 'pad': Qt.Key.Key_Backspace}
#  The keys that take the controls from the ascent guidance.
TAKING = (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Z,
          Qt.Key.Key_X, Qt.Key.Key_T, Qt.Key.Key_F, Qt.Key.Key_R,
          Qt.Key.Key_Backspace, *AIMING, *ROLLING)
HINT = ('click the view: look round   wheel: zoom   Esc: let the mouse go'
        '   click a lamp: do it')
MAP_HINT = ('drag: turn   wheel: zoom   click a name: look at it   '
            '⌫: back to the rocket   M: back to flying')


class SpaceWindow(QMainWindow):
  """
  SpaceWindow flies a creative 'Vessel' through the solar system of the
  day it opens ('system', its time kept by 'keeper'), seen through a
  'SpaceViewport': the flight view ('chase', a 'ChaseCamera') with its
  artificial horizon ('navball') and control board, or the map
  ('orrery', M). It readies itself first on a thread of its own (the
  flight's kernel compiled, the looks painted: 'readying'), then each
  frame takes the keys, lets the ascent guidance fly ('guidance', J),
  flies the vessel ('Flight', on the GPU), moves time on and draws
  ('Scenery'). Time warp only above the air, off the ground, the engine
  shut (the spec); warping to the apoapsis eases off 'APOAPSIS_LEAD' s
  before it. W S A D move the autopilot's aim (over the horizon, off the
  path), never the rocket about its own axes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    QMainWindow.__init__(self)
    self.setWindowTitle('Space')
    self.began = datetime.now(timezone.utc)
    self.system = solarSystemOn(julianOf(self.began))
    self.keeper = Timekeeper(self.system)
    self.vessel = Vessel()
    self.guidance = AscentGuidance()
    self._padded()
    self.chase, self.orrery, self.scenery = (ChaseCamera(), Orrery(),
                                             Scenery())
    self.navball = Navball()
    self.flight, self.files, self.readying = None, None, 'starting'
    self.trouble, self.held, self.mapOpen = None, {}, False
    self.note, self._noted, self._flashed = '', 0.0, {}
    self._dragged, self._dragFrom, self._pressedAt = False, None, None
    self._ticked = time.perf_counter()
    self.viewport = SpaceViewport()
    self.setCentralWidget(self.viewport)
    self.viewport.quick.installEventFilter(self)
    self.viewport.boardPicked.connect(self._boardPicked)
    self.pointer = Pointer(self.viewport.quick)
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.tick)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: object) -> None:
    """Shown the first time, the window readies itself on a thread of its
    own and starts its frames."""
    if not self.timer.isActive():
      threading.Thread(target=self._readied, daemon=True).start()
      self.timer.start(TICK)
    QMainWindow.showEvent(self, event)

  def closeEvent(self, event: object) -> None:
    """Closed, the window stops its frames."""
    self.timer.stop()
    QMainWindow.closeEvent(self, event)

  def eventFilter(self, watched: object, event: object) -> bool:
    """Takes the keys and the mouse from the viewport's scene window (a
    click on the control board or the horizon is the scene's own)."""
    if watched is not self.viewport.quick:
      return False
    kind = event.type()
    if kind == QEvent.Type.KeyPress and not event.isAutoRepeat():
      self.held.setdefault(event.key(), time.perf_counter())
      return self._pressed(event.key())
    if kind == QEvent.Type.KeyRelease and not event.isAutoRepeat():
      self.held.pop(event.key(), None)
      return True
    if kind == QEvent.Type.FocusOut:
      self.held.clear()
      self.pointer.letGo()
      return False
    if kind == QEvent.Type.MouseButtonPress and (
        not self.pointer.taken) and self.viewport.takesClick(
          event.position()):
      return False
    if self.mapOpen:
      return self._mapMouse(kind, event)
    if kind == QEvent.Type.MouseButtonPress and not self.pointer.taken:
      self.pointer.take()
      return True
    if kind == QEvent.Type.MouseMove:
      self.pointer.movedTo(event.globalPosition(), event.position())
    elif kind == QEvent.Type.Wheel:
      self.chase.zoomed(event.angleDelta().y() / 120.0)
      return True
    elif kind == QEvent.Type.Leave:
      self.pointer.forget()
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def tick(self, ) -> None:
    """The 'tick' method takes the keys, lets the ascent guidance fly,
    flies the vessel through the frame's time (warped), and draws."""
    now = time.perf_counter()
    real, self._ticked = min(LONGEST_REAL, now - self._ticked), now
    viewport = self.viewport
    if self.trouble is not None:
      viewport.hudShown('', '', 'Could not ready the flight:\n%s'
                        % self.trouble)
      return
    if self.flight is None or not viewport.loaded:
      problems = '\n'.join(viewport.problems)
      viewport.hudShown('', '', problems or 'Readying: %s' % self.readying)
      return
    if not viewport.furnishedYet:
      viewport.furnished(self.system, self.files,
                         self.scenery.orbitsOf(self.system),
                         self.navball.pictureReady())
      return
    keeper, vessel, system = self.keeper, self.vessel, self.system
    self._steered(real)
    self.guidance.acted(vessel, system, keeper)
    vessel.aimKept(system)
    self._warpKept()
    seconds = keeper.secondsOf(real)
    self.flight.flown((vessel,), system, keeper.now, seconds)
    keeper.ticked(seconds)
    right, down = self.pointer.moved()
    if right or down:
      self.chase.turned(right, down)
    if self.mapOpen:
      quick = viewport.quick
      viewport.mapShown(self.scenery.mapOf(
        system, vessel, self.orrery, keeper.now, quick.width(),
        quick.height()))
    else:
      viewport.flightShown(self.scenery.flightOf(
        system, vessel, self.chase, keeper.now), system, vessel.anchor)
      viewport.navballShown(self.navball.frameOf(vessel, system,
                                                 NAV_RADIUS))
    viewport.boardShown(self._boardOf(now))
    viewport.hudShown(self._readout(), MAP_HINT if self.mapOpen else HINT,
                      '')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _readied(self, ) -> None:
    """Readies the flight on a thread of its own: its kernel compiled on
    the GPU (or the CPU without one), the looks painted; says each step
    and how long it took ('readying', and on the console)."""
    try:
      from ._flight import Flight, preloadedFlight
      from ._looks import looksReady
      from worQt.phys._compiled import gpuDevice
      device = gpuDevice() or 'cpu'
      self._said('the flight computer on %s (the first time ~10 s)'
                 % device)
      took = preloadedFlight(device)
      self._said('flight computer ready in %.1f s; painting the planets'
                 % took)
      began = time.perf_counter()
      files = looksReady(device, self._said)
      self._said('the planets painted in %.1f s'
                 % (time.perf_counter() - began))
      self.files, self.flight = files, Flight(device)
    except Exception as error:
      self.trouble = '%s: %s' % (type(error).__name__, error)
      print('[space] could not ready: %s' % self.trouble, flush=True)

  def _said(self, line: str) -> None:
    """Says how readying goes: on screen and on the console."""
    self.readying = line
    print('[space] %s' % line, flush=True)

  def _padded(self, ) -> None:
    """Stands the vessel on Terra's pad now, the engine shut, the
    autopilot off, the guidance let go."""
    vessel = self.vessel
    self.guidance.stopped(vessel)
    vessel.stood(self.system, self.system.named('Terra'), PAD[0], PAD[1],
                 self.keeper.now)
    vessel.engine.throttled(0.0)
    vessel.autopilot.engaged('off', vessel.turn)
    vessel.steered(0.0, 0.0, 0.0)
    self.keeper.realtime()

  def _pressed(self, key: object) -> bool:
    """Acts on a key pressed; returns whether it was one of the
    window's."""
    vessel, keeper, system = self.vessel, self.keeper, self.system
    pilot = vessel.autopilot
    if key in CAPS:
      self._flashed[CAPS[key]] = time.perf_counter()
    if key in TAKING and self.guidance.on:
      self.guidance.stopped(vessel)
      self._noteOf('Ascent guidance off: you took the controls')
    if key == Qt.Key.Key_Escape:
      self.pointer.letGo()
    elif key in AIMING:
      up, right = AIMING[key]
      vessel.aimNudged(system, up * AIM_STEP, right * AIM_STEP)
    elif key == Qt.Key.Key_Z:
      vessel.engine.throttled(1.0)
    elif key == Qt.Key.Key_X:
      vessel.engine.throttled(0.0)
    elif key == Qt.Key.Key_T:
      pilot.engaged('off' if pilot.mode == 'hold' else 'hold', vessel.turn)
    elif key == Qt.Key.Key_F:
      pilot.engaged('off' if pilot.mode == 'prograde' else 'prograde',
                    vessel.turn)
    elif key == Qt.Key.Key_R:
      pilot.engaged('off' if pilot.mode == 'retrograde'
                    else 'retrograde', vessel.turn)
    elif key == Qt.Key.Key_J:
      if self.guidance.on:
        self.guidance.stopped(vessel)
      else:
        self.guidance.started(vessel, system)
    elif key == Qt.Key.Key_BracketLeft:
      self.guidance.targeted(-1)
    elif key == Qt.Key.Key_BracketRight:
      self.guidance.targeted(1)
    elif key == Qt.Key.Key_Period:
      why = self._noWarp()
      if why:
        self._noteOf('No warp: %s' % why)
      else:
        keeper.faster()
    elif key == Qt.Key.Key_Comma:
      keeper.slower()
    elif key == Qt.Key.Key_Slash:
      keeper.realtime()
    elif key == Qt.Key.Key_G:
      self._toApoapsis()
    elif key == Qt.Key.Key_M:
      self.mapOpen = not self.mapOpen
      if self.mapOpen:
        self.pointer.letGo()
        self.orrery.opened(vessel, system)
    elif key == Qt.Key.Key_Backspace:
      if self.mapOpen:
        self.orrery.opened(vessel, system)
      else:
        self._padded()
    elif key not in ROLLING and key not in (Qt.Key.Key_Shift,
                                            Qt.Key.Key_Control):
      return False
    return True

  def _boardPicked(self, action: str) -> None:
    """Does what a click on the board's lamp 'action' asks: as its key
    does; the aim's lamp aims where the nose points."""
    if action == 'aim':
      if self.guidance.on:
        self.guidance.stopped(self.vessel)
      self.vessel.aimNudged(self.system, 0.0, 0.0)
      return
    key = ACTIONS.get(action)
    if key is not None:
      self._pressed(key)

  def _steered(self, real: float) -> None:
    """Sets the throttle and the roll from the keys held, and moves the
    aim on while its keys are held past a tap."""
    held, engine, vessel = self.held, self.vessel.engine, self.vessel
    now = time.perf_counter()
    if Qt.Key.Key_Shift in held:
      engine.throttled(engine.throttle + THROTTLE_RATE * real)
    if Qt.Key.Key_Control in held:
      engine.throttled(engine.throttle - THROTTLE_RATE * real)
    roll = sum(sign for key, sign in ROLLING.items() if key in held)
    vessel.steered(0.0, 0.0, roll)
    up = right = 0.0
    for key, (a, b) in AIMING.items():
      if key in held and now - held[key] > REPEAT_AFTER:
        up, right = up + a, right + b
    if up or right:
      vessel.aimNudged(self.system, up * AIM_RATE * real,
                       right * AIM_RATE * real)

  def _noWarp(self, ) -> str:
    """Returns why time may not be warped now ('' it may): in the air,
    on the ground, the engine burning."""
    vessel = self.vessel
    body = self.system.bodies[vessel.anchor]
    if vessel.touching:
      return 'on the ground'
    if vessel.engine.throttle > 0.0:
      return 'the engine burns'
    if body.air is not None and vessel.heightOver(self.system) < (
        body.air.top):
      return 'in the air (above %s)' % lengthText(body.air.top)
    return ''

  def _warpKept(self, ) -> None:
    """Ends the warp the moment it may not go on, saying why."""
    if self.keeper.factor > 1:
      why = self._noWarp()
      if why:
        self.keeper.realtime()
        self._noteOf('Warp stopped: %s' % why)

  def _toApoapsis(self, ) -> None:
    """Warps to 'APOAPSIS_LEAD' s before the apoapsis, if time may warp
    and the path has one."""
    why = self._noWarp()
    conic = self.vessel.conicOf(self.system)
    if why or conic is None or not conic.closed:
      self._noteOf('No warp to the apoapsis: %s' % (
        why or 'the path leaves'))
      return
    self.keeper.aim(conic.timeToApoapsis(0.0) - APOAPSIS_LEAD)

  def _noteOf(self, text: str) -> None:
    """Shows 'text' a few seconds."""
    self.note, self._noted = text, time.perf_counter()

  def _boardOf(self, now: float) -> dict:
    """Returns what the control board shows: the throttle, the
    autopilot's mode, the warp, the guidance, the map, the keys held and
    those just tapped."""
    guidance = self.guidance
    held = {CAPS[key] for key in self.held if key in CAPS}
    held |= {name for name, at in self._flashed.items()
             if now - at < FLASH}
    phase = {'climb': 'climbing', 'turn': 'turning', 'coast': 'coasting',
             'round': 'rounding', 'done': 'in orbit'}.get(guidance.phase,
                                                          '')
    return {'throttle': self.vessel.engine.throttle,
            'mode': self.vessel.autopilot.mode,
            'warp': self.keeper.factor,
            'toAp': self.keeper.aimed is not None,
            'ascent': guidance.on, 'phase': phase,
            'target': lengthText(guidance.target),
            'map': self.mapOpen, 'held': sorted(held)}

  def _mapMouse(self, kind: object, event: object) -> bool:
    """Takes the mouse on the map: a drag turns it, the wheel zooms, a
    click on a mark looks at what it marks."""
    if kind == QEvent.Type.MouseButtonPress:
      self._dragFrom = self._pressedAt = event.position()
      self._dragged = False
      return True
    if kind == QEvent.Type.MouseMove and self._dragFrom is not None:
      at = event.position()
      moved = at - self._dragFrom
      self._dragFrom = at
      if (at - self._pressedAt).manhattanLength() > 4.0:
        self._dragged = True
      self.orrery.turned(moved.x(), moved.y())
      return True
    if kind == QEvent.Type.MouseButtonRelease:
      if not self._dragged and self._pressedAt is not None:
        self._picked(self._pressedAt)
      self._dragFrom = self._pressedAt = None
      return True
    if kind == QEvent.Type.Wheel:
      self.orrery.zoomed(event.angleDelta().y() / 120.0)
      return True
    return False

  def _picked(self, at: QPointF) -> None:
    """Looks at the body (or the vessel) whose mark is nearest 'at', if
    one is near enough."""
    quick = self.viewport.quick
    marks = self.orrery.marksOf(self.vessel, self.system, self.keeper.now,
                                quick.width(), quick.height())
    near = [(math.hypot(m['x'] - at.x(), m['y'] - at.y()), m['index'])
            for m in marks if m['index'] >= -1]
    if near:
      gap, index = min(near)
      if gap <= PICKED:
        self.orrery.focused(index, self.system)

  def _readout(self, ) -> str:
    """Returns what the flight says: where, how high and fast, the path's
    apsides, the aim, the guidance, the date; how the frames go."""
    system, vessel, keeper = self.system, self.vessel, self.keeper
    body = system.bodies[vessel.anchor]
    height = vessel.heightOver(system)
    ground = norm(vessel.groundVelocity(system))
    speed = norm(vessel.velocity)
    climb = dot(vessel.velocity, unit(vessel.place))
    conic = vessel.conicOf(system)
    lines = ['%-10s %s' % (body.name, (self.began + timedelta(
      seconds=keeper.elapsed)).strftime('%Y-%m-%d %H:%M:%S UTC')),
             'Height     %-12s Climb %s/s' % (lengthText(height),
                                              lengthText(climb)),
             'Speed      %-12s Ground %s/s' % (lengthText(speed) + '/s',
                                               lengthText(ground))]
    if conic is None:
      lines.append('Apoapsis   none: falling straight')
      lines.append('Periapsis  none')
    elif conic.closed:
      lines.append('Apoapsis   %-12s in %s' % (lengthText(
        conic.apoapsis - body.radius), timeText(conic.timeToApoapsis(
          0.0))))
    else:
      lines.append('Apoapsis   none: the path leaves %s' % body.name)
    if conic is not None:
      peri = conic.timeToPeriapsis(0.0)
      lines.append('Periapsis  %-12s %s' % (lengthText(
        conic.periapsis - body.radius), 'in %s' % timeText(peri)
                                            if peri is not None else ''))
    pilot = vessel.autopilot
    if pilot.mode == 'aim':
      off = ('off the path %+.0f°' % math.degrees(pilot.turn)
             if pilot.travel else 'heading %03.0f°'
                                  % math.degrees(pilot.heading))
      lines.append('Aim        %+.0f° over the horizon, %s' % (
        math.degrees(pilot.pitch), off))
    if self.guidance.on:
      lines.append('Ascent     to %s: %s' % (lengthText(
        self.guidance.target), self.guidance.phase))
    lines.append('%.0f fps, flight %.2f ms (%d steps)' % (
      self.viewport.fps, self.flight.lastMs, self.flight.lastSteps))
    if self.note and time.perf_counter() - self._noted < NOTE_LASTS:
      lines.append(self.note)
    return '\n'.join(lines)
