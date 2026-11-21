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
from typing import TYPE_CHECKING

import numpy
from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtWidgets import QMainWindow

from worQt.gaming.sandbox._pointer import Pointer
from worQt.gaming.sandbox._speaker import Speaker

from ._accelerometer import Accelerometer
from ._aerospike import G0
from ._ascentguidance import AscentGuidance
from ._autoflight import SAID, Autoflight
from ._cabinworld import DOOR, PAD_FACES, ROCKET_FACES, STEP, STILL
from ._cabinmixer import CRASH, CRASHES, DOCKS, EATS, HURTS, THRUSTING
from ._cabinmixer import THUD, THUDS
from ._cabinmixer import FOOD_NEAR, LAUGHS, SNACKS, TOLD
from ._chasecamera import ChaseCamera
from ._cockpit import CUSHION, DIALS, EYE, LAMPS, LIMITS, LIT_KEYS
from ._cockpit import GUARD_HOLD, THRUSTS, Cockpit
from ._dashboard import LEGENDS
from ._dockingguidance import RCS_ACCEL, DockingGuidance
from ._dockingport import DockingPort
from ._egg import Egg
from ._crewman import HEFT, MIDDLE, SIT, Crewman
from ._dashpictures import picturesReady
from ._furnishings import candleLight, looseThings, rationCrate, sofaSeat
from ._deckthings import TELEPORTED, DeckThings, deckThings
from ._deckthings import deckWorldThings
from ._instruments import GUARD_EASE, Instruments, limitNotch
from ._navball import Navball
from ._orrery import Orrery, lengthText, timeText
from ._approach import closestApproach
from ._savegame import SLOTS, SaveGame, keptOf, keptTo, savesListed
from ._savegame import skyOf, skyTo, slotPath
from ._sight import boxGap, inSight
from ._elevator import ARRIVED, AWAY, DECK_STOP, HUB_STOP, Elevator
from ._elevator import CAGE_MASS, CAR_HIGH, HANDLE_ASIDE, PLATE_HALVES
from ._elevator import SEAT_HIGH
from ._kolonihave import gardenSolids
from ._night import MORNING, morningIn, nightIn, restWhy
from ._headlamp import Headlamp
from ._inventory import HOTBAR, Inventory
from ._jetpack import Jetpack
from ._quest import CHECKLIST, Quest
from ._rendezvousguidance import RendezvousGuidance
from ._stationinterior import DECK, PLANE, SHAFT_FROM, rocketInside
from ._stationinterior import roomOf, roomsInside, shaftWays, stationWay
from ._terminal import terminalSolids
from ._levels import CEILING, DOOR_WAYS, HEAD, WALL, doorMiddle
from ._shaftdoor import LEAF_MASS as SHAFT_LEAF, MIDDLE_FAR as SHAFT_FAR
from ._shaftdoor import ShaftDoor
from ._ladder import RUNS, Ladder, usable
from ._stationlamps import cageLampOf
from ._planets import PAD, julianOf, solarSystemOn
from ._scenery import Scenery
from ._sleep import Sleep
from ._tally import Tally
from ._spaceviewport import SpaceViewport
from ._station import Station
from ._teleprinter import ICONS
from ._timekeeper import WARPS, Timekeeper
from ._turns import cross, dot, norm, product, quaternionOf, rotated
from ._turns import unit
from ._vessel import MASS, Vessel
from ._vitals import Vitals
from ._walkway import SECTIONS, Walkway, doorwayInside, walkwayInside
from ._door import LEAF_MASS, MIDDLE_FAR, Door
from ._pad import Pad, fromPad, movingFromPad, movingToPad, posesOf
from ._pad import toPad, turnedFromPad, turnedToPad
from ._launchtower import LIFT_FOOT, LIFT_TOP, START, groundsInside
from ._launchtower import rocketLegs, towerSolids
from ._towerlift import FOOT, TOP, TowerLift
from ._cockpit import inCabin

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._cabinworld import CabinWorld

#  The window ticks once a frame drawn (user, 2026-11-17: "it feels like
#  it polls every t0, whilst somethign else renders at t1. If t0 != t1,
#  then gcd(t0, t1) == 1": a 16 ms timer beat against the screen's
#  refresh, the mouse's turn shown unevenly; now t0 = t1); a timer every
#  'TICK' ms ticks only when no frame has for 'IDLE' s (readying, the
#  window hidden); the longest step a frame takes, s.
TICK = 50
IDLE = 0.04
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
#  Asger in the tower's hall facing the walkway. False (the render
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
#  The kitchen's music heard whole this near the rations' crate, gone
#  this far from it, m.
FOOD_HEARD = (2.0, 6.0)
#  The launch tower's lift is called from this near its door, m.
LIFT_CALL = 2.5
#  The doorway through the hull, a room of the cabin's world always
#  ('_cabin_kernels.rocketRooms'): the door's leaf shuts it.
DOORWAY = 2
#  Asger goes out into the pad's world once his middle is this far out
#  of the doorway and the cabin (their rooms, m: less than nought), in
#  again once it is this far into either.
WORLD_CROSS = (-0.15, 0.05)
#  The rocket's pose in the pad's axes ('_pad.Pad.rocketIn'): standing
#  where it stands nominally; off Terra, far away.
STILL_POSE = ((0.0, 0.0, 0.0), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                                (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0),
              (0.0, 0.0, 0.0))
FAR_POSE = ((0.0, 0.0, 1e7),) + STILL_POSE[1:]
STUCK = 60.0
#  Why nothing is saved or loaded while the game readies.
READYING = 'the game is still readying'
#  The debug menu's warps, beside the open inventory (user, 2026-11-18:
#  "we need a debug menu available from the inventory that lets Asger
#  warp to certain locations, such as: 1. Spawn 2. Rocket room 3. Terra
#  Prime center. The room that has two docking ports"; 2026-11-19 the
#  center is the docked rocket's top floor; "give me a thing in the
#  inventory where i can jump to having the rocket already docked with
#  Asger sitting in the pilot seat"): each place's name and what its
#  button says; warped to the center, Asger floats this far from the
#  pole toward door nought, m.
TELEPORTS = (('spawn', 'Spawn'), ('rocket', 'Rocket room'),
             ('hub', 'Terra Prime center'),
             ('docked', 'Docked, in the seat'))
CENTRE_OFF = 1.0
#  Warped into the rocket room, Asger stands behind his chair, his head
#  turned this far (yaw, pitch, rad) to look over the room, the sofa
#  and the shelves (ahead, the cockpit's front is dark at night).
ROCKET_VIEW = (-1.6, -0.3)
#  The debug view's lines are shown anew this often, real s (user,
#  2026-11-18: "we don't need to refresh the fps counter 1200 times pers
#  second": ten times a second; each frame its figures flickered).
DEBUG_EVERY = 0.1
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
#  Q rolls the vessel about its nose, the wheels straight (E is his use
#  and inventory key, in his chair too: user, 2026-11-17; the other roll
#  key is the user's to choose: "As for manual controls, let's defer
#  those decisions for now").
ROLLING = {Qt.Key.Key_Q: 1.0}
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
        Qt.Key.Key_J: 'J', Qt.Key.Key_H: 'H', Qt.Key.Key_N: 'N',
        Qt.Key.Key_Space: 'Space', Qt.Key.Key_Return: 'Enter',
        Qt.Key.Key_Enter: 'Enter', Qt.Key.Key_Home: 'Home',
        Qt.Key.Key_BracketLeft: '[',
        Qt.Key.Key_BracketRight: ']', Qt.Key.Key_M: 'M',
        Qt.Key.Key_Backspace: '⌫', Qt.Key.Key_Tab: 'Tab', Qt.Key.Key_V: 'V',
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
               Qt.Key.Key_G: 'toAp', Qt.Key.Key_J: 'ap orbit',
               Qt.Key.Key_H: 'ap rendezvous', Qt.Key.Key_N: 'ap dock',
               Qt.Key.Key_Space: 'launch', Qt.Key.Key_Return: 'action',
               Qt.Key.Key_Enter: 'action',
               Qt.Key.Key_BracketRight: 'higher',
               Qt.Key.Key_BracketLeft: 'lower', Qt.Key.Key_M: 'map',
               Qt.Key.Key_Backspace: 'pad', Qt.Key.Key_Tab: 'view',
               Qt.Key.Key_V: 'vehicle',
               Qt.Key.Key_P: 'play', Qt.Key.Key_O: 'halt',
               Qt.Key.Key_I: 'eject', Qt.Key.Key_B: 'buckle',
               Qt.Key.Key_Y: 'limit down', Qt.Key.Key_U: 'limit up',
               Qt.Key.Key_K: 'camera', Qt.Key.Key_L: 'match',
               Qt.Key.Key_C: 'engage', Qt.Key.Key_Delete: 'undock',
               Qt.Key.Key_Home: 'autowarp'}
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
#  The hotbar's keys (user, 2026-11-17: "Give Asger a hotbar and an
#  inventory like in minecraft": 1 to 9 as Minecraft's; E opens the
#  inventory when there is nothing to use: "key_E should still be the
#  general interaction"; "I meant even when in the seat"), the
#  telescope's magnification (held
#  in hand, the right button held: "give Asger also a telescope"), how
#  fast the view eases to it, s.
DIGITS = {getattr(Qt.Key, 'Key_%d' % (k + 1)): k for k in range(HOTBAR)}
SCOPE = 8.0
SCOPE_EASE = 0.08
#  Up, looking within this of his chair's cushion, E sits him, rad.
CHAIR_AIM = math.radians(25.0)
#  E within this of an elevator's stop's door calls it there (the deck's;
#  the drum's: within 'HOLE_REACH' of the top floor's doorway), m.
CALL_REACH = 6.0
HOLE_REACH = 1.5
#  Up, within 'DOOR_REACH' m of a top floor door's middle, looking within
#  'DOOR_AIM' rad of it, E works it.
DOOR_REACH = 2.2
DOOR_AIM = math.radians(35.0)
#  E held this long takes or lets go of the handles where E has nothing
#  else to work (user, 2026-11-19: "You hold e for a second whilst a
#  circular fills"; let go sooner, the inventory), s.
HOLD_E = 1.0
#  A top floor door this far open lets the handles' run through it.
DOOR_OPEN = 0.97
#  An elevator's button pressed stays in this long, s.
CAR_BUTTON_IN = 0.25
#  Seated in an elevator, its button within this of his eyes, looked at
#  within this, is pressed by E or a click, m and rad.
CAR_BUTTON_REACH = 1.2
CAR_BUTTON_AIM = math.radians(15.0)
#  The mouse free in play (Esc, the inventory shut), the view says so
#  (a click in the window takes it to look round again).
FREE_SAID = 'Click to look round'
#  The pause menu's exit asks to save first once the game has run this
#  long since it was last saved or loaded (or began), s of its time.
UNSAVED_AFTER = 1.0
#  Seen from behind him (Tab): the eye this far back along his look and
#  this far up, m, and no nearer a wall or a solid than 'BEHIND_CLEAR',
#  m; no such spot 'BEHIND_LEAST' m back or more: his own eyes.
BEHIND = (3.2, 0.6)
BEHIND_CLEAR = 0.15
BEHIND_LEAST = 0.6
#  A cage's inside, a room in its shaft, reaches this far past its
#  plates, m (they hold him in; the room only where the cage is).
CAGE_OVER = 0.3
#  Riding an elevator's seat, the view is Terra Prime round Asger: from
#  'RIDE_FAR' m off him, its way off him above the station's plane,
#  aside and back toward its axis (each share); the small frame's camera
#  'FACE_OFF' m before his face, m.
RIDE_FAR = 140.0
RIDE_WAY = (0.55, 0.35, 0.75)
FACE_OFF = 1.1
#  The rooms as the readout says them.
ROOMS_SAID = {'level 1': 'level 1', 'level 2': 'the top floor',
              'hatch': 'a hatch', 'doorway': 'a top floor door',
              'shaft': 'a spoke\'s shaft', 'ring': 'the ring\'s deck'}
#  The closest approach to the station is worked out anew this often,
#  s of real time (some 2 ms each).
CLOSEST_EVERY = 0.25
#  The range's number tubes show a new reading this often, s of real
#  time, as a counter's gate (their canvas took 10 ms a paint, painted
#  nearly every frame).
TUBES_EVERY = 0.25
#  WARP TO ACTION warps only to a burn at least this far off, s.
ACTION_LEAST = 2.0
#  The autopilot's modes as the AUTOPILOT's status line says them; the
#  dials' names (read off as WAILA does: '_readOf').
MODES_SAID = {'off': 'MANUAL', 'hold': 'HOLD', 'prograde': 'PROGRADE',
              'retrograde': 'RETROGRADE', 'match': 'MATCH SPIN'}
DIAL_NAMES = tuple(name for name, _ in DIALS)
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
DEAD_KEYS = ('map', 'view', 'vehicle', 'buckle')
#  Out of his chair (user, 2026-11-17: getting up, "FAFO rules") Asger
#  works the dashboard only by reaching it (a click on what he looks at);
#  these keys still do their work (the view's own; B sits him down), his
#  legs take W A S D ('MOVING') and Space (a jump, or a push off what he
#  touches).
UP_KEYS = ('map', 'view', 'vehicle', 'buckle')
MOVING = {Qt.Key.Key_W: 'ahead', Qt.Key.Key_S: 'back',
          Qt.Key.Key_A: 'left', Qt.Key.Key_D: 'right'}
#  The actions that take the controls from the autopilot.
TAKING = ('full', 'cut', 'hold', 'prograde', 'retrograde', 'aim',
          'throttle', 'pad')
HINT = ('click: look round   wheel: zoom   Esc: pause menu   click a'
        ' lamp: do it   Tab: third person   V: vehicle view   Shift: get'
        ' up (up: crouch)   E: use (nothing to use: inventory; hold:'
        ' handles)   1-9: hotbar   F5: save   F9: load')
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
    from worQt.phys._compiled import gpuDevice
    self.device = gpuDevice() or 'cpu'
    print('[space] flying the sky on %s (the first time ~20 s)'
          % self.device, flush=True)
    if START_OUTSIDE:
      self.began += timedelta(0, _nightStart(self.began, self.device))
    self.system = solarSystemOn(julianOf(self.began), self.device)
    self.keeper = Timekeeper(self.system)
    self.station = (Station(self.system, -RISEN) if START_OUTSIDE else
                    Station(self.system))
    self.walkway, self.quest = Walkway(START_OUTSIDE), Quest()
    self.door, self._doorSent = Door(not START_OUTSIDE), None
    self.pad, self.padMeter = Pad(self.system), Accelerometer()
    self.padWorld, self._padman = None, Crewman()
    self._padman.buckled, self._outside = False, False
    self._rocket, self._padSolids, self._padDoorSent = STILL_POSE, None, None
    self._padMoving, self._legsFirst = None, 0
    self.towerLift, self._towered = TowerLift(), False
    self._manualOpen, self._laughedAt = False, -LAUGH_EVERY
    self.vessel = Vessel()
    self.guidance = AscentGuidance()
    self.accelerometer, self.world, self._leaping = (Accelerometer(), None,
                                                     False)
    self.vitals = Vitals()
    self.egg = Egg()
    self.jetpack, self.headlamp = Jetpack(), Headlamp()
    self._turnedBack = (0.0, 0.0, 0.0)
    self.sleep = Sleep()
    self.docking = DockingPort(self.station)
    self.autodock, self._docks = DockingGuidance(), 0
    self._crashes, self._crash, self._bumping = 0, 0.0, False
    self._closest, self._closestAt, self._closestReal = None, 0.0, 0.0
    self._tubes, self._tubesReal = None, 0.0
    self.elevators = [Elevator() for _ in range(4)]
    self._stationed, self._fixed = False, None
    self.shaftDoors = [ShaftDoor(k) for k in range(len(DOOR_WAYS))]
    self.ladder, self._eSince = Ladder(), None
    self._autoWarp = False
    self._carGuard, self._carGuardUntil, self._carPressedAt = 0.0, 0.0, 0.0
    self._carSeat, self.deck = None, DeckThings()
    self.rendezvous = RendezvousGuidance(self.station)
    self.autoflight = Autoflight(self.guidance, self.rendezvous,
                                 self.autodock, self.docking)
    self._laughs = 0
    self._noseCamera, self._pulses, self._reading = False, {}, None
    self._ball = None
    self._padded()
    self.chase, self.orrery, self.scenery = (ChaseCamera(), Orrery(),
                                             Scenery())
    self.navball = Navball()
    self.cockpit, self.inside, self.third = Cockpit(), True, False
    self.instruments = Instruments(self.cockpit)
    self.speaker = Speaker('worQt.gaming.space._cabinmixer:CabinMixer',
                           TOLD)
    self.flight, self.files, self.readying = None, None, 'starting'
    self._step, self._stuck = time.perf_counter(), False
    self.trouble, self.held, self.mapOpen = None, {}, False
    self._cabinRate, self._flightRate = Tally(), Tally()
    self._sentSolids = None
    self._debugAt = -math.inf
    self._stoodBy = False
    self.inventory, self._inventoryOpen = Inventory(), False
    self._scoping, self._zoom, self._heldSince = False, 1.0, 0.0
    self.note, self._noted, self._flashed = '', 0.0, {}
    self._dragged, self._dragFrom, self._clickedAt = False, None, None
    self._ticked = time.perf_counter()
    self.viewport = SpaceViewport()
    self.setCentralWidget(self.viewport)
    self.viewport.quick.installEventFilter(self)
    self.viewport.boardPicked.connect(self._acted)
    self.viewport.inventoryClicked.connect(self._inventoryClicked)
    self.viewport.teleportPicked.connect(self._teleported)
    self.viewport.gearPicked.connect(self._geared)
    self.viewport.inventoryShutPicked.connect(self._inventoryShutPicked)
    self.viewport.pausePicked.connect(self._pausePicked)
    self._paused, self._pauseAsk, self._pauseNote = False, '', ''
    self._pauseSlots, self._pauseSlot = [], 0
    self._cleanAt = 0.0
    self.pointer = Pointer(self.viewport.quick)
    self.timer = QTimer(self)
    self.timer.timeout.connect(self._idled)
    self.viewport.quick.frameSwapped.connect(self._framed)
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
      if event.key() == Qt.Key.Key_E:
        self._eReleased()
      return True
    if kind == QEvent.Type.FocusOut:
      self.held.clear()
      self.pointer.letGo()
      self._heldReleased()
      return False
    if kind == QEvent.Type.MouseButtonPress and (
        not self.pointer.taken) and self.viewport.takesClick(
          event.position()):
      return False
    if kind == QEvent.Type.MouseButtonRelease and not self.pointer.taken:
      #  The scene's own (user, 2026-11-18: "the inventory desyncs the
      #  mouse from the screen": a release kept from it left the slot
      #  pressed holding the mouse, the stack carried stuck).
      if event.button() == Qt.MouseButton.RightButton:
        self._heldReleased()
      return False
    if self.mapOpen:
      return self._mapMouse(kind, event)
    if kind == QEvent.Type.MouseButtonPress and not self.pointer.taken:
      self.pointer.take()
      return True
    if kind == QEvent.Type.MouseButtonPress and self.inside:
      right = event.button() == Qt.MouseButton.RightButton
      if not (right and self._heldPressed()):
        self._used(right)
      return True
    if kind == QEvent.Type.MouseButtonRelease and self.inside:
      if event.button() == Qt.MouseButton.RightButton:
        self._heldReleased()
      return True
    if kind == QEvent.Type.MouseMove:
      if not self.pointer.taken:
        self.viewport.pointedAt(event.position())
      self.pointer.movedTo(event.globalPosition(), event.position(),
                           event.timestamp() / 1000.0)
    elif kind == QEvent.Type.Wheel:
      notches = event.angleDelta().y() / 120.0
      if not self.inside:
        self.chase.zoomed(notches)
      elif self._looked() == 'throttle':
        engine = self.vessel.engine
        engine.throttled(engine.throttle + WHEEL_THROTTLE * notches)
      elif notches and not self._inventoryOpen:
        self.inventory.scrolled(-1 if notches > 0 else 1)
        self._heldSince = time.perf_counter()
      return True
    elif kind == QEvent.Type.Leave:
      #  Taken, it never leaves (gamescope holds it); if it did, it got
      #  away: let go, so a click in the window takes it again (user,
      #  2026-11-19: "the mouse escapes with now way back").
      if self.pointer.taken:
        self.pointer.letGo()
      self.pointer.forget()
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _framed(self, ) -> None:
    """A frame drawn: the next tick (it draws the next frame)."""
    if self.timer.isActive():
      self.tick()

  def _idled(self, ) -> None:
    """The timer: a tick if no frame has ticked for 'IDLE' s."""
    if time.perf_counter() - self._ticked >= IDLE:
      self.tick()

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
    if self._paused:
      viewport.pauseShown(True, self._pauseAsk, self._pauseNote,
                          not self._saveWhy(), self._loadable(),
                          self._pauseSlots)
      self._drawn(now, 0.0)
      return
    viewport.pauseShown(False, '', '', False, False, [])
    self._steered(real)
    self._autoKept()
    vessel.aimKept(system)
    self._sleepKept(now)
    self._warpKept()
    self._autoWarpKept()
    seconds = keeper.secondsOf(real)
    self._docking()
    station = self.station
    flown = (station.body,) if vessel.docked else (vessel, station.body)
    self.flight.flown(flown, system, keeper.now, seconds, math.inf,
                      station, keeper.factor > 1)
    if not vessel.docked:
      self._bumped()
    self._flightRate.counted(0 if vessel.docked else self.flight.lastSteps,
                             time.perf_counter())
    keeper.ticked(seconds)
    station.at = keeper.now
    self._dockedOrNot()
    self._approachKept(now)
    self.accelerometer.measured(vessel, seconds)
    self._cabinMoved(real)
    self._lived(real)
    flying = self.autoflight
    self.instruments.switched = {
      'ap orbit': flying.mode == 'orbit',
      'ap rendezvous': flying.mode == 'rendezvous',
      'ap dock': flying.mode == 'dock', 'engage': flying.engaged,
      'action': not self._actionWhy(), 'autowarp': self._autoWarp,
      'camera': self._noseCamera}
    self.instruments.acted(real, vessel, system, keeper, self.guidance,
                           self.mapOpen, self._header())
    told = list(self.instruments.told(vessel, system, self.inside))
    told[THUDS] = self.world.thuds + self.padWorld.thuds
    told[THUD] = max(self.world.loudest, self.padWorld.loudest)
    told[HURTS], told[EATS] = self.vitals.hurts, self.vitals.meals
    told[THRUSTING] = min(1.0, norm(vessel.rcs) / (RCS_ACCEL * MASS))
    told[DOCKS] = self._docks
    told[CRASHES], told[CRASH] = self._crashes, self._crash
    told[LAUGHS] = self._laughs
    told[FOOD_NEAR] = self._foodNear()
    told[SNACKS] = self.vitals.snacks
    self.speaker.heard(tuple(told))
    self._drawn(now, real)

  def _drawn(self, now: float, real: float) -> None:
    """Draws the frame ('real' s since the last; nought, paused): Asger's
    look turned by the mouse, the hotbar and inventory, the view (the
    map or the flight), the dashboard and the readouts."""
    viewport = self.viewport
    keeper, vessel, system = self.keeper, self.vessel, self.system
    right, down = self.pointer.movedBy(time.perf_counter())
    zoom = self._scopeKept(real)
    if right or down:
      if self.inside:
        self.cockpit.turned(right / zoom, down / zoom)
      else:
        self.chase.turned(right, down)
    inventory = self.inventory
    viewport.inventoryShown(inventory.rows(), inventory.selected,
                            self._inventoryOpen, inventory.carried,
                            self.inside and not self.mapOpen,
                            time.perf_counter() - self._heldSince)
    viewport.heldShown(inventory.held, zoom)
    viewport.teleportsOffered([{'name': name, 'title': title}
                               for name, title in TELEPORTS])
    viewport.gearShown(self.jetpack.on, self.jetpack.thrust,
                       self.headlamp.on)
    if self.mapOpen:
      quick = viewport.quick
      viewport.mapShown(self.scenery.mapOf(
        system, vessel, self.orrery, keeper.now, quick.width(),
        quick.height()))
    else:
      ball = self.navball.frameOf(vessel, system, NAV_RADIUS)
      self._ball = ball
      eye, look, up, own = self._seen()
      frame = self.scenery.flightOf(system, vessel, (eye, look, up),
                                    keeper.now)
      cabin = self.scenery.cabinOf(system, vessel, self.cockpit,
                                   frame['rocket'], ball, self._dash(),
                                   own)
      viewport.flightShown(frame, cabin, system, vessel.anchor)
      viewport.navballShown(ball)
    viewport.boardShown(self._boardOf(now))
    if self._tubes is None or now - self._tubesReal >= TUBES_EVERY:
      self._tubes = self._rangeOf(), self._portText()
      self._tubesReal = now
    viewport.cockpitShown(self.inside, self._prompt(),
                          self.instruments.printer.paper(),
                          (self._statusOf(),) + self._tubes)
    viewport.hudShown(self._readout(), MAP_HINT if self.mapOpen else HINT,
                      self._freeSaid())
    self._holdKept(now)
    self._debugKept(time.perf_counter())
    viewport.monitorShown(self._noseCamera)
    vitals = self.vitals
    viewport.vitalsShown(vitals.health, vitals.food, vitals.hurt,
                         vitals.eaten, vitals.cause or '')
    if vitals.reminder():
      self._noteOf('Peckish? There are pork scratchings under the '
                   'dashboard, by your right knee (E)')
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
      device = self.device
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
      self.world = CabinWorld(device, looseThings() + deckWorldThings())
      self.world.bodiesPlaced(len(looseThings()), DeckThings().laid(
        TELEPORTED), (0.0,) * len(deckThings()))
      self.padWorld = CabinWorld(device, (), False)
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
    """Stands the vessel on Terra's pad now, the engine shut and dark
    till LAUNCH, the assists off, the autopilot let go."""
    vessel = self.vessel
    self.autoflight.letGo(vessel)
    self.guidance.stopped(vessel)
    vessel.stood(self.system, self.system.named('Terra'), PAD[0], PAD[1],
                 self.keeper.now)
    vessel.engine.throttled(0.0)
    vessel.engine.lit = False
    vessel.autopilot.engaged('off', vessel.turn)
    vessel.steered(0.0, 0.0, 0.0)
    self.keeper.realtime()

  def _pressed(self, key: object) -> bool:
    """Acts on a key pressed (its action, Asger glancing at the input
    working it); returns whether it was one of the window's."""
    if key in CAPS:
      self._flashed[CAPS[key]] = time.perf_counter()
    if key == Qt.Key.Key_F5:
      self._quickSaved()
      return True
    if key == Qt.Key.Key_F9:
      self._quickLoaded()
      return True
    if self._paused:
      if key == Qt.Key.Key_Escape and self._pauseAsk:
        self._pausePicked('cancel')
      elif key == Qt.Key.Key_Escape:
        self._resumed()
      return True
    if key == Qt.Key.Key_E:
      self._ePressed()
      return True
    if self._manualOpen:
      if key == Qt.Key.Key_Escape:
        self._manualOpen = False
      return True
    if self._inventoryOpen:
      if key == Qt.Key.Key_Escape:
        self._inventoryShut()
      return True
    if key == Qt.Key.Key_Escape:
      self._pauseOpened()
      return True
    if key in DIGITS and self.inside:
      self.inventory.chosen(DIGITS[key])
      self._heldSince = time.perf_counter()
      return True
    if self.vitals.cause is not None:
      action = KEY_ACTIONS.get(key)
      if action in DEAD_KEYS:
        self._acted(action)
      return True
    if self.sleep.on:
      return True
    if key == Qt.Key.Key_Shift:
      crewman = self.cockpit.crewman
      if crewman.buckled:
        self._gotUp()
        self._stoodBy = True
      elif crewman.lounge is not None and self._carSeat is not None:
        self._carStood()
        self._stoodBy = True
      elif crewman.lounge is not None:
        crewman.offSofa()
        self._stoodBy = True
        self._noteOf('Asger gets up off the sofa')
      return True
    if key == Qt.Key.Key_Space and self._carSeat is not None:
      self._carSent()
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
      self._shutSaid()
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
    """Lets the autopilot go if 'action' takes the controls (said)."""
    if action not in TAKING or not self.autoflight.engaged:
      return
    self.autoflight.letGo(self.vessel)
    self.keeper.realtime()
    self._noteOf('Autopilot off: you took the controls')

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
      self._shutSaid()
    elif action == 'cut':
      engine.throttled(0.0)
    elif action == 'throttle':
      engine.throttled(engine.throttle + (-CLICK_THROTTLE if back
                                          else CLICK_THROTTLE))
      self._shutSaid()
    elif action in ('ap orbit', 'ap rendezvous', 'ap dock'):
      self._noteOf(self.autoflight.chosen(action[len('ap '):], vessel,
                                          system, keeper))
    elif action == 'engage':
      self._noteOf(self.autoflight.toggled(vessel, system, keeper))
      if not self.autoflight.engaged:
        keeper.realtime()
    elif action == 'launch':
      self._launched()
    elif action == 'action':
      self._warpedToAction()
    elif action == 'autowarp':
      self._autoWarpToggled()
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
      self._viewed()
    elif action == 'vehicle':
      self.inside = not self.inside
    elif action == 'buckle':
      self._buckled()
    elif action in ('limit', 'limit up', 'limit down'):
      self._limited(action == 'limit down' or (action == 'limit' and back))
    elif action.startswith('rcs '):
      self._pulses[action] = time.perf_counter() + PULSE
    elif action == 'camera':
      self._noseCamera = not self._noseCamera
    elif action in ('match', 'undock'):
      self._docked(action)
    elif action == 'eat':
      why = self.vitals.ate()
      self._noteOf(why or 'Asger eats a ration (RCIR)')
      if not why:
        self._questTicked('ate')
    elif action == 'snack':
      why = self.vitals.snacked()
      self._noteOf(why or 'Asger crunches a handful of pork scratchings')
    elif action in ('door', 'door outside'):
      self._doorWorked()
    elif action == 'lock':
      why = self.door.locking() if (self.walkway.attached
                                    or not self.door.locked) else (
        'the walkway is gone: it is a long way down')
      self._noteOf(why or ('The door is locked' if self.door.locked
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
                   ' down (or reach the input: E)')
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
    the ground"), Asger up in the tower's hall facing the walkway,
    looking up a little, told the first step; else in his chair, the
    walkway's steps done."""
    if not START_OUTSIDE:
      for name in ('aboard', 'locked', 'dismissed'):
        self.quest.ticked(name)
      return
    self._atStart()
    self.vitals.food = SUPPERLESS
    self._noteOf('Night at the launch tower. Ahead the walkway to the '
                 'rocket; behind you the EXIT, stairs or a lift down to '
                 'the ground (Terra Prime passes over: look up). Quest: %s'
                 % self.quest.textOf(self.quest.current))

  def _atStart(self, ) -> None:
    """Puts Asger where the game starts: up in the launch tower's hall,
    still, facing the walkway, looking ahead."""
    soles, facing = START
    self._placedAt((soles[0], soles[1], soles[2] + MIDDLE), facing)

  def _placedAt(self, middle: tuple, facing: tuple) -> None:
    """Gets Asger up and puts his middle at 'middle' (the vessel's own
    axes), still, upright, facing 'facing', looking ahead."""
    cockpit = self.cockpit
    cockpit.gotUp()
    crewman = cockpit.crewman
    crewman.placed(middle, (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), tuple(facing)
    cockpit.yaw, cockpit.pitch = 0.0, 0.0

  def _teleported(self, where: str) -> None:
    """The debug menu's warp to 'where' (a name of 'TELEPORTS'), at once,
    the inventory shut: 'spawn', the rocket stood on the pad anew, the
    walkway at its door and the tower's lift as the game starts them,
    Asger in the tower's hall where it starts; 'rocket', Asger behind
    his chair looking over the room ('ROCKET_VIEW'), the rocket where it
    is; 'hub', the rocket docked at Terra Prime (the walkway gone, the
    door locked, the engine lit), Asger floating by the pole on the top
    floor (the station's middle); 'docked', docked so, Asger in his
    chair. Time runs real; the sky, his vitals, his inventory and the
    quest stay as they are; the gun lets go, he wakes; off the station
    the top floor's doors are shut. Refused while the game readies or
    he is dead (said)."""
    titles = dict(TELEPORTS)
    if where not in titles:
      raise ValueError('no warp to %r: %s' % (where, sorted(titles)))
    if not self._inventoryOpen:
      return
    if self._saveWhy() == READYING:
      self._noteOf('Cannot warp: %s' % READYING)
      return
    if self.vitals.cause is not None:
      self._noteOf('Cannot warp: Asger is dead')
      return
    vessel, now = self.vessel, self.keeper.now
    if where == 'spawn':
      self.docking.parted(vessel, self.system, now)
      vessel.jolt, vessel.latch = (0.0, 0.0, 0.0), None
      self._padded()
      self.walkway, self.towerLift = Walkway(True), TowerLift()
      self.door = Door(False)
      self.shaftDoors = [ShaftDoor(k) for k in range(len(DOOR_WAYS))]
    elif where in ('hub', 'docked') and not vessel.docked:
      self.autoflight.letGo(vessel)
      self.guidance.stopped(vessel)
      self.walkway, self.door = Walkway(False), Door(True)
      vessel.engine.lit = True
      self.docking.teleported(vessel, self.system, now)
    self.keeper.realtime()
    self.ladder = Ladder()
    self.cockpit.crewman.climbing = False
    if where == 'spawn':
      self._atStart()
    elif where == 'rocket':
      self.cockpit.gotUp()
      self.cockpit.yaw, self.cockpit.pitch = ROCKET_VIEW
    elif where == 'docked':
      self.cockpit.strappedIn()
    else:
      self._placedAt((CENTRE_OFF, 0.0, PLANE), (1.0, 0.0, 0.0))
    self.world.teleported()
    self.inside = True
    self._settledAnew()
    self._noteOf('Warped to %s' % titles[where])

  def _foodNear(self, ) -> float:
    """Returns how near the food Asger's ears are: one within the first
    of 'FOOD_HEARD' m of the rations' crate, nought past the second (the
    kitchen's music fades between)."""
    near, far = FOOD_HEARD
    away = math.dist(self.cockpit.eye(), rationCrate()[0])
    return min(1.0, max(0.0, (far - away) / (far - near)))

  def _promptOf(self, control: object) -> str:
    """Returns what working 'control' does now (the door's keys as the
    door is: open or shut, locked or not)."""
    door = self.door
    if control.action in ('door', 'door outside'):
      return 'Close the door' if door.wanted else 'Open the door'
    if control.action == 'lock':
      return 'Unlock the door' if door.locked else 'Lock the door'
    vessel = self.vessel
    valued = {'warp': 'Warp %sx' % _grouped(self.keeper.factor, 0),
              'limit': 'Engine limited to %g g' % LIMITS[limitNotch(
                vessel.engine)],
              'orbit': 'Orbit %s' % lengthText(self.guidance.target),
              'throttle': 'Thrust %.0f %%' % (100.0
                                              * vessel.engine.throttle)}
    if control.action in valued:
      return valued[control.action]
    said = control.peep.prompt()
    if control.name in LIT_KEYS:
      lit = self.instruments.legends[LEGENDS.index(control.name)]
      return '%s (%s)' % (said, 'on' if lit else 'off')
    return said

  def _doorWorked(self, ) -> None:
    """Opens the door (with the walkway at it), or closes it (what is in
    the doorway stops it: '_door'), said."""
    door = self.door
    if door.wanted:
      door.closed()
      self._noteOf('The door slides shut')
      return
    why = door.opened() if self.walkway.attached else (
      'the walkway is gone: it is a long way down')
    self._noteOf(('The door stays shut: %s' % why) if why else
                 'The door slides open')

  def _doorMoved(self, real: float) -> None:
    """Moves the door 'real' s on ('_door'), pushed by what Asger pushed
    its leaf by over the last frame (round the rocket's axis), pulled as
    the cabin pulls at its leaf, and puts its leaf in the cabin's world;
    the rocket takes back what moving the leaf took (its mass times how
    it sped up, less what Asger gave it if his pushes are not the
    rocket's: outside on the pad); the leaf's weight the rocket carries
    already (its mass is the rocket's)."""
    door = self.door
    way, middle = door.wayAt()
    moving = tuple(door.speed * w for w in way)
    pull = self.accelerometer.pullAt(middle, moving)
    still = self.accelerometer.pullAt(middle, (0.0, 0.0, 0.0))
    struck = self.world.struck(DOOR, 1)
    if self._outside:
      rocket = self._rocket
      hit, about = self.padWorld.struck(DOOR, 1)
      about = tuple(a - c for a, c in zip(about, cross(rocket[0], hit)))
      struck = (turnedFromPad(rocket, hit), turnedFromPad(rocket, about))
    push = struck[1][2] / MIDDLE_FAR
    faster = door.moved(real, dot(pull, way), push)
    back = [-LEAF_MASS * (faster * w - (p - s)) * real
            for w, p, s in zip(way, pull, still)]
    if self._outside:
      back = [b + a for b, a in zip(back, struck[0])]
    if any(back):
      self._kicked(tuple(back), cross(middle, tuple(back)))
    box = door.boxOf()
    if box != self._doorSent:
      self.world.doorPlaced(*box)
      self._doorSent = box
    if self.walkway.attached:
      rocket = self._rocket
      posed = (toPad(rocket, box[0]), box[1], product(
        _turnOfPose(rocket), box[2]), movingToPad(rocket, box[0], box[3]))
      if posed != self._padDoorSent:
        self.padWorld.doorPlaced(*posed)
        self._padDoorSent = posed

  def _dismissed(self, ) -> None:
    """Sends the walkway away if Asger and everything loose are in the
    cabin (said)."""
    crewman = self.cockpit.crewman
    if not crewman.sitting and not inCabin(crewman.middle):
      self._noteOf('Asger is out on the walkway')
      return
    if any(not inCabin(place) for place, _ in self._cabinLoose()):
      self._noteOf('Something loose is out on the walkway')
      return
    why = self.walkway.dismissed() if self.door.locked else (
      'lock the door first')
    self._noteOf(why or 'The walkway swings back to the tower')

  def _launched(self, ) -> None:
    """LAUNCH (user, 2026-11-17: "independently of the auto pilot we need
    a launch button. When the autopilot set to a valid mode and
    activated, hitting the launch button will cause the autopilot to
    launch. A manual launch, would have the Asger set the thrust either
    before or after the launch button, but only after the launch button
    will the rocket actually move"; 2026-11-19: "The launch switch allows
    the throttle"): the engine lit, its throttle free to open (it stays
    shut till then: '_aerospike'; the autopilot's ORBIT opens it itself);
    refused with the walkway
    still out: Risitas laughs at Asger (user, 2026-11-17: "have risitas
    laugh at Asger and then restate the quest info"), the next step said
    again."""
    vessel = self.vessel
    if vessel.engine.lit:
      self._noteOf('Launched already')
      return
    if not self.walkway.away:
      now = time.perf_counter()
      if now - self._laughedAt >= LAUGH_EVERY:
        self._laughedAt, self._laughs = now, self._laughs + 1
      current = self.quest.current
      self._noteOf('Risitas laughs at Asger: the walkway is still out. %s'
                   % ('Next: %s' % self.quest.textOf(current) if current
                      else ''))
      return
    vessel.engine.lit = True
    flying = self.autoflight
    if flying.engaged and flying.mode == 'orbit':
      self._noteOf('LAUNCH! The autopilot flies up to orbit')
    else:
      self._noteOf('LAUNCH! The engine is lit: push the throttle in (+)')

  def _shutSaid(self, ) -> None:
    """Says the throttle is shut till LAUNCH, if the engine is dark."""
    if not self.vessel.engine.lit:
      self._noteOf('The throttle is shut till LAUNCH (Space, under its'
                   ' guard)')

  def _autoKept(self, ) -> None:
    """Before the frame's flight: the autopilot flies its mode a frame
    on (said when it is done or stops); ORBIT tops up only with Asger in
    his chair."""
    vessel = self.vessel
    reading = self.docking.readingOf(vessel, self.system, self.keeper.now)
    said = self.autoflight.acted(vessel, self.system, self.keeper, reading,
                                 self.cockpit.crewman.buckled)
    if said:
      self._noteOf(said)

  def _actionWhy(self, ) -> str:
    """Returns why WARP TO ACTION may not warp now ('' it may: the
    autopilot waits for its next burn, its stop set, and time may warp:
    user, 2026-11-17, "When the autopilot begins waiting for a new burn,
    this button activates")."""
    keeper = self.keeper
    stops = keeper.stopsAt
    if not self.autoflight.engaged or stops is None or (
        stops - keeper.elapsed < ACTION_LEAST):
      return 'the autopilot waits for no burn'
    return self._noWarp()

  def _warpedToAction(self, ) -> None:
    """WARP TO ACTION: time as fast as it warps, eased off before the
    autopilot's next burn (its stop); or said why not."""
    why = self._actionWhy()
    if why:
      self._noteOf('No warp to action: %s' % why)
      return
    self.keeper.fastest()
    self._noteOf('Warp to action: the burn in %s' % timeText(
      self.keeper.stopsAt - self.keeper.elapsed))

  def _autoWarpToggled(self, ) -> None:
    """AUTO WARP (user, 2026-11-19: "give the autopilot an 'auto warp'
    thing. yes i know i said i didn't want that, but we are ready for it
    now"): on, the autopilot's every wait for a burn is warped through by
    itself ('_autoWarpKept'); off, warp is his alone again (said)."""
    self._autoWarp = not self._autoWarp
    if not self._autoWarp:
      self._noteOf('Auto warp off')
      return
    why = self._actionWhy()
    self._noteOf('Auto warp on' + (' (for now no warp: %s)' % why
                                   if why else ''))

  def _autoWarpKept(self, ) -> None:
    """With AUTO WARP on, warps to the autopilot's next burn as WARP TO
    ACTION does whenever it may ('_actionWhy') and time runs slower
    than that (said as it starts)."""
    if not self._autoWarp or self._actionWhy():
      return
    keeper = self.keeper
    if keeper.factor >= WARPS[-1]:
      return
    before = keeper.factor
    keeper.fastest()
    if keeper.factor > before and before == 1:
      self._noteOf('Auto warp: the burn in %s' % timeText(
        keeper.stopsAt - keeper.elapsed))

  def _questKept(self, ) -> None:
    """Ticks off the quest's steps done this frame (said)."""
    quest, vessel = self.quest, self.vessel
    crewman = self.cockpit.crewman
    done = quest.done
    checks = (
      ('aboard', not crewman.sitting and inCabin(crewman.middle)),
      ('locked', self.door.locked and 'aboard' in done),
      ('dismissed', not self.walkway.attached),
      ('seated', crewman.buckled and 'aboard' in done),
      ('armed', self.autoflight.engaged
       and self.autoflight.mode == 'orbit'),
      ('launched', not vessel.touching and 'launched' not in done
       and vessel.heightOver(self.system) > 30.0),
      ('orbit', 'launched' in done and 'orbit' not in done
       and self._inOrbit()),
      ('docked', vessel.docked))
    for name, met in checks:
      if met and name not in done:
        self._questTicked(name)
    if vessel.docked and not crewman.sitting:
      room = roomOf(crewman.middle, shaftWays(self.docking.relative),
                    self._cages())
      if room in ('doorway', 'shaft'):
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
    the engine burning, or the rocket not at rest on all its legs (the
    night is then skipped as it would pass: at rest on the turning
    ground it stays at rest, carried round with it; user, 2026-11-18,
    "PHYSICS MUST BE REAL"); off it, whatever stops a warp; the
    automatic systems flying."""
    vessel = self.vessel
    if self.autodock.on or self.rendezvous.on or self.guidance.on:
      return 'the automatic systems are flying'
    if vessel.touching:
      if vessel.engine.throttle > 0.0:
        return 'the engine burns'
      return restWhy(self.vessel, self.system)
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
        station = self.station
        self.flight.flown((station.body,), self.system, keeper.now,
                          sleep.wait, math.inf, station, True)
        vessel.carried(self.system, sleep.wait)
        keeper.leapt(sleep.wait)
        station.at = keeper.now
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
    self._noteOf('Asger is up: W A S D, Space, Shift crouches; E at the'
                 ' chair sits him; 1-9 his hotbar, E (nothing to use) his'
                 ' inventory; the right button uses what he holds')

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

  def _carSeatOf(self, ) -> int | None:
    """Returns the elevator Asger, up (or on the handles) and docked, is
    in the cage of (E sits him in its seat: user, 2026-11-19, "it is
    retarded that the e button is both activate the elevator and sit in
    chair so you can never actually sit in the chair": in a cage E only
    sits); None: none."""
    crewman = self.cockpit.crewman
    if not self.vessel.docked or crewman.sitting:
      return None
    for k, (elevator, way) in enumerate(zip(self.elevators, shaftWays(
        self.docking.relative))):
      if elevator.holds(way, crewman.middle):
        return k
    return None

  def _carSat(self, k: int) -> None:
    """Sits Asger in elevator 'k''s seat (off the handles), said: the
    car goes only when its button is pressed ('_carSent')."""
    if self.ladder.held:
      self._ladderLeft(False)
    elevator = self.elevators[k]
    way = shaftWays(self.docking.relative)[k]
    seat, facing, up = elevator.seatOf(way, self._axial())
    self.cockpit.crewman.lounged(seat, facing, up, tuple(
      elevator.speed * w for w in way))
    self.cockpit.yaw, self.cockpit.pitch = 0.0, -0.35
    self._carSeat = k
    self._noteOf('Asger sits. Space (the red button under its guard, by'
                 ' his right hand) sends the elevator; Shift gets up')

  def _carSent(self, ) -> None:
    """The car's button (user, 2026-11-19: "a single guarded button like
    in the pilot seat. when this is triggered only then do we go down"):
    its guard flips up, the button goes in, the car is sent to its other
    stop (from the drum it waits for its door to shut: '_hoisted'),
    said; on its way already, nothing but that said."""
    k = self._carSeat
    if k is None:
      return
    now = time.perf_counter()
    self._carGuardUntil, self._carPressedAt = now + GUARD_HOLD, now
    elevator = self.elevators[k]
    if elevator.target is not None:
      self._noteOf('The elevator is on its way')
      return
    elevator.called()
    self._noteOf('The elevator rides %s' % (
      'down to the ring' if elevator.target > HUB_STOP else
      'up to the rocket'))

  def _carButtonAimed(self, ) -> bool:
    """Returns whether Asger, in an elevator's seat, looks at its button
    (E or a click presses it)."""
    k = self._carSeat
    if k is None:
      return False
    cockpit = self.cockpit
    way = shaftWays(self.docking.relative)[k]
    button = self.elevators[k].buttonOf(way, self._axial(), 0.0)[0]
    eye = cockpit.eye()
    if math.dist(button, eye) > CAR_BUTTON_REACH:
      return False
    toward = unit(tuple(b - e for b, e in zip(button, eye)))
    return dot(toward, cockpit.looking()[0]) > math.cos(CAR_BUTTON_AIM)

  def _carGuardKept(self, real: float) -> None:
    """Eases the car's button's guard open while it is worked and
    'GUARD_HOLD' s after, shut again after."""
    wanted = 1.0 if time.perf_counter() < self._carGuardUntil else 0.0
    self._carGuard += (wanted - self._carGuard) * (
      1.0 - math.exp(-real / GUARD_EASE))

  def _riding(self, ) -> bool:
    """Returns whether Asger sits in an elevator on its way (the ride's
    view then: '_rideEye')."""
    return (self._carSeat is not None
            and self.elevators[self._carSeat].target is not None)

  def _carKept(self, ) -> None:
    """Keeps Asger seated in his elevator's seat where it is now, moving
    with it (his body is not moved while he sits); docked no more, or up
    off it, he is no longer in it."""
    k, crewman = self._carSeat, self.cockpit.crewman
    if k is None:
      return
    if not self.vessel.docked or crewman.lounge is None:
      self._carSeat = None
      return
    elevator = self.elevators[k]
    way = shaftWays(self.docking.relative)[k]
    seat, facing, up = elevator.seatOf(way, self._axial())
    crewman.lounged(seat, facing, up, tuple(elevator.speed * w
                                            for w in way))

  def _carStood(self, ) -> None:
    """Stands Asger up out of his elevator's seat, before it in the cage,
    facing the way it does, moving with it (said)."""
    k, crewman = self._carSeat, self.cockpit.crewman
    self._carSeat = None
    elevator = self.elevators[k]
    way = shaftWays(self.docking.relative)[k]
    seat, facing, up = elevator.seatOf(way, self._axial())
    crewman.lounge = None
    floor = tuple(s - SEAT_HIGH * u for s, u in zip(seat, up))
    middle = tuple(f + 0.5 * a + MIDDLE * u for f, a, u in zip(
      floor, facing, up))
    crewman.placed(middle, tuple(elevator.speed * w for w in way), 0,
                   (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = up, facing
    self._noteOf('Asger gets up out of the elevator\'s seat')

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
      pull = self._pullOnAsger()
      self.vitals.fell(self._asgerWorld().landed)
    self.vitals.lived(real, norm(pull) / G0, crewman.buckled,
                      self.keeper.factor > 1)
    if alive and self.vitals.cause is not None:
      if self.ladder.held:
        self._ladderLeft(False)
      self._noteOf('Asger died: %s' % self.vitals.cause)

  def _cabinMoved(self, real: float) -> None:
    """Moves what is loose in the cabin 'real' s on: Asger (righted
    against the pull on him, his legs as the keys held want, a leap
    once; or on the handles, carried along them as W and S ask, nothing
    else moving him: '_climbed'), the loose things and the gravity egg's
    marble."""
    cockpit, accelerometer = self.cockpit, self.accelerometer
    crewman = cockpit.crewman
    self._padKept()
    self._worldChosen()
    self._ladderKept()
    self._carGuardKept(real)
    want, self._turnedBack = STILL, (0.0, 0.0, 0.0)
    if self.ladder.held:
      self._climbed(real)
    elif not crewman.sitting and self.vitals.cause is None:
      pull = self._pullOnAsger()
      fans = self.jetpack.thrust if self.jetpack.on else 0.0
      cockpit.yaw, cockpit.pitch, self._turnedBack = crewman.righted(
        pull, real, cockpit.yaw, cockpit.pitch, fans)
      held = {MOVING[key] for key in self.held if key in MOVING}
      if Qt.Key.Key_Shift not in self.held:
        self._stoodBy = False
      crewman.crouching = (Qt.Key.Key_Shift in self.held
                           and not self._stoodBy)
      wanted, walking, wanting = crewman.wantOf(held, cockpit.yaw,
                                                cockpit.pitch, pull)
      leap = (0.0, 0.0, 0.0)
      if self._leaping:
        leap = crewman.leapOf(pull)
      want = (wanted, walking, wanting, leap)
    elif not crewman.sitting:
      pull = self._pullOnAsger()
      cockpit.yaw, cockpit.pitch, _ = crewman.righted(
        pull, real, cockpit.yaw, cockpit.pitch, 0.0, True)
    self._leaping = False
    self._towerKept(real)
    self._aboard(real)
    self._walkwayMoved(real)
    self._doorMoved(real)
    rooms = self.walkway.outside | DOORWAY | (
      self.towerLift.doors if self.walkway.attached else 0)
    self.world.walked(rooms)
    gun, jet = None, self._jetOf()
    if self._outside:
      rocket = self._rocket
      wanted, walking, wanting, leap = want
      want = (turnedToPad(rocket, wanted), walking, wanting,
              turnedToPad(rocket, leap))
      if gun is not None:
        gun = (turnedToPad(rocket, gun[0]), None, (0.0, 0.0, 0.0))
      self.padWorld.walked(rooms)
      self.padWorld.stepped(real, self.padMeter, self._padmanOf(), want,
                            gun, turnedToPad(rocket, jet))
      self._padmanBack()
      self.world.stepped(real, accelerometer, crewman, STILL, None,
                         (0.0, 0.0, 0.0), False)
    else:
      self.world.stepped(real, accelerometer, crewman, want, gun, jet)
    self._pushedBack()
    self._cabinRate.counted(self._asgerWorld().lastSteps,
                            time.perf_counter())
    self.egg.stepped(real, accelerometer)

  def _pushedBack(self, ) -> None:
    """Pushes the vessel back by what the cabin's world pushed this
    frame ('CabinWorld.pushedBack'; Asger's own, 'asgerPushed', while he
    is in it, less what he pushed the pad's faces by); out on the pad,
    what he pushed the rocket's hull and legs by (user, 2026-11-18:
    "rocket legs are part of the rocket. If Asger pushes hard enough to
    rocket should fall over"; the rest the tower's and the ground's,
    Terra's); docked, the pair (the station's flown body: its rooms are
    the rocket's world's then)."""
    world = self.world
    push, twist = world.pushedBack
    crewman = self.cockpit.crewman
    if not crewman.sitting and not self._outside:
      own, turned = world.asgerPushed
      ground, about = world.struck(PAD_FACES, 1)
      push = tuple(a + b - g for a, b, g in zip(push, own, ground))
      twist = tuple(a + b + c - g for a, b, c, g in zip(
        twist, turned, self._turnedBack, about))
    elif self._outside:
      rocket, pad = self._rocket, self.padWorld
      hit, about = pad.struck(ROCKET_FACES, 1)
      legs, round_ = pad.struck(self._legsFirst, len(rocketLegs()))
      hit = tuple(a + b for a, b in zip(hit, legs))
      about = tuple(a + b - c for a, b, c in zip(about, round_, cross(
        rocket[0], hit)))
      push = tuple(p + h for p, h in zip(push, turnedFromPad(rocket, hit)))
      twist = tuple(t + a for t, a in zip(twist, turnedFromPad(rocket,
                                                                about)))
    if any(push) or any(twist):
      self._kicked(push, twist)

  def _padKept(self, ) -> None:
    """Keeps the pad's world where the pad is (user, 2026-11-18: "the pad
    needs to be there"): with the walkway at the rocket, what its ground
    feels and where the rocket stands on it ('_pad.Pad.rocketIn'; both
    worlds' rooms posed so: '_pad.posesOf'); the rocket off Terra, far
    from it."""
    if not self.walkway.attached:
      return
    system, now = self.system, self.keeper.now
    rocket = self.pad.rocketIn(self.vessel, system, now)
    self._rocket = FAR_POSE if rocket is None else rocket
    cabin, pad = posesOf(self._rocket)
    self.world.posed(*cabin)
    self.padWorld.posed(*pad)
    self.padMeter.grounded(*self.pad.feltOf(system, now))

  def _worldChosen(self, ) -> None:
    """Puts Asger in the world he is in: the pad's once his middle is out
    past the doorway with the walkway at the rocket (the pad's axes,
    what its ground feels: '_padmanOf'), the cabin's once it is in the
    doorway or in the cabin ('WORLD_CROSS': not back and forth on the
    line); the world he leaves lets his box go."""
    crewman = self.cockpit.crewman
    inner = max(rocketInside(crewman.middle), doorwayInside(crewman.middle))
    out = (self.walkway.attached and not self.vessel.docked
           and not crewman.sitting and (
             inner < WORLD_CROSS[1] if self._outside else
             inner < WORLD_CROSS[0]))
    if out == self._outside:
      return
    (self.world if out else self.padWorld).left()
    self._outside = out

  def _asgerWorld(self, ) -> CabinWorld:
    """Returns the world Asger is in: the pad's or the cabin's."""
    return self.padWorld if self._outside else self.world

  def _pullOnAsger(self, ) -> tuple:
    """Returns the pull on Asger where he is (the rocket's own axes): out
    on the pad what its ground feels, else what the cabin feels."""
    crewman = self.cockpit.crewman
    if not self._outside:
      return self.accelerometer.pullAt(crewman.middle, crewman.velocity)
    rocket = self._rocket
    pull = self.padMeter.pullAt(toPad(rocket, crewman.middle), movingToPad(
      rocket, crewman.middle, crewman.velocity))
    return turnedFromPad(rocket, pull)

  def _padmanOf(self, ) -> Crewman:
    """Returns Asger as the pad's world sees him: his body in its axes,
    moving and spinning as it sees it ('_padman')."""
    crewman, padman = self.cockpit.crewman, self._padman
    rocket = self._rocket
    padman.buckled, padman.lounge = False, None
    padman.middle = toPad(rocket, crewman.middle)
    padman.velocity = movingToPad(rocket, crewman.middle, crewman.velocity)
    padman.up = turnedToPad(rocket, crewman.up)
    padman.ahead = turnedToPad(rocket, crewman.ahead)
    padman.spin = tuple(s + w for s, w in zip(
      turnedToPad(rocket, crewman.spin), rocket[3]))
    padman.ground = None if crewman.ground is None else turnedToPad(
      rocket, crewman.ground)
    padman.floor = None if crewman.floor is None else turnedToPad(
      rocket, crewman.floor)
    padman.touches, padman.crouched = crewman.touches, crewman.crouched
    padman.crouching, padman.rising = crewman.crouching, crewman.rising
    padman.fallen = crewman.fallen
    return padman

  def _padmanBack(self, ) -> None:
    """Takes Asger's body back from the pad's world (the rocket's own
    axes: '_padmanOf' undone)."""
    crewman, padman = self.cockpit.crewman, self._padman
    rocket = self._rocket
    crewman.middle = fromPad(rocket, padman.middle)
    crewman.velocity = movingFromPad(rocket, padman.middle,
                                     padman.velocity)
    crewman.spin = turnedFromPad(rocket, tuple(
      s - w for s, w in zip(padman.spin, rocket[3])))
    crewman.ground = None if padman.ground is None else turnedFromPad(
      rocket, padman.ground)
    crewman.floor = None if padman.floor is None else turnedFromPad(
      rocket, padman.floor)
    crewman.touches, crewman.crouched = padman.touches, padman.crouched
    crewman.rising = padman.rising

  def _padSolidsSent(self, boxes: tuple) -> None:
    """Puts the launch tower's still solids in the pad's world (its axes)
    unless they are there already (its lift's car and the walkway's
    sections after them, moving: '_towerKept')."""
    if boxes != self._padSolids:
      self.padWorld.stationed(False, (), boxes)
      self._padSolids, self._padMoving = boxes, None

  def _walkwayMoved(self, real: float) -> None:
    """Moves the walkway 'real' s on (its motors: '_walkway'), at the
    door pushed by what Asger pushed its sections by over the last frame
    (the pad's world: 'CabinWorld.struck') and by its seal against the
    rocket's hull, which pushes the rocket as hard (user, 2026-11-18: "Use
    a soft inflatable thing like for airliners")."""
    walkway = self.walkway
    along, about, rocket = 0.0, 0.0, None
    if walkway.attached and self._towered:
      first = len(towerSolids()) + len(self.towerLift.boxesOf())
      along, about = walkway.loadsOf(tuple(
        self.padWorld.struck(first + 4 * k, 4) for k in range(SECTIONS)))
      rocket = self._rocket
    pressed, point = walkway.moved(real, along, about, rocket)
    if rocket is not None and any(pressed):
      hit = turnedFromPad(rocket, tuple(p * real for p in pressed))
      self._kicked(hit, cross(fromPad(rocket, point), hit))

  def _solidBoxes(self, ) -> tuple:
    """Returns the solids in the worlds now (the cabin's; with the
    walkway at the rocket, the pad's too, in the rocket's own axes):
    their middles, half sizes and axes as columns."""
    middles, halves, axes = self.world.solidBoxes()
    if not self.walkway.attached:
      return middles, halves, axes
    padMiddles, padHalves, padAxes = self.padWorld.solidBoxes()
    own = numpy.asarray(self._rocket[1], numpy.float64)
    padMiddles = (padMiddles - numpy.asarray(self._rocket[0])) @ own.T
    padAxes = numpy.einsum('ij,njk->nik', own, padAxes)
    return (numpy.concatenate([middles, padMiddles]),
            numpy.concatenate([halves, padHalves]),
            numpy.concatenate([axes, padAxes]))

  def _kicked(self, push: tuple, twist: tuple) -> None:
    """Pushes the vessel by 'push' (N s) and twists it by 'twist' about
    its middle (N m s), its own axes; docked, the pair (the station's
    flown body)."""
    vessel = self.vessel
    if vessel.docked:
      station = self.station
      arm = rotated(station.body.turn, self.docking.held)
      station.kickedAt(rotated(vessel.turn, push),
                       rotated(vessel.turn, twist), arm)
    else:
      vessel.kicked(push, twist)

  def _jetOf(self, ) -> tuple:
    """Returns the jetpack's push on Asger over his mass (m/s², the
    vessel's own axes): up out of his chair and alive, along the way the
    movement keys held ask ('Crewman.wayOf'); else none (held on the
    ladder the keys carry him along it: '_ladder')."""
    crewman, cockpit = self.cockpit.crewman, self.cockpit
    if (crewman.buckled or self.vitals.cause is not None
            or not self.jetpack.on):
      return 0.0, 0.0, 0.0
    if self.ladder.held:
      return 0.0, 0.0, 0.0
    held = {MOVING[key] for key in self.held if key in MOVING}
    way = crewman.wayOf(held, cockpit.yaw, cockpit.pitch)
    return tuple(p / HEFT for p in self.jetpack.pushOf(way))

  def _geared(self, what: str) -> None:
    """The inventory's gear controls ('what': 'jetpack' switches the
    jetpack on or off, 'stronger' and 'weaker' set its level, 'lamp'
    switches the headlamp), said; only while the inventory is open."""
    if not self._inventoryOpen:
      return
    jetpack = self.jetpack
    if what == 'jetpack':
      jetpack.toggled()
      self._noteOf('Jetpack %s' % ('on' if jetpack.on else 'off'))
    elif what == 'stronger':
      jetpack.stronger()
    elif what == 'weaker':
      jetpack.weaker()
    elif what == 'lamp':
      self.headlamp.toggled()
      self._noteOf('Headlamp %s' % ('on' if self.headlamp.on else 'off'))
    else:
      raise ValueError('no gear control %r' % what)

  def _aboard(self, real: float) -> None:
    """Docked, joins the space station's rooms to the cabin's world (its
    elevators' cages where they are as the frame begins, the world moving
    them through it; the top floor's doors' leaves; the garden, still)
    and moves its elevators and the doors 'real' s on; undocked, takes
    them away again."""
    docked = self.vessel.docked
    if docked != self._stationed:
      self._deckMoved(docked)
    if docked:
      relative = self.docking.relative
      ways, axial = shaftWays(relative), self._axial()
      if self._fixed is None or self._fixed[0] != relative:
        self._fixed = relative, gardenSolids(relative) + terminalSolids(
          relative)
      self._shaftDoorsMoved(real)
      self._solidsSent(True, ways, tuple(
        box for elevator, way in zip(self.elevators, ways)
        for box in elevator.boxesOf(way, axial)) + tuple(
          door.boxOf() for door in self.shaftDoors) + self._fixed[1],
                       self._cages())
      self._hoisted(real, ways)
      self._carKept()
    elif self._stationed:
      self._solidsSent(False, (), ())
    self._stationed = docked

  def _deckMoved(self, docked: bool) -> None:
    """Docking, the deck's furnishings ('_deckthings') come into the
    cabin's world where they are on the station (the docked rocket's
    axes), each its mass; leaving, they are kept where they are on the
    station and put away in the world (no mass)."""
    first, count = len(looseThings()), len(deckThings())
    relative = self.docking.relative
    if relative is None:
      return
    if docked:
      self.world.bodiesPlaced(first, self.deck.laid(relative), tuple(
        thing[5] for thing in deckThings()))
      return
    self._deckKept()
    self.world.bodiesPlaced(first, self.deck.laid(relative), (0.0,) * count)

  def _deckKept(self, ) -> None:
    """Takes where the deck's furnishings are in the cabin's world back
    onto the station (docked)."""
    first, count = len(looseThings()), len(deckThings())
    if self.docking.relative is not None:
      self.deck.kept(self.world.shown()[first:first + count],
                     self.docking.relative)

  def _axial(self, ) -> tuple:
    """Returns the station's own z in the docked rocket's own axes."""
    return stationWay((0.0, 0.0, 1.0), self.docking.relative)

  def _cages(self, ) -> tuple:
    """Returns each elevator's cage's inside along its shaft (from, to:
    'CAGE_OVER' past its plates either way), m: the shaft's only room
    (user, 2026-11-19: "the spokes are not pressurized. Only the
    elevators are")."""
    return tuple((e.floor - CAR_HIGH - CAGE_OVER, e.floor + CAGE_OVER)
                 for e in self.elevators)

  def _doorOfShaft(self, way: tuple) -> ShaftDoor:
    """Returns the top floor door facing the shaft out along 'way'."""
    return max(self.shaftDoors, key=lambda door: dot(DOOR_WAYS[door.k],
                                                     way))

  def _hoisted(self, real: float, ways: tuple) -> None:
    """Moves the station's elevators 'real' s on, each by its motor
    ('_hoist'), pulled along its shaft as the station's turning pulls
    there, pushed by what Asger pushed its cage by over the last frame
    ('CabinWorld.struck': his weight standing in it); what the station
    pushed each cage by (its motor, its brake, the shaft's walls: the
    cage's mass times how it sped up less how it is pulled, less what
    he pushed it by) each pushes the pair back by, at the cage; a cage
    sent from the hub's stop waits, braked, till its top floor door has
    slid shut (the shaft is vacuum: the door is closed for it) (his own
    pushes the cabin's world gives back as if the cage were the pair's:
    '_pushedBack'). Its weight there the station carries already (its
    mass is the station's: only its moving, and the shaft holding it
    against the turning as it moves (Coriolis), push the station)."""
    push, twist = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    first = 0
    for elevator, way in zip(self.elevators, ways):
      middle = elevator.middleOf(way)
      moving = tuple(elevator.speed * w for w in way)
      pull = self.accelerometer.pullAt(middle, moving)
      along = dot(pull, way)
      count = len(PLATE_HALVES)
      load = dot(self.world.struck(first, count)[0], way)
      first += count
      door = self._doorOfShaft(way)
      if (elevator.target is not None and not door.shut
              and abs(elevator.floor - HUB_STOP) < ARRIVED):
        door.closed()
        continue
      faster = elevator.moved(real, along, load)
      still = self.accelerometer.pullAt(middle, (0.0, 0.0, 0.0))
      back = tuple(-CAGE_MASS * (faster * w - (p - s)) * real
                   for w, p, s in zip(way, pull, still))
      push = [a + b for a, b in zip(push, back)]
      twist = [a + b for a, b in zip(twist, cross(middle, back))]
    vessel, station = self.vessel, self.station
    arm = rotated(station.body.turn, self.docking.held)
    station.kickedAt(rotated(vessel.turn, tuple(push)),
                     rotated(vessel.turn, tuple(twist)), arm)

  def _solidsSent(self, docked: bool, ways: tuple, boxes: tuple,
                  cages: tuple = ()) -> None:
    """Puts the station's or the launch tower's solids in the cabin's
    world ('CabinWorld.stationed'; docked, the cages' insides too)
    unless they are there already as they are (user, 2026-11-18: "10 to
    30 fps bro...?": the tower's 288 sent every frame took some 5 ms of
    it; a lift moving is sent anew each frame)."""
    sent = (docked, ways, boxes, cages)
    if sent != self._sentSolids:
      self.world.stationed(docked, ways, boxes, cages)
      self._sentSolids = sent

  def _openDepth(self, point: tuple) -> float:
    """Returns how deep 'point' is in the rooms Asger may be in now (the
    cabin; docked, the station's; on the pad, the walkway's, the launch
    tower's and the doorway if open), m (nought or less: out of them)."""
    docked = self.vessel.docked
    ways = shaftWays(self.docking.relative) if docked else ()
    depth = roomsInside(point, docked, ways, self._cages())
    walkway = self.walkway
    if self.door.passable:
      depth = max(depth, doorwayInside(point))
    if docked or not walkway.attached:
      return depth
    lift = self.towerLift
    return max(depth, walkwayInside(point), groundsInside(
      point, lift.atTop, lift.atFoot))

  def _inSight(self, eye: tuple, there: tuple) -> bool:
    """Returns whether nothing is in the way from 'eye' to 'there' (the
    vessel's own axes): the rooms all the way, no solid (what the
    Grav-Gun sees through: user, 2026-11-17, "the fucking gravity gun
    still works through walls")."""
    return inSight(eye, there, self._openDepth, self._solidBoxes())

  def _towerKept(self, real: float) -> None:
    """On the pad with the walkway out, the launch tower's solids (its
    stairs, its legs, the rocket's legs) and its lift's car (moved on
    'real' s, pushed by what Asger pushed it by over the last frame) are
    in the cabin's world; else, docked or not, the station's
    ('_aboard')."""
    if self.vessel.docked:
      return
    if self.walkway.attached:
      lift, solids = self.towerLift, towerSolids()
      middle = lift.middleOf()
      pull = self.padMeter.pullAt(middle, (0.0, 0.0, lift.speed))
      load = self.padWorld.struck(len(solids), len(lift.boxesOf()))[0][2]
      lift.moved(real, pull[2], load if self._towered else 0.0)
      self._padSolidsSent(solids)
      walkway, rocket = self.walkway.boxesOf(), self._rocket
      self._legsFirst = len(solids) + len(lift.boxesOf()) + len(walkway)
      turn = _turnOfPose(rocket)
      legs = tuple((toPad(rocket, m), h, product(turn, t), movingToPad(
        rocket, m, v)) for m, h, t, v in rocketLegs())
      moving = lift.boxesOf() + walkway + legs
      if moving != self._padMoving:
        self.padWorld.restationed(len(solids), moving)
        self._padMoving = moving
      self._towered = True
    elif self._towered:
      self._padSolidsSent(())
      self._towered = False

  def _towerLiftOf(self, ) -> tuple | None:
    """Returns what E does with the launch tower's lift (the walkway out,
    Asger up): in its car, ride it to the other stop; at a door with the
    car away, call it there; None: nothing."""
    lift, crewman = self.towerLift, self.cockpit.crewman
    if not self.walkway.attached or crewman.sitting:
      return None
    middle = toPad(self._rocket, crewman.middle)
    if lift.holds(middle):
      if lift.target is not None:
        return None
      if lift.atTop:
        return lift, FOOT, 'Ride the lift down to the ground'
      return lift, TOP, 'Ride the lift up to the hall'
    for stop, door in ((TOP, LIFT_TOP), (FOOT, LIFT_FOOT)):
      there = tuple(0.5 * (a + b) for a, b in zip(*door))
      if (math.dist(middle, there) < LIFT_CALL and lift.target != stop
              and abs(lift.floor - stop) > 0.005):
        return lift, stop, 'Call the lift'
    return None

  def _elevatorOf(self, ) -> tuple | None:
    """Returns what E does with an elevator for Asger (docked, up): the
    elevator and its stop to send it to, and what it is said to do: at a
    stop's door with the cage away, that stop (in a cage, nothing: E sits
    him, its button sends it, '_carSent'); on the pad, the launch tower's
    lift; None: nothing."""
    crewman = self.cockpit.crewman
    if not self.vessel.docked:
      return self._towerLiftOf()
    if crewman.buckled:
      return None
    middle = crewman.middle
    ways = shaftWays(self.docking.relative)
    if any(elevator.holds(way, middle) for elevator, way in zip(
        self.elevators, ways)):
      return None
    for elevator, way in zip(self.elevators, ways):
      for stop, door, reach in ((HUB_STOP, SHAFT_FROM - 0.3, HOLE_REACH),
                                (DECK_STOP, DECK - 1.0, CALL_REACH)):
        there = (door * way[0], door * way[1], PLANE)
        if (math.dist(middle, there) < reach
                and abs(elevator.floor - stop) > ARRIVED
                and elevator.target != stop):
          return elevator, stop, 'Call the elevator'
    return None

  def _shaftDoorOf(self, ) -> int | None:
    """Returns the top floor door E works for Asger (up, within
    'DOOR_REACH' of its middle, looking within 'DOOR_AIM' of it); None:
    none."""
    cockpit = self.cockpit
    if cockpit.crewman.sitting or self._outside:
      return None
    eye, look = cockpit.eye(), cockpit.looking()[0]
    best, least = None, DOOR_AIM
    for k in range(len(self.shaftDoors)):
      off = tuple(m - e for m, e in zip(doorMiddle(k), eye))
      far = norm(off)
      if far > DOOR_REACH or far < 1e-6:
        continue
      angle = math.acos(max(-1.0, min(1.0, dot(off, look) / far)))
      if angle < least:
        best, least = k, angle
    return best

  def _shaftDoorWorked(self, k: int) -> None:
    """Opens top floor door 'k' (docked, its shaft's cage at the hub's
    stop: it opens into the cage; else it stays shut, the shaft is
    vacuum) or closes it (what is in the doorway stops it), said."""
    door = self.shaftDoors[k]
    if door.wanted:
      if self._inDoorway(k):
        self._noteOf('The door stays open: Asger is in the doorway')
        return
      door.closed()
      self._noteOf('The door slides shut')
      return
    here = False
    if self.vessel.docked:
      for elevator, way in zip(self.elevators, shaftWays(
          self.docking.relative)):
        if self._doorOfShaft(way) is door:
          here = elevator.atHub
    if self.vessel.docked and not here:
      self._noteOf('The door stays shut: the elevator is not here (call '
                   'it: E by the door)')
      return
    why = door.opened(self.vessel.docked)
    self._noteOf(('The door stays shut: %s' % why) if why else
                 'The door slides open onto the shaft')

  def _inDoorway(self, k: int) -> bool:
    """Returns whether Asger is on the handles through top floor door 'k'
    (past its wall's inside, or in its cage): the leaf would close
    through him (he is out of the cabin's world on them; off them, the
    leaf meets his body)."""
    ladder = self.ladder
    if not ladder.held:
      return False
    _, _, kind, door = RUNS[ladder.on]
    if door != k or kind not in ('door', 'cage'):
      return False
    return dot(ladder.spot, DOOR_WAYS[k]) > HEAD - WALL - 0.3

  def _shaftDoorsMoved(self, real: float) -> None:
    """Moves the top floor's doors 'real' s on, docked ('_shaftdoor'), each
    pushed by what Asger pushed its leaf by over the last frame (round
    the rocket's axis: its leaf is the station's solids' after the
    cages'), pulled as the cabin pulls at its leaf; the rocket takes back
    what moving a leaf took (its mass times how it sped up, less how it
    is pulled: its weight the rocket carries)."""
    first = len(self.elevators) * len(PLATE_HALVES)
    for k, door in enumerate(self.shaftDoors):
      way, middle = door.wayAt()
      moving = tuple(door.speed * w for w in way)
      pull = self.accelerometer.pullAt(middle, moving)
      still = self.accelerometer.pullAt(middle, (0.0, 0.0, 0.0))
      struck = self.world.struck(first + k, 1)
      faster = door.moved(real, dot(pull, way), struck[1][2] / SHAFT_FAR)
      back = tuple(-SHAFT_LEAF * (faster * w - (p - q)) * real
                   for w, p, q in zip(way, pull, still))
      if any(back):
        self._kicked(back, cross(middle, back))

  def _ladderKept(self, ) -> None:
    """Off the handles if he sits, dies, is out on the pad or the run he
    is on is gone (a cage gone, its door shut)."""
    crewman, ladder = self.cockpit.crewman, self.ladder
    if not ladder.held:
      return
    if (crewman.sitting or self._outside or self.vitals.cause is not None
            or not usable(ladder.on, *self._ladderFlags())):
      self._ladderLeft(False)

  def _ladderFlags(self, ) -> tuple:
    """Returns what the handles' runs depend on: docked, each top floor
    door open, each cage at the drum ('_ladder.usable')."""
    return (self.vessel.docked,
            tuple(door.share >= DOOR_OPEN for door in self.shaftDoors),
            tuple(elevator.atHub for elevator in self.elevators))

  def _climbed(self, real: float) -> None:
    """Carries Asger 'real' s on along the handles as W and S ask, the
    way he looks (user, 2026-11-19: "When Asger is in ladder mode, no
    more physics. Asger just moves through the ladder system"): his
    middle where the handles have it, moving as they carry him, upright
    in the rocket, his body turned to where his head looks."""
    cockpit, ladder = self.cockpit, self.ladder
    crewman = cockpit.crewman
    keys = {MOVING[key] for key in self.held if key in MOVING}
    ask = ('ahead' in keys) - ('back' in keys)
    look = cockpit.looking()[0]
    velocity = ladder.moved(real, ask, look, *self._ladderFlags())
    self._facedAlong(look)
    crewman.middle, crewman.velocity = ladder.spot, velocity
    crewman.spin, crewman.touches = (0.0, 0.0, 0.0), True

  def _facedAlong(self, look: tuple) -> None:
    """Turns Asger's body upright in the rocket facing where his head
    looks ('look'), his head straight on it (his look kept)."""
    cockpit = self.cockpit
    crewman = cockpit.crewman
    flat = (look[0], look[1], 0.0)
    if norm(flat) > 0.05:
      crewman.up, crewman.ahead = (0.0, 0.0, 1.0), unit(flat)
      cockpit.yaw = 0.0
      cockpit.pitch = math.asin(max(-1.0, min(1.0, look[2])))

  def _ladderTaken(self, on: int, along: float) -> None:
    """Puts Asger on the handles at 'along' m along run 'on' (said):
    out of the cabin's world, moved by them alone."""
    cockpit = self.cockpit
    crewman = cockpit.crewman
    look = cockpit.looking()[0]
    self.ladder.taken(on, along)
    crewman.climbing, crewman.fallen, crewman.crouching = True, False, False
    self._facedAlong(look)
    crewman.middle, crewman.velocity = self.ladder.spot, (0.0, 0.0, 0.0)
    self._noteOf('On the handles: W and S along them where you look,'
                 ' hold E to let go')

  def _ladderLeft(self, said: bool) -> None:
    """Takes Asger off the handles where he is, still (said if
    'said'): back in the cabin's world."""
    self.ladder.leftOff()
    crewman = self.cockpit.crewman
    crewman.climbing, crewman.velocity = False, (0.0, 0.0, 0.0)
    if said:
      self._noteOf('Asger lets go of the handles')

  def _holdKept(self, now: float) -> None:
    """E held for the handles ('_eSince'): the ring fills over 'HOLD_E'
    s; full, he takes hold of them or lets go (said); E let go sooner is
    a tap ('_eReleased')."""
    viewport = self.viewport
    if self._eSince is None:
      viewport.holdShown(0.0, False, '')
      return
    ladder = self.ladder
    if Qt.Key.Key_E not in self.held or self.vitals.cause is not None:
      self._eSince = None
      viewport.holdShown(0.0, False, '')
      return
    share = (now - self._eSince) / HOLD_E
    if share < 1.0:
      viewport.holdShown(share, True, 'Let go of the handles'
                         if ladder.held else 'Take hold of the handles')
      return
    self._eSince = None
    viewport.holdShown(0.0, False, '')
    if ladder.held:
      self._ladderLeft(True)
      return
    near = self._ladderNear()
    if near is not None:
      self._ladderTaken(*near)

  def _ePressed(self, ) -> None:
    """E pressed: shuts the manual or the inventory; else works at once
    what E works there (an input, a seat, a door, a call: user,
    2026-11-19, "the game is broken again because the EVERYWHERE IS E TO
    LADDER!! so no way to sit!": the handles' hold came first); else, by
    the handles or on them, starts their hold ('_holdKept'; let go
    sooner, the inventory: '_eReleased'); else opens the inventory."""
    if self._manualOpen:
      self._manualOpen = False
    elif self._inventoryOpen:
      self._inventoryShut()
    elif self.inside and self._usable():
      self._used(False)
    elif self.ladder.held or self._ladderNear() is not None:
      self._eSince = time.perf_counter()
    else:
      self._inventoryOpened()

  def _eReleased(self, ) -> None:
    """E let go before the handles' ring filled (nothing else to work
    there: '_ePressed'): a tap, the inventory."""
    if self._eSince is None:
      return
    tapped = time.perf_counter() - self._eSince < HOLD_E
    self._eSince = None
    self.viewport.holdShown(0.0, False, '')
    if tapped:
      self._inventoryOpened()

  def _ladderNear(self, ) -> tuple | None:
    """Returns where Asger, up in the rocket, can take hold of the
    handles: the handle he aims at (the run and how far along it:
    '_ladder.Ladder.aimed'; user, 2026-11-19, "Make it so you have to aim
    at the handles!"); None: none (holding E takes hold)."""
    cockpit = self.cockpit
    if (cockpit.crewman.sitting or self._outside or not self.inside
            or self.vitals.cause is not None):
      return None
    aside = (0.0, 0.0, 0.0)
    if self.vessel.docked:
      aside = tuple(HANDLE_ASIDE * a for a in self._axial())
    return self.ladder.aimed(cockpit.eye(), cockpit.looking()[0],
                             *self._ladderFlags(), aside)

  def _aboardWhy(self, ) -> str:
    """Returns why the rocket may not leave the station ('' it may): a
    top floor door not shut, Asger or something loose aboard it (out of
    the rocket's rooms)."""
    if not self.vessel.docked:
      return ''
    if not all(door.shut for door in self.shaftDoors):
      return 'a top floor door is open'
    crewman = self.cockpit.crewman
    if not crewman.buckled and rocketInside(crewman.middle) < 0.0:
      return 'Asger is aboard Terra Prime'
    for place, _ in self._cabinLoose():
      if rocketInside(place) < 0.0:
        return 'something loose is aboard Terra Prime'
    return ''

  def _cabinLoose(self, ) -> tuple:
    """Returns the cabin's own loose things where they are (as
    'CabinWorld.shown'), not the deck's furnishings after them (they
    belong to Terra Prime: counted, the walkway was never dismissed,
    user, 2026-11-19: "i can't dismiss the walkway")."""
    return self.world.shown()[:len(looseThings())]

  def _dash(self, ) -> dict:
    """Returns what the cabin shows now: the instruments', the loose
    things where they are, his eyes' place and frame (what is in his hand
    is drawn in it), the pull at the candles (g)."""
    dash = self.instruments.dash()
    dash['loose'] = self.world.shown()
    dash['egg'] = self.egg.place
    cockpit = self.cockpit
    dash['gun'] = (False, cockpit.eye(), self._eyesFrame(), (0.0, 0.0, 0.0))
    kind = self.inventory.held
    dash['hand'] = (kind is not None and self.vitals.cause is None
                    and self._zoom < 1.3)
    look, lookUp = cockpit.looking()
    dash['headlamp'] = (self.headlamp.on, cockpit.eye(), look, lookUp)
    dash['nose'] = self._noseCamera
    dash['door'], dash['walkway'] = self.door.share, self.walkway.posesOf()
    dash['outdoor'] = not self.walkway.away
    dash['aboard'] = self.vessel.docked
    dash['shaftDoors'] = tuple(door.share for door in self.shaftDoors)
    dash['checks'] = [name in self.quest.done for name, _ in CHECKLIST]
    lift = self.towerLift
    dash['lift'] = [(middle, turn, self.walkway.attached)
                    for middle, _, turn, _ in lift.boxesOf()]
    cars, lamps, seats, buttons, guards = [], [], [], [], []
    if self.vessel.docked:
      axial = self._axial()
      pressed = max(0.0, 1.0 - (time.perf_counter() - self._carPressedAt)
                    / CAR_BUTTON_IN)
      for k, (elevator, way) in enumerate(zip(self.elevators, shaftWays(
          self.docking.relative))):
        boxes = elevator.boxesOf(way, axial)
        cars += [(middle, turn, middle != AWAY)
                 for middle, _, turn, _ in boxes]
        lamps.append(cageLampOf(elevator.floor, way) + (boxes[0][2],))
        seats.append((elevator.middleOf(way), boxes[0][2]))
        mine = k == self._carSeat
        buttons.append(elevator.buttonOf(way, axial, pressed if mine
                                         else 0.0))
        guards.append(elevator.guardOf(way, axial, self._carGuard if mine
                                       else 0.0))
    dash['cars'], dash['carLamps'] = cars, lamps
    dash['carSeats'] = seats
    dash['carButtons'], dash['carGuards'] = buttons, guards
    first = len(looseThings())
    dash['deck'] = (self.world.shown()[first:] if self.vessel.docked
                    else ())
    dash['ride'] = self._rideFace()
    crewman = self.cockpit.crewman
    dash['cabinLit'] = (crewman.sitting or self._outside
                        or inCabin(crewman.middle)
                        or crewman.middle[2] < CEILING)
    pull = self.accelerometer.pullAt(candleLight(), (0.0, 0.0, 0.0))
    dash['weight'] = norm(pull) / G0
    return dash

  def _seen(self, ) -> tuple:
    """Returns where the eye is from the vessel's middle, the way it
    looks, its up and whether they are his own eyes (his head and arms
    hidden): Asger's eyes (sunk by the thrust, shaken by the engine),
    behind him ('third': '_behind'; no room for it, his own), the
    ride's while his elevator goes ('_rideEye') or the chase camera's
    round the vehicle."""
    vessel = self.vessel
    if not self.inside:
      return self.chase.eyeOf(vessel, self.system) + (False,)
    engine = vessel.engine
    felt = self.accelerometer.felt[2] / G0
    eye = self.cockpit.eyeOf(felt, engine.throttle)
    look, up = self.cockpit.looking()
    own = True
    if self._riding():
      eye, look, up = self._rideEye()
      own = False
    elif self.third:
      behind = self._behind(eye, look, up)
      if behind is not None:
        eye, own = behind, False
    turn = vessel.turn
    return (rotated(turn, eye), rotated(turn, look), rotated(turn, up),
            own)

  def _rideEye(self, ) -> tuple:
    """Returns the eye riding an elevator's seat (user, 2026-11-19: "when
    you get in the seat, we see the third person view of Terra Prime
    centered on Asger"): 'RIDE_FAR' m off him, above the station's
    plane, aside, back toward its axis, looking at him out along the
    spoke (the ring beyond), the station's axis up; the vessel's own
    axes."""
    k, crewman = self._carSeat, self.cockpit.crewman
    way = shaftWays(self.docking.relative)[k]
    axial = self._axial()
    side = unit(cross(axial, way))
    high, aside, back = RIDE_WAY
    off = unit(tuple(high * z + aside * s - back * w for z, s, w in zip(
      axial, side, way)))
    eye = tuple(m + RIDE_FAR * o for m, o in zip(crewman.middle, off))
    look = tuple(-o for o in off)
    up = unit(tuple(z - dot(axial, look) * c for z, c in zip(axial,
                                                              look)))
    return eye, look, up

  def _rideFace(self, ) -> tuple:
    """Returns what the ride's small frame shows: riding, True, the
    second camera before his face (its place, the way it looks, its up)
    and his middle (the frame points at it in the big view; the vessel's
    own axes); else (False,)."""
    if not self._riding() or not self.inside:
      return (False,)
    cockpit = self.cockpit
    crewman = cockpit.crewman
    eye = cockpit.eye()
    facing, up = crewman.ahead, crewman.up
    place = tuple(e + FACE_OFF * a for e, a in zip(eye, facing))
    return True, place, tuple(-a for a in facing), up, crewman.middle

  def _viewed(self, ) -> None:
    """Tab (user, 2026-11-19: "key_TAB should be third person view of
    Asger vehicle or no vehicle"): from the vehicle's chase view to Asger
    seen from behind; else between his eyes and behind him."""
    if not self.inside:
      self.inside, self.third = True, True
    else:
      self.third = not self.third

  def _behind(self, eye: tuple, look: tuple, up: tuple) -> tuple | None:
    """Returns where the eye is seen from behind Asger: 'BEHIND' back
    from his eyes along his look and a little up, drawn in short of any
    wall between (the rooms walked out from his eyes, 'BEHIND_CLEAR' off
    a wall), at the farthest point there 'BEHIND_CLEAR' clear of every
    solid (a camera in the bookshelf or the seat's headrest saw nothing
    but black, 2026-11-19); none 'BEHIND_LEAST' back or further, None
    (the vessel's own axes)."""
    back, lift = BEHIND
    far = tuple(e - back * w + lift * u for e, w, u in zip(eye, look, up))
    boxes = self._solidBoxes()
    steps = 24
    best = None
    for k in range(1, steps + 1):
      share = k / steps
      point = tuple(e + share * (f - e) for e, f in zip(eye, far))
      if self._openDepth(point) < BEHIND_CLEAR:
        break
      if boxGap(point, boxes) >= BEHIND_CLEAR:
        best = point
    if best is None or math.dist(best, eye) < BEHIND_LEAST:
      return None
    return best

  def _looked(self, ) -> str:
    """Returns the action of the input Asger looks at ('' none; a
    readout is read, not worked)."""
    control = self.cockpit.lookedAt()
    return control.action if control and control.peep is not None else ''

  def _used(self, back: bool) -> None:
    """Works the input Asger looks at ('back': a right click, the other
    way: the slide down, the knobs back); out of his chair with none in
    reach, an elevator, a top floor door, his chair; dead, nothing."""
    if self.vitals.cause is not None or self.sleep.on:
      return
    action = self._looked()
    if action:
      self._acted(action, back)
      return
    if self._carButtonAimed():
      self._carSent()
      return
    crewman = self.cockpit.crewman
    if crewman.sitting or back:
      return
    seat = self._carSeatOf()
    if seat is not None:
      self._carSat(seat)
      return
    lift = self._elevatorOf()
    if lift is not None:
      elevator, stop, _ = lift
      elevator.sent(stop)
      return
    door = self._shaftDoorOf()
    if door is not None:
      self._shaftDoorWorked(door)
      return
    if self._chairAimed():
      self._buckled()

  def _usable(self, ) -> bool:
    """Returns whether E has something to work (user, 2026-11-17: "key_E
    should still be the general interaction"; with nothing to work it
    opens the inventory, in his chair too): an input or the household's
    looked at in reach; in an elevator's seat its button looked at; out
    of his chair an elevator's seat (in its cage), a call, a top floor
    door, his chair."""
    if self.vitals.cause is not None or self.sleep.on:
      return False
    if self._looked() or self._carButtonAimed():
      return True
    if self.cockpit.crewman.sitting:
      return False
    return (self._carSeatOf() is not None
            or self._elevatorOf() is not None
            or self._shaftDoorOf() is not None or self._chairAimed())

  def _heldPressed(self, ) -> bool:
    """The right button pressed with no input in reach: what is in his
    hand is used (user, 2026-11-17: "Give Asger a hotbar and an inventory
    like in minecraft. then one tool is the gravgun, then give Asger also
    a telescope"): the telescope looked through while it is held ('SCOPE'
    times), a commando bar eaten. Returns whether it did anything."""
    if self.vitals.cause is not None or self.sleep.on or self._looked():
      return False
    held = self.inventory.held
    if held == 'telescope':
      self._scoping = True
      return True
    if held == 'commando':
      why = self.vitals.munched()
      if why:
        self._noteOf(why)
      else:
        self.inventory.usedUp()
        self._noteOf('Asger eats a commando bar')
      return True
    if held == 'scratchings':
      why = self.vitals.snacked()
      if why:
        self._noteOf(why)
      else:
        self.inventory.usedUp()
        self._noteOf('Asger crunches a handful of pork scratchings')
      return True
    return False

  def _heldReleased(self, ) -> None:
    """The right button let go: the telescope lowered."""
    self._scoping = False

  def _inventoryOpened(self, ) -> None:
    """Opens the inventory (E): the mouse let go to click its slots,
    the telescope lowered."""
    self._inventoryOpen, self._scoping = True, False
    self.pointer.letGo()

  def _inventoryShut(self, ) -> None:
    """Shuts the inventory (E or Esc): the stack on the pointer put back;
    the mouse stays free till a click in the window takes it (user,
    2026-11-19: "I used to hit escape and then click which somehow
    allowed the mouse to snap back": taken from a key, gamescope never
    held it)."""
    self.inventory.closed()
    self._inventoryOpen = False

  def _inventoryShutPicked(self, ) -> None:
    """The open inventory's close button pressed: shut, and the mouse
    taken on that press (a click is what takes it)."""
    if self._inventoryOpen:
      self._inventoryShut()
      self.pointer.take()

  def _inventoryClicked(self, slot: int, right: bool) -> None:
    """A slot of the open inventory clicked (right: the right
    button)."""
    if self._inventoryOpen:
      self.inventory.clicked(slot, right)

  def _scopeKept(self, real: float) -> float:
    """Eases the view's magnification toward the telescope's while it
    is looked through (in his hand, his eyes'), else back to none;
    returns it."""
    held = self.inventory.held
    want = SCOPE if (self._scoping and held == 'telescope'
                     and self.inside and self.vitals.cause is None) else 1.0
    share = 1.0 - math.exp(-real / SCOPE_EASE) if real > 0.0 else 0.0
    self._zoom = math.exp(math.log(self._zoom) + share * (
      math.log(want) - math.log(self._zoom)))
    return self._zoom

  def _eyesFrame(self, ) -> tuple:
    """Returns the turn (w x y z) of his eyes' frame (right, up, back)
    in the vessel's own axes: what he holds is held in it."""
    look, up = self.cockpit.looking()
    right = cross(look, up)
    return quaternionOf(tuple((right[k], up[k], -look[k])
                              for k in range(3)))

  def _prompt(self, ) -> tuple | None:
    """Returns what Asger's eyes are on to work (its key and what working
    it does): an input in reach; out of his chair, an elevator, a door,
    his chair, the ladder (on it, climbing it); what is in his hand;
    None: nothing (or not his eyes)."""
    if not self.inside or self.vitals.cause is not None:
      return None
    looked = self.cockpit.lookedAt()
    if looked is not None and looked.peep is None:
      return '', self._readOf(looked.action)
    if looked is not None:
      return looked.key, self._promptOf(looked)
    if self._carSeat is not None:
      if self._riding():
        return 'Shift', 'Get up'
      down = self.elevators[self._carSeat].atHub
      return 'Space', 'Lift the guard and press: ride %s' % (
        'down to the ring' if down else 'up to the rocket')
    if self._carSeatOf() is not None:
      return 'E', 'Sit down'
    lift = self._elevatorOf()
    if lift is not None:
      return 'E', lift[2]
    door = self._shaftDoorOf()
    if door is not None:
      return 'E', ('Close the door' if self.shaftDoors[door].wanted else
                   'Open the door')
    if self._chairAimed():
      return 'E', 'Sit down'
    if self.ladder.held:
      return 'W / S, hold E', 'Along the handles where you look / let go'
    if self._ladderNear() is not None:
      return 'Hold E', 'Take hold of the handles'
    held = self.inventory.held
    if held == 'telescope' and not self._scoping:
      return 'Right button', 'Hold to look through the telescope'
    if held == 'commando':
      return 'Right button', 'Eat a commando bar'
    if held == 'scratchings':
      return 'Right button', 'Eat some pork scratchings'
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
    if self.autoflight.engaged:
      self.autoflight.letGo(self.vessel)
      self.keeper.realtime()
      self._noteOf('Autopilot off: you took the thrusters')
    total = tuple(sum(way[k] for way in ways) for k in range(3))
    size = norm(total)
    self.vessel.rcs = (0.0, 0.0, 0.0) if size < 1e-9 else tuple(
      RCS_ACCEL * MASS * x / size for x in total)

  def _docked(self, action: str) -> None:
    """Does a docking action by hand: MATCH (turn with the station, nose
    down its axis, or let go), UNDOCK (said when it cannot)."""
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
      self._noteOf('Undocked: pushed off at 0.3 m/s')
    elif pilot.mode == 'match':
      pilot.engaged('off', vessel.turn)
    elif vessel.docked:
      self._noteOf('Docked: Terra Prime turns you')
    elif reading['distance'] > MATCH_REACH:
      self._noteOf('No match: Terra Prime is %.0f km off (within %.0f'
                   ' km)' % (reading['distance'] / 1e3,
                             MATCH_REACH / 1e3))
    else:
      self.docking.aligned(vessel, now)
      pilot.matched(self.docking.turnAt(now), reading['spin'])

  def _inOrbit(self, ) -> bool:
    """Returns whether the rocket is in orbit round Terra Prime's planet
    (its path closed, its periapsis over the air), its engine shut and
    the ascent done: the quest's way into orbit."""
    vessel = self.vessel
    if self.guidance.on or vessel.engine.push > 0.0:
      return False
    return self.autoflight.inOrbit(vessel, self.system)

  def _docking(self, ) -> None:
    """Before the frame's flight: docked, the engine stays shut; else
    MATCH (by hand) keeps turning with the station."""
    vessel, now = self.vessel, self.keeper.now
    if vessel.docked:
      if vessel.engine.throttle > 0.0:
        vessel.engine.throttled(0.0)
        self._noteOf('Docked: undock first (Del)')
      return
    if not self.autodock.on and vessel.autopilot.mode == 'match':
      reading = self.docking.readingOf(vessel, self.system, now)
      vessel.autopilot.matched(self.docking.turnAt(now), reading['spin'])

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
    vessel, now, docking = self.vessel, self.keeper.now, self.docking
    if vessel.docked:
      docking.heldOn(vessel, self.system, now)
      self._reading = docking.readingOf(vessel, self.system, now)
      return
    reading = docking.readingOf(vessel, self.system, now)
    self._reading = reading
    if vessel.latch is not None:
      if docking.home(vessel, reading, now):
        docking.latched(vessel, self.system, now)
        self._docks += 1
        self._noteOf('Docked to Terra Prime: both hatches open overhead.'
                     ' Up: the Grav-Gun on a bolt (right button)')
      return
    if docking.caught(reading):
      docking.captured(vessel, now)
      self.autodock.stopped(vessel)
      self._noteOf('Terra Prime\'s port caught the nose: drawing it in')

  def _statusOf(self, ) -> str:
    """Returns the AUTOPILOT's status line (user, 2026-11-17: "All the
    auto stuff has to be in one place"): the mode chosen, OFF unless it
    has the controls, else what it flies and how far along."""
    flying, keeper = self.autoflight, self.keeper
    said = SAID[flying.mode]
    if not flying.engaged:
      return '%s: OFF' % said
    if flying.mode == 'dock':
      reading = self._reading
      far = '' if reading is None else ' ' + lengthText(reading[
        'distance'])
      return ('DOCK: %s%s' % (self.autodock.phase, far)).upper()
    if flying.mode == 'rendezvous':
      guide = self.rendezvous
      if guide.phase in ('plane', 'wait'):
        return 'RNDZ: BURN IN %s' % timeText(guide.depart
                                             - keeper.elapsed)
      return ('RNDZ: %s %s' % (RENDEZVOUS_SAID.get(guide.phase,
                                                   guide.phase), timeText(
        max(0.0, guide.arrival - keeper.elapsed)))).upper()
    if not self.vessel.engine.lit:
      return 'ORBIT: READY, LAUNCH'
    return ('ORBIT: %s %s' % (self.guidance.phase, lengthText(
      self.guidance.target))).upper()

  def _rangeOf(self, ) -> tuple:
    """Returns Terra Prime's range as its tubes show it ('-' where out
    of them): how far (km), how fast closing (m/s, falling apart less
    than nought), its next closest approach (km) and in how long
    (h:mm)."""
    reading, closest = self._reading, self.orrery.closest
    if reading is None:
      return ('-----',) * 3 + ('--:--',)
    offset = reading['offset']
    apart = norm(offset)
    closing = -dot(reading['drift'], offset) / max(1e-9, apart)
    near = '-----' if closest is None else _tubed(closest[1] / 1e3)
    when = '--:--' if closest is None or closest[0] >= 360000.0 else (
      '%2d:%02d' % (closest[0] // 3600.0, (closest[0] % 3600.0) // 60.0))
    return (_tubed(apart / 1e3), _signed(closing), near, when)

  def _readOf(self, action: str) -> str:
    """Returns what Asger reads off a readout he looks at (user,
    2026-11-17: "when reaching a dial the precise value should be shown.
    like with WAILA"): a dial's exact value, a lamp's on or off, Terra
    Prime's range in full, the status line, the globe's pitch and
    heading."""
    what = action[len('read '):]
    if what == 'THRUST':
      push = self.instruments.valuesOf(self.vessel, self.system)[what]
      return 'Thrust: %.2f g (limited to %g g)' % (push,
                                                   self.instruments.limit)
    if what in DIAL_NAMES:
      value = self.instruments.valuesOf(self.vessel, self.system)[what]
      unit = 'm/s' if what == 'SPEED' else 'm'
      if value >= 1e9:
        return '%s: none (no closed orbit)' % what.capitalize()
      return '%s: %s %s' % (what.capitalize(), _grouped(value, 1), unit)
    if what.startswith('lamp '):
      name = what[len('lamp '):]
      lit = self.instruments.lamps[[n for n, _ in LAMPS].index(name)]
      return '%s: %s' % (name.capitalize(), 'on' if lit else 'off')
    if what == 'range':
      reading, closest = self._reading, self.orrery.closest
      if reading is None:
        return 'Terra Prime: out of range'
      offset = reading['offset']
      apart = norm(offset)
      closing = -dot(reading['drift'], offset) / max(1e-9, apart)
      said = 'Terra Prime %s m, closing %+.1f m/s' % (_grouped(apart, 0),
                                                      closing)
      if closest is not None:
        said += '; closest %s m in %s, passing at %.1f m/s' % (
          _grouped(closest[1], 0), timeText(closest[0]), closest[2])
      return said
    if what == 'status':
      return 'Autopilot: %s' % self._statusOf()
    if what == 'port':
      return self._portText().replace('\n', '   ')
    if what == 'checklist':
      done = self.quest.done
      left = [line for name, line in CHECKLIST if name not in done]
      return 'Launch checklist: %d of %d done%s' % (
        len(CHECKLIST) - len(left), len(CHECKLIST),
        '; next: %s' % left[0].capitalize() if left else '')
    ball = self._ball
    if ball is None:
      return 'The horizon'
    return 'Pitch %+.1f\u00b0, heading %05.1f\u00b0' % (
      ball['pitch'], ball['heading'] % 360.0)

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

  def _portText(self, ) -> str:
    """Returns the docking port's numbers as the display under the CCTV
    shows them (within 'DOCK_SHOWN' of the port): how far, closing how
    fast; off the axis, tilted; what flies it."""
    reading = self._reading
    if reading is None or reading['distance'] > DOCK_SHOWN:
      return 'PORT  -----'
    vessel = self.vessel
    state = ('DOCKED' if vessel.docked else 'AUTO %s' % self.autodock.phase
             if self.autodock.on else 'MATCH' if vessel.autopilot.mode
             == 'match' else 'BY HAND')
    return ('PORT %7.1f M  CLOSE %+6.2f M/S\n'
            'OFF %5.1f M  TILT %4.1f\u00b0  %s' % (
              reading['distance'], reading['closing'], reading['across'],
              math.degrees(reading['tilt']), state.upper()))

  def _noWarp(self, ) -> str:
    """Returns why time may not be warped now ('' it may): Asger out of
    his chair or not fed full (user, 2026-11-17: "Asger must be seated
    and fully saturated for warp to be permitted"), in the air ("Only
    when above the atmosphere must warp be permitted"), on the ground,
    the engine or the thrusters firing, near the station (within
    'WARP_CLEAR' of its port, not docked)."""
    vessel = self.vessel
    body = self.system.bodies[vessel.anchor]
    if not self.cockpit.crewman.buckled:
      return 'Asger must sit in his chair'
    if not self.vitals.full:
      return 'Asger must be fed full first'
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
    """Ends the warp the moment it may not go on, saying why (warp is
    his: user, 2026-11-17, "Warp should not be automatic!"; the
    automatic systems only stop it before they act, 'Timekeeper.
    stopAt'; his AUTO WARP warps for him: '_autoWarpKept')."""
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

  def _quickSaved(self, ) -> str:
    """F5 (user, 2026-11-18: "Also implement the save load system now";
    Kerbal's quick save): the game written to the quick save
    ('_savedTo'). Returns what it said ('' saved)."""
    return self._savedTo(0)

  def _quickLoaded(self, ) -> str:
    """F9: the quick save put back ('_loadedFrom'). Returns what it said
    ('' loaded)."""
    return self._loadedFrom(0)

  def _savedTo(self, slot: int) -> str:
    """Writes the game as it is now to save slot 'slot' ('_savegame':
    nought the quick save, one to 'SLOTS' the pause menu's; user,
    2026-11-19, "we need multiple save files"), what was there replaced,
    with its summary ('_whereSaid'); refused while it readies, Asger
    asleep or dead; a file that cannot be written is said (on screen
    and on the console). Returns what it said ('' saved)."""
    why = self._saveWhy()
    if why:
      self._noteOf('Cannot save: %s' % why)
      return self.note
    if self._inventoryOpen:
      self._inventoryShut()
    path = slotPath(slot)
    try:
      SaveGame(self._gameState(), None, self._whereSaid()).written(path)
    except OSError as error:
      print('[space] could not save to %s: %s' % (path, error), flush=True)
      self._noteOf('Could not save: %s' % error)
      return self.note
    print('[space] saved to %s' % path, flush=True)
    self._cleanAt = self.keeper.elapsed
    self._noteOf('Saved (F9 loads it)' if slot == 0 else
                 'Saved to slot %d' % slot)
    return ''

  def _loadedFrom(self, slot: int) -> str:
    """Puts the game back as save slot 'slot' has it (from this session
    or another); refused while it readies or with nothing there; one
    that cannot be read is said. Returns what it said ('' loaded)."""
    if self._saveWhy() == READYING:
      self._noteOf('Cannot load: %s' % READYING)
      return self.note
    path = slotPath(slot)
    if not path.exists():
      self._noteOf('No quick save yet (F5 saves)' if slot == 0 else
                   'Slot %d is empty' % slot)
      return self.note
    try:
      save = SaveGame.read(path)
    except (OSError, ValueError, KeyError) as error:
      print('[space] could not read %s: %s' % (path, error), flush=True)
      self._noteOf('Could not load: %s' % error)
      return self.note
    self._gameRestored(save.state)
    self._cleanAt = self.keeper.elapsed
    print('[space] loaded %s' % path, flush=True)
    self._noteOf('Loaded %s of %s' % (
      'the quick save' if slot == 0 else 'slot %d' % slot,
      save.saved.astimezone().strftime('%Y-%m-%d %H:%M')))
    return ''

  def _whereSaid(self, ) -> str:
    """Returns a save's summary: where the game is (on the pad, aboard
    Terra Prime, docked there, in orbit with its apsides, flying and how
    high) and its clock (since it began)."""
    vessel, system = self.vessel, self.system
    crewman = self.cockpit.crewman
    if vessel.docked:
      aboard = (not crewman.buckled
                and rocketInside(crewman.middle) < 0.0)
      where = 'Aboard Terra Prime' if aboard else 'Docked at Terra Prime'
    elif vessel.touching:
      where = 'On the pad'
    else:
      where = 'Flying, %s up' % lengthText(vessel.heightOver(system))
      conic = vessel.conicOf(system)
      if conic is not None and self._inOrbit():
        body = system.bodies[vessel.anchor]
        where = 'In orbit of %s, %s x %s' % (
          body.name, lengthText(conic.apoapsis - body.radius),
          lengthText(conic.periapsis - body.radius))
    return '%s, game %s' % (where, timeText(self.keeper.elapsed))

  def _slotsListed(self, saving: bool) -> list:
    """Returns the pause menu's list of saves (saving: the slots to save
    to; loading: the quick save and the slots to load from, the empty
    ones greyed): each its button's words, what picking it says and
    whether it may be picked."""
    out = []
    for slot, save in savesListed():
      if saving and slot == 0:
        continue
      name = 'Quick save' if slot == 0 else 'Slot %d' % slot
      if save is None:
        label, live = '%s: empty' % name, saving
      elif isinstance(save, str):
        label, live = '%s: unreadable (%s)' % (name, save[:40]), saving
      else:
        saved = save.saved.astimezone().strftime('%d %b %H:%M')
        label, live = '%s: %s, saved %s' % (name, save.summary, saved), True
      out.append({'label': label, 'live': live,
                  'what': '%s %d' % ('slot save' if saving else
                                     'slot load', slot)})
    return out

  def _pauseOpened(self, ) -> None:
    """Opens the pause menu (Esc; user, 2026-11-19: "Implement a pause
    menu distinct from the inventory"): the game stands still (no frame
    of it flown: 'tick'), the keys held let go, the telescope lowered,
    the mouse let go to click its buttons."""
    self._paused, self._pauseAsk, self._pauseNote = True, '', ''
    self._scoping = False
    self.held.clear()
    self.pointer.letGo()

  def _pausePicked(self, what: str) -> None:
    """A button of the open pause menu pressed ('what'; on the press: a
    click is what takes the mouse, user, 2026-11-19): 'resume' (the game
    goes on, the mouse taken again), 'load' and 'save' (the list of saves
    to load from or save to: user, 2026-11-19, "we need multiple save
    files"), 'slot load k' (save 'k' put back, then on), 'slot save k'
    (the game written to slot 'k', said; a slot holding a save asks
    first: 'overwrite'), 'overwrite' (written over it), 'back' (the
    menu again), 'exit' (the window shut; asked first if the game has
    run since it was last saved or loaded, '_unsaved'), 'exit save'
    (the quick save written, then shut), 'exit anyway' (shut unsaved),
    'cancel' (no question); 'options' is not there yet (greyed)."""
    if not self._paused:
      return
    if what == 'resume':
      self._resumed()
      self.pointer.take()
    elif what in ('load', 'save'):
      self._pauseAsk, self._pauseNote = what, ''
      self._pauseSlots = self._slotsListed(what == 'save')
    elif what.startswith('slot load '):
      why = self._loadedFrom(int(what.split()[-1]))
      if why:
        self._pauseNote = why
      else:
        self._pausePicked('resume')
    elif what.startswith('slot save '):
      slot = int(what.split()[-1])
      if slotPath(slot).exists():
        self._pauseAsk, self._pauseSlot = 'overwrite', slot
        self._pauseNote = 'Slot %d holds a save' % slot
        return
      self._pauseNote = self._savedTo(slot) or self.note
      self._pauseSlots = self._slotsListed(True)
    elif what == 'overwrite':
      self._pauseAsk = 'save'
      self._pauseNote = self._savedTo(self._pauseSlot) or self.note
      self._pauseSlots = self._slotsListed(True)
    elif what == 'back':
      self._pauseAsk, self._pauseNote, self._pauseSlots = '', '', []
    elif what == 'exit':
      if self._unsaved():
        self._pauseAsk, self._pauseNote = 'exit', ''
      else:
        self.close()
    elif what == 'exit save':
      why = self._quickSaved()
      if why:
        self._pauseNote = why
      else:
        self.close()
    elif what == 'exit anyway':
      self.close()
    elif what == 'cancel':
      self._pauseAsk, self._pauseNote = '', ''
    elif what != 'options':
      raise ValueError('no pause menu button %r' % (what,))

  def _freeSaid(self, ) -> str:
    """Returns what the middle of the view says with the mouse free and
    nothing open to click ('FREE_SAID': a click takes it), else ''."""
    if (self.pointer.taken or self._inventoryOpen or self._paused
            or self._manualOpen or self.mapOpen
            or self.vitals.cause is not None):
      return ''
    return FREE_SAID

  def _resumed(self, ) -> None:
    """Shuts the pause menu: the game goes on (Esc: the mouse free till
    a click in the window takes it)."""
    self._paused, self._pauseAsk, self._pauseNote = False, '', ''

  def _deckSaved(self, ) -> dict:
    """Returns the deck's furnishings as a save keeps them (where they are
    on the station: docked, taken from the cabin's world first)."""
    if self.vessel.docked:
      self._deckKept()
    return keptOf(self.deck)

  def _loadable(self, ) -> bool:
    """Returns whether a save may be loaded now (there is one, the quick
    save or a slot's, the game ready)."""
    return self._saveWhy() != READYING and any(
      slotPath(slot).exists() for slot in range(SLOTS + 1))

  def _unsaved(self, ) -> bool:
    """Returns whether the game has changed since it was last saved or
    loaded (or began): its time has run more than 'UNSAVED_AFTER' s."""
    return self.keeper.elapsed - self._cleanAt > UNSAVED_AFTER

  def _saveWhy(self, ) -> str:
    """Returns why the game may not be saved now ('' it may)."""
    if (self.flight is None or self.world is None
            or not self.viewport.furnishedYet):
      return READYING
    if self.sleep.on:
      return 'Asger is asleep'
    if self.vitals.cause is not None:
      return 'Asger is dead'
    return ''

  def _gameState(self, ) -> dict:
    """Returns the game's state as a save keeps it: when it began, the
    sky, time, the rocket, its guidances and autopilot, Asger (his
    place, his look, his vitals, his inventory), the quest, the walkway,
    the lifts, the instruments (the printer's paper, the log, the tape),
    the loose things, the gravity egg's marble, the ladder's hold, the
    view and the CCTV's feed. What is worked out anew each frame is not
    kept."""
    return {'began': self.began.isoformat(), 'sky': skyOf(self.system),
            'keeper': keptOf(self.keeper), 'vessel': keptOf(self.vessel),
            'ascent': keptOf(self.guidance),
            'rendezvous': keptOf(self.rendezvous),
            'docking': keptOf(self.autodock),
            'port': keptOf(self.docking),
            'autoflight': keptOf(self.autoflight),
            'cockpit': keptOf(self.cockpit), 'vitals': keptOf(self.vitals),
            'inventory': keptOf(self.inventory),
            'quest': keptOf(self.quest), 'walkway': keptOf(self.walkway),
            'door': keptOf(self.door),
            'shaftDoors': [keptOf(d) for d in self.shaftDoors],
            'towerLift': keptOf(self.towerLift),
            'elevators': [keptOf(e) for e in self.elevators],
            'instruments': keptOf(self.instruments),
            'world': self.world.kept(), 'egg': keptOf(self.egg),
            'station': keptOf(self.station),
            'jetpack': keptOf(self.jetpack),
            'headlamp': keptOf(self.headlamp),
            'ladder': keptOf(self.ladder), 'deck': self._deckSaved(),
            'inside': self.inside, 'noseCamera': self._noseCamera}

  def _gameRestored(self, state: dict) -> None:
    """Puts the game back as 'state' ('_gameState') had it, in real time;
    what the window works out as it goes (the station's rooms and solids,
    the tower's, the bolts, the hatch, the closest approach, the tubes)
    worked out anew; asleep, the manual or the inventory open, the
    telescope raised: no more."""
    if len(state['elevators']) != len(self.elevators):
      raise ValueError('the save has %d elevators, the station %d' % (
        len(state['elevators']), len(self.elevators)))
    self.began = datetime.fromisoformat(state['began'])
    skyTo(self.system, state['sky'])
    keptTo(self.keeper, state['keeper'])
    self.keeper.realtime()
    for thing, name in ((self.vessel, 'vessel'), (self.guidance, 'ascent'),
                        (self.rendezvous, 'rendezvous'),
                        (self.autodock, 'docking'), (self.docking, 'port'),
                        (self.autoflight, 'autoflight'),
                        (self.cockpit, 'cockpit'), (self.vitals, 'vitals'),
                        (self.inventory, 'inventory'),
                        (self.quest, 'quest'), (self.walkway, 'walkway'),
                        (self.door, 'door'),
                        (self.towerLift, 'towerLift'),
                        (self.instruments, 'instruments')):
      keptTo(thing, state[name])
    for elevator, kept in zip(self.elevators, state['elevators']):
      keptTo(elevator, kept)
    for door, kept in zip(self.shaftDoors, state['shaftDoors']):
      keptTo(door, kept)
    keptTo(self.egg, state['egg'])
    keptTo(self.station, state['station'])
    keptTo(self.jetpack, state['jetpack'])
    keptTo(self.headlamp, state['headlamp'])
    self.world.keptFrom(state['world'])
    keptTo(self.ladder, state['ladder'])
    keptTo(self.deck, state['deck'])
    self.inside, self._noseCamera = state['inside'], state['noseCamera']
    self._settledAnew()

  def _settledAnew(self, ) -> None:
    """After a load or a warp: what went on stopped (asleep, the manual
    or the inventory open, the telescope raised, a leap, a glance) and
    what the window works out as it goes worked out anew (the tower's
    and the station's solids, the closest approach, the tubes, the map's
    paths)."""
    if self._inventoryOpen:
      self._inventoryShut()
    self.sleep, self._manualOpen = Sleep(), False
    self._eSince = None
    self._scoping, self._leaping, self.cockpit.glancing = False, False, None
    self._towered, self._stationed, self._fixed = False, False, None
    self._sentSolids, self._doorSent = None, None
    self._padSolids, self._padDoorSent = None, None
    self._padMoving, self._legsFirst = None, 0
    if self.padWorld is not None:
      self.padWorld.teleported()
    self._outside = False
    self._closest, self._tubes = None, None
    self.viewport.orbitsRedrawn(self.scenery.orbitsOf(self.system))

  def _boardOf(self, now: float) -> dict:
    """Returns what the control board shows: the throttle, the
    assists, the warp, the autopilot, the map, the keys held and those
    just tapped."""
    guidance = self.guidance
    held = {CAPS[key] for key in self.held if key in CAPS}
    held |= {name for name, at in self._flashed.items()
             if now - at < FLASH}
    return {'throttle': self.vessel.engine.throttle,
            'launched': self.vessel.engine.lit,
            'mode': self.vessel.autopilot.mode,
            'warp': self.keeper.factor,
            'toAp': self.keeper.aimed is not None,
            'action': not self._actionWhy(),
            'autowarp': self._autoWarp,
            'apMode': self.autoflight.mode,
            'engaged': self.autoflight.engaged,
            'phase': self._statusOf().capitalize(),
            'target': lengthText(guidance.target),
            'map': self.mapOpen, 'held': sorted(held),
            'limit': '%g g' % LIMITS[limitNotch(self.vessel.engine)],
            'match': self.vessel.autopilot.mode == 'match',
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

  def _debugKept(self, now: float) -> None:
    """Shows the debug view's lines anew if 'DEBUG_EVERY' s have passed
    since they last were ('now': real s, 'time.perf_counter')."""
    if now - self._debugAt >= DEBUG_EVERY:
      self._debugAt = now
      self.viewport.debugShown(self._debugText())

  def _debugText(self, ) -> str:
    """Returns the debug view's lines (user, 2026-11-18: "implement
    debug view in the top left listing fps, and phys rate"): frames a
    second; each physics' steps a second (the cabin's: Asger and the
    loose things, real time in steps of '_cabinworld.STEP'; the
    flight's: the rocket, off docked), the last frame's steps and how
    long they took."""
    fps, world, flight = self.viewport.fps, self.world, self.flight
    lines = ['%4.0f fps     %6.1f ms a frame' % (
      fps, 1e3 / fps if fps > 0.0 else 0.0)]
    lines.append('Cabin  %6.0f Hz  %4d steps %6.2f ms (of %.0f Hz)' % (
      self._cabinRate.rate, world.lastSteps, world.lastMs, 1.0 / STEP))
    if self.vessel.docked:
      lines.append('Flight   off, docked')
    else:
      lines.append('Flight %6.0f Hz  %4d steps %6.2f ms' % (
        self._flightRate.rate, flight.lastSteps, flight.lastMs))
    return '\n'.join(lines)

  def _readout(self, ) -> str:
    """Returns what the flight says: where, how high and fast, the path's
    apsides, the aim, the guidance, the date; the sound if it failed."""
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
      room = roomOf(crewman.middle, shaftWays(self.docking.relative),
                    self._cages())
      if room and room != 'cabin':
        pull = norm(self._pullOnAsger())
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
    if self.speaker.trouble is not None:
      lines.append('No sound: %s' % self.speaker.trouble)
    if self.note and time.perf_counter() - self._noted < NOTE_LASTS:
      lines.append(self.note)
    return '\n'.join(lines)


def _turnOfPose(rocket: tuple) -> tuple:
  """Returns the turn (w x y z) taking the rocket's own axes to the
  pad's, its pose 'rocket'."""
  own = rocket[1]
  return quaternionOf(tuple((own[0][i], own[1][i], own[2][i])
                            for i in range(3)))


def _grouped(value: float, places: int) -> str:
  """Returns 'value' with 'places' decimals, its thousands set apart by
  spaces."""
  return ('{:,.%df}' % places).format(value).replace(',', ' ')


def _tubed(km: float) -> str:
  """Returns 'km' as five number tubes show it: two decimals under a
  hundred, one under ten thousand; past that dashes."""
  if km < 99.995:
    return '%6.2f' % km
  if km < 9999.95:
    return '%6.1f' % km
  return '-----'


def _signed(speed: float) -> str:
  """Returns 'speed' (m/s) as five number tubes show it, signed: one
  decimal under a thousand; past a hundred thousand dashes."""
  if abs(speed) < 999.95:
    return '%+6.1f' % speed
  if abs(speed) < 99999.5:
    return '%+5.0f' % speed
  return '-----'


def _nightStart(now: datetime, device: str) -> float:
  """Returns how long after 'now' the game starts outside: nought if it
  is night on the pad with 'NIGHT_LEFT' s of it left; else 'INTO_NIGHT'
  s after the next dusk there (the sky flown on 'device')."""
  from ._vessel import LEGS
  system = solarSystemOn(julianOf(now), device)
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
