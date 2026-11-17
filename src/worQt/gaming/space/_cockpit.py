"""
Cockpit is the creative rocket's capsule as Asger sits in it (user,
2026-11-16: "We need Asger in that rocket. in first person the hud
hides and instead Asger is presented iwth a fully functional diegetic
dashboard"; "Asger sits upright on the launch pad"; "a style that is
more 1970's B&O but with dials, switches and indicators illuminated.
*Every* fourtpeep input ... must visibly deform when activated. Instead
of a terminal ... a teleprinter"): his seat and pose, his eyes and
where he looks (and glances, a key pressed), the dashboard: its inputs
(each a FourthPeep of the sandbox's: switch, key, knob, slide control)
and which he looks at, its dials, lamps, ball, monitor and
teleprinter; the tape deck at his right; its windows.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from worQt.gaming.sandbox import FourthPeep, Knob, Pushbutton, Slider

from ._ascentguidance import TARGET, TARGETS
from ._control import Control
from ._turns import aboutAxis
from ._vessel import CAPSULE, CENTRE, RADIUS, SIZE

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._crewman import Crewman

#  The capsule from inside, the vessel's own axes (z its nose, Asger
#  facing x: east on the pad): its floor (the tank's top), its cone's
#  radius at the floor and at the nose's foot, its wall's thickness, m.
FLOOR = CAPSULE[0] - CENTRE
NOSE = CAPSULE[1] - 0.4 * SIZE - CENTRE
WALL = 0.05
#  Asger's place in the capsule (user, 2026-11-16: "Asger sits in what is
#  more like an office chair. To his left is a window. The chair is like
#  1/8 the diameter of the rocket from the hull"): the middle of his rig
#  (his chair, the dashboard before him, the consoles at his sides; all
#  laid out round it as they were round the old capsule's middle), its
#  x and y from the capsule's axis, m; he faces x (east on the pad), the
#  hull close on his left (+y), the room on his right.
SEAT_AT = (0.0, RADIUS - 0.125 * 2.0 * RADIUS)


def seated(x: float, y: float, z: float) -> tuple:
  """Returns the point 'x' ahead, 'y' to the left of his rig's middle
  and 'z' over the floor, the vessel's own axes."""
  return SEAT_AT[0] + x, SEAT_AT[1] + y, FLOOR + z


#  Its windows, each a span of the cone's round (deg from x, toward y)
#  and of height (m): a big one on his left, from his knees to over his
#  head, a little ahead of him and behind.
WINDOWS = (((66.0, 104.0), (FLOOR + 0.55, FLOOR + 2.3)),)
#  The office chair: its seat and its back (middle, half sizes), m; how
#  much higher its seat is than the old capsule's (everything he sees and
#  reaches is that much higher, as near him as it was).
CUSHION = (seated(-0.27, 0.0, 0.47), (0.25, 0.25, 0.05))
LIFT = 0.17
BACKREST = (seated(-0.55, 0.0, 0.92), (0.04, 0.24, 0.3))
#  Asger seated: his skin's pixel in metres, where his soles' point is
#  (his hips 'HIPS' m over the cushion), his arms' and legs' turns about
#  their left (rad: legs straight ahead, arms reaching for the panel).
SCALE = 0.055
HIPS = 0.08
FIGURE = seated(-0.25, 0.0, CUSHION[0][2] - FLOOR + CUSHION[1][2] + HIPS
                - 12 * SCALE)
LIMBS = {'right arm': -1.05, 'left arm': -1.05, 'right leg': -0.5 * math.pi,
         'left leg': -0.5 * math.pi}
#  His eyes: on his face (its front, 28 of 32 pixels up), a hair ahead.
EYE = (FIGURE[0] + 4 * SCALE + 0.02, FIGURE[1], FIGURE[2] + 28 * SCALE)
#  How far he may turn his head (rad): round, and up or down; how fast
#  the mouse turns it (rad a pixel); a key pressed, he glances at its
#  control, his head eased there (most of the way in 'GLANCE' s).
YAW_MOST, PITCH_MOST = 2.4, 1.4
TURN = 0.0035
GLANCE = 0.1
#  The thrust presses him into his seat: his eyes sink this far a g,
#  m, at most 'SINK_MOST'; the engine shakes them this much at full
#  throttle, m.
SINK = 0.012
SINK_MOST = 0.05
SHAKE = 0.0025
#  The dashboard: its face's middle, tilted back 'PANEL_TILT' (deg) to
#  face his eyes; its right (his right: -y), up (along its face) and out
#  (toward him); half its width and height, its thickness, m; the
#  rosewood frame round it, m.
PANEL_TILT = 31.0
PANEL_MIDDLE = seated(0.55, 0.0, 0.93 + LIFT)
_TILT = math.radians(PANEL_TILT)
PANEL_AXES = ((0.0, -1.0, 0.0), (math.sin(_TILT), 0.0, math.cos(_TILT)),
              (-math.cos(_TILT), 0.0, math.sin(_TILT)))
PANEL_HALF = (0.4, 0.25)
PANEL_THICK = 0.03
FRAME = 0.025
#  The panel in framed sections, each titled on its face (user,
#  2026-11-16: "Have a clearer section devoted to autopolit functions"):
#  title, left, bottom, right, top (right, up from its middle, m).
SECTIONS = (('AUTOPILOT', -0.39, -0.055, -0.112, 0.095),
            ('ASCENT GUIDANCE', 0.112, -0.055, 0.39, 0.112),
            ('TIME AND ENGINE', -0.39, -0.235, -0.09, -0.085),
            ('DOCKING', 0.085, -0.235, 0.39, -0.085))
#  On the panel (right, up from its middle, m), its outputs: the dials
#  (each its name and middle; their radius): the altimeter by the orbit
#  knob, its pink mark at the guidance's target ("The orbit knob is
#  there, but not the indication of the current set value. Place the
#  altimeter near it and put the pink line there"), each needle a lever
#  on its turning shaft ("the needle should be modelled as an actually
#  moving lever on a rotating actuator"); the lamps (name, middle;
#  radius); the closed circuit monitor ("make it more 1970 B&O just
#  smaller"; 2026-11-17: "Move the CCTV to the space beneath the
#  tele-printer": its screen's middle, half its size (4:3), how far its
#  housing stands out). The horizon's ball is the globe's ('GLOBE_AT'):
#  its radius, its glass dome's (from its middle).
DIALS = (('HEIGHT', (0.175, 0.025)), ('SPEED', (-0.205, 0.17)),
         ('APOAPSIS', (0.215, 0.17)), ('PERIAPSIS', (0.33, 0.17)))
DIAL_RADIUS = 0.04
LAMPS = (('ENGINE', (-0.1, 0.205)), ('AIR', (-0.06, 0.205)),
         ('GROUND', (-0.02, 0.205)), ('WARP', (0.02, 0.205)),
         ('GUIDE', (0.06, 0.205)), ('ORBIT', (0.1, 0.205)),
         ('DOCK', (0.14, 0.205)))
LAMP_RADIUS = 0.008
BALL_RADIUS = 0.15
GLASS = BALL_RADIUS + 0.02
SCREEN_AT, SCREEN_HALF, MONITOR_OUT = (0.0, -0.165), (0.052, 0.039), 0.03
#  Its inputs: the switches (name, key, action, middle; their bat's
#  length; off down, on up, rad about the panel's right), each with a
#  lit legend over it ('LEGEND_UP' m higher); the knobs (name, key,
#  action, middle, notches, first notch's turn, a notch's turn: rad about
#  the panel's out, clockwise as he sees it going on; their radius): the
#  orbit knob a notch for each of the guidance's targets, marked ("The
#  orbit input dial should have clearer markings on it"); the keys
#  (name, key, action, middle; half their size and their travel in): by
#  section. Each switch and knob has a guard flipped up while it is
#  worked ("it should have a safety gaurd that is lifted up when
#  adjusted. same for all toggle switch"): half its size, how far it
#  flips up (rad), how long it stays up after, s. Docking (user,
#  2026-11-17: "we include buttons so that a try-hard *could* manually do
#  the thing ... But where we also provide an automated system ... put
#  ins some whater the fuck necessary buttons for the tryhards, next to
#  the CCTV, but also put an auto system"): right of the monitor, the
#  docking thrusters' keys, the monitor's feed (CAM: aft or the nose's
#  docking camera), UNDOCK, the MATCH and AUTO switches; the limiter
#  joined the warp, the map's switch went to the left console. (The
#  gravity knob, the
#  magic gravity, is gone: user, 2026-11-17, "Remove the fake gravity
#  magic switch"; a station's spin is to give gravity.) The engine's
#  limiter right of the monitor (user,
#  2026-11-17: "for deep space missinos... We need to have another engine
#  control that restricts the engine output to a particular g, for
#  example 1. Then no need for magic gravity"): the most the engine may
#  push, g ('LIMITS', its notches; the last its full thrust: no limit).
SWITCHES = (('HOLD', 'T', 'hold', (-0.35, 0.0)),
            ('PRO', 'F', 'prograde', (-0.285, 0.0)),
            ('RETRO', 'R', 'retrograde', (-0.22, 0.0)),
            ('AIM', 'W', 'aim', (-0.155, 0.0)),
            ('ASCENT', 'J', 'ascent', (0.352, 0.01)),
            ('MATCH', 'L', 'match', (0.31, -0.19)),
            ('AUTO', 'C', 'autodock', (0.365, -0.19)))
BAT_LONG = 0.03
BAT_OFF, BAT_ON = 0.5, -0.5
LEGEND_UP = 0.042
LEGEND_HALF = (0.026, 0.009)
KNOBS = (('WARP', '. ,', 'warp', (-0.335, -0.165), 8, math.radians(105),
          -math.radians(30)),
         ('LIMIT', 'Y U', 'limit', (-0.225, -0.165), 8, math.radians(105),
          -math.radians(30)),
         ('ORBIT', '[ ]', 'orbit', (0.27, 0.025), len(TARGETS),
          math.radians(150), -math.radians(30)))
KNOB_RADIUS = 0.022
KEYS = (('REAL', '/', 'stop', (-0.13, -0.125)),
        ('TO AP', 'G', 'toAp', (-0.13, -0.19)),
        ('UP', '\u2191', 'rcs up', (0.155, -0.125)),
        ('DOWN', '\u2193', 'rcs down', (0.155, -0.211)),
        ('LEFT', '\u2190', 'rcs left', (0.11, -0.168)),
        ('RIGHT', '\u2192', 'rcs right', (0.2, -0.168)),
        ('FWD', 'PgUp', 'rcs ahead', (0.25, -0.13)),
        ('BACK', 'PgDn', 'rcs back', (0.25, -0.2)),
        ('CAM', 'K', 'camera', (0.3, -0.108)),
        ('UNDOCK', 'Del', 'undock', (0.36, -0.108)))
#  The docking thrusters' keys' ways, the rocket's own axes (the nose
#  camera looks along its z, its picture's up its x: up, down, left,
#  right as it shows them; ahead and back along the nose).
THRUSTS = {'rcs up': (1.0, 0.0, 0.0), 'rcs down': (-1.0, 0.0, 0.0),
           'rcs left': (0.0, -1.0, 0.0), 'rcs right': (0.0, 1.0, 0.0),
           'rcs ahead': (0.0, 0.0, 1.0), 'rcs back': (0.0, 0.0, -1.0)}
LIMITS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
KEY_HALF, KEY_TRAVEL = (0.02, 0.014), 0.006
GUARD_SWITCH = (0.017, 0.025, 0.022)
GUARD_KNOB = (KNOB_RADIUS + 0.006, KNOB_RADIUS + 0.006, 0.02)
GUARD_OPEN = math.radians(105.0)
GUARD_HOLD = 1.2
#  The consoles either side of his chair at his armrests (middle, half
#  sizes; their aluminium plates on top, faces at 'TOP'), facing up,
#  aluminium on rosewood: on his right the throttle's slide control on
#  the outer edge (its near end, its length along x, m) and the full and
#  cut keys on the inner, clear of it as he looks; on his left back to
#  the pad and the view's switch. The teleprinter is in the dashboard
#  (user, 2026-11-16: "The teleprinter should be even less audible and
#  should be more promenently on the dashboard"): its paper in a window
#  in the panel's middle (its middle, on the panel; its paper's size).
TOP = FLOOR + 0.54 + LIFT
RIGHT_CONSOLE = (seated(0.08, -0.52, 0.5 * (TOP - FLOOR) - 0.002),
                 (0.2, 0.12, 0.5 * (TOP - FLOOR) - 0.002))
LEFT_CONSOLE = (seated(0.08, 0.52, 0.5 * (TOP - FLOOR) - 0.002),
                (0.2, 0.12, 0.5 * (TOP - FLOOR) - 0.002))
SLIDER_FROM = seated(-0.06, -0.58, TOP - FLOOR + 0.004)
SLIDER_LONG = 0.28
CONSOLE_KEYS = (('FULL', 'Z', 'full', seated(0.12, -0.45, 0.0)[:2]),
                ('CUT', 'X', 'cut', seated(-0.04, -0.45, 0.0)[:2]),
                ('PAD', '\u232b', 'pad', seated(0.24, 0.43, 0.0)[:2]))
CONSOLE_SWITCHES = (('VIEW', 'V', 'view', seated(0.24, 0.6, 0.0)[:2]),
                    ('MAP', 'M', 'map', seated(0.08, 0.6, 0.0)[:2]))
CONSOLE_KEY_HALF = (0.03, 0.03)
PAPER_AT = (0.0, 0.05)
PAPER_WIDE, PAPER_HIGH = 0.19, 0.24
#  The sideboard at his right, the tape deck on it and its keys before it
#  (user, 2026-11-16: "The tape controls should be over by the actual
#  tape deck"): its middle and half sizes; the deck's keys (name, key,
#  action, place on its top).
SIDEBOARD = (seated(0.1, -1.0, 0.5 * (TOP - FLOOR)),
             (0.32, 0.2, 0.5 * (TOP - FLOOR)))
DECK_KEYS = (('PLAY', 'P', 'play', seated(-0.06, -0.835, 0.0)[:2]),
             ('STOP', 'O', 'halt', seated(0.01, -0.835, 0.0)[:2]),
             ('EJECT', 'I', 'eject', seated(0.08, -0.835, 0.0)[:2]))
#  The horizon (user, 2026-11-16: "The horizon should not be in the
#  dashboard as such. It should be more like it's own piece of furniture
#  almost. like a globe"): its ball's middle on a stand at his front
#  right, facing his eyes, and its radius, m.
GLOBE_AT = seated(0.62, -0.74, 0.95 + LIFT)


def _globeAxes() -> tuple:
  """Returns the globe's axes: right and up as he sees it, out toward
  his eyes (its up as near the vessel's z as it can be)."""
  out = tuple(e - g for e, g in zip(EYE, GLOBE_AT))
  size = math.sqrt(sum(x * x for x in out))
  out = tuple(x / size for x in out)
  right = (-out[1], out[0], 0.0)
  size = math.hypot(right[0], right[1])
  right = (right[0] / size, right[1] / size, 0.0)
  up = (out[1] * right[2] - out[2] * right[1],
        out[2] * right[0] - out[0] * right[2],
        out[0] * right[1] - out[1] * right[0])
  return right, up, out


GLOBE_AXES = _globeAxes()
#  The closed circuit camera on the hull (the vessel's own axes): at the
#  capsule's foot on his left, outside the tank, looking aft down the
#  rocket and a little in, its picture's up away from the hull (the hull
#  along the picture's foot); its view's height, deg.
CAMERA_AT = (0.0, RADIUS + 0.35, FLOOR - 0.4)
CAMERA_LOOK = (0.0, -0.15, -1.0)
CAMERA_UP = (0.0, 1.0, 0.0)
CAMERA_VIEW = 64.0
#  The reel-to-reel deck (user, 2026-11-16: "use @previews/stereo reel
#  to reel"; "it should prolly be off to the right of Asger"): its model
#  (in 'models', CC-BY: 'models/CREDITS.md'; its frame x right as one
#  faces it, y up, z out of its face, its foot's middle the origin), how
#  much of its size, where its origin is (on the sideboard at his right)
#  and its frame's axes in the vessel's (it faces him: its x his back,
#  its y up, its z toward him).
TAPE_MODEL = 'Stereo Reel to Reel Tape Deck.glb'
TAPE_SCALE = 0.6
TAPE_ORIGIN = (SIDEBOARD[0][0], SIDEBOARD[0][1] - 0.05, TOP + 0.014)
TAPE_AXES = ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
#  A ray from his eyes looks this far at most, m. The gravity gun reaches
#  a magic bolt this far, m, pointed at within 'AIM' rad (or its ring
#  seen from there, 'BOLT_SEEN' m round).
REACH = 1.6
GUN_REACH = 25.0
AIM = math.radians(3.0)
BOLT_SEEN = 0.15
UP = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
#  A console's top, its axes as he reads it: right (his right, -y), up
#  along it (away from him, +x), out (+z).
CONSOLE_AXES = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def capsuleRadius(z: float) -> float:
  """Returns the capsule cone's outer radius at height 'z' (the vessel's
  own axes), m."""
  share = min(1.0, max(0.0, (z - FLOOR) / (NOSE - FLOOR)))
  return RADIUS + share * (0.45 * SIZE - RADIUS)


def panelPoint(right: float, up: float, out: float) -> tuple:
  """Returns the point 'right', 'up', 'out' m from the panel's middle
  along its axes, the vessel's own axes."""
  return tuple(c + right * a + up * b + out * n for c, a, b, n in zip(
    PANEL_MIDDLE, *PANEL_AXES))


def _negative(axis: tuple) -> tuple:
  """Returns 'axis' the other way."""
  return tuple(-x for x in axis)


def _galley() -> tuple:
  """Returns what he may work away from the dashboard: the rations'
  crate (look at it within reach and click: he eats one)."""
  from ._furnishings import rationCrate
  middle, axes, half = rationCrate()
  top = tuple(m + half[2] * u for m, u in zip(middle, axes[2]))
  peep = Pushbutton('RCIR', None, top, (0.0, 0.0, -1.0), 0.01,
                    ('Eat a ration (RCIR)',) * 2)
  return (Control('RCIR', 'E', 'eat', middle, axes, half, peep),)


def _controls() -> tuple:
  """Returns the dashboard's inputs, each a 'Control' with its
  FourthPeep: the panel's switches, knobs and keys, the consoles' keys
  and the deck's (on the sideboard), the view's switch, the throttle's
  slide control."""
  out = []
  face = 0.5 * PANEL_THICK
  for name, key, action, (u, v) in SWITCHES:
    pivot = panelPoint(u, v, face)
    peep = FourthPeep(name, None, pivot, PANEL_AXES[0], BAT_LONG, BAT_OFF,
                      BAT_ON, ('Switch %s on' % name,
                               'Switch %s off' % name))
    out.append(Control(name, key, action, panelPoint(u, v, face + 0.015),
                       PANEL_AXES, (0.012, 0.02, 0.018), peep))
  for name, key, action, (u, v), notches, near, step in KNOBS:
    pivot = panelPoint(u, v, face)
    peep = Knob(name, None, pivot, PANEL_AXES[2], KNOB_RADIUS, near, step,
                notches)
    first = {'orbit': TARGETS.index(TARGET), 'limit': len(LIMITS) - 1}
    if action in first:
      peep.set(first[action])
      peep.value = float(peep.notch)
    out.append(Control(name, key, action, panelPoint(u, v, face + 0.012),
                       PANEL_AXES, (KNOB_RADIUS, KNOB_RADIUS, 0.012), peep))
  for name, key, action, (u, v) in KEYS:
    out_ = face
    pivot = panelPoint(u, v, out_)
    peep = Pushbutton(name, None, pivot, _negative(PANEL_AXES[2]),
                      KEY_TRAVEL)
    out.append(Control(name, key, action, panelPoint(u, v, out_ + 0.008),
                       PANEL_AXES, KEY_HALF + (0.008,), peep))
  for name, key, action, (x, y) in CONSOLE_KEYS + DECK_KEYS:
    pivot = (x, y, TOP)
    peep = Pushbutton(name, None, pivot, (0.0, 0.0, -1.0), KEY_TRAVEL)
    out.append(Control(name, key, action, (x, y, TOP + 0.012),
                       CONSOLE_AXES, CONSOLE_KEY_HALF + (0.012,), peep))
  for name, key, action, (x, y) in CONSOLE_SWITCHES:
    pivot = (x, y, TOP)
    peep = FourthPeep(name, None, pivot, CONSOLE_AXES[0], BAT_LONG,
                      BAT_OFF, BAT_ON, ('Switch %s' % name,) * 2)
    out.append(Control(name, key, action, (x, y, TOP + 0.015),
                       CONSOLE_AXES, (0.015, 0.02, 0.018), peep))
  peep = Slider('THROTTLE', None, SLIDER_FROM, (1.0, 0.0, 0.0),
                SLIDER_LONG)
  middle = (SLIDER_FROM[0] + 0.5 * SLIDER_LONG, SLIDER_FROM[1],
            SLIDER_FROM[2] + 0.02)
  out.append(Control('THROTTLE', 'Shift Ctrl', 'throttle', middle, UP,
                     (0.5 * SLIDER_LONG + 0.02, 0.03, 0.03), peep))
  return tuple(out)


class Cockpit:
  """
  Cockpit holds Asger in the capsule: where he looks ('yaw', round from
  ahead toward his left, 'pitch', up; rad, his head's own, the capsule
  turning him with it), where he glances ('glancing': a key pressed
  turns his head to its control, eased; the mouse takes over at once)
  and the dashboard's inputs ('controls': each a 'Control' and its
  FourthPeep, made anew a cockpit). His eyes sink into his seat with
  the thrust and shake with the engine ('eyeOf'); what he looks at is
  the nearest input along his eyes' middle within 'REACH' ('lookedAt').
  His figure sits in the seat ('figureOf'), its head left out when it
  is his own eyes we see through. Out of his chair ('crewman': user,
  2026-11-17: "when can Asger get up and float around in
  micro-gravity?") his head turns from his body's up and ahead, his eyes
  and figure are his body's, and he reaches what is near his eyes. What
  he may work away from
  the dashboard is the 'galley' (the rations' crate: user, 2026-11-17:
  "To eat, Asger goes to the kitchen"), looked at as the inputs are.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  yaw: float
  pitch: float
  glancing: tuple | None
  controls: tuple
  crewman: Crewman
  galley: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    from ._crewman import Crewman
    self.yaw, self.pitch, self.glancing = 0.0, -0.12, None
    self.controls, self.galley = _controls(), _galley()
    self.crewman = Crewman()
    self._shaker = random.Random(2026)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def turned(self, right: float, down: float) -> None:
    """The 'turned' method turns his head as the mouse moved 'right' and
    'down' pixels (a glance given up)."""
    self.glancing = None
    self.yaw -= TURN * right
    if self.crewman.buckled:
      self.yaw = max(-YAW_MOST, min(YAW_MOST, self.yaw))
    else:
      self.yaw = math.remainder(self.yaw, 2.0 * math.pi)
    self.pitch = max(-PITCH_MOST, min(PITCH_MOST, self.pitch
                                      - TURN * down))

  def gotUp(self, ) -> None:
    """The 'gotUp' method gets him out of his chair, still looking where
    he looked."""
    self.crewman.unbuckled()
    self.glancing = None

  def satDown(self, ) -> bool:
    """The 'satDown' method sits him in his chair if he is near it
    enough, his head turned to look where it looked (within the seat's
    reach); returns whether he could."""
    look = self.looking()[0]
    if not self.crewman.satDown():
      return False
    self.yaw = max(-YAW_MOST, min(YAW_MOST, math.atan2(look[1], look[0])))
    self.pitch = max(-PITCH_MOST, min(PITCH_MOST, math.asin(max(
      -1.0, min(1.0, look[2])))))
    return True

  def boltAimed(self, bolts: tuple) -> int | None:
    """The 'boltAimed' method returns the magic bolt (its index in
    'bolts': each its place and the way it faces) the gravity gun points
    at out of his chair: within 'GUN_REACH' of his eyes, facing him,
    nearest to his eyes' middle within 'AIM' or its ring; None if
    none (or he sits)."""
    if self.crewman.buckled:
      return None
    eye, look = self.eye(), self.looking()[0]
    best, least = None, math.inf
    for k, (place, way) in enumerate(bolts):
      off = tuple(p - e for p, e in zip(place, eye))
      far = math.sqrt(sum(x * x for x in off))
      if far > GUN_REACH or far < 1e-6 or sum(
          w * o for w, o in zip(way, off)) >= 0.0:
        continue
      along = sum(o * l for o, l in zip(off, look)) / far
      angle = math.acos(max(-1.0, min(1.0, along)))
      if angle <= max(AIM, math.atan(BOLT_SEEN / far)) and angle < least:
        best, least = k, angle
    return best

  def strappedIn(self, ) -> None:
    """The 'strappedIn' method puts him in his chair wherever he is (he
    wakes there), looking ahead."""
    self.crewman.strappedIn()
    self.yaw, self.pitch, self.glancing = 0.0, -0.12, None

  def eye(self, ) -> tuple:
    """The 'eye' method returns his eyes' place (seated: 'EYE')."""
    if self.crewman.buckled:
      return EYE
    return self.crewman.eyeOf(self.yaw)

  def glanced(self, action: str) -> None:
    """The 'glanced' method turns his head toward the input working
    'action' (user, 2026-11-16: "When I press a keyboard key my view will
    turn to center on that key"); none such, nothing."""
    control = self.controlOf(action)
    if control is None or not self.crewman.buckled:
      return
    way = tuple(a - b for a, b in zip(control.centre, EYE))
    size = math.sqrt(sum(x * x for x in way))
    self.glancing = (math.atan2(way[1], way[0]),
                     math.asin(max(-1.0, min(1.0, way[2] / size))))

  def acted(self, seconds: float) -> None:
    """The 'acted' method moves his head 'seconds' on toward where he
    glances, and every input toward where the hand puts it."""
    if self.glancing is not None:
      share = 1.0 - math.exp(-seconds / GLANCE)
      self.yaw += share * (self.glancing[0] - self.yaw)
      self.pitch += share * (self.glancing[1] - self.pitch)
      if abs(self.glancing[0] - self.yaw) + abs(
          self.glancing[1] - self.pitch) < 1e-3:
        self.glancing = None
    for control in self.controls:
      control.peep.acted([], seconds)

  def controlOf(self, action: str) -> Control | None:
    """The 'controlOf' method returns the input working 'action' (None:
    none)."""
    for control in self.controls:
      if control.action == action:
        return control
    return None

  def looking(self, ) -> tuple:
    """The 'looking' method returns where he looks and his head's up,
    unit vectors in the vessel's own axes (out of his chair, his head
    turned from his body's up and ahead)."""
    crewman = self.crewman
    if not crewman.buckled:
      look = crewman.lookOf(self.yaw, self.pitch)
      facing = crewman.facing(self.yaw)
      cp, sp = math.cos(self.pitch), math.sin(self.pitch)
      return look, tuple(-sp * f + cp * u for f, u in zip(facing,
                                                           crewman.up))
    cy, sy = math.cos(self.yaw), math.sin(self.yaw)
    cp, sp = math.cos(self.pitch), math.sin(self.pitch)
    return (cp * cy, cp * sy, sp), (-sp * cy, -sp * sy, cp)

  def eyeOf(self, felt: float, throttle: float) -> tuple:
    """The 'eyeOf' method returns his eyes' place in the vessel's own
    axes, sunk into his seat by 'felt' (the push along the nose, in g)
    and shaken by the engine at 'throttle' (out of his chair: his body's
    eyes, swaying with his stride)."""
    if not self.crewman.buckled:
      return self.crewman.eyeOf(self.yaw)
    sink = max(-SINK_MOST, min(SINK_MOST, -SINK * felt))
    shake = SHAKE * throttle
    jiggle = tuple(shake * self._shaker.uniform(-1.0, 1.0)
                   for _ in range(3))
    return EYE[0] + jiggle[0], EYE[1] + jiggle[1], EYE[2] + sink + jiggle[2]

  def lookedAt(self, ) -> Control | None:
    """The 'lookedAt' method returns the input his eyes' middle rests on
    (the nearest within 'REACH'), None if none."""
    way, eye = self.looking()[0], self.eye()
    best, nearest = None, REACH
    for control in self.controls + self.galley:
      far = control.hitBy(eye, way)
      if far is not None and far < nearest:
        best, nearest = control, far
    return best

  def figureOf(self, ) -> tuple:
    """The 'figureOf' method returns how his figure sits (or, out of his
    chair, stands, walks or floats): each of the skin's parts (by its
    index in 'PARTS'), its pivot's place and its turn (w x y z), the
    vessel's own axes."""
    from worQt.gaming.sandbox._skin import PARTS
    if not self.crewman.buckled:
      return self.crewman.figureOf(self.yaw, PARTS)
    out = []
    for index, part in enumerate(PARTS):
      pivot = part[2]
      place = tuple(f + SCALE * p for f, p in zip(FIGURE, pivot))
      out.append((index, place, aboutAxis((0.0, 1.0, 0.0), LIMBS.get(
        part[0], 0.0))))
    return tuple(out)


def inWindow(way: tuple, start: tuple) -> bool:
  """Returns whether the ray from 'start' along 'way' (the vessel's own
  axes) leaves the capsule through a window."""
  low, high = 0.0, 3.0
  for _ in range(60):
    middle = 0.5 * (low + high)
    point = tuple(s + middle * w for s, w in zip(start, way))
    if math.hypot(point[0], point[1]) < capsuleRadius(point[2]) - WALL:
      low = middle
    else:
      high = middle
  point = tuple(s + high * w for s, w in zip(start, way))
  angle = math.degrees(math.atan2(point[1], point[0]))
  return any(a0 <= angle <= a1 and z0 <= point[2] <= z1
             for (a0, a1), (z0, z1) in WINDOWS)
