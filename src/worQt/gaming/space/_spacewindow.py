"""
SpaceWindow flies the creative rocket (user, 2026-11-16: "let's start
with a 'creative' rocket with inf fuel"): the keys and the mouse, time
and its warp, the flight each frame, the flight view or the map.
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

from ._chasecamera import ChaseCamera
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
#  Warping to the apoapsis stops this long before it, s.
APOAPSIS_LEAD = 30.0
#  A note on screen stays this long, s.
NOTE_LASTS = 3.0
#  A click on the map picks the mark within this many pixels.
PICKED = 22.0
#  The keys on the reaction wheels: pitch, yaw, roll (user's KSP).
STEERING = {Qt.Key.Key_W: (0, 1.0), Qt.Key.Key_S: (0, -1.0),
            Qt.Key.Key_D: (1, 1.0), Qt.Key.Key_A: (1, -1.0),
            Qt.Key.Key_Q: (2, 1.0), Qt.Key.Key_E: (2, -1.0)}
HINT = ('W S pitch   A D yaw   Q E roll   Shift Ctrl throttle (Z full, '
        'X cut)   T hold   F prograde   R retrograde   , . warp (/ stop, '
        'G to apoapsis)   M map   Backspace: back on the pad   click: '
        'look round, Esc lets go')
MAP_HINT = ('drag: turn   wheel: zoom   click a name: look at it   '
            'Backspace: back to the rocket   M: back to flying   , . warp')


class SpaceWindow(QMainWindow):
  """
  SpaceWindow flies a creative 'Vessel' through the solar system of the
  day it opens ('system', its time kept by 'keeper'), seen through a
  'SpaceViewport': the flight view ('chase', a 'ChaseCamera') or the
  map ('orrery', M). It readies itself first on a thread of its own (the
  flight's kernel compiled, the looks painted: 'readying'), then each
  frame takes the keys, flies the vessel ('Flight', on the GPU), moves
  time on and draws ('Scenery'). Time warp only above the air, off the
  ground, the engine shut (the spec); warping to the apoapsis eases off
  'APOAPSIS_LEAD' s before it.
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
    self._padded()
    self.chase, self.orrery, self.scenery = (ChaseCamera(), Orrery(),
                                             Scenery())
    self.flight, self.files, self.readying = None, None, 'starting'
    self.trouble, self.held, self.mapOpen = None, set(), False
    self.note, self._noted = '', 0.0
    self._dragged, self._dragFrom, self._pressedAt = False, None, None
    self._ticked = time.perf_counter()
    self.viewport = SpaceViewport()
    self.setCentralWidget(self.viewport)
    self.viewport.quick.installEventFilter(self)
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
    """Takes the keys and the mouse from the viewport's scene window."""
    if watched is not self.viewport.quick:
      return False
    kind = event.type()
    if kind == QEvent.Type.KeyPress and not event.isAutoRepeat():
      self.held.add(event.key())
      return self._pressed(event.key())
    if kind == QEvent.Type.KeyRelease and not event.isAutoRepeat():
      self.held.discard(event.key())
      return True
    if kind == QEvent.Type.FocusOut:
      self.held.clear()
      self.pointer.letGo()
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
    """The 'tick' method takes the keys, flies the vessel through the
    frame's time (warped), and draws."""
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
                         self.scenery.orbitsOf(self.system))
      return
    self._steered(real)
    self._warpKept()
    keeper, vessel = self.keeper, self.vessel
    seconds = keeper.secondsOf(real)
    self.flight.flown((vessel,), self.system, keeper.now, seconds)
    keeper.ticked(seconds)
    right, down = self.pointer.moved()
    if right or down:
      self.chase.turned(right, down)
    if self.mapOpen:
      quick = viewport.quick
      viewport.mapShown(self.scenery.mapOf(
        self.system, vessel, self.orrery, keeper.now, quick.width(),
        quick.height()))
    else:
      viewport.flightShown(self.scenery.flightOf(
        self.system, vessel, self.chase, keeper.now), self.system,
        vessel.anchor)
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
    autopilot off."""
    vessel = self.vessel
    vessel.stood(self.system, self.system.named('Terra'), PAD[0], PAD[1],
                 self.keeper.now)
    vessel.engine.throttled(0.0)
    vessel.autopilot.engaged('off', vessel.turn)
    vessel.steered(0.0, 0.0, 0.0)
    self.keeper.realtime()

  def _pressed(self, key: object) -> bool:
    """Acts on a key pressed; returns whether it was one of the
    window's."""
    vessel, keeper = self.vessel, self.keeper
    pilot = vessel.autopilot
    if key == Qt.Key.Key_Escape:
      self.pointer.letGo()
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
        self.orrery.opened(vessel, self.system)
    elif key == Qt.Key.Key_Backspace:
      if self.mapOpen:
        self.orrery.opened(vessel, self.system)
      else:
        self._padded()
    elif key not in STEERING and key not in (Qt.Key.Key_Shift,
                                             Qt.Key.Key_Control):
      return False
    return True

  def _steered(self, real: float) -> None:
    """Sets the throttle and the wheels from the keys held."""
    held, engine = self.held, self.vessel.engine
    if Qt.Key.Key_Shift in held:
      engine.throttled(engine.throttle + THROTTLE_RATE * real)
    if Qt.Key.Key_Control in held:
      engine.throttled(engine.throttle - THROTTLE_RATE * real)
    steer = [0.0, 0.0, 0.0]
    for key, (axis, sign) in STEERING.items():
      if key in held:
        steer[axis] += sign
    self.vessel.steered(*steer)

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
    apsides, the throttle, the autopilot, the warp, the date; how the
    frames go."""
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
    lines.append('Throttle   %-12s Autopilot %s' % (
      '%.0f %%' % (100.0 * vessel.engine.throttle), vessel.autopilot.mode))
    lines.append('Warp       %-12s %s' % ('%dx' % keeper.factor, (
      'to the apoapsis' if keeper.aimed is not None else '')))
    lines.append('%.0f fps, flight %.2f ms (%d steps)' % (
      self.viewport.fps, self.flight.lastMs, self.flight.lastSteps))
    if self.note and time.perf_counter() - self._noted < NOTE_LASTS:
      lines.append(self.note)
    return '\n'.join(lines)
