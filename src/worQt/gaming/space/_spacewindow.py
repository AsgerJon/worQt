"""
SpaceWindow flies the creative rocket (user, 2026-11-16: "let's start
with a 'creative' rocket with inf fuel"): the keys and the mouse, time
and its warp, the ascent guidance, the flight each frame, Asger's
cockpit and its instruments and their sound, the chase view with its
artificial horizon and control board, or the map.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import faulthandler
import math
import sys
import threading
import time
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtWidgets import QMainWindow

from worQt.gaming.sandbox._pointer import Pointer
from worQt.gaming.sandbox._speaker import Speaker

from ._accelerometer import Accelerometer
from ._aerospike import G0
from ._ascentguidance import AscentGuidance
from ._cabinmixer import EATS, HURTS, THUD, THUDS, TOLD
from ._chasecamera import ChaseCamera
from ._cockpit import EYE, LIMITS, Cockpit
from ._crewman import SIT
from ._dashpictures import picturesReady
from ._furnishings import candleLight
from ._instruments import Instruments, limitNotch
from ._navball import Navball
from ._orrery import Orrery, lengthText, timeText
from ._planets import PAD, julianOf, solarSystemOn
from ._scenery import Scenery
from ._spaceviewport import SpaceViewport
from ._teleprinter import ICONS
from ._timekeeper import Timekeeper
from ._turns import dot, norm, rotated, unit
from ._vessel import MASS, Vessel
from ._vitals import EATING, Vitals

#  A frame, ms; the longest step a frame takes, s.
TICK = 16
LONGEST_REAL = 0.1
#  Loading that cannot be told from failing is failing (user, 2026-11-16:
#  "If correct loading cannot be distinguished from failed loading, it
#  *is* failed loading"): the window's thread frozen this long, s, every
#  thread's stack goes to the console (faulthandler's own thread: it
#  needs no Python, so it speaks even when Python is locked); a readying
#  step taking this long is called stuck on screen and on the console.
FROZEN = 10.0
STUCK = 60.0
#  The last readying step's words (the scene furnished on Qt's thread).
FURNISHING = 'furnishing the cabin (the deck, the room, the dashboard)'
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
#  Looking at the throttle's slide, the wheel moves it this much a
#  notch, a click this much (a right click back).
WHEEL_THROTTLE = 0.05
CLICK_THROTTLE = 0.1
#  The keys as their caps on the board name them.
CAPS = {Qt.Key.Key_Shift: 'Shift', Qt.Key.Key_Control: 'Ctrl',
        Qt.Key.Key_Z: 'Z', Qt.Key.Key_X: 'X', Qt.Key.Key_T: 'T',
        Qt.Key.Key_F: 'F', Qt.Key.Key_R: 'R', Qt.Key.Key_W: 'W',
        Qt.Key.Key_S: 'S', Qt.Key.Key_A: 'A', Qt.Key.Key_D: 'D',
        Qt.Key.Key_Q: 'Q', Qt.Key.Key_E: 'E', Qt.Key.Key_Comma: ',',
        Qt.Key.Key_Period: '.', Qt.Key.Key_Slash: '/', Qt.Key.Key_G: 'G',
        Qt.Key.Key_J: 'J', Qt.Key.Key_BracketLeft: '[',
        Qt.Key.Key_BracketRight: ']', Qt.Key.Key_M: 'M',
        Qt.Key.Key_Backspace: '⌫', Qt.Key.Key_V: 'V',
        Qt.Key.Key_P: 'P', Qt.Key.Key_O: 'O', Qt.Key.Key_I: 'I',
        Qt.Key.Key_K: 'K', Qt.Key.Key_L: 'L', Qt.Key.Key_B: 'B',
        Qt.Key.Key_Y: 'Y', Qt.Key.Key_U: 'U'}
#  The action each key asks for.
KEY_ACTIONS = {Qt.Key.Key_Z: 'full', Qt.Key.Key_X: 'cut',
               Qt.Key.Key_T: 'hold', Qt.Key.Key_F: 'prograde',
               Qt.Key.Key_R: 'retrograde', Qt.Key.Key_Period: 'faster',
               Qt.Key.Key_Comma: 'slower', Qt.Key.Key_Slash: 'stop',
               Qt.Key.Key_G: 'toAp', Qt.Key.Key_J: 'ascent',
               Qt.Key.Key_BracketRight: 'higher',
               Qt.Key.Key_BracketLeft: 'lower', Qt.Key.Key_M: 'map',
               Qt.Key.Key_Backspace: 'pad', Qt.Key.Key_V: 'view',
               Qt.Key.Key_P: 'play', Qt.Key.Key_O: 'halt',
               Qt.Key.Key_I: 'eject', Qt.Key.Key_K: 'lighter',
               Qt.Key.Key_L: 'heavier', Qt.Key.Key_B: 'buckle',
               Qt.Key.Key_Y: 'limit down', Qt.Key.Key_U: 'limit up'}
#  The cabin's input each action is worked by (Asger glances at it: user,
#  2026-11-16: "When I press a keyboard key my view will turn to center
#  on that key"), where it differs from the action's own.
WORKED_BY = {'faster': 'warp', 'slower': 'warp', 'higher': 'orbit',
             'lower': 'orbit', 'aim': 'aim', 'throttle': 'throttle',
             'lighter': 'gravity', 'heavier': 'gravity',
             'limit down': 'limit', 'limit up': 'limit'}
#  Dead (user, 2026-11-17: "4g would kill Asger in 20 seconds"), these
#  keys still do their work (B wakes him in his chair).
DEAD_KEYS = ('map', 'view', 'buckle')
#  Out of his chair (user, 2026-11-17: getting up, "FAFO rules") Asger
#  works the dashboard only by reaching it (a click on what he looks at);
#  these keys still do their work (the view's own; B sits him down), his
#  legs take W A S D ('MOVING') and Space (a jump, or a push off what he
#  touches).
UP_KEYS = ('map', 'view', 'buckle')
MOVING = {Qt.Key.Key_W: 'ahead', Qt.Key.Key_S: 'back',
          Qt.Key.Key_A: 'left', Qt.Key.Key_D: 'right'}
#  The actions that take the controls from the ascent guidance.
TAKING = ('full', 'cut', 'hold', 'prograde', 'retrograde', 'aim',
          'throttle', 'pad')
HINT = ('click the view: look round   wheel: zoom   Esc: let the mouse go'
        '   click a lamp: do it   V: Asger\'s eyes   B: get up / sit')
MAP_HINT = ('drag: turn   wheel: zoom   click a name: look at it   '
            '⌫: back to the rocket   M: back to flying')


class SpaceWindow(QMainWindow):
  """
  SpaceWindow flies a creative 'Vessel' through the solar system of the
  day it opens ('system', its time kept by 'keeper'), seen through a
  'SpaceViewport': Asger's eyes in his cockpit ('cockpit', its
  'instruments': the dashboard alive, its sound in a process of its own,
  'speaker'), the chase view ('chase') with its artificial horizon
  ('navball') and control board, or the map ('orrery', M). It readies
  itself first on a thread of its own (the flight's kernel compiled, the
  looks painted: 'readying'), then each frame takes the keys, lets the
  ascent guidance fly ('guidance', J), flies the vessel ('Flight', on the
  GPU), moves time on and draws ('Scenery'). Every key, click on the
  cabin's inputs and click on the board's lamps asks for an action
  ('_acted'); a key turns Asger's head to the input working it. Time
  warp only above the air, off the ground, the engine shut (the spec).
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
    self.accelerometer, self.world, self._leaping = (Accelerometer(), None,
                                                     False)
    self.vitals = Vitals()
    self._padded()
    self.chase, self.orrery, self.scenery = (ChaseCamera(), Orrery(),
                                             Scenery())
    self.navball = Navball()
    self.cockpit, self.inside = Cockpit(), True
    self.instruments = Instruments(self.cockpit)
    self.speaker = Speaker('worQt.gaming.space._cabinmixer:CabinMixer',
                           TOLD)
    self.flight, self.files, self.readying = None, None, 'starting'
    self._step, self._stuck = time.perf_counter(), False
    self.trouble, self.held, self.mapOpen = None, {}, False
    self.note, self._noted, self._flashed = '', 0.0, {}
    self._dragged, self._dragFrom, self._clickedAt = False, None, None
    self._ticked = time.perf_counter()
    self.viewport = SpaceViewport()
    self.setCentralWidget(self.viewport)
    self.viewport.quick.installEventFilter(self)
    self.viewport.boardPicked.connect(self._acted)
    self.pointer = Pointer(self.viewport.quick)
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.tick)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: object) -> None:
    """Shown the first time, the window readies itself on a thread of its
    own, starts its sound and its frames."""
    if not self.timer.isActive():
      faulthandler.dump_traceback_later(FROZEN, False, sys.stderr)
      threading.Thread(target=self._readied, daemon=True).start()
      self.speaker.start()
      self.timer.start(TICK)
    QMainWindow.showEvent(self, event)

  def closeEvent(self, event: object) -> None:
    """Closed, the window stops its frames and its sound."""
    self.timer.stop()
    faulthandler.cancel_dump_traceback_later()
    self.speaker.close()
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
    if kind == QEvent.Type.MouseButtonPress and self.inside:
      self._used(event.button() == Qt.MouseButton.RightButton)
      return True
    if kind == QEvent.Type.MouseMove:
      self.pointer.movedTo(event.globalPosition(), event.position())
    elif kind == QEvent.Type.Wheel:
      notches = event.angleDelta().y() / 120.0
      if not self.inside:
        self.chase.zoomed(notches)
      elif self._looked() == 'throttle':
        engine = self.vessel.engine
        engine.throttled(engine.throttle + WHEEL_THROTTLE * notches)
      return True
    elif kind == QEvent.Type.Leave:
      self.pointer.forget()
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def tick(self, ) -> None:
    """The 'tick' method takes the keys, lets the ascent guidance fly,
    flies the vessel through the frame's time (warped), keeps the cabin
    alive, tells the sound, and draws."""
    now = time.perf_counter()
    faulthandler.dump_traceback_later(FROZEN, False, sys.stderr)
    real, self._ticked = min(LONGEST_REAL, now - self._ticked), now
    viewport = self.viewport
    if self.trouble is not None:
      viewport.hudShown('', '', 'Could not ready the flight:\n%s'
                        % self.trouble)
      return
    if self.flight is None or not viewport.loaded:
      problems = '\n'.join(viewport.problems)
      viewport.hudShown('', '', problems or self._readyingText(now))
      return
    if not viewport.furnishedYet:
      self._furnished(now)
      return
    keeper, vessel, system = self.keeper, self.vessel, self.system
    self._steered(real)
    self.guidance.acted(vessel, system, keeper)
    vessel.aimKept(system)
    self._warpKept()
    seconds = keeper.secondsOf(real)
    self.flight.flown((vessel,), system, keeper.now, seconds)
    keeper.ticked(seconds)
    self.accelerometer.measured(vessel, system, seconds, keeper.factor > 1)
    self._cabinMoved(real)
    self._lived(real)
    self.instruments.acted(real, vessel, system, keeper, self.guidance,
                           self.mapOpen, self.inside, self._header())
    told = list(self.instruments.told(vessel, system, self.inside))
    told[THUDS], told[THUD] = self.world.thuds, self.world.loudest
    told[HURTS], told[EATS] = self.vitals.hurts, self.vitals.meals
    self.speaker.heard(tuple(told))
    right, down = self.pointer.moved()
    if right or down:
      (self.cockpit if self.inside else self.chase).turned(right, down)
    if self.mapOpen:
      quick = viewport.quick
      viewport.mapShown(self.scenery.mapOf(
        system, vessel, self.orrery, keeper.now, quick.width(),
        quick.height()))
    else:
      ball = self.navball.frameOf(vessel, system, NAV_RADIUS)
      frame = self.scenery.flightOf(system, vessel, self._seen(),
                                    keeper.now)
      cabin = self.scenery.cabinOf(system, vessel, self.cockpit,
                                   frame['rocket'], ball, self._dash(),
                                   self.inside)
      viewport.flightShown(frame, cabin, system, vessel.anchor)
      viewport.navballShown(ball)
    viewport.boardShown(self._boardOf(now))
    looked = self.cockpit.lookedAt() if self.inside else None
    stamp = (self.began + timedelta(seconds=keeper.elapsed)).strftime(
      '%Y-%m-%d  %H:%M:%S')
    viewport.cockpitShown(self.inside, (looked.key, looked.peep.prompt())
                          if looked else None,
                          self.instruments.printer.paper(), stamp)
    viewport.hudShown(self._readout(), MAP_HINT if self.mapOpen else HINT,
                      '')
    vitals = self.vitals
    viewport.vitalsShown(vitals.health, vitals.food, vitals.hurt,
                         1.0 - vitals.eating / EATING if vitals.eating
                         else 0.0, vitals.cause or '')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _readied(self, ) -> None:
    """Readies the flight on a thread of its own: its kernel compiled on
    the GPU (or the CPU without one), the looks painted; says each step
    and how long it took ('readying', and on the console)."""
    try:
      from ._cabinworld import CabinWorld
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
      self._said('the planets painted in %.1f s; the cabin\'s physics on'
                 ' %s (the first time ~10 s)' % (time.perf_counter()
                                                 - began, device))
      began = time.perf_counter()
      self.world = CabinWorld(device)
      self._said('the cabin\'s physics ready in %.1f s'
                 % (time.perf_counter() - began))
      self.files, self.flight = files, Flight(device)
    except Exception as error:
      self.trouble = '%s: %s' % (type(error).__name__, error)
      print('[space] could not ready: %s' % self.trouble, flush=True)

  def _furnished(self, now: float) -> None:
    """Furnishes the scene (on this thread: Qt's), said first on screen
    and on the console (a frame drawn with it before the work), then how
    long it took and that it flies."""
    if self.readying != FURNISHING:
      self._said(FURNISHING)
      self.viewport.hudShown('', '', self._readyingText(now))
      return
    began = time.perf_counter()
    if not self.viewport.furnished(self.system, self.files,
                                   self.scenery.orbitsOf(self.system),
                                   self.navball.pictureReady(),
                                   picturesReady(),
                                   self.scenery.cabinPieces(self.cockpit)):
      self.trouble = 'the scene was gone when it was to be furnished'
      print('[space] could not ready: %s' % self.trouble, flush=True)
      return
    self._said('the cabin furnished in %.1f s; ready, flying'
               % (time.perf_counter() - began))

  def _said(self, line: str) -> None:
    """Says how readying goes: on screen and on the console (its step's
    clock started anew)."""
    self.readying, self._step, self._stuck = line, time.perf_counter(), False
    print('[space] %s' % line, flush=True)

  def _readyingText(self, now: float) -> str:
    """Returns what the screen says while readying: the step and how
    long it has taken; past 'STUCK' s, that it is stuck (said once on the
    console too, with every thread's stack)."""
    took = now - self._step
    text = 'Readying: %s  (%.0f s)' % (self.readying, took)
    if took < STUCK:
      return text
    if not self._stuck:
      self._stuck = True
      print('[space] STUCK: %.0f s on "%s"; every thread now:'
            % (took, self.readying), flush=True)
      faulthandler.dump_traceback(sys.stderr, True)
    return text + '\nSTUCK: over %.0f s on this step (the console has' \
                  ' every thread)' % STUCK

  def _header(self, ) -> str:
    """Returns the teleprinter's first line: where and when."""
    return '%s WORQT SPACE  TERRA  %s' % (ICONS['rocket'],
                                          self.began.strftime(
                                            '%Y-%m-%d %H:%M UTC'))

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
    self.accelerometer.reset()

  def _pressed(self, key: object) -> bool:
    """Acts on a key pressed (its action, Asger glancing at the input
    working it); returns whether it was one of the window's."""
    if key in CAPS:
      self._flashed[CAPS[key]] = time.perf_counter()
    if key == Qt.Key.Key_Escape:
      self.pointer.letGo()
      return True
    if self.vitals.cause is not None:
      action = KEY_ACTIONS.get(key)
      if action in DEAD_KEYS:
        self._acted(action)
      return True
    if key == Qt.Key.Key_E and self.inside:
      self._used(False)
      return True
    if not self.cockpit.crewman.buckled:
      return self._upPressed(key)
    if key in AIMING:
      up, right = AIMING[key]
      self._taken('aim')
      self.vessel.aimNudged(self.system, up * AIM_STEP, right * AIM_STEP)
      self._glanced('aim')
      return True
    if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control):
      self._taken('throttle')
      self._glanced('throttle')
      return True
    if key in ROLLING:
      self._taken('aim')
      return True
    action = KEY_ACTIONS.get(key)
    if action is None:
      return False
    self._acted(action)
    self._glanced(action)
    return True

  def _glanced(self, action: str) -> None:
    """Turns Asger's head to the input working 'action' (from his eyes
    only: the chase view's camera is the mouse's alone)."""
    if self.inside:
      self.cockpit.glanced(WORKED_BY.get(action, action))

  def _taken(self, action: str) -> None:
    """Lets the ascent guidance go if 'action' takes the controls."""
    if action in TAKING and self.guidance.on:
      self.guidance.stopped(self.vessel)
      self._noteOf('Ascent guidance off: you took the controls')

  def _acted(self, action: str, back: bool = False) -> None:
    """Does what 'action' asks (a key, a click on the cabin's input or on
    the board's lamp; 'back': a right click, the other way): the input's
    key sinks if it is one."""
    vessel, keeper, system = self.vessel, self.keeper, self.system
    pilot, engine = vessel.autopilot, vessel.engine
    self._taken(action)
    self.instruments.pressed(action)
    if action in ('hold', 'prograde', 'retrograde'):
      pilot.engaged('off' if pilot.mode == action else action, vessel.turn)
    elif action == 'aim':
      if pilot.mode == 'aim':
        pilot.engaged('off', vessel.turn)
      else:
        vessel.aimNudged(system, 0.0, 0.0)
    elif action == 'full':
      engine.throttled(1.0)
    elif action == 'cut':
      engine.throttled(0.0)
    elif action == 'throttle':
      engine.throttled(engine.throttle + (-CLICK_THROTTLE if back
                                          else CLICK_THROTTLE))
    elif action == 'ascent':
      if self.guidance.on:
        self.guidance.stopped(vessel)
      else:
        self.guidance.started(vessel, system)
    elif action in ('higher', 'lower', 'orbit'):
      self.guidance.targeted(-1 if action == 'lower' or back else 1)
    elif action in ('faster', 'warp') and not back:
      why = self._noWarp()
      if why:
        self._noteOf('No warp: %s' % why)
      else:
        keeper.faster()
    elif action in ('slower', 'warp'):
      keeper.slower()
    elif action == 'stop':
      keeper.realtime()
    elif action == 'toAp':
      self._toApoapsis()
    elif action == 'map':
      self.mapOpen = not self.mapOpen
      if self.mapOpen:
        self.pointer.letGo()
        self.orrery.opened(vessel, system)
    elif action == 'pad':
      if self.mapOpen:
        self.orrery.opened(vessel, system)
      else:
        self._padded()
    elif action == 'view':
      self.inside = not self.inside
    elif action == 'buckle':
      self._buckled()
    elif action in ('limit', 'limit up', 'limit down'):
      self._limited(action == 'limit down' or (action == 'limit' and back))
    elif action == 'eat':
      self._noteOf(self.vitals.ate() or 'Asger eats a ration (RCIR)')
    elif action in ('gravity', 'heavier', 'lighter'):
      lighter = action == 'lighter' or (action == 'gravity' and back)
      if self.cockpit.heavier(-1 if lighter else 1):
        self._noteOf('Gravity %s' % _gravityText(self.cockpit.weight()))
    elif action == 'play':
      self.instruments.deck.play()
    elif action == 'halt':
      self.instruments.deck.halt()
    elif action == 'eject':
      self.instruments.deck.eject()

  def _upPressed(self, key: object) -> bool:
    """Acts on a key pressed while Asger is out of his chair: his legs'
    keys (held; Space a leap), the view's own keys and B; the dashboard's
    others he cannot reach from here (said)."""
    if key in MOVING:
      return True
    if key == Qt.Key.Key_Space:
      self._leaping = True
      return True
    if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control) or key in ROLLING:
      return True
    action = KEY_ACTIONS.get(key)
    if action is None:
      return False
    if action in UP_KEYS:
      self._acted(action)
    else:
      self._noteOf('Asger is out of his chair: B sits him down (or reach'
                   ' the input and click it)')
    return True

  def _buckled(self, ) -> None:
    """Gets Asger up out of his chair, or sits him down if he is near
    enough to it (said either way); dead, wakes him whole in it."""
    cockpit = self.cockpit
    if self.vitals.cause is not None:
      self.vitals.revived()
      cockpit.strappedIn()
      self._noteOf('Asger wakes in his chair')
    elif cockpit.crewman.buckled:
      cockpit.gotUp()
      self._noteOf('Asger is up: W A S D, Space, B to sit again')
    elif cockpit.satDown():
      self._noteOf('Asger sits')
    else:
      self._noteOf('Too far from the chair (%.1f m): within %.0f m'
                   % (cockpit.crewman.seatFar(), SIT))

  def _limited(self, down: bool) -> None:
    """Moves the engine's limiter a notch down (or up), said."""
    engine = self.vessel.engine
    notch = max(0, min(len(LIMITS) - 1, limitNotch(engine)
                       + (-1 if down else 1)))
    engine.limited(LIMITS[notch] * G0 * MASS)
    self._noteOf('Engine limited to %g g' % LIMITS[notch]
                 if notch < len(LIMITS) - 1 else 'Engine unlimited (%g g)'
                 % LIMITS[notch])

  def _lived(self, real: float) -> None:
    """Lives Asger 'real' s on, pulled as hard as the cabin pulls where
    he is (in his chair: at his eyes); says it if that killed him."""
    cockpit, crewman = self.cockpit, self.cockpit.crewman
    if crewman.buckled:
      pull = self.accelerometer.pullAt(EYE, (0.0, 0.0, 0.0),
                                       cockpit.weight())
    else:
      pull = self.accelerometer.pullAt(crewman.middle, crewman.velocity,
                                       cockpit.weight())
    alive = self.vitals.cause is None
    self.vitals.lived(real, norm(pull) / G0)
    if alive and self.vitals.cause is not None:
      self._noteOf('Asger died: %s' % self.vitals.cause)

  def _cabinMoved(self, real: float) -> None:
    """Moves what is loose in the cabin 'real' s on: Asger (righted
    against the pull on him, his legs as the keys held want, a leap
    once) and the loose things."""
    cockpit, accelerometer = self.cockpit, self.accelerometer
    crewman, weight = cockpit.crewman, cockpit.weight()
    want = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0))
    if not crewman.buckled and self.vitals.cause is None:
      pull = accelerometer.pullAt(crewman.middle, crewman.velocity, weight)
      crewman.righted(pull, real)
      held = {MOVING[key] for key in self.held if key in MOVING}
      wanted, walking, wanting = crewman.wantOf(held, cockpit.yaw,
                                                cockpit.pitch, pull)
      leap = crewman.leapOf(pull) if self._leaping else (0.0, 0.0, 0.0)
      want = (wanted, walking, wanting, leap)
    self._leaping = False
    self.world.stepped(real, accelerometer, crewman, weight, want)

  def _dash(self, ) -> dict:
    """Returns what the cabin shows now: the instruments', the loose
    things where they are, the pull at the candles (g)."""
    dash = self.instruments.dash()
    dash['loose'] = self.world.shown()
    pull = self.accelerometer.pullAt(candleLight(), (0.0, 0.0, 0.0),
                                     self.cockpit.weight())
    dash['weight'] = norm(pull) / G0
    return dash

  def _seen(self, ) -> tuple:
    """Returns where the eye is from the vessel's middle, the way it
    looks and its up: Asger's eyes (sunk by the thrust, shaken by the
    engine) or the chase camera's."""
    vessel = self.vessel
    if not self.inside:
      return self.chase.eyeOf(vessel, self.system)
    engine = vessel.engine
    felt = self.accelerometer.felt[2] / G0 + self.cockpit.weight()
    eye = self.cockpit.eyeOf(felt, engine.throttle)
    look, up = self.cockpit.looking()
    turn = vessel.turn
    return rotated(turn, eye), rotated(turn, look), rotated(turn, up)

  def _looked(self, ) -> str:
    """Returns the action of the input Asger looks at ('' none)."""
    control = self.cockpit.lookedAt()
    return control.action if control else ''

  def _used(self, back: bool) -> None:
    """Works the input Asger looks at ('back': a right click, the other
    way: the slide down, the knobs back); dead, nothing."""
    action = self._looked()
    if action and self.vitals.cause is None:
      self._acted(action, back)

  def _steered(self, real: float) -> None:
    """Sets the throttle and the roll from the keys held, and moves the
    aim on while its keys are held past a tap."""
    held, engine, vessel = self.held, self.vessel.engine, self.vessel
    now = time.perf_counter()
    if not self.cockpit.crewman.buckled or self.vitals.cause is not None:
      vessel.steered(0.0, 0.0, 0.0)
      return
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
    """Shows 'text' a few seconds (and types it, inside)."""
    self.note, self._noted = text, time.perf_counter()
    self.instruments.printer.said(text)

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
            'map': self.mapOpen, 'held': sorted(held),
            'gravity': _gravityText(self.cockpit.weight()),
            'limit': '%g g' % LIMITS[limitNotch(self.vessel.engine)],
            'up': not self.cockpit.crewman.buckled}

  def _mapMouse(self, kind: object, event: object) -> bool:
    """Takes the mouse on the map: a drag turns it, the wheel zooms, a
    click on a mark looks at what it marks."""
    if kind == QEvent.Type.MouseButtonPress:
      self._dragFrom = self._clickedAt = event.position()
      self._dragged = False
      return True
    if kind == QEvent.Type.MouseMove and self._dragFrom is not None:
      at = event.position()
      moved = at - self._dragFrom
      self._dragFrom = at
      if (at - self._clickedAt).manhattanLength() > 4.0:
        self._dragged = True
      self.orrery.turned(moved.x(), moved.y())
      return True
    if kind == QEvent.Type.MouseButtonRelease:
      if not self._dragged and self._clickedAt is not None:
        self._picked(self._clickedAt)
      self._dragFrom = self._clickedAt = None
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
    lines.append('%.0f fps, flight %.2f ms (%d steps)%s' % (
      self.viewport.fps, self.flight.lastMs, self.flight.lastSteps,
      '' if self.speaker.trouble is None else ', no sound: %s'
                                              % self.speaker.trouble))
    if self.note and time.perf_counter() - self._noted < NOTE_LASTS:
      lines.append(self.note)
    return '\n'.join(lines)


def _gravityText(weight: float) -> str:
  """Returns the gravity enchantment's pull in words: '0 g', '0.3 g',
  '1 g'."""
  return '%s g' % ('%.1f' % weight).rstrip('0').rstrip('.')
