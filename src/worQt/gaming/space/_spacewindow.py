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
import random
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
from ._bolts import holdOf, rocketBolts, stationBolts
from ._cabinmixer import CRASH, CRASHES, DOCKS, EATS, HURTS, THRUSTING
from ._cabinmixer import THUD, THUDS
from ._cabinmixer import LAUGHS, TOLD, TOWING, TOWS
from ._chasecamera import ChaseCamera
from ._cockpit import CUSHION, EYE, LIMITS, THRUSTS, Cockpit
from ._dockingguidance import RCS_ACCEL, REACH, DockingGuidance
from ._dockingport import DockingPort
from ._crewman import MIDDLE, PUSH, SIT
from ._dashpictures import picturesReady
from ._furnishings import candleLight, sofaSeat
from ._instruments import Instruments, limitNotch
from ._navball import Navball
from ._orrery import Orrery, lengthText, timeText
from ._approach import closestApproach
from ._gunbeam import muzzle, strengthOf
from ._elevator import ARRIVED, AWAY, DECK_STOP, HUB_STOP, Elevator
from ._kolonihave import gardenSolids
from ._night import MORNING, morningIn, nightIn
from ._quest import Quest
from ._rendezvousguidance import RendezvousGuidance
from ._stationinterior import DECK, HUB_INSIDE, PLANE, cabinInside, roomOf
from ._stationinterior import shaftWays
from ._planets import PAD, julianOf, solarSystemOn
from ._scenery import Scenery
from ._sleep import Sleep
from ._spaceviewport import SpaceViewport
from ._station import SPIN, Station
from ._teleprinter import ICONS
from ._timekeeper import Timekeeper
from ._turns import cross, dot, norm, quaternionOf, rotated, unit
from ._vessel import MASS, Vessel
from ._vitals import EATING, Vitals
from ._walkway import PLATFORM_FAR, Walkway, doorwayInside
from ._cockpit import FLOOR, inCabin

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
#  The game starts outside (user, 2026-11-17: "Asger must start outside
#  in the night where we can reasonably spot Terra Prime from the
#  ground"): at night on the pad (now if it is dark with 'NIGHT_LEFT' s
#  of it left, else 'INTO_NIGHT' s after the next dusk), Terra Prime
#  'RISEN' rad of its path short of overhead (over him a minute on),
#  Asger on the tower's platform facing the walkway. False (the render
#  and window scripts): in his chair, now, the walkway away.
START_OUTSIDE = True
NIGHT_LEFT = 3600.0
INTO_NIGHT = 3600.0
RISEN = 0.06
#  He comes to the pad without his dinner (the quest's fourth step: "Eat
#  food"): this hungry, points of food.
SUPPERLESS = 12.0
#  Launching with the walkway still out, Asger is laughed at (user,
#  2026-11-17: "have risitas laugh at Asger and then restate the quest
#  info"), no more often than every 'LAUGH_EVERY' real s.
LAUGH_EVERY = 5.0
#  Something this near the doorway (m from it) keeps the door open.
DOORWAY_CLEAR = 0.35
STUCK = 60.0
#  The last readying step's words (the scene furnished on Qt's thread).
FURNISHING = 'furnishing the cabin (the deck, the room, the dashboard)'
#  The throttle's keys (user, 2026-11-17: "key_SHIFT is reserved to
#  getting up out of the chair": the throttle left Shift and Ctrl for +
#  and -; = is + unshifted on a US board): how fast they open and close
#  it, a s.
THROTTLE_UP = (Qt.Key.Key_Plus, Qt.Key.Key_Equal)
THROTTLE_DOWN = (Qt.Key.Key_Minus,)
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
CAPS = {Qt.Key.Key_Shift: 'Shift', Qt.Key.Key_Plus: '+',
        Qt.Key.Key_Equal: '+', Qt.Key.Key_Minus: '\u2212',
        Qt.Key.Key_Z: 'Z', Qt.Key.Key_X: 'X', Qt.Key.Key_T: 'T',
        Qt.Key.Key_F: 'F', Qt.Key.Key_R: 'R', Qt.Key.Key_W: 'W',
        Qt.Key.Key_S: 'S', Qt.Key.Key_A: 'A', Qt.Key.Key_D: 'D',
        Qt.Key.Key_Q: 'Q', Qt.Key.Key_E: 'E', Qt.Key.Key_Comma: ',',
        Qt.Key.Key_Period: '.', Qt.Key.Key_Slash: '/', Qt.Key.Key_G: 'G',
        Qt.Key.Key_J: 'J', Qt.Key.Key_BracketLeft: '[',
        Qt.Key.Key_BracketRight: ']', Qt.Key.Key_M: 'M',
        Qt.Key.Key_Backspace: '⌫', Qt.Key.Key_V: 'V',
        Qt.Key.Key_P: 'P', Qt.Key.Key_O: 'O', Qt.Key.Key_I: 'I',
        Qt.Key.Key_B: 'B',
        Qt.Key.Key_Y: 'Y', Qt.Key.Key_U: 'U', Qt.Key.Key_Up: '\u2191',
        Qt.Key.Key_Down: '\u2193', Qt.Key.Key_Left: '\u2190',
        Qt.Key.Key_Right: '\u2192', Qt.Key.Key_PageUp: 'PgUp',
        Qt.Key.Key_PageDown: 'PgDn', Qt.Key.Key_K: 'K', Qt.Key.Key_L: 'L',
        Qt.Key.Key_C: 'C', Qt.Key.Key_Delete: 'Del'}
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
               Qt.Key.Key_I: 'eject', Qt.Key.Key_B: 'buckle',
               Qt.Key.Key_Y: 'limit down', Qt.Key.Key_U: 'limit up',
               Qt.Key.Key_K: 'camera', Qt.Key.Key_L: 'match',
               Qt.Key.Key_C: 'autodock', Qt.Key.Key_Delete: 'undock'}
#  The docking thrusters' keys (user, 2026-11-17: docking by hand for
#  the try-hards): held, each pushes its way ('_cockpit.THRUSTS'); a
#  click on the dashboard's key pushes 'PULSE' s.
THRUST_KEYS = {Qt.Key.Key_Up: 'rcs up', Qt.Key.Key_Down: 'rcs down',
               Qt.Key.Key_Left: 'rcs left', Qt.Key.Key_Right: 'rcs right',
               Qt.Key.Key_PageUp: 'rcs ahead',
               Qt.Key.Key_PageDown: 'rcs back'}
KEY_ACTIONS.update(THRUST_KEYS)
PULSE = 0.3
#  The monitor shows the docking's numbers within 'DOCK_SHOWN' m of the
#  station's port; MATCH turns with the station within 'MATCH_REACH' m.
DOCK_SHOWN = 5e3
MATCH_REACH = 5e4
#  The readout says how far the station is within this, m.
STATION_SAID = 2e6
#  Time is not warped within this of the station's port (its solids met
#  in short steps; its antennas sweep out to 1.2 km), m.
WARP_CLEAR = 2e3
#  Up, looking within this of his chair's cushion, E sits him, rad.
CHAIR_AIM = math.radians(25.0)
#  E within this of an elevator's stop's door calls it there, m.
CALL_REACH = 6.0
#  The station's rooms as the readout says them.
ROOMS_SAID = {'hatch': 'the hatch', 'port': 'the docking port',
              'hub': 'the hub', 'shaft': 'a spoke\'s shaft',
              'ring': 'the ring\'s deck'}
#  The gravity gun holding a bolt: its beam turns this fast (rad/s), the
#  gun shakes this much as it strains (m: user, 2026-11-17, "give the
#  gravity gun some cool animations, like a laser beam").
BEAM_TURNS = 9.0
STRAIN = 0.002
#  The hatch's lid opens (and closes) most of the way in this, s.
HATCH_EASE = 0.5
#  The closest approach to the station is worked out anew this often,
#  s of real time (some 2 ms each).
CLOSEST_EVERY = 0.25
#  The rendezvous's phases as the board and the readout say them.
RENDEZVOUS_SAID = {'plane': 'to its plane', 'wait': 'waiting',
                   'burn': 'burning', 'coast': 'coasting',
                   'match': 'matching'}
#  The cabin's input each action is worked by (Asger glances at it: user,
#  2026-11-16: "When I press a keyboard key my view will turn to center
#  on that key"), where it differs from the action's own.
WORKED_BY = {'faster': 'warp', 'slower': 'warp', 'higher': 'orbit',
             'lower': 'orbit', 'aim': 'aim', 'throttle': 'throttle',
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
HINT = ('click: look round   wheel: zoom   Esc: free the mouse   click a'
        ' lamp: do it   V: Asger\'s eyes   Shift: get up   E at the chair:'
        ' sit')
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
    if START_OUTSIDE:
      self.began += timedelta(0, _nightStart(self.began))
    self.system = solarSystemOn(julianOf(self.began))
    self.keeper = Timekeeper(self.system)
    self.station = (Station(self.system, -RISEN) if START_OUTSIDE else
                    Station(self.system))
    self.walkway, self.quest = Walkway(START_OUTSIDE), Quest()
    self._manualOpen, self._laughedAt = False, -LAUGH_EVERY
    self.vessel = Vessel()
    self.guidance = AscentGuidance()
    self.accelerometer, self.world, self._leaping = (Accelerometer(), None,
                                                     False)
    self.vitals, self.bolts, self._tows = Vitals(), rocketBolts(), 0
    self.sleep = Sleep()
    self.docking = DockingPort(self.station)
    self.autodock, self._docks = DockingGuidance(), 0
    self._crashes, self._crash, self._bumping = 0, 0.0, False
    self._closest, self._closestAt, self._closestReal = None, 0.0, 0.0
    self.elevators = [Elevator() for _ in range(4)]
    self._stationed, self._hatch, self._garden = False, 0.0, None
    self._beamSince, self._shaking = 0.0, random.Random(3)
    self.rendezvous = RendezvousGuidance(self.station)
    self._armed, self._laughs = False, 0
    self._noseCamera, self._pulses, self._reading = False, {}, None
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
    self._started()

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
    self._launchKept(now)
    vessel.aimKept(system)
    self._sleepKept(now)
    self._warpKept()
    seconds = keeper.secondsOf(real)
    self._docking()
    if not vessel.docked:
      self.flight.flown((vessel,), system, keeper.now, seconds, math.inf,
                        self.station)
      self._bumped()
    keeper.ticked(seconds)
    self._dockedOrNot()
    self._approachKept(now)
    self.accelerometer.measured(vessel, system, seconds, keeper.factor > 1)
    self._cabinMoved(real)
    self._lived(real)
    self.instruments.switched = {'autodock': (self.autodock.on
                                              or self.rendezvous.on
                                              or self._armed),
                                 'camera': self._noseCamera}
    self.instruments.acted(real, vessel, system, keeper, self.guidance,
                           self.mapOpen, self.inside, self._header())
    told = list(self.instruments.told(vessel, system, self.inside))
    told[THUDS], told[THUD] = self.world.thuds, self.world.loudest
    told[HURTS], told[EATS] = self.vitals.hurts, self.vitals.meals
    told[TOWING] = 0.0 if self.cockpit.crewman.towTo is None else 1.0
    told[TOWS] = self._tows
    told[THRUSTING] = min(1.0, norm(vessel.rcs) / (RCS_ACCEL * MASS))
    told[DOCKS] = self._docks
    told[CRASHES], told[CRASH] = self._crashes, self._crash
    told[LAUGHS] = self._laughs
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
    stamp = (self.began + timedelta(seconds=keeper.elapsed)).strftime(
      '%Y-%m-%d  %H:%M:%S')
    viewport.cockpitShown(self.inside, self._prompt(),
                          self.instruments.printer.paper(), stamp)
    viewport.hudShown(self._readout(), MAP_HINT if self.mapOpen else HINT,
                      '')
    viewport.monitorShown(self._noseCamera, self._dockText())
    vitals = self.vitals
    viewport.vitalsShown(vitals.health, vitals.food, vitals.hurt,
                         1.0 - vitals.eating / EATING if vitals.eating
                         else 0.0, vitals.cause or '')
    viewport.sleepShown(self.sleep.shade(now))
    self._questKept()
    viewport.questShown(self.quest.rows())
    viewport.manualShown(self._manualOpen)

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
      from ._transfers import Transfers
      took = preloadedFlight(device)
      self.rendezvous.transfers = Transfers(device)
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
    if self._manualOpen:
      if key in (Qt.Key.Key_E, Qt.Key.Key_Escape):
        self._manualOpen = False
      return True
    if key == Qt.Key.Key_Escape:
      self.pointer.letGo()
      return True
    if self.vitals.cause is not None:
      action = KEY_ACTIONS.get(key)
      if action in DEAD_KEYS:
        self._acted(action)
      return True
    if self.sleep.on:
      return True
    if key == Qt.Key.Key_E and self.inside:
      self._used(False)
      return True
    if key == Qt.Key.Key_Shift:
      crewman = self.cockpit.crewman
      if crewman.buckled:
        self._gotUp()
      elif crewman.lounge is not None:
        crewman.offSofa()
        self._noteOf('Asger gets up off the sofa')
      return True
    if not self.cockpit.crewman.buckled:
      return self._upPressed(key)
    if key in AIMING:
      up, right = AIMING[key]
      self._taken('aim')
      self.vessel.aimNudged(self.system, up * AIM_STEP, right * AIM_STEP)
      self._glanced('aim')
      return True
    if key in THROTTLE_UP + THROTTLE_DOWN:
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
    """Lets the ascent guidance, the rendezvous and the automatic
    docking go if 'action' takes the controls (said)."""
    if action not in TAKING:
      return
    if self.guidance.on:
      self.guidance.stopped(self.vessel)
      self._noteOf('Ascent guidance off: you took the controls')
    if self.rendezvous.on or self.autodock.on:
      self.rendezvous.stopped(self.vessel)
      self.autodock.stopped(self.vessel)
      self.keeper.realtime()
      self._noteOf('Auto docking off: you took the controls')

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
      elif self._aboardWhy():
        self._noteOf('Not back to the pad: %s' % self._aboardWhy())
      else:
        vessel.docked = False
        self._padded()
    elif action == 'view':
      self.inside = not self.inside
    elif action == 'buckle':
      self._buckled()
    elif action in ('limit', 'limit up', 'limit down'):
      self._limited(action == 'limit down' or (action == 'limit' and back))
    elif action.startswith('rcs '):
      self._pulses[action] = time.perf_counter() + PULSE
    elif action == 'camera':
      self._noseCamera = not self._noseCamera
    elif action in ('match', 'autodock', 'undock'):
      self._docked(action)
    elif action == 'eat':
      why = self.vitals.ate()
      self._noteOf(why or 'Asger eats a ration (RCIR)')
      if not why:
        self._questTicked('ate')
    elif action in ('door', 'door outside'):
      self._doorWorked()
    elif action == 'lock':
      why = self.walkway.locking()
      self._noteOf(why or ('The door is locked' if self.walkway.locked
                           else 'The door is unlocked'))
    elif action == 'walkway':
      self._dismissed()
    elif action == 'manual':
      self._manualOpen = True
      self._questTicked('read')
    elif action == 'lounge':
      self.cockpit.crewman.lounged(*sofaSeat())
      self._questTicked('lounged')
      self._noteOf('Asger chills out on the sofa (Shift: get up)')
    elif action == 'sleep':
      self._slept()
    elif action == 'play':
      self.instruments.deck.play()
    elif action == 'halt':
      self.instruments.deck.halt()
    elif action == 'eject':
      self.instruments.deck.eject()

  def _upPressed(self, key: object) -> bool:
    """Acts on a key pressed while Asger is out of his chair: his legs'
    keys (held; Space a leap), the view's own keys and B (Shift: he is
    up already); the dashboard's others he cannot reach from here
    (said)."""
    if key in MOVING:
      return True
    if key == Qt.Key.Key_Space:
      self._leaping = True
      return True
    if key in THROTTLE_UP + THROTTLE_DOWN or key in ROLLING:
      return True
    if key == Qt.Key.Key_Shift:
      return True
    action = KEY_ACTIONS.get(key)
    if action is None:
      return False
    if action in UP_KEYS:
      self._acted(action)
    else:
      self._noteOf('Asger is out of his chair: E at the chair sits him'
                   ' down (or reach the input and click it)')
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
      self._gotUp()
    elif cockpit.satDown():
      self._noteOf('Asger sits')
    else:
      self._noteOf('Too far from the chair (%.1f m): within %.0f m'
                   % (cockpit.crewman.seatFar(), SIT))

  def _started(self, ) -> None:
    """Starts the game: outside (user, 2026-11-17: "Asger must start
    outside in the night where we can reasonably spot Terra Prime from
    the ground"), Asger up on the tower's platform facing the walkway,
    looking up a little, told the first step; else in his chair, the
    walkway's steps done."""
    if not START_OUTSIDE:
      for name in ('aboard', 'locked', 'dismissed'):
        self.quest.ticked(name)
      return
    cockpit = self.cockpit
    cockpit.gotUp()
    crewman = cockpit.crewman
    crewman.placed((PLATFORM_FAR + 1.2, 0.0, FLOOR + 0.002 + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    cockpit.yaw, cockpit.pitch = 0.0, 0.35
    self.vitals.food = SUPPERLESS
    self._noteOf('Night on the pad, Terra Prime passing over: look up. '
                 'Then: %s' % self.quest.textOf(self.quest.current))

  def _promptOf(self, control: object) -> str:
    """Returns what working 'control' does now (the door's keys as the
    door is: open or shut, locked or not)."""
    walkway = self.walkway
    if control.action in ('door', 'door outside'):
      return 'Close the door' if walkway.wanted else 'Open the door'
    if control.action == 'lock':
      return 'Unlock the door' if walkway.locked else 'Lock the door'
    return control.peep.prompt()

  def _doorWorked(self, ) -> None:
    """Opens the door, or closes it if nothing is in the doorway
    (said)."""
    walkway = self.walkway
    if walkway.wanted:
      if self._inDoorway():
        self._noteOf('Something is in the doorway')
        return
      walkway.closed()
      self._noteOf('The door slides shut')
      return
    why = walkway.opened()
    self._noteOf(('The door stays shut: %s' % why) if why else
                 'The door slides open')

  def _inDoorway(self, ) -> bool:
    """Returns whether Asger or something loose is in the doorway."""
    crewman = self.cockpit.crewman
    points = [place for place, _ in self.world.shown()]
    if not crewman.sitting:
      points += [crewman.middle, crewman.soles()]
    return any(doorwayInside(point) > -DOORWAY_CLEAR for point in points)

  def _dismissed(self, ) -> None:
    """Sends the walkway away if Asger and everything loose are in the
    cabin (said)."""
    crewman = self.cockpit.crewman
    if not crewman.sitting and not inCabin(crewman.middle):
      self._noteOf('Asger is out on the walkway')
      return
    if any(not inCabin(place) for place, _ in self.world.shown()):
      self._noteOf('Something loose is out on the walkway')
      return
    why = self.walkway.dismissed()
    self._noteOf(why or 'The walkway swings back to the tower')

  def _launchKept(self, now: float) -> None:
    """On the ground with the walkway still out, the engine stays shut
    and the ascent guidance stops: Risitas laughs at Asger (user,
    2026-11-17: "have risitas laugh at Asger and then restate the quest
    info"), and the next step is said again."""
    vessel = self.vessel
    if not vessel.touching or self.walkway.away:
      return
    if vessel.engine.throttle <= 0.0 and not self.guidance.on:
      return
    vessel.engine.throttled(0.0)
    if self.guidance.on:
      self.guidance.stopped(vessel)
    if now - self._laughedAt < LAUGH_EVERY:
      return
    self._laughedAt, self._laughs = now, self._laughs + 1
    current = self.quest.current
    self._noteOf('Risitas laughs at Asger: the walkway is still out. %s'
                 % ('Next: %s' % self.quest.textOf(current) if current
                    else ''))

  def _questKept(self, ) -> None:
    """Ticks off the quest's steps done this frame (said)."""
    quest, vessel = self.quest, self.vessel
    crewman = self.cockpit.crewman
    done = quest.done
    checks = (
      ('aboard', not crewman.sitting and inCabin(crewman.middle)),
      ('locked', self.walkway.locked and 'aboard' in done),
      ('dismissed', not self.walkway.attached),
      ('seated', crewman.buckled and 'aboard' in done),
      ('armed', self._armed or self.rendezvous.on),
      ('launched', not vessel.touching and 'launched' not in done
       and vessel.heightOver(self.system) > 30.0),
      ('orbit', 'launched' in done and 'orbit' not in done
       and self._inOrbit()),
      ('docked', vessel.docked))
    for name, met in checks:
      if met and name not in done:
        self._questTicked(name)
    if vessel.docked and not crewman.sitting:
      room = roomOf(crewman.middle, shaftWays(self.docking.relative))
      if room == 'hub':
        self._questTicked('hub')
      elif room == 'ring':
        self._questTicked('deck')

  def _questTicked(self, name: str) -> None:
    """Ticks off quest step 'name' (or a part of one), saying it and the
    next if that finished it."""
    quest = self.quest
    step = name if name not in ('ate', 'lounged') else 'rested'
    if not quest.ticked(name):
      return
    current = quest.current
    done = quest.textOf(step)
    self._noteOf('Done: %s%s %s' % (done, '' if done.endswith('!') else
                                    '.', ('Next: %s' % quest.textOf(
      current)) if current else 'Welcome to Asger\'s kolonihave i '
                                'rummet!'))

  def _slept(self, ) -> None:
    """Puts Asger to bed till morning if it is night where the rocket
    is (user, 2026-11-17: "Asger should be able to key_E into bed to
    advance the time to morning if it is dark, otherwise it should say
    like in Minecraft, 'you can only sleep at night'"), said either way;
    not while the rocket may not be left to itself ('_sleepWhy')."""
    why = self._sleepWhy()
    if why:
      self._noteOf('You may not sleep now: %s' % why)
      return
    wait = morningIn(self.system, self.vessel, self.keeper.now)
    if wait is None:
      self._noteOf('You can only sleep at night')
      return
    self.sleep.lay(time.perf_counter(), wait, self.keeper.elapsed)
    self._noteOf('Asger goes to bed')

  def _sleepWhy(self, ) -> str:
    """Returns why Asger may not sleep now ('' he may): on the ground,
    the engine burning; off it, whatever stops a warp; the automatic
    systems flying."""
    vessel = self.vessel
    if self.autodock.on or self.rendezvous.on or self.guidance.on:
      return 'the automatic systems are flying'
    if vessel.touching:
      return 'the engine burns' if vessel.engine.throttle > 0.0 else ''
    return self._noWarp()

  def _sleepKept(self, now: float) -> None:
    """Keeps Asger's sleep: the screen dark, time is sent on to the
    morning (leapt on the ground, the rocket carried round with it;
    warped off it); there (or the warp ended), he wakes, said."""
    sleep, keeper, vessel = self.sleep, self.keeper, self.vessel
    if not sleep.on or sleep.woke is not None:
      return
    if sleep.due(now):
      sleep.sent = True
      if vessel.touching:
        vessel.carried(self.system, sleep.wait)
        keeper.leapt(sleep.wait)
        self.accelerometer.reset()
      else:
        keeper.aim(sleep.wait)
      return
    if sleep.sent and keeper.aimed is None:
      sleep.waking(now)
      slept = max(0.0, keeper.elapsed - (sleep.until - sleep.wait))
      self._noteOf('Good morning! Asger slept %d h %02d min' % (
        slept // 3600.0, (slept % 3600.0) // 60.0))

  def _gotUp(self, ) -> None:
    """Gets Asger up out of his chair (user, 2026-11-17: Shift), said."""
    self.cockpit.gotUp()
    self._noteOf('Asger is up: W A S D, Space; E at the chair sits him;'
                 ' click a glowing bolt: the gun pulls him there')

  def _chairAimed(self, ) -> bool:
    """Returns whether Asger, up, looks at his chair within 'SIT' of it
    (E or a click sits him there: user, 2026-11-17, "Asger needs a way to
    get in an out of the seat")."""
    cockpit = self.cockpit
    crewman = cockpit.crewman
    if crewman.buckled or crewman.seatFar() > SIT:
      return False
    eye = cockpit.eye()
    toward = unit(tuple(c - e for c, e in zip(CUSHION[0], eye)))
    return dot(toward, cockpit.looking()[0]) > math.cos(CHAIR_AIM)

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
    he is (in his chair: at his eyes, and the chair keeps the pull from
    hurting him), hurt by what he met hard out of it (user, 2026-11-17:
    falls); says it if that killed him (the gun lets him go)."""
    crewman = self.cockpit.crewman
    alive = self.vitals.cause is None
    if crewman.buckled:
      pull = self.accelerometer.pullAt(EYE, (0.0, 0.0, 0.0))
    else:
      pull = self.accelerometer.pullAt(crewman.middle, crewman.velocity)
      self.vitals.fell(self.world.landed)
    self.vitals.lived(real, norm(pull) / G0, crewman.buckled)
    if alive and self.vitals.cause is not None:
      crewman.letGo()
      self._noteOf('Asger died: %s' % self.vitals.cause)

  def _cabinMoved(self, real: float) -> None:
    """Moves what is loose in the cabin 'real' s on: Asger (righted
    against the pull on him, his legs as the keys held want, a leap
    once: held at a magic bolt, a push off it; or the gravity gun
    pulling him) and the loose things."""
    cockpit, accelerometer = self.cockpit, self.accelerometer
    crewman = cockpit.crewman
    want = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0), 0)
    if not crewman.buckled and self.vitals.cause is None:
      pull = accelerometer.pullAt(crewman.middle, crewman.velocity)
      crewman.righted(pull, real)
      held = {MOVING[key] for key in self.held if key in MOVING}
      wanted, walking, wanting = crewman.wantOf(held, cockpit.yaw,
                                                cockpit.pitch, pull)
      leap, sure = (0.0, 0.0, 0.0), 0
      if self._leaping and crewman.towing is not None:
        way = self.bolts[crewman.towing][1]
        leap, sure = tuple(PUSH * w for w in way), 1
        crewman.letGo()
      elif self._leaping:
        leap = crewman.leapOf(pull)
      want = (wanted, walking, wanting, leap, sure)
    self._leaping = False
    self._aboard(real)
    self.walkway.moved(real)
    self.world.walked(self.walkway.outside)
    self.world.stepped(real, accelerometer, crewman, want)

  def _aboard(self, real: float) -> None:
    """Docked, joins the space station's rooms to the cabin's world (its
    elevators' cages where they are as the frame begins, the world moving
    them through it) and moves its elevators 'real' s on; undocked, takes
    them away again."""
    docked = self.vessel.docked
    self._hatch += ((1.0 if docked else 0.0) - self._hatch) * min(
      1.0, real / HATCH_EASE)
    if docked:
      relative = self.docking.relative
      ways = shaftWays(relative)
      if self._garden is None or self._garden[0] != relative:
        self._garden = relative, gardenSolids(relative)
      self.world.stationed(True, ways, tuple(
        box for elevator, way in zip(self.elevators, ways)
        for box in elevator.boxesOf(way)) + self._garden[1])
      for elevator in self.elevators:
        elevator.moved(real)
      self.bolts = rocketBolts() + stationBolts(ways, tuple(
        elevator.floor for elevator in self.elevators))
    elif self._stationed:
      self.world.stationed(False, (), ())
      self.bolts = rocketBolts()
      if (self.cockpit.crewman.towing or 0) >= len(self.bolts):
        self.cockpit.crewman.letGo()
    self._stationed = docked

  def _elevatorOf(self, ) -> tuple | None:
    """Returns what E does with an elevator for Asger (docked, up): the
    elevator and its stop to send it to, and what it is said to do:
    standing in its cage, the other stop; at a stop's door with the cage
    away, that stop; None: nothing."""
    crewman = self.cockpit.crewman
    if not self.vessel.docked or crewman.buckled:
      return None
    middle = crewman.middle
    ways = shaftWays(self.docking.relative)
    for elevator, way in zip(self.elevators, ways):
      if elevator.holds(way, middle):
        if elevator.target is not None:
          return None
        if elevator.atHub:
          return elevator, DECK_STOP, 'Ride the elevator down to the deck'
        return elevator, HUB_STOP, 'Ride the elevator up to the hub'
    for elevator, way in zip(self.elevators, ways):
      for stop, door in ((HUB_STOP, HUB_INSIDE - 1.0),
                         (DECK_STOP, DECK - 1.0)):
        there = (door * way[0], door * way[1], PLANE)
        if (math.dist(middle, there) < CALL_REACH
                and abs(elevator.floor - stop) > ARRIVED
                and elevator.target != stop):
          return elevator, stop, 'Call the elevator'
    return None

  def _aboardWhy(self, ) -> str:
    """Returns why the rocket may not leave the station ('' it may):
    Asger, or something loose, aboard it (out of the cabin)."""
    if not self.vessel.docked:
      return ''
    crewman = self.cockpit.crewman
    if not crewman.buckled and cabinInside(crewman.middle) < 0.0:
      return 'Asger is aboard Terra Prime'
    for place, _ in self.world.shown():
      if cabinInside(place) < 0.0:
        return 'something loose is aboard Terra Prime'
    return ''

  def _dash(self, ) -> dict:
    """Returns what the cabin shows now: the instruments', the loose
    things where they are, the gravity gun (shown out of his chair: his
    eyes' place and frame), the pull at the candles (g)."""
    dash = self.instruments.dash()
    dash['loose'] = self.world.shown()
    cockpit = self.cockpit
    look, up = cockpit.looking()
    right = cross(look, up)
    frame = quaternionOf(tuple((right[k], up[k], -look[k])
                               for k in range(3)))
    held = not cockpit.crewman.buckled and self.vitals.cause is None
    eye = cockpit.eye()
    towing = cockpit.crewman.towing if held else None
    beam = (False,)
    if towing is not None:
      since = time.perf_counter() - self._beamSince
      eye = tuple(e + STRAIN * self._shaking.uniform(-1.0, 1.0)
                  for e in eye)
      start = tuple(e + m for e, m in zip(eye, rotated(frame, muzzle())))
      beam = (True, start, self.bolts[towing][0], BEAM_TURNS * since,
              strengthOf(since))
    dash['gun'] = (held, eye, frame)
    dash['beam'] = beam
    dash['nose'] = self._noseCamera
    dash['hatch'] = self._hatch
    dash['door'], dash['swing'] = self.walkway.door, self.walkway.swing
    dash['sbolts'] = self.bolts[len(rocketBolts()):]
    dash['aboard'] = self.vessel.docked
    cars = []
    if self.vessel.docked:
      for elevator, way in zip(self.elevators, shaftWays(
          self.docking.relative)):
        cars += [(middle, turn, middle != AWAY)
                 for middle, _, turn, _ in elevator.boxesOf(way)]
    dash['cars'] = cars
    pull = self.accelerometer.pullAt(candleLight(), (0.0, 0.0, 0.0))
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
    felt = self.accelerometer.felt[2] / G0
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
    way: the slide down, the knobs back); out of his chair with none in
    reach, the gravity gun: pointed at a magic bolt it pulls him there
    (user, 2026-11-17: "The gravity gun can pull Asger towards them"), a
    right click lets him go; dead, nothing."""
    if self.vitals.cause is not None or self.sleep.on:
      return
    action = self._looked()
    if action:
      self._acted(action, back)
      return
    crewman = self.cockpit.crewman
    if crewman.buckled:
      return
    if back:
      crewman.letGo()
      return
    lift = self._elevatorOf()
    if lift is not None:
      elevator, stop, _ = lift
      elevator.sent(stop)
      return
    if self._chairAimed():
      self._buckled()
      return
    aimed = self.cockpit.boltAimed(self.bolts)
    if aimed is not None:
      crewman.towed(aimed, holdOf(self.bolts[aimed]))
      self._tows += 1
      self._beamSince = time.perf_counter()
      self._noteOf('The gun tries to pick up the bolt; it will not budge,'
                   ' so it pulls Asger instead')

  def _prompt(self, ) -> tuple | None:
    """Returns what Asger's eyes are on to work (its key and what working
    it does): an input in reach; out of his chair, a magic bolt the gun
    points at, or held at one, pushing off it; None: nothing (or not
    his eyes)."""
    if not self.inside or self.vitals.cause is not None:
      return None
    looked = self.cockpit.lookedAt()
    if looked is not None:
      return looked.key, self._promptOf(looked)
    lift = self._elevatorOf()
    if lift is not None:
      return 'E', lift[2]
    if self._chairAimed():
      return 'E', 'Sit down'
    if self.cockpit.boltAimed(self.bolts) is not None:
      return 'Click', 'Pick up the magic bolt'
    if self.cockpit.crewman.towing is not None:
      return 'Space', 'Push off the bolt (right click: let go)'
    return None

  def _steered(self, real: float) -> None:
    """Sets the throttle and the roll from the keys held, and moves the
    aim on while its keys are held past a tap."""
    held, engine, vessel = self.held, self.vessel.engine, self.vessel
    now = time.perf_counter()
    if not self.cockpit.crewman.buckled or self.vitals.cause is not None:
      vessel.steered(0.0, 0.0, 0.0)
      if not (self.autodock.on or self.rendezvous.on):
        vessel.rcs = (0.0, 0.0, 0.0)
      return
    self._thrusted(now)
    if any(key in held for key in THROTTLE_UP):
      engine.throttled(engine.throttle + THROTTLE_RATE * real)
    if any(key in held for key in THROTTLE_DOWN):
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

  def _thrusted(self, now: float) -> None:
    """Fires the docking thrusters as their keys are held or their
    dashboard keys were just clicked ('PULSE'), each its way, together
    as hard as one ('RCS_ACCEL'); firing takes them from the automatic
    docking (said)."""
    ways = [THRUSTS[action] for key, action in THRUST_KEYS.items()
            if key in self.held]
    ways += [THRUSTS[action] for action, until in self._pulses.items()
             if until > now]
    if not ways:
      if not (self.autodock.on or self.rendezvous.on):
        self.vessel.rcs = (0.0, 0.0, 0.0)
      return
    if self.vessel.docked:
      return
    if self.autodock.on or self.rendezvous.on:
      self.autodock.stopped(self.vessel)
      self.rendezvous.stopped(self.vessel)
      self.keeper.realtime()
      self._noteOf('Auto docking off: you took the thrusters')
    total = tuple(sum(way[k] for way in ways) for k in range(3))
    size = norm(total)
    self.vessel.rcs = (0.0, 0.0, 0.0) if size < 1e-9 else tuple(
      RCS_ACCEL * MASS * x / size for x in total)

  def _docked(self, action: str) -> None:
    """Does a docking action: MATCH (turn with the station, nose down
    its axis, or let go), AUTO (dock by itself, or stop), UNDOCK (said
    when it cannot)."""
    vessel, now = self.vessel, self.keeper.now
    reading = self.docking.readingOf(vessel, self.system, now)
    pilot = vessel.autopilot
    if action == 'undock':
      if not vessel.docked:
        self._noteOf('Not docked')
        return
      why = self._aboardWhy()
      if why:
        self._noteOf('No undocking: %s' % why)
        return
      self.docking.released(vessel, self.system, now)
      self.accelerometer.reset()
      self._noteOf('Undocked: pushed off at 0.3 m/s')
    elif action == 'match':
      if pilot.mode == 'match':
        pilot.engaged('off', vessel.turn)
      elif vessel.docked:
        self._noteOf('Docked: Terra Prime turns you')
      elif reading['distance'] > MATCH_REACH:
        self._noteOf('No match: Terra Prime is %.0f km off (within %.0f'
                     ' km)' % (reading['distance'] / 1e3,
                               MATCH_REACH / 1e3))
      else:
        self.docking.aligned(vessel, now)
        pilot.matched(self.docking.turnAt(now), tuple(
          SPIN * a for a in reading['axis']))
    elif self.autodock.on or self.rendezvous.on or self._armed:
      self.autodock.stopped(vessel)
      self.rendezvous.stopped(vessel)
      self._armed = False
      self.keeper.realtime()
      self._noteOf('Rendezvous and docking off')
    elif vessel.docked:
      self._noteOf('Docked already')
    elif reading['distance'] > REACH and not self._inOrbit():
      self._armed = True
      self._noteOf('Rendezvous and docking armed: once in orbit, the'
                   ' engine shut, to Terra Prime and docked')
    elif reading['distance'] > REACH:
      self._rendezvoused()
    else:
      self._autodocked(reading)

  def _inOrbit(self, ) -> bool:
    """Returns whether the rocket is in orbit round Terra Prime's planet
    as the rendezvous asks (its path closed, its periapsis over the air),
    its engine shut and the ascent guidance done: step 1 over."""
    vessel = self.vessel
    if self.guidance.on or vessel.engine.throttle > 0.0 or vessel.touching:
      return False
    if vessel.anchor != self.station.parent:
      return False
    conic = vessel.conicOf(self.system)
    body = self.system.bodies[vessel.anchor]
    top = body.air.top if body.air is not None else 0.0
    return conic is not None and conic.closed and (
      conic.periapsis - body.radius > top)

  def _rendezvoused(self, ) -> None:
    """Starts the rendezvous with Terra Prime (step 2), said; or says
    why not."""
    why = self.rendezvous.started(self.vessel, self.system, self.keeper)
    if why:
      self._noteOf('No rendezvous: %s' % why)
    else:
      self._noteOf('Rendezvous: to Terra Prime, the burn in %s' % (
        timeText(self.rendezvous.depart - self.keeper.elapsed)))

  def _autodocked(self, reading: dict) -> None:
    """Starts the automatic docking from where the rocket is ('reading':
    its nose to the port), the nose's camera on the monitor; or says why
    not."""
    why = self.autodock.started(self.vessel, self.docking, reading,
                                self.keeper.now)
    if why:
      self._noteOf('No auto docking: %s' % why)
    else:
      self._noseCamera = True
      self._noteOf('Auto docking: closing in on Terra Prime')

  def _docking(self, ) -> None:
    """Before the frame's flight: the automatic docking flies (or MATCH
    keeps turning with the station); docked, the engine stays shut."""
    vessel, now = self.vessel, self.keeper.now
    if vessel.docked:
      if vessel.engine.throttle > 0.0:
        vessel.engine.throttled(0.0)
        self._noteOf('Docked: undock first (Del)')
      return
    if self._armed and self._inOrbit():
      self._armed = False
      reading = self.docking.readingOf(vessel, self.system, now)
      if reading['distance'] > REACH:
        self._rendezvoused()
      else:
        self._autodocked(reading)
    if self.rendezvous.on:
      self.rendezvous.acted(vessel, self.system, self.keeper)
    reading = self.docking.readingOf(vessel, self.system, now)
    if self.rendezvous.phase == 'done':
      self.rendezvous.phase = 'off'
      self._autodocked(reading)
    if self.autodock.on:
      self.autodock.acted(vessel, self.docking, reading, now)
      if self.keeper.aimed is None:
        self.keeper.factor = self.autodock.hurried(reading)
    elif vessel.autopilot.mode == 'match':
      vessel.autopilot.matched(self.docking.turnAt(now), tuple(
        SPIN * a for a in reading['axis']))

  def _approachKept(self, now: float) -> None:
    """Works out the closest approach to the station anew every
    'CLOSEST_EVERY' s of real time (a try-hard's aid: the map marks it,
    the readout says it), its time left kept each frame."""
    keeper = self.keeper
    if now - self._closestReal >= CLOSEST_EVERY:
      self._closest = closestApproach(self.vessel, self.system,
                                      self.station, keeper.now)
      self._closestAt, self._closestReal = keeper.elapsed, now
    closest = self._closest
    if closest is not None:
      passed = keeper.elapsed - self._closestAt
      closest = (closest[0] - passed,) + closest[1:]
      if closest[0] < 0.0:
        closest = None
    self.orrery.closest = closest

  def _bumped(self, ) -> None:
    """Counts a hit on the station as the hull first meets it (said,
    how hard; heard), its hardest kept for the sound."""
    bump = self.vessel.bumped
    if bump > 0.0 and not self._bumping:
      self._crashes += 1
      self._crash = bump
      self._noteOf('Hit Terra Prime at %.1f m/s' % bump)
    elif bump > self._crash and self._bumping:
      self._crash = bump
    self._bumping = bump > 0.0

  def _dockedOrNot(self, ) -> None:
    """After the frame's flight: docked, the station carries the rocket;
    else the latch catches it if it may (said, and heard)."""
    vessel, now = self.vessel, self.keeper.now
    if vessel.docked:
      self.docking.heldOn(vessel, self.system, now)
      self._reading = self.docking.readingOf(vessel, self.system, now)
      return
    reading = self.docking.readingOf(vessel, self.system, now)
    self._reading = reading
    if self.docking.caught(reading):
      self.docking.latched(vessel, now)
      self.docking.heldOn(vessel, self.system, now)
      self.autodock.stopped(vessel)
      self.accelerometer.reset()
      self._docks += 1
      self._noteOf('Docked to Terra Prime')

  def _rendezvousText(self, ) -> str:
    """Returns the readout's line of the rendezvous: its phase, and how
    long to the burn (waiting) or to the station's point (on the way)."""
    guide, keeper = self.rendezvous, self.keeper
    said = RENDEZVOUS_SAID[guide.phase]
    if guide.phase in ('plane', 'wait'):
      return 'Rendezvous %s, the burn in %s' % (said, timeText(
        guide.depart - keeper.elapsed))
    return 'Rendezvous %s, there in %s' % (said, timeText(max(
      0.0, guide.arrival - keeper.elapsed)))

  def _dockText(self, ) -> str:
    """Returns the docking's numbers for the monitor (the nose's feed,
    within 'DOCK_SHOWN' of the station's port; '' none): how far, out
    and off the axis, closing how fast, tilted, turning off the
    station's; what flies it."""
    reading = self._reading
    if (not self._noseCamera or reading is None
            or reading['distance'] > DOCK_SHOWN):
      return ''
    vessel = self.vessel
    state = ('DOCKED' if vessel.docked else 'AUTO %s' % self.autodock.phase
             if self.autodock.on else 'AUTO %s' % self.rendezvous.phase
             if self.rendezvous.on else 'MATCH' if vessel.autopilot.mode
             == 'match' else 'BY HAND')
    return ('PORT %7.1f m  OUT %7.1f  OFF %5.1f\n'
            'CLOSE %+6.2f m/s  TILT %4.1f\u00b0  SPIN %+.3f\n%s' % (
              reading['distance'], reading['along'], reading['across'],
              reading['closing'], math.degrees(reading['tilt']),
              reading['turning'], state))

  def _noWarp(self, ) -> str:
    """Returns why time may not be warped now ('' it may): in the air,
    on the ground, the engine or the thrusters firing, near the station
    (within 'WARP_CLEAR' of its port, not docked)."""
    vessel = self.vessel
    body = self.system.bodies[vessel.anchor]
    if vessel.touching:
      return 'on the ground'
    if vessel.engine.throttle > 0.0:
      return 'the engine burns'
    if any(vessel.rcs):
      return 'the docking thrusters fire'
    if not vessel.docked and self._reading is not None and (
        self._reading['distance'] < WARP_CLEAR):
      return 'within %s of Terra Prime' % lengthText(WARP_CLEAR)
    if body.air is not None and vessel.heightOver(self.system) < (
        body.air.top):
      return 'in the air (above %s)' % lengthText(body.air.top)
    return ''

  def _warpKept(self, ) -> None:
    """Ends the warp the moment it may not go on, saying why (the
    automatic docking and rendezvous keep the warp they ask for: the
    docking hurries time while its thrusters fire)."""
    if self.autodock.on or self.rendezvous.on:
      return
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
            'limit': '%g g' % LIMITS[limitNotch(self.vessel.engine)],
            'match': self.vessel.autopilot.mode == 'match',
            'docking': ('docked' if self.vessel.docked else
                        RENDEZVOUS_SAID[self.rendezvous.phase]
                        if self.rendezvous.on else 'armed'
                        if self._armed else self.autodock.phase),
            'nose': self._noseCamera,
            'thrusting': any(self.vessel.rcs),
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
    reading = self._reading
    if reading is not None and reading['distance'] < STATION_SAID:
      lines.append('Terra Prime %-11s %s' % (lengthText(
        reading['distance']), 'docked' if vessel.docked else
        'drifting %s/s' % lengthText(norm(reading['drift']))))
    crewman = self.cockpit.crewman
    if vessel.docked and not crewman.buckled:
      room = roomOf(crewman.middle, shaftWays(self.docking.relative))
      if room and room != 'cabin':
        pull = norm(self.accelerometer.pullAt(crewman.middle,
                                              crewman.velocity))
        lines.append('Aboard     %s, pulled %.2f g' % (ROOMS_SAID[room],
                                                       pull / G0))
    closest = self.orrery.closest
    if closest is not None and (closest[1] < STATION_SAID or (
        reading is not None and reading['distance'] < STATION_SAID)):
      lines.append('Closest    %-12s in %s, passing at %s/s' % (
        lengthText(closest[1]), timeText(closest[0]),
        lengthText(closest[2])))
    pilot = vessel.autopilot
    if pilot.mode == 'aim':
      off = ('off the path %+.0f°' % math.degrees(pilot.turn)
             if pilot.travel else 'heading %03.0f°'
                                  % math.degrees(pilot.heading))
      lines.append('Aim        %+.0f° over the horizon, %s' % (
        math.degrees(pilot.pitch), off))
    if self.rendezvous.on:
      lines.append(self._rendezvousText())
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


def _nightStart(now: datetime) -> float:
  """Returns how long after 'now' the game starts outside: nought if it
  is night on the pad with 'NIGHT_LEFT' s of it left; else 'INTO_NIGHT'
  s after the next dusk there."""
  from ._vessel import LEGS
  system = solarSystemOn(julianOf(now))
  vessel = Vessel()
  vessel.stood(system, system.named('Terra'), PAD[0], PAD[1], 0.0)
  vessel.touching = len(LEGS)
  dusk = nightIn(system, vessel, 0.0)
  if dusk == 0.0:
    morning = morningIn(system, vessel, 0.0)
    if morning - MORNING >= NIGHT_LEFT:
      return 0.0
    vessel.carried(system, morning)
    dusk = morning + nightIn(system, vessel, morning)
  return dusk + INTO_NIGHT
