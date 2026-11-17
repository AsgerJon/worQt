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
#  The dashboard (user, 2026-11-17: "have the dashboard curve maybe?";
#  "When setting in the pilot seat every control should be within reach
#  of Asger"): its face a strip of a cone round the middle between his
#  shoulders ('PANEL_AXIS': x, y), 'PANEL_RADIUS' m out from it along
#  its middle line 'PANEL_HIGH' m over the floor, tilted back
#  'PANEL_TILT' deg to face his eyes, from 'PANEL_SPAN' rad round on his
#  left to as far on his right; up its slant from 'FACE_LOW' to
#  'FACE_HIGH' m off its middle line; its body 'PANEL_DEEP' m deep behind
#  its face; the rosewood border printed round its face, m. A place on
#  it is 'right' m along its middle line from its middle (his right),
#  'up' its slant, 'out' toward him ('panelPoint'; 'panelAxes': right,
#  up and out there).
PANEL_AXIS = seated(-0.25, 0.0, 0.0)[:2]
PANEL_RADIUS = 0.6
PANEL_HIGH = 0.93 + LIFT
PANEL_TILT = 31.0
PANEL_SPAN = math.radians(70.0)
FACE_LOW, FACE_HIGH = -0.27, 0.17
PANEL_DEEP = 0.12
FRAME = 0.012
_TILT = math.radians(PANEL_TILT)
#  The hood over its middle (user, 2026-11-17: "Move the indicator dials
#  above the dashboard"): a strip of a steeper cone standing on the
#  face's top edge, 'HOOD_SPAN' rad round either way, tilted back
#  'HOOD_TILT' rad, 'HOOD_HIGH' m up its slant, 'HOOD_DEEP' m deep; a
#  place on it is 'right' m along its middle line, 'up' its slant from
#  its foot, 'out' ('hoodPoint', 'hoodAxes').
HOOD_SPAN = math.radians(30.0)
HOOD_TILT = math.radians(10.0)
HOOD_HIGH = 0.17
HOOD_DEEP = 0.06
HOOD_FOOT = PANEL_RADIUS + FACE_HIGH * math.sin(_TILT)
HOOD_RADIUS = HOOD_FOOT + 0.5 * HOOD_HIGH * math.sin(HOOD_TILT)


def _conePoint(foot: float, low: float, tilt: float, theta: float,
               up: float, out: float) -> tuple:
  """Returns the point on a cone round 'PANEL_AXIS' ('foot' m out from
  it at 'low' m over the floor, tilted back 'tilt' rad) at 'theta' rad
  round (toward his left), 'up' its slant and 'out' toward him."""
  radius = foot + up * math.sin(tilt) - out * math.cos(tilt)
  return (PANEL_AXIS[0] + radius * math.cos(theta),
          PANEL_AXIS[1] + radius * math.sin(theta),
          FLOOR + low + up * math.cos(tilt) + out * math.sin(tilt))


def _coneAxes(tilt: float, theta: float) -> tuple:
  """Returns a cone's axes at 'theta' rad round: right (his), up its
  slant, out toward him."""
  c, s = math.cos(theta), math.sin(theta)
  return ((s, -c, 0.0), (math.sin(tilt) * c, math.sin(tilt) * s,
                         math.cos(tilt)),
          (-math.cos(tilt) * c, -math.cos(tilt) * s, math.sin(tilt)))


def panelPoint(right: float, up: float, out: float) -> tuple:
  """Returns the point 'right' m along the panel's middle line from its
  middle (his right), 'up' m up its slant, 'out' m toward him, the
  vessel's own axes."""
  return _conePoint(PANEL_RADIUS, PANEL_HIGH, _TILT, -right / PANEL_RADIUS,
                    up, out)


def panelAxes(right: float) -> tuple:
  """Returns the panel's axes 'right' m along its middle line: right,
  up its slant, out toward him."""
  return _coneAxes(_TILT, -right / PANEL_RADIUS)


def panelWide(up: float) -> float:
  """Returns how much wider the panel is 'up' m up its slant than along
  its middle line (a metre along it there is this many true)."""
  return (PANEL_RADIUS + up * math.sin(_TILT)) / PANEL_RADIUS


def hoodPoint(right: float, up: float, out: float) -> tuple:
  """Returns the point 'right' m along the hood's middle line, 'up' m
  up its slant from its foot, 'out' m toward him."""
  return _conePoint(HOOD_FOOT, PANEL_HIGH + FACE_HIGH * math.cos(_TILT),
                    HOOD_TILT, -right / HOOD_RADIUS, up, out)


def hoodAxes(right: float) -> tuple:
  """Returns the hood's axes 'right' m along its middle line."""
  return _coneAxes(HOOD_TILT, -right / HOOD_RADIUS)


PANEL_MIDDLE = panelPoint(0.0, 0.0, 0.0)
PANEL_AXES = panelAxes(0.0)
#  The panel's sections, each framed and titled on its face (left to
#  right: TIME, the AUTOPILOT with all that flies by itself (user,
#  2026-11-17: "All the auto stuff has to be in one place"; its three
#  modes: "Orbit, Rendezvous and Docking"), the teleprinter unframed, the
#  ASSISTS (the attitude's: "The auto pilot has four functions: hold,
#  pro, retro and aim. These should be moved to a separate group on the
#  other side of the teleprinter, where they are called 'ASSISTS'"), the
#  THRUST with the LAUNCH key and its checklist, the MANUAL DOCKING):
#  title, left, bottom, right, top (right, up on the panel, m).
SECTIONS = (('TIME', -0.721, -0.255, -0.535, 0.155),
            ('AUTOPILOT', -0.523, -0.255, -0.193, 0.155),
            ('ASSISTS', 0.193, -0.255, 0.283, 0.155),
            ('THRUST', 0.293, -0.255, 0.503, 0.155),
            ('MANUAL DOCKING', 0.513, -0.255, 0.721, 0.155))
#  Its outputs on the hood: the dials (each its name and middle (right,
#  up on the hood); their radius), each needle a lever on its turning
#  shaft ("the needle should be modelled as an actually moving lever on
#  a rotating actuator"), the altimeter's pink mark at the guidance's
#  target; the lamps (name, middle; radius); Terra Prime's range in
#  glowing number tubes (user, 2026-11-17: "When I got to orbit it
#  wasn't at all clear how near I was to Terra Prime": its middle and
#  half its size). On the panel: the AUTOPILOT's lit status line (its
#  middle and half its size); the closed circuit monitor ("make it more
#  1970 B&O just smaller") under nothing now, in the MANUAL DOCKING
#  (its screen's middle, half its size (4:3), how far its housing
#  stands out); the horizon's globe under the teleprinter (user,
#  2026-11-17: "put the globe horizon thing under the printer"): its
#  ball's middle on the panel and how far before its face, its radius,
#  its glass dome's. The THRUST's dial is on the panel (user, 2026-11-17:
#  "Also on the thrust panel, have an indicator on the currently applied
#  g": 'PANEL_DIALS'), the rest on the hood.
DIALS = (('SPEED', (-0.30, 0.088)), ('HEIGHT', (-0.195, 0.088)),
         ('APOAPSIS', (0.195, 0.088)), ('PERIAPSIS', (0.30, 0.088)),
         ('THRUST', (0.36, 0.085)))
PANEL_DIALS = ('THRUST',)
DIAL_RADIUS = 0.04
LAMPS = (('ENGINE', (-0.12, 0.143)), ('AIR', (-0.08, 0.143)),
         ('GROUND', (-0.04, 0.143)), ('WARP', (0.0, 0.143)),
         ('GUIDE', (0.04, 0.143)), ('ORBIT', (0.08, 0.143)),
         ('DOCK', (0.12, 0.143)))
LAMP_RADIUS = 0.008
RANGE = ((0.0, 0.068), (0.135, 0.033))
STATUS = ((-0.41, 0.108), (0.1, 0.02))
SCREEN_AT, SCREEN_HALF, MONITOR_OUT = (0.617, 0.048), (0.072, 0.054), 0.03
#  The docking port's numbers under the CCTV (user, 2026-11-17: "The
#  CCTV must be bigger and not cluttered with text. The port indicator
#  and all that should be below it by the other manual docking
#  controls"): its window's middle and half its size.
PORT = ((0.617, -0.043), (0.09, 0.015))
GLOBE_ON, BALL_OUT = (0.0, -0.15), 0.03
BALL_RADIUS = 0.08
GLASS = BALL_RADIUS + 0.02
#  Its inputs: the keys (name, key, action, middle (right, up on the
#  panel), half their size; their travel in): the AUTOPILOT's modes, lit
#  the one chosen (user, 2026-11-17: "we should have the three modes"),
#  ENGAGE lit while it has the controls ("an indicator of the auto pilot
#  being allowed to have control"), WARP TO ACTION beside its display
#  (grey until it waits for a burn, then lit and glinting as the warp
#  knob: "When the autopilot begins waiting for a new burn, this button
#  activates with the same enchanted glint as the general warp dial");
#  the ASSISTS lit while they hold; LAUNCH under a guard ("independently
#  of the auto pilot we need a launch button"), in once the engine is
#  lit; REAL WARP right by the warp knob ("it should be right near the
#  enchanted warp control and say 'REAL WARP'"); the knobs (name, key,
#  action, middle, notches, first notch's turn, a notch's turn: rad
#  about the panel's out, clockwise as he sees it going on; their
#  radius), each under a guard flipped up while it is worked ("it should
#  have a safety gaurd that is lifted up when adjusted"): half its size,
#  how far it flips up (rad), how long it stays up after, s; LAUNCH's
#  guard's half size. The throttle a push-pull knob as a Cessna 172's
#  ("let it be a control that is pulled out when off and in when full"):
#  its shaft's foot on the panel (right, up), how far it pulls out, m, its
#  knob's radius. The docking (the try-hard's: "we include buttons so
#  that a try-hard *could* manually do the thing"): the thrusters' keys
#  (arrows; PgUp, PgDn), MATCH, the monitor's feed (CAM: aft or the
#  nose's docking camera), UNDOCK.
MODE_HALF = (0.03, 0.015)
AUTO_HALF = (0.042, 0.02)
THRUSTER_HALF = (0.016, 0.012)
ROW_HALF = (0.026, 0.014)
KEYS = (('REAL WARP', '/', 'stop', (-0.585, 0.03), (0.03, 0.018)),
        ('TO AP', 'G', 'toAp', (-0.585, -0.065), (0.03, 0.014)),
        ('WARP TO ACTION', 'Enter', 'action', (-0.25, 0.108),
         (0.045, 0.022)),
        ('ORBIT', 'J', 'ap orbit', (-0.462, 0.025), AUTO_HALF),
        ('RNDZ', 'H', 'ap rendezvous', (-0.358, 0.025), AUTO_HALF),
        ('DOCK', 'N', 'ap dock', (-0.254, 0.025), AUTO_HALF),
        ('ENGAGE', 'C', 'engage', (-0.3, -0.135), (0.075, 0.03)),
        ('HOLD', 'T', 'hold', (0.238, 0.095), MODE_HALF),
        ('PRO', 'F', 'prograde', (0.238, 0.04), MODE_HALF),
        ('RETRO', 'R', 'retrograde', (0.238, -0.015), MODE_HALF),
        ('AIM', 'W', 'aim', (0.238, -0.07), MODE_HALF),
        ('FULL', 'Z', 'full', (0.455, 0.105), (0.025, 0.014)),
        ('CUT', 'X', 'cut', (0.455, 0.058), (0.025, 0.014)),
        ('LAUNCH', 'Space', 'launch', (0.455, -0.18), (0.03, 0.03)),
        ('UP', '\u2191', 'rcs up', (0.565, -0.094), THRUSTER_HALF),
        ('DOWN', '\u2193', 'rcs down', (0.565, -0.17), THRUSTER_HALF),
        ('LEFT', '\u2190', 'rcs left', (0.527, -0.132), THRUSTER_HALF),
        ('RIGHT', '\u2192', 'rcs right', (0.603, -0.132), THRUSTER_HALF),
        ('FWD', 'PgUp', 'rcs ahead', (0.67, -0.105), (0.022, 0.014)),
        ('BACK', 'PgDn', 'rcs back', (0.67, -0.16), (0.022, 0.014)),
        ('MATCH', 'L', 'match', (0.555, -0.222), ROW_HALF),
        ('CAM', 'K', 'camera', (0.617, -0.222), ROW_HALF),
        ('UNDOCK', 'Del', 'undock', (0.679, -0.222), ROW_HALF))
#  The keys lit while what they work is on (amber letters on smoked
#  glass), and what each key's cap reads where it is not its name.
LIT_KEYS = ('ORBIT', 'RNDZ', 'DOCK', 'ENGAGE', 'WARP TO ACTION', 'HOLD',
            'PRO', 'RETRO', 'AIM', 'MATCH')
CAPS = {'REAL WARP': 'REAL\nWARP', 'WARP TO ACTION': 'WARP TO\nACTION'}
KEY_TRAVEL = 0.006
KNOBS = (('WARP', '. ,', 'warp', (-0.665, -0.03), 8, math.radians(105),
          -math.radians(30)),
         ('LIMIT', 'Y U', 'limit', (0.455, -0.03), 8, math.radians(105),
          -math.radians(30)),
         ('ORBIT KM', '[ ]', 'orbit', (-0.46, -0.135), len(TARGETS),
          math.radians(150), -math.radians(30)))
KNOB_RADIUS = 0.022
THROTTLE_AT, THROTTLE_TRAVEL, THROTTLE_KNOB = (0.36, -0.03), 0.08, 0.018
#  The LAUNCH key's checklist beside it (user, 2026-11-17: "the relevant
#  items from teh quests take diegetic shape in the form of a check list
#  next it that includes the first 8 items"; '_quest.CHECKLIST'): its
#  first line's lamp's middle (right, up), a line's height down, its
#  lamps' radius.
CHECK_AT, CHECK_LINE, CHECK_RADIUS = (0.305, -0.115), 0.0172, 0.0042
#  The docking thrusters' keys' ways, the rocket's own axes (the nose
#  camera looks along its z, its picture's up its x: up, down, left,
#  right as it shows them; ahead and back along the nose).
THRUSTS = {'rcs up': (1.0, 0.0, 0.0), 'rcs down': (-1.0, 0.0, 0.0),
           'rcs left': (0.0, -1.0, 0.0), 'rcs right': (0.0, 1.0, 0.0),
           'rcs ahead': (0.0, 0.0, 1.0), 'rcs back': (0.0, 0.0, -1.0)}
LIMITS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
GUARD_KNOB = (KNOB_RADIUS + 0.006, KNOB_RADIUS + 0.006, 0.02)
GUARD_SWITCH = (0.017, 0.025, 0.022)
GUARD_LAUNCH = (0.036, 0.036, 0.016)
GUARD_OPEN = math.radians(105.0)
GUARD_HOLD = 1.2
#  The console switches (the view's and the map's, on his left): their
#  bat's length; off down, on up (rad about the console's right), each
#  with a lit legend beside it (half its size).
BAT_LONG = 0.03
BAT_OFF, BAT_ON = 0.5, -0.5
LEGEND_HALF = (0.026, 0.009)
#  The consoles either side of his chair at his armrests (middle, half
#  sizes; their aluminium plates on top, faces at 'TOP'), facing up,
#  aluminium on rosewood, back beside his hips where the panel's wings
#  leave them in sight: on his right the tape deck's keys (user,
#  2026-11-17: "every control should be within reach of Asger": the
#  deck behind him keeps its own too), on his left back to the pad, the
#  view's and the map's switches. The panel's wings rest on them, a
#  rosewood riser each ('RISER': its middle ahead of the console's and
#  in from it, half its size across).
TOP = FLOOR + 0.54 + LIFT
RIGHT_CONSOLE = (seated(-0.12, -0.52, 0.5 * (TOP - FLOOR) - 0.002),
                 (0.2, 0.12, 0.5 * (TOP - FLOOR) - 0.002))
LEFT_CONSOLE = (seated(-0.12, 0.52, 0.5 * (TOP - FLOOR) - 0.002),
                (0.2, 0.12, 0.5 * (TOP - FLOOR) - 0.002))
RISER = ((0.06, 0.07), (0.03, 0.03))
CONSOLE_KEYS = (('PLAY', 'P', 'play', seated(-0.28, -0.47, 0.0)[:2]),
                ('STOP', 'O', 'halt', seated(-0.21, -0.47, 0.0)[:2]),
                ('EJECT', 'I', 'eject', seated(-0.14, -0.47, 0.0)[:2]),
                ('PAD', '\u232b', 'pad', seated(-0.16, 0.47, 0.0)[:2]))
CONSOLE_SWITCHES = (('VIEW', 'V', 'view', seated(-0.16, 0.58, 0.0)[:2]),
                    ('MAP', 'M', 'map', seated(-0.26, 0.58, 0.0)[:2]))
CONSOLE_KEY_HALF = (0.03, 0.03)
#  The teleprinter in the panel's middle (user, 2026-11-17: "the
#  teleprinter should be larger"): its paper's middle (right, up) and
#  its size: 77 a line at a Teletype's pitch made 1.6 times larger
#  ('_teleprinter.PITCH').
PAPER_AT = (0.0, 0.065)
PAPER_WIDE, PAPER_HIGH = 1.6 * 8.5 * 0.0254, 0.18
#  The sideboard behind him on his right, the tape deck on it facing
#  forward (toward his chair's back) and its keys before it (user,
#  2026-11-16: "The tape controls should be over by the actual tape
#  deck"; 2026-11-17: "move the stereo to behind Asger to the right. This
#  allows a path for Asger to get up and take a walk": at his right, by
#  the globe, it closed his way out): its middle and half sizes (its long
#  side across the cabin); the deck's keys (name, key, action, place on
#  its top: left to right as one faces it).
SIDEBOARD = (seated(-1.4, -1.0, 0.5 * (TOP - FLOOR)),
             (0.2, 0.32, 0.5 * (TOP - FLOOR)))
DECK_KEYS = (('PLAY', 'P', 'play', seated(-1.265, -1.07, 0.0)[:2]),
             ('STOP', 'O', 'halt', seated(-1.265, -1.0, 0.0)[:2]),
             ('EJECT', 'I', 'eject', seated(-1.265, -0.93, 0.0)[:2]))
#  The horizon's globe (user, 2026-11-16: "like a globe"; 2026-11-17:
#  "put the globe horizon thing under the printer"): set in the panel
#  under the teleprinter, its ball's middle and its axes (the panel's
#  there: right, up, out toward him).
GLOBE_AT = panelPoint(GLOBE_ON[0], GLOBE_ON[1], BALL_OUT)
GLOBE_AXES = panelAxes(GLOBE_ON[0])
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
#  much of its size, where its origin is (on the sideboard behind him on
#  his right) and its frame's axes in the vessel's (it faces forward,
#  toward his chair: its x his left, its y up, its z ahead).
TAPE_MODEL = 'Stereo Reel to Reel Tape Deck.glb'
TAPE_SCALE = 0.6
TAPE_ORIGIN = (SIDEBOARD[0][0] - 0.05, SIDEBOARD[0][1], TOP + 0.014)
TAPE_AXES = ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
#  A ray from his eyes looks this far at most, m. The Grav-Gun reaches
#  a magic bolt this far, m (the space station's hub is 120 m long: its
#  bolts are some 30 m apart), pointed at within 'AIM' rad (or its ring
#  seen from there, 'BOLT_SEEN' m round).
REACH = 1.6
GUN_REACH = 40.0
#  The gun sees a bolt if the way to it runs through the rooms, looked at
#  every 'SIGHT_STEP' m, up to 'SIGHT_SHORT' m before the bolt, m.
SIGHT_STEP = 0.15
SIGHT_SHORT = 0.2
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


def _inSight(eye: tuple, off: tuple, far: float, open_: object) -> bool:
  """Returns whether the way from 'eye' along 'off' ('far' m long) to a
  bolt runs through the rooms ('open_'), up to 'SIGHT_SHORT' m before
  it (the bolt is on a wall)."""
  count = int((far - SIGHT_SHORT) // SIGHT_STEP)
  for k in range(1, count + 1):
    share = k * SIGHT_STEP / far
    if not open_(tuple(e + share * o for e, o in zip(eye, off))):
      return False
  return True


def inCabin(point: tuple) -> bool:
  """Returns whether 'point' is inside the cabin's walls."""
  x, y, z = point
  return FLOOR < z < NOSE and math.hypot(x, y) < capsuleRadius(z) - WALL


def _negative(axis: tuple) -> tuple:
  """Returns 'axis' the other way."""
  return tuple(-x for x in axis)


#  The pork scratchings under the dashboard by his right knee, in reach
#  of his chair (user, 2026-11-17: "Asger needs to be able to grab some
#  snacks whilst sitting in his chair"): the bag on its tray (middle,
#  axes, half sizes), under the panel's lower edge, over his right shin.
SNACK_BAG = (seated(0.13, -0.19, 0.81), ((0.0, -1.0, 0.0),
                                         (0.0, 0.0, 1.0),
                                         (-1.0, 0.0, 0.0)),
             (0.07, 0.09, 0.035))
#  What is worked from outside the cabin (the door's key on the walkway;
#  the rest from inside it).
OUTSIDE = ('door outside',)
#  What the door's keys do, as said before they are worked (the window
#  says it as it is: open or closed, locked or not).
KEY_PROMPTS = {'door': 'Open or close the door', 'lock': 'Lock the door',
               'walkway': 'Dismiss the walkway'}


def _household() -> tuple:
  """Returns what he may work away from the dashboard (looked at within
  reach, a click): the rations' crate (he eats one), the daybed
  (he sleeps till morning, if it is night), the sofa (he sits on it),
  the pork scratchings under the dashboard (in reach of his chair),
  the door's keys (outside on the walkway: the door; inside by it: the
  door, its lock, the walkway), the warning placard (a closer look)."""
  from ._furnishings import bedBox, rationCrate, sofaBox
  from ._walkwaymeshes import INSIDE_KEYS, KEY_HALF, insideKey
  from ._walkwaymeshes import outsideKey, placardBox
  keys = [(name, action, KEY_PROMPTS[action], insideKey(across) + (
    KEY_HALF,)) for name, _, action, across in INSIDE_KEYS]
  out = []
  for name, action, prompt, (middle, axes, half) in [
      ('RCIR', 'eat', 'Eat a ration (RCIR)', rationCrate()),
      ('BED', 'sleep', 'Sleep till morning', bedBox()),
      ('SOFA', 'lounge', 'Chill out on the sofa', sofaBox()),
      ('SNACKS', 'snack', 'Grab some pork scratchings', SNACK_BAG),
      ('DOOR', 'door outside', KEY_PROMPTS['door'], outsideKey()),
      ('MANUAL', 'manual', 'Read the warning manual', placardBox())] + keys:
    top = tuple(m + half[2] * u for m, u in zip(middle, axes[2]))
    peep = Pushbutton(name, None, top, (0.0, 0.0, -1.0), 0.01,
                      (prompt,) * 2)
    out.append(Control(name, 'Click', action, middle, axes, half, peep))
  return tuple(out)


#  What the panel's keys say they do, by their actions (the rest:
#  'Press' and their name).
PROMPTS = {'stop': 'Real time: stop the warp',
           'toAp': 'Warp to the apoapsis', 'hold': 'Hold the attitude',
           'prograde': 'Point prograde', 'retrograde': 'Point retrograde',
           'aim': 'Fly the aim', 'ap orbit': 'Autopilot mode: up to orbit',
           'ap rendezvous': 'Autopilot mode: rendezvous with Terra Prime',
           'ap dock': 'Autopilot mode: dock with Terra Prime',
           'engage': 'Engage the autopilot (or let go)',
           'action': 'Warp to the autopilot\'s next burn',
           'launch': 'LAUNCH', 'full': 'Full thrust',
           'cut': 'Cut the engine',
           'rcs up': 'Thrust up', 'rcs down': 'Thrust down',
           'rcs left': 'Thrust left', 'rcs right': 'Thrust right',
           'rcs ahead': 'Thrust ahead', 'rcs back': 'Thrust back',
           'match': 'Match Terra Prime\'s spin',
           'camera': 'Switch the monitor\'s camera',
           'undock': 'Undock', 'play': 'Play the tape',
           'halt': 'Stop the tape', 'eject': 'Rewind the tape',
           'pad': 'Back to the pad'}


def _controls() -> tuple:
  """Returns the dashboard's inputs, each a 'Control' with its
  FourthPeep: the panel's knobs and keys, the consoles' keys and the
  deck's (on the sideboard), the consoles' switches, the throttle's
  lever on the panel."""
  out = []
  for name, key, action, (u, v), notches, near, step in KNOBS:
    axes = panelAxes(u)
    peep = Knob(name, None, panelPoint(u, v, 0.0), axes[2], KNOB_RADIUS,
                near, step, notches)
    first = {'orbit': TARGETS.index(TARGET), 'limit': len(LIMITS) - 1}
    if action in first:
      peep.set(first[action])
      peep.value = float(peep.notch)
    out.append(Control(name, key, action, panelPoint(u, v, 0.012), axes,
                       (KNOB_RADIUS, KNOB_RADIUS, 0.012), peep))
  for name, key, action, (u, v), half in KEYS:
    axes = panelAxes(u)
    said = PROMPTS.get(action, 'Press %s' % name)
    peep = Pushbutton(name, None, panelPoint(u, v, 0.0), _negative(axes[2]),
                      KEY_TRAVEL, (said, said))
    out.append(Control(name, key, action, panelPoint(u, v, 0.008), axes,
                       half + (0.008,), peep))
  for name, key, action, (x, y) in CONSOLE_KEYS + DECK_KEYS:
    said = PROMPTS.get(action, 'Press %s' % name)
    peep = Pushbutton(name, None, (x, y, TOP), (0.0, 0.0, -1.0), KEY_TRAVEL,
                      (said, said))
    out.append(Control(name, key, action, (x, y, TOP + 0.012),
                       CONSOLE_AXES, CONSOLE_KEY_HALF + (0.012,), peep))
  for name, key, action, (x, y) in CONSOLE_SWITCHES:
    pivot = (x, y, TOP)
    peep = FourthPeep(name, None, pivot, CONSOLE_AXES[0], BAT_LONG,
                      BAT_OFF, BAT_ON, ('Switch %s' % name,) * 2)
    out.append(Control(name, key, action, (x, y, TOP + 0.015),
                       CONSOLE_AXES, (0.015, 0.02, 0.018), peep))
  u, v = THROTTLE_AT
  axes = panelAxes(u)
  peep = Slider('THROTTLE', None, panelPoint(u, v, 0.0), axes[2],
                THROTTLE_TRAVEL, ('Throttle: push in for thrust, pull out'
                                  ' to cut',) * 2)
  out.append(Control('THROTTLE', '+ \u2212', 'throttle', panelPoint(
    u, v, 0.5 * THROTTLE_TRAVEL + 0.01), axes, (THROTTLE_KNOB + 0.006,
                                                THROTTLE_KNOB + 0.006,
                                                0.5 * THROTTLE_TRAVEL
                                                + 0.025), peep))
  return tuple(out)


def dialPoint(index: int, out: float) -> tuple:
  """Returns dial 'index''s middle, 'out' m before its face (the
  panel's or the hood's: 'PANEL_DIALS')."""
  name, (u, v) = DIALS[index]
  if name in PANEL_DIALS:
    return panelPoint(u, v, out)
  return hoodPoint(u, v, out)


def dialFrame(index: int) -> tuple:
  """Returns dial 'index''s axes (right, up, out: the panel's or the
  hood's there)."""
  name, (u, _) = DIALS[index]
  return panelAxes(u) if name in PANEL_DIALS else hoodAxes(u)


def _readouts() -> tuple:
  """Returns what he may read a value off by looking at it (user,
  2026-11-17: "when reaching a dial the precise value should be shown.
  like with WAILA"): each a 'Control' with no peep and no key, its
  action 'read' and what: the dials, the lamps, Terra Prime's range, the
  AUTOPILOT's status line, the globe."""
  out = []
  for k, (name, _) in enumerate(DIALS):
    out.append(Control(name, '', 'read ' + name, dialPoint(k, 0.005),
                       dialFrame(k), (DIAL_RADIUS, DIAL_RADIUS, 0.01),
                       None))
  for name, (u, v) in LAMPS:
    out.append(Control(name, '', 'read lamp ' + name, hoodPoint(
      u, v, 0.004), hoodAxes(u), (0.015, 0.012, 0.01), None))
  (u, v), half = RANGE
  out.append(Control('RANGE', '', 'read range', hoodPoint(u, v, 0.002),
                     hoodAxes(u), half + (0.01,), None))
  (u, v), half = STATUS
  out.append(Control('STATUS', '', 'read status', panelPoint(u, v, 0.002),
                     panelAxes(u), half + (0.01,), None))
  (u, v), half = PORT
  out.append(Control('PORT', '', 'read port', panelPoint(u, v, 0.002),
                     panelAxes(u), half + (0.01,), None))
  out.append(Control('GLOBE', '', 'read globe', GLOBE_AT, GLOBE_AXES,
                     (GLASS, GLASS, GLASS), None))
  u, v = CHECK_AT
  middle = (u + 0.05, v - 3.5 * CHECK_LINE)
  out.append(Control('CHECKLIST', '', 'read checklist', panelPoint(
    middle[0], middle[1], 0.002), panelAxes(middle[0]), (
    0.06, 4.0 * CHECK_LINE + 0.01, 0.01), None))
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
  he may work away from the dashboard is the 'household' (the rations'
  crate: user, 2026-11-17: "To eat, Asger goes to the kitchen"; the
  daybed: "Asger should be able to key_E into bed"), looked at as the
  inputs are.
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
  household: tuple
  readouts: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    from ._crewman import Crewman
    self.yaw, self.pitch, self.glancing = 0.0, -0.12, None
    self.controls, self.household = _controls(), _household()
    self.readouts = _readouts()
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

  def boltAimed(self, bolts: tuple, open_: object = None) -> int | None:
    """The 'boltAimed' method returns the magic bolt (its index in
    'bolts': each its place and the way it faces) the gravity gun points
    at out of his chair: within 'GUN_REACH' of his eyes, facing him, in
    sight (user, 2026-11-17: "the gravgun should not be able to grab
    bolts through walls": 'open_' says whether a point is in the rooms,
    every 'SIGHT_STEP' m from his eyes to before the bolt; None: no
    walls), nearest to his eyes' middle within 'AIM' or its ring; None
    if none (or he sits)."""
    if self.crewman.sitting:
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
        if open_ is None or _inSight(eye, off, far, open_):
          best, least = k, angle
    return best

  def looseAimed(self, things: tuple, open_: object = None) -> int | None:
    """The 'looseAimed' method returns the loose thing (its index in
    'things': each its middle and its half sizes) the Grav-Gun points at
    out of his chair: the nearest whose round (its half sizes' length)
    his eyes' middle passes through, within 'GUN_REACH', in sight
    ('open_', as 'boltAimed'); None if none (or he sits)."""
    if self.crewman.sitting:
      return None
    eye, look = self.eye(), self.looking()[0]
    best, nearest = None, math.inf
    for k, (middle, half) in enumerate(things):
      off = tuple(m - e for m, e in zip(middle, eye))
      along = sum(o * l for o, l in zip(off, look))
      if along <= 0.0 or along > GUN_REACH:
        continue
      round_ = math.sqrt(sum(h * h for h in half))
      aside = math.sqrt(max(0.0, sum(o * o for o in off) - along * along))
      if aside <= round_ and along < nearest:
        far = math.sqrt(sum(o * o for o in off))
        if open_ is None or _inSight(eye, off, far, open_):
          best, nearest = k, along
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
    (the nearest within 'REACH'), None if none: those on the cabin's side
    of its wall his eyes are on ('OUTSIDE': the door's key on the
    walkway); what he reads a value off too ('readouts': no peep)."""
    way, eye = self.looking()[0], self.eye()
    best, nearest = None, REACH
    inside = inCabin(eye)
    for control in self.controls + self.household + self.readouts:
      if (control.action in OUTSIDE) == inside:
        continue
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
