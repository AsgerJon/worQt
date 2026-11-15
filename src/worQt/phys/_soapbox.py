"""
The soapbox (user, 2026-11-14: "Here's our first car: rolling down hill
picking up speed until it can complete a loop de loop... steering on
front wheel only. breaks on all four wheels. no drive train"; before it
"the fucking diff is what fucked us before!!"): a gravity racer on four
of the tyre rig's corners ('_rig': double wishbones in rubber, the
knuckle on two ball joints, the shock, the Soufflé wheel and its disc
brake, the tyre with its slip law), mirrored for the right side, the
front two steered by one rack from a column the driver's hands turn
('TurnPoint'), the rear two held by tie rods to the chassis (their toe
set by their length), the four calipers on one brake line (the
driver's foot: a fourth wall point), each wheel tuned as the rig's
('TuneUp': four, front left, front right, rear left, rear right); the
driver (the walker) sat in its tub, held there by its walls and by
what holds the car to the track, as the car is (slow over the loop's
top and they both fall).

Its track, planks of wood ('trackPieces', one body, part of the world):
a straight ramp down from a deck on a tower, bending into the flat, a
run up, then the loop: a teardrop as a roller
coaster's is (its curve growing as it climbs, a quarter turn, then a
half circle over the top, then easing as it falls: its pull on the
car at most about 3.5 g, a circle's would be 6), stepping aside as it
goes round ('LOOP_STEP': it comes out beside where it went in, not
onto it), so a car rolling straight follows it round (the loop is a
curve drawn along the ground swept across it: rolled out flat, a
straight line on it is the line a car rolls straight along, the
loop's own line crossing it at an angle, 'loopAngle', that the run up
meets it at), and out along a run out; all planks, lying on the ground
where it is flat, nothing of it level with the ground.

The car's frame: x forward (the front axle at nought), y left, z up
from the road under its wheels.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._assembly import Actuator, Assembly, BrakeLine, Bush, Contact
from ._assembly import DiscBrake, Fixed, FourthWall, HeldStroke, Hinge
from ._assembly import RackAndPinion, Slide, Spring, Tie, TurnPoint
from ._axle import HANDS, PINION, STRAP, _frame, columnBody
from ._axle import columnLength
from ._body import Body, State
from ._brakes import DISC_AT, DISC_INNER, DISC_OUTER, brakedWheel
from ._rig import HUB_HEIGHT, LOWER_BALL, LOWER_PIVOT_Y, LOWER_SPREAD
from ._rig import RACK_TRAVEL, SHOCK_FOOT, SHOCK_TOP, STEEL, TIE_INNER
from ._rig import TIE_OUTER, UPPER_BALL, UPPER_PIVOT_Y, UPPER_SPREAD
from ._rig import WHEEL_Y, TuneUp, WheelSetup, _about, _box, _padAt
from ._rig import armPieces, knucklePieces, tunedCorner
from ._gears import prismOf
from ._shape import Shape
from ._shock import Shock, coilOf, shockOf
from ._tyred import _WALKER_ON_RUBBER, tyreOf
from ._vectors import Vector, conjugate, cross, dot, minus, norm, plus
from ._vectors import product, rotated, scaled, turnAbout

#  The track: how wide its planks are across, how thick, m; wood; how
#  high its flat stretches stand, lying on the ground sunk a centimetre
#  into it (user, 2026-11-14: "it does the thing where the track and the
#  terrain occupy the same bits": laid 5 mm under the ground where they
#  met it, the two flickered through each other; and its planks, run 3
#  cm under each other, likewise: now edge to edge, the road all planks
#  from the deck to the run out's end, nothing of it level with the
#  ground); how far the run out runs past the loop, m.
TRACK_WIDTH, PLANK, WOOD = 2.4, 0.06, 600.0
ROAD = PLANK - 0.01
RUN_OUT = 60.0
#  The loop: the radius over its top, m (its curve grows from nought
#  over a quarter turn up to it, holds it over the half circle at the
#  top, and eases back to nought over the last quarter), how far aside
#  it comes out from where it goes in, m (its planks' width and a gap),
#  its planks' length along it, m.
LOOP_TOP, LOOP_STEP, LOOP_PLANK = 3.0, 4.2, 0.25
#  The ramp: its deck's height over the ground (the top of its slope),
#  m; its slope; the radius it bends into the flat by, m; how far the
#  flat runs from the bend's foot to the loop, m; its planks' length on
#  the slope and in the bend, m; how far apart its posts stand along
#  it, m; the deck's length behind the slope's top, m.
RAMP_TOP, RAMP_SLOPE, RAMP_BEND = 12.5, math.radians(30.0), 10.0
RUN_UP = 6.0
RAMP_PLANK, BEND_PLANK, POST_EVERY = 1.0, 0.25, 2.5
DECK = 3.0
#  The car: its wheelbase, m; the corners (where each axle is along x,
#  its side: left positive), front left, front right, rear left, rear
#  right.
WHEELBASE = 2.0
CORNERS = ((0.0, 1.0), (0.0, -1.0), (-WHEELBASE, 1.0),
           (-WHEELBASE, -1.0))
#  The steering: its rack across the front, its middle behind the axle
#  (its ends the tie rods' inner); the column from its pinion beside the
#  rack up and back to the steering wheel before the driver ('_axle':
#  'columnBody', a turn a lock), at this slope.
RACK_MIDDLE = (TIE_INNER[0], 0.0, TIE_INNER[2])
RACK_HALF = TIE_INNER[1]
COLUMN_FOOT = (TIE_INNER[0] - 0.025, 0.0, TIE_INNER[2])
COLUMN_RISE = math.radians(26.7)
COLUMN_TOP = plus(COLUMN_FOOT, scaled(
  (-math.cos(COLUMN_RISE), 0.0, math.sin(COLUMN_RISE)), columnLength()))
#  The chassis: its ends (nose, tail), its rails' height and top (its
#  floor 15 cm over the road: at 8 cm it scraped the loop, the corners'
#  9 cm of travel taken by 4 g, and stalled it short of the top), how
#  thick its side plates are, m, and its hollow parts' steel (its rails
#  a 3 mm wall on a 40 by 120 mm section, its brackets and cross members
#  boxes of 4 mm plate: about a fifth of each solid); the driver's tub
#  (its back, front and either side's inner faces, its floor's top), the
#  driver sat in it: where their ball's middle is.
NOSE, TAIL = 0.25, -WHEELBASE - 0.30
RAIL_LOW, RAIL_TOP, PLATE = 0.15, 0.27, 0.004
HOLLOW = 0.2
TUB_BACK, TUB_FRONT, TUB_SIDE, TUB_FLOOR = -1.815, -1.185, 0.305, 0.165
SEAT = (-1.5, 0.0, TUB_FLOOR + 0.302)
#  The shocks here: the rig's coil and dampers, their free lengths set
#  for the car's lighter corners so it rides as built (front, rear:
#  the driver sits nearer the rear axle).
FRONT_SHOCK = Shock(1.2e5, 0.1960, 3400.0, 7600.0)
REAR_SHOCK = Shock(1.2e5, 0.1989, 3400.0, 7600.0)
#  The brake line's pressure holding the car on the ramp until it is let
#  go, Pa; the tyres on the planks (a road's grip), the walker on them
#  and on the chassis (painted steel), the chassis on the planks
#  (scraping: its edges' points 'CHASSIS_SPACING' apart, the planks'
#  edges too many to count).
HOLD = 30e5
_TYRE_ON_PLANK = (1e5, 1.0, 1.0, 1e5, 300.0)
_WALKER_ON_WOOD = (1e6, 1.0, 0.6, 1e6, 2e3)
_STEEL_ON_WOOD = (1e6, 1.0, 0.4, 1e6, 2e3)
CHASSIS_SPACING = 0.2
#  The line keeper's hands ('LineKeeper'): how far they turn the
#  steering wheel for each metre the car is left of its line, rad, and
#  for each radian its heading is, the most either way, rad (a road
#  wheel's 7 degrees), and how fast they turn, rad/s.
LINE_GAIN, HEADING_GAIN, LINE_MOST, LINE_RATE = 1.0, 6.0, 1.8, 6.0
#  The bodies: the walker, the track, the chassis, the corners (each its
#  lower and upper wishbones, knuckle, wheel, shock's tube and rod), the
#  rack, the column.
TRACK, CHASSIS, FIRST_CORNER = 1, 2, 3
RACK, COLUMN = FIRST_CORNER + 6 * len(CORNERS), FIRST_CORNER + (
  6 * len(CORNERS)) + 1


class SoapboxControls(NamedTuple):
  """
  SoapboxControls are what the driver works: the brakes' line ('line',
  its pressure the foot's), the steering wheel ('steer': the hands on
  it, rad, left positive), the wheels' tune-up ('tune', a 'TuneUp' of
  four; None: as built).
  """

  line: BrakeLine
  steer: FourthWall
  tune: TuneUp = None


class LineKeeper:
  """
  LineKeeper is a driver's hands holding the soapbox on its line
  (rolled out flat, the loop's line is straight: 'loopAngle' to the
  loop's own; before it the run up's, after it its way out, both along
  x): it turns the steering wheel ('wall', the hands' fourth wall
  point) against how far the car's middle is to the line's left
  ('LINE_GAIN' rad a metre) and how far its heading is left of the
  line's ('HEADING_GAIN' rad a radian), never past 'LINE_MOST' either
  way, as fast as hands turn ('LINE_RATE' rad/s). Hands off, the car
  falls 0.75 m short of the line three quarters round (its wheels,
  rolling straight across the loop, follow a turn's step 4 % short at
  its top, and its warped corners slip) and off the planks' inner edge.
  Where along the loop the car is ('s', m along its line) is kept from
  step to step (its entry and its way down cross in its own plane).
  """

  __slots__ = ('wall', 's')

  def __init__(self, wall: FourthWall) -> None:
    self.wall = wall
    self.s = -1.0

  def wanted(self, chassis: State, body: Body) -> float:
    """The 'wanted' method returns the steering wheel's angle the hands
    want for the chassis ('body' as it is in 'chassis'), rad, left
    positive."""
    place, turn = loopFrame()
    back = conjugate(turn)
    middle = rotated(back, minus(chassis.place, place))
    ahead = rotated(back, rotated(chassis.turn, (1.0, 0.0, 0.0)))
    length, slope = loopLength(), math.tan(loopAngle())
    if middle[0] < 0.0 and self.s <= 0.0:
      self.s = middle[0]
    elif self.s >= length:
      self.s = length + middle[0] - loopLine()[-1][1]
    else:
      self.s = _nearestAlong(middle, self.s)
    heading = loopHeading(self.s)
    along = (math.cos(heading), 0.0, math.sin(heading))
    off = middle[1] - slope * self.s
    turned = math.atan2(ahead[1], dot(ahead, along)) - loopAngle()
    angle = -LINE_GAIN * off - HEADING_GAIN * turned
    return max(-LINE_MOST, min(LINE_MOST, angle))

  def steer(self, chassis: State, body: Body, seconds: float) -> None:
    """The 'steer' method turns the hands toward the angle they want
    ('wanted'), as fast as hands turn, over 'seconds'."""
    want = self.wanted(chassis, body)
    step = LINE_RATE * seconds
    value = self.wall.value
    self.wall.value = value + max(-step, min(step, want - value))


def _nearestAlong(point: Vector, near: float) -> float:
  """Returns how far along the loop's line (its own frame) the point of
  it nearest 'point' (in its plane: along the ground and up) is, of
  those within 2 m of 'near' along it (its entry and its way down cross
  each other)."""
  best, found = math.inf, near
  for s, x, z in loopLine():
    if abs(s - near) > 2.0:
      continue
    far = (point[0] - x) ** 2 + (point[2] - z) ** 2
    if far < best:
      best, found = far, s
  return found


def _sided(point: Vector, side: float, at: float) -> Vector:
  """Returns 'point' of the left front corner as it is at the corner
  'at' along x on 'side' (left positive: the right's mirrored)."""
  return point[0] + at, side * point[1], point[2]


def _sidedShape(shape: Shape, side: float, at: float) -> Shape:
  """Returns 'shape' (of the left front corner) at the corner 'at' on
  'side' (mirrored: its faces' order turned, outside still out)."""
  points = tuple(_sided(point, side, at) for point in shape.points)
  faces = shape.faces if side > 0.0 else tuple(
    (i, k, j) for i, j, k in shape.faces)
  return Shape(points, faces)


def _sidedPieces(pieces: tuple, side: float, at: float) -> tuple:
  """Returns 'pieces' ((key, shape), ...) at the corner 'at' on
  'side'."""
  return tuple((key, _sidedShape(shape, side, at)) for key, shape in pieces)


def _sidedTurn(turn: tuple, side: float) -> tuple:
  """Returns 'turn' (of the left side) mirrored onto 'side'."""
  if side > 0.0:
    return turn
  return turn[0], -turn[1], turn[2], -turn[3]


def _joined(shapes: tuple) -> Shape:
  """Returns 'shapes' as one."""
  shape = shapes[0]
  for piece in shapes[1:]:
    shape = shape.joined(piece)
  return shape


def _summed(parts: tuple, shape: Shape) -> Body:
  """Returns 'parts' ((shape, density), ...) as one body of 'shape':
  masses and moments summed (parallel axes)."""
  from ._axle import _summed as summed
  return summed(tuple(Body.of(piece, density) for piece, density in parts),
                shape)


def _slab(start: Vector, end: Vector, across: Vector, middles: tuple,
          half: float) -> Shape:
  """Returns a plank, its top's middle line from 'start' to 'end' moved
  'middles' m along 'across' (a unit, square to the line) at its two
  ends (a plank of a line crossing the loop's slantwise: its ends square
  to the loop's line, its sides along the car's, each plank's meeting
  the next's), 'half' m across either way, 'PLANK' thick under it (its
  top facing the line's way crossed with 'across')."""
  along = minus(end, start)
  up = cross(scaled(along, 1.0 / norm(along)), across)
  points = []
  for i in range(8):
    base = end if i & 1 else start
    middle = middles[1] if i & 1 else middles[0]
    aside = middle + (half if i & 2 else -half)
    points.append(plus(base, plus(scaled(across, aside),
                                  scaled(up, 0.0 if i & 4 else -PLANK))))
  from ._shape import boxShape
  return Shape(tuple(points), boxShape(1.0, 1.0, 1.0).faces)


def loopCurve(s: float) -> float:
  """The 'loopCurve' function returns how fast the loop's line turns
  'LOOP_TOP' along it from its foot, rad/m: growing evenly from nought
  over its first quarter turn, the top's over its half circle, falling
  evenly to nought over its last quarter."""
  top = 1.0 / LOOP_TOP
  quarter = math.pi * LOOP_TOP
  if s <= 0.0 or s >= 3.0 * quarter:
    return 0.0
  if s < quarter:
    return top * s / quarter
  if s > 2.0 * quarter:
    return top * (3.0 * quarter - s) / quarter
  return top


def loopHeading(s: float) -> float:
  """The 'loopHeading' function returns how far the loop's line has
  turned up from level 's' m along it from its foot, rad ('loopCurve'
  summed)."""
  top = 1.0 / LOOP_TOP
  quarter = math.pi * LOOP_TOP
  s = max(0.0, min(3.0 * quarter, s))
  if s < quarter:
    return 0.5 * top * s * s / quarter
  if s <= 2.0 * quarter:
    return 0.5 * math.pi + top * (s - quarter)
  left = 3.0 * quarter - s
  return 2.0 * math.pi - 0.5 * top * left * left / quarter


def loopLength() -> float:
  """The 'loopLength' function returns how long the loop's line is from
  its foot round to its foot again, m."""
  return 3.0 * math.pi * LOOP_TOP


def loopAngle() -> float:
  """The 'loopAngle' function returns the angle the car's line crosses
  the loop's at (rolled out flat: 'LOOP_STEP' aside over its length),
  rad; the run up comes in at it."""
  return math.atan2(LOOP_STEP, loopLength())


@functools.lru_cache(maxsize=1)
def loopLine() -> tuple[tuple[float, float, float], ...]:
  """The 'loopLine' function returns the loop's line, in its own frame
  (along it and up, from its foot), at its planks' ends: each (how far
  along it, m; how far along the ground, m; how high, m), from its foot
  ('ROAD' high) round to its foot again."""
  length = loopLength()
  count = max(1, round(length / LOOP_PLANK))
  out = [(0.0, 0.0, ROAD)]
  x, z, s, steps = 0.0, ROAD, 0.0, 64
  for k in range(1, count + 1):
    end = length * k / count
    ds = (end - s) / steps
    for j in range(steps):
      heading = loopHeading(s + (j + 0.5) * ds)
      x += ds * math.cos(heading)
      z += ds * math.sin(heading)
    s = end
    out.append((s, x, z))
  return tuple(out)


def loopFrame() -> tuple[Vector, tuple]:
  """The 'loopFrame' function returns where the loop's frame lies in
  the world: its foot at the world's middle (the run up's end), turned
  so the run up along x comes in at 'loopAngle' to its line, which
  steps aside toward its own y."""
  return (0.0, 0.0, 0.0), turnAbout((0.0, 0.0, 1.0), -loopAngle())


@functools.lru_cache(maxsize=1)
def rampLine() -> tuple[Vector, ...]:
  """The 'rampLine' function returns the ramp's line at its planks'
  ends, in the world (along x, up): from the slope's top down to the
  bend, round the bend into the flat ('ROAD' high), 'RUN_UP' from the
  loop."""
  bendAt = (-RUN_UP, RAMP_BEND + ROAD)
  low = (bendAt[0] - RAMP_BEND * math.sin(RAMP_SLOPE),
         bendAt[1] - RAMP_BEND * math.cos(RAMP_SLOPE))
  run = (RAMP_TOP - low[1]) / math.sin(RAMP_SLOPE)
  top = (low[0] - run * math.cos(RAMP_SLOPE), RAMP_TOP)
  count = max(1, round(run / RAMP_PLANK))
  out = [(top[0] + (low[0] - top[0]) * k / count, 0.0,
          top[1] + (low[1] - top[1]) * k / count) for k in range(count)]
  bend = max(1, round(RAMP_BEND * RAMP_SLOPE / BEND_PLANK))
  for k in range(bend + 1):
    angle = RAMP_SLOPE * (1.0 - k / bend)
    out.append((bendAt[0] - RAMP_BEND * math.sin(angle), 0.0,
                bendAt[1] - RAMP_BEND * math.cos(angle)))
  return tuple(out)


def rampTop() -> Vector:
  """The 'rampTop' function returns the slope's top, in the world (its
  line's)."""
  return rampLine()[0]


def trackPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'trackPieces' function returns the track by its parts, in the
  world, its planks edge to edge: the ramp's, the run up (one plank,
  its far end cut square to the loop's line), the loop's, the run out
  (likewise from the loop's end, along x; 'plank' and 'board' in turn,
  so they are seen to pass), the deck on the tower and the posts under
  it and under the slope ('post', sunk 5 cm into the ground)."""
  out = []
  line, half = rampLine(), 0.5 * TRACK_WIDTH
  y = (0.0, 1.0, 0.0)
  for k, (start, end) in enumerate(zip(line[:-1], line[1:])):
    out.append(('plank' if k % 2 == 0 else 'board',
                _slab(start, end, y, (0.0, 0.0), half)))
  place, turn = loopFrame()
  across = rotated(turn, y)
  slope = math.tan(loopAngle())
  wide = half / math.cos(loopAngle())
  cut = half * slope
  out.append(('board', prismOf(((-RUN_UP, -half), (-cut, -half),
                                (cut, half), (-RUN_UP, half)),
                               ROAD - PLANK, ROAD)))
  loop = loopLine()
  for k, (a, b) in enumerate(zip(loop[:-1], loop[1:])):
    start = plus(place, rotated(turn, (a[1], 0.0, a[2])))
    end = plus(place, rotated(turn, (b[1], 0.0, b[2])))
    out.append(('plank' if k % 2 == 0 else 'board',
                _slab(start, end, across, (slope * a[0], slope * b[0]),
                      wide)))
  far = loop[-1]
  right, left = (plus(place, rotated(turn, (far[1], 0.0, 0.0))),) * 2
  right = plus(right, scaled(across, slope * far[0] - wide))
  left = plus(left, scaled(across, slope * far[0] + wide))
  out.append(('plank', prismOf(((right[0], right[1]),
                                (right[0] + RUN_OUT, right[1]),
                                (left[0] + RUN_OUT, left[1]),
                                (left[0], left[1])), ROAD - PLANK, ROAD)))
  top = rampTop()
  deck = (top[0] - DECK, top[0])
  out.append(('plank', _box((deck[0], -half, RAMP_TOP - PLANK),
                            (deck[1], half, RAMP_TOP))))
  posts = [deck[0] + 0.1, deck[1] - 0.1]
  x = top[0] + POST_EVERY
  while x < line[-1][0] - 2.0:
    posts.append(x)
    x += POST_EVERY
  for x in posts:
    under = _under(x) - PLANK
    if under < 0.3:
      continue
    for side in (-1.0, 1.0):
      y0 = side * (half - 0.12)
      out.append(('post', _box((x - 0.06, y0 - 0.06, -0.05),
                               (x + 0.06, y0 + 0.06, under))))
  return tuple(out)


def _under(x: float) -> float:
  """Returns how high the ramp's line (or the deck) is over 'x', m."""
  line = rampLine()
  if x <= line[0][0]:
    return RAMP_TOP
  for a, b in zip(line[:-1], line[1:]):
    if a[0] <= x <= b[0]:
      return a[2] + (b[2] - a[2]) * (x - a[0]) / (b[0] - a[0])
  return ROAD


@functools.lru_cache(maxsize=1)
def trackBody() -> Body:
  """The 'trackBody' function returns the track, wood (part of the
  world), in the world."""
  return Body.of(_joined(tuple(shape for _, shape in trackPieces())), WOOD)


def _cornerBrackets() -> tuple[Shape, ...]:
  """Returns the chassis' brackets at the left front corner (as the
  rig's boom's): its side plate, the wishbones' brackets, the shock's
  top."""
  pieces = [_box((-0.30, 0.20 - PLATE, RAIL_LOW), (0.25, 0.20, 0.62))]
  for x in (-LOWER_SPREAD, LOWER_SPREAD):
    for side in (-1.0, 1.0):
      ear = x + side * 0.04
      pieces.append(_box((ear - 0.006, 0.20, 0.13),
                         (ear + 0.006, LOWER_PIVOT_Y + 0.02, 0.19)))
  for x in (UPPER_BALL[0] - UPPER_SPREAD, UPPER_BALL[0] + UPPER_SPREAD):
    pieces.append(_box((x - 0.05, 0.20, UPPER_BALL[2] - 0.03),
                       (x + 0.05, UPPER_PIVOT_Y - 0.04,
                        UPPER_BALL[2] + 0.03)))
    for side in (-1.0, 1.0):
      ear = x + side * 0.04
      pieces.append(_box((ear - 0.006, UPPER_PIVOT_Y - 0.04,
                          UPPER_BALL[2] - 0.03),
                         (ear + 0.006, UPPER_PIVOT_Y + 0.02,
                          UPPER_BALL[2] + 0.03)))
  pieces.append(_box((SHOCK_TOP[0] - 0.06, 0.20, SHOCK_TOP[2] + 0.02),
                     (SHOCK_TOP[0] + 0.06, SHOCK_TOP[1] + 0.03,
                      SHOCK_TOP[2] + 0.06)))
  return tuple(pieces)


def _tubWalls() -> tuple[Shape, ...]:
  """Returns the driver's tub (plywood, 25 mm): its floor, back, front
  and sides."""
  back, front, side = TUB_BACK, TUB_FRONT, TUB_SIDE
  return (_box((back - 0.025, -side - 0.025, RAIL_LOW),
               (front + 0.025, side + 0.025, TUB_FLOOR)),
          _box((back - 0.025, -side - 0.025, TUB_FLOOR), (back, side + 0.025,
                                                          0.62)),
          _box((front, -side - 0.025, TUB_FLOOR), (front + 0.025,
                                                   side + 0.025, 0.49)),
          _box((back, side, TUB_FLOOR), (front, side + 0.025, 0.52)),
          _box((back, -side - 0.025, TUB_FLOOR), (front, -side, 0.52)))


def _chassisParts() -> tuple[tuple[Shape, ...], ...]:
  """Returns the chassis' parts by what they are made of, in the car's
  frame: its hollow steel (its two rails, nose to tail, under the
  corners' side plates; cross members at the axles, the corners'
  brackets, the rear tie rods' brackets, the dash hoop the column
  passes through, the rack's housing); its plates (the corners' side
  plates); its plywood (the floor between the rails, the driver's tub,
  the nose and tail boards)."""
  steel = [_box((TAIL, side * 0.20 - 0.015, RAIL_LOW),
                (NOSE, side * 0.20 + 0.015, RAIL_TOP))
           for side in (-1.0, 1.0)]
  steel += [_box((at - 0.04, -0.185, RAIL_LOW), (at + 0.04, 0.185,
                                                RAIL_LOW + 0.06))
           for at in (0.0, -WHEELBASE)]
  hoop = COLUMN_FOOT[0] + 0.75 * (COLUMN_TOP[0] - COLUMN_FOOT[0])
  lift = COLUMN_FOOT[2] + 0.75 * (COLUMN_TOP[2] - COLUMN_FOOT[2])
  for side in (-1.0, 1.0):
    steel.append(_box((hoop - 0.02, side * 0.20 - 0.015, RAIL_TOP),
                      (hoop + 0.02, side * 0.20 + 0.015, lift + 0.04)))
  steel.append(_box((hoop - 0.02, -0.215, lift + 0.02),
                    (hoop + 0.02, 0.215, lift + 0.06)))
  steel.append(_box((RACK_MIDDLE[0] - 0.02, -0.24, RACK_MIDDLE[2] - 0.02),
                    (RACK_MIDDLE[0] + 0.02, 0.24, RACK_MIDDLE[2] + 0.02)))
  inner = TIE_INNER
  bracket = _box((inner[0] - 0.02, 0.20, inner[2] - 0.02),
                 (inner[0] + 0.02, inner[1] + 0.01, inner[2] + 0.02))
  plates = []
  for at, side in CORNERS:
    shapes = _cornerBrackets() + ((bracket,) if at != 0.0 else ())
    plates.append(_sidedShape(shapes[0], side, at))
    steel += [_sidedShape(shape, side, at) for shape in shapes[1:]]
  wood = (_box((TAIL, -0.185, RAIL_LOW), (NOSE, 0.185, RAIL_LOW + 0.015)),
          _box((NOSE - 0.02, -0.185, RAIL_LOW + 0.015),
               (NOSE, 0.185, 0.41)),
          _box((TAIL, -0.185, RAIL_LOW + 0.015),
               (TAIL + 0.02, 0.185, 0.41))) + _tubWalls()
  return tuple(steel), tuple(plates), wood


def chassisPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'chassisPieces' function returns the chassis by its parts, in
  the car's frame ('_chassisParts'): ('frame', its steel), ('wood', its
  plywood)."""
  steel, plates, wood = _chassisParts()
  return ('frame', _joined(steel + plates)), ('wood', _joined(wood))


def chassisShape() -> Shape:
  """The 'chassisShape' function returns how the chassis meets the track
  and the walker, in the car's frame: its rails before and behind the
  tub (one block each), the tub's floor and walls."""
  half = 0.215
  return _joined((_box((TUB_FRONT + 0.025, -half, RAIL_LOW),
                       (NOSE, half, RAIL_TOP)),
                  _box((TAIL, -half, RAIL_LOW),
                       (TUB_BACK - 0.025, half, RAIL_TOP)))
                 + _tubWalls())


@functools.lru_cache(maxsize=1)
def chassisBody() -> Body:
  """The 'chassisBody' function returns the chassis (about 120 kg), in
  the car's frame: its side plates solid steel, its rails, brackets and
  cross members hollow ('HOLLOW' of them steel), its plywood
  ('_chassisParts'); its shape 'chassisShape'."""
  steel, plates, wood = _chassisParts()
  return _summed(((_joined(steel), STEEL * HOLLOW),
                  (_joined(plates), STEEL), (_joined(wood), WOOD)),
                 chassisShape())


@functools.lru_cache(maxsize=8)
def cornerArm(lower: bool, side: float, at: float) -> Body:
  """The 'cornerArm' function returns a wishbone of the corner 'at' on
  'side', steel, in the car's frame."""
  return Body.of(_joined(tuple(shape for _, shape in _sidedPieces(
    armPieces(lower), side, at))), STEEL)


@functools.lru_cache(maxsize=4)
def cornerKnuckle(side: float, at: float) -> Body:
  """The 'cornerKnuckle' function returns the knuckle of the corner 'at'
  on 'side', steel, in the car's frame."""
  return Body.of(_joined(tuple(shape for _, shape in _sidedPieces(
    knucklePieces(), side, at))), STEEL)


def rackShape() -> Shape:
  """The 'rackShape' function returns the steering's rack, a steel bar
  22 mm square across the car, in the car's frame."""
  return _box(minus(RACK_MIDDLE, (0.011, RACK_HALF, 0.011)),
              plus(RACK_MIDDLE, (0.011, RACK_HALF, 0.011)))


@functools.lru_cache(maxsize=1)
def rackBody() -> Body:
  """The 'rackBody' function returns the rack, steel, in the car's
  frame."""
  return Body.of(rackShape(), STEEL)


def columnTurn() -> tuple:
  """The 'columnTurn' function returns how the column lies in the car's
  frame: its own z up it toward the driver, its own y the steering
  wheel's top, its own x the driver's right."""
  way = minus(COLUMN_TOP, COLUMN_FOOT)
  way = scaled(way, 1.0 / norm(way))
  return _frame((0.0, -1.0, 0.0), (way[2], 0.0, -way[0]), way)


def startPlace() -> tuple[Vector, tuple]:
  """The 'startPlace' function returns where the car's frame stands at
  the start, in the world: its front axle's road 'WHEELBASE' and a half
  metre down the slope from its top, pitched down the slope."""
  top = rampTop()
  down = WHEELBASE + 0.5
  place = (top[0] + down * math.cos(RAMP_SLOPE), 0.0,
           top[2] - down * math.sin(RAMP_SLOPE))
  return place, turnAbout((0.0, 1.0, 0.0), RAMP_SLOPE)


def addCorners(corners: tuple, setups: tuple, shocks: tuple, chassis: int,
               first: int, rack: int, line: object, track: int | None,
               world: object, state: object, carTurn: tuple, bodies: list,
               states: list, connections: list) -> None:
  """The 'addCorners' function adds a car's corners (the tyre rig's,
  'corners' each (where its axle is along x, its side: left positive;
  the right mirrored), each set up as 'setups' says ('tunedCorner'))
  to 'bodies', 'states' and 'connections': each its lower and upper
  wishbones (bushed to the chassis, body 'chassis'), knuckle, wheel and
  shock's tube and rod (six bodies a corner from 'first'), the front
  ones' tie rods from the rack (body 'rack'), the rear ones' from the
  chassis, every brake on 'line' (or, a tuple, each corner's on its own:
  an anti-lock system's), every tyre on body 'track' (None: the
  ground alone), the shocks' makes 'shocks' (front, rear); 'world' and
  'state' put the car's frame's points and bodies in the world (its
  turn 'carTurn')."""
  x, axis = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
  lines = line if isinstance(line, tuple) else (line,) * len(corners)
  for c, ((at, side), setup) in enumerate(zip(corners, setups)):
    lower, upper, knuckle, wheel, tube = (first + 6 * c + k
                                          for k in range(5))
    turn, shim, swing, rod = tunedCorner(setup)
    turn, swing = _sidedTurn(turn, side), _sidedTurn(swing, side)
    across = (0.0, side * shim, 0.0)
    ball = _sided(LOWER_BALL, side, at)
    pivots = _sided((UPPER_BALL[0], UPPER_PIVOT_Y + shim, UPPER_BALL[2]),
                    side, at)
    arms = cornerArm(True, side, at), cornerArm(False, side, at)
    hub = cornerKnuckle(side, at)
    bodies += [arms[0], arms[1], hub, brakedWheel()]
    states.append(state(arms[0].centre))
    states.append(state(_about(plus(arms[1].centre, across), pivots,
                               swing), swing))
    states.append(state(_about(hub.centre, ball, turn), turn))
    upright = product(turn, _sidedTurn(turnAbout(x, -0.5 * math.pi), side))
    middle = _sided((0.0, WHEEL_Y, HUB_HEIGHT), side, at)
    states.append(State(plus(world(_about(middle, ball, turn)), rotated(
      product(carTurn, upright), brakedWheel().centre)),
                        product(carTurn, upright)))
    for armAt, (low, y, x0, spread) in enumerate((
        (LOWER_BALL, LOWER_PIVOT_Y, 0.0, LOWER_SPREAD),
        (UPPER_BALL, UPPER_PIVOT_Y, UPPER_BALL[0], UPPER_SPREAD))):
      for way in (-1.0, 1.0):
        pivot = _sided((x0 + way * spread, y, low[2]), side, at)
        onChassis = plus(pivot, across) if armAt == 1 else pivot
        connections.append(Hinge(chassis, onChassis, x, lower + armAt,
                                 pivot, x, Bush()))
      joint = _sided(low, side, at)
      connections.append(Tie(lower + armAt, joint, knuckle, joint))
    inner = rack if at == 0.0 else chassis
    connections.append(Actuator(inner, _sided(TIE_INNER, side, at),
                                knuckle, _sided(TIE_OUTER, side, at),
                                HeldStroke(rod)))
    for w in (0.02, 0.07):
      connections.append(Tie(knuckle, plus(middle, (0.0, side * w, 0.0)),
                             wheel, (0.0, 0.0, w)))
    connections.append(DiscBrake(wheel, knuckle, (0.0, 0.0, DISC_AT), axis,
                                 _sided(_padAt(), side, at), DISC_INNER,
                                 DISC_OUTER, lines[c]))
    connections.append(tyreOf(wheel, setup.pressure))
    if track is not None:
      connections.append(Contact(wheel, track, *_TYRE_ON_PLANK))
    top, foot = _sided(SHOCK_TOP, side, at), _sided(SHOCK_FOOT, side, at)
    shocked, shockStates, parts = shockOf(
      shocks[0] if at == 0.0 else shocks[1], chassis, top, lower, foot,
      tube, world(top), world(foot))
    bodies += list(shocked)
    states += list(shockStates)
    connections += list(parts)


def columnTopOf(length: float, rise: float) -> Vector:
  """The 'columnTopOf' function returns where the steering wheel's
  middle is, in the car's frame, its column 'length' m from its pinion
  ('COLUMN_FOOT') up and back at 'rise' rad (the soapbox's)."""
  return plus(COLUMN_FOOT, scaled((-math.cos(rise), 0.0, math.sin(rise)),
                                  length))


def addSteering(chassis: int, rack: int, column: int, steer: object,
                foot: Vector, top: Vector, world: object, state: object,
                carTurn: tuple, bodies: list, states: list,
                connections: list) -> None:
  """The 'addSteering' function adds a car's steering to 'bodies',
  'states' and 'connections': the rack (body 'rack') sliding across the
  chassis (body 'chassis') between its stops, the column and steering
  wheel (body 'column', straight from its pinion's middle 'foot' on the
  rack to the wheel's middle 'top', in the car's frame) turning on it
  (its own x the driver's right, level), the pinion meshing the rack,
  the hands on the wheel ('steer', a fourth wall point)."""
  axis = (0.0, 0.0, 1.0)
  length = norm(minus(top, foot))
  way = scaled(minus(top, foot), 1.0 / length)
  right = plus((0.0, -1.0, 0.0), scaled(way, way[1]))
  right = scaled(right, 1.0 / norm(right))
  wheel, bar = columnBody(length), rackBody()
  lean = _frame(right, cross(way, right), way)
  bodies += [bar, wheel]
  states += [state(bar.centre), State(plus(world(top), rotated(
    product(carTurn, lean), wheel.centre)), product(carTurn, lean))]
  connections += [
    Slide(chassis, RACK_MIDDLE, (0.0, 1.0, 0.0), rack, RACK_MIDDLE,
          (0.0, 1.0, 0.0)),
    Spring(chassis, RACK_MIDDLE, rack, RACK_MIDDLE, STRAP, RACK_TRAVEL,
           2000.0, True, False),
    Hinge(chassis, top, rotated(lean, axis), column,
          (0.0, 0.0, 0.0), axis),
    RackAndPinion(column, axis, rack, (0.0, -1.0, 0.0), chassis, PINION),
    TurnPoint(column, chassis, axis, steer, *HANDS)]


def soapbox(controls: SoapboxControls, start: tuple = None,
            track: Body = None) -> tuple[Assembly, tuple[State, ...]]:
  """The 'soapbox' function returns the soapbox worked by 'controls' on
  its track: the walker (body 0) sat in its tub, the track (1, part of
  the world), the chassis (2), each corner's lower and upper wishbones,
  knuckle, wheel and shock's tube and rod (3 on, six a corner, in
  'CORNERS' order), the rack ('RACK') and the column and steering wheel
  ('COLUMN'), all as built (and as its tune-up sets each corner:
  'tunedCorner', mirrored on the right), still, straight ahead, where
  'start' puts the car's frame (its place and turn; None: on the
  ramp, 'startPlace'), on 'track' (in the world, as the track is; None:
  'trackBody')."""
  from ._scenes import WALKER
  carAt, carTurn = startPlace() if start is None else start

  def world(point: Vector) -> Vector:
    """Returns 'point' of the car's frame in the world."""
    return plus(carAt, rotated(carTurn, point))

  def state(centre: Vector, turn: tuple = (1.0, 0.0, 0.0, 0.0)) -> State:
    """Returns the state of a body whose centre is at 'centre' in the
    car's frame, turned 'turn' from it."""
    return State(world(centre), product(carTurn, turn))

  setups = (WheelSetup(),) * len(CORNERS) if controls.tune is None else (
    tuple(controls.tune.wheels))
  track = trackBody() if track is None else track
  chassis = chassisBody()
  bodies = [WALKER.body(), track, chassis]
  states = [State(world(SEAT)), State(track.centre), state(chassis.centre)]
  connections = [Fixed(TRACK)]
  addCorners(CORNERS, setups, (FRONT_SHOCK, REAR_SHOCK), CHASSIS,
             FIRST_CORNER, RACK, controls.line, TRACK, world, state, carTurn,
             bodies, states, connections)
  addSteering(CHASSIS, RACK, COLUMN, controls.steer, COLUMN_FOOT,
              columnTopOf(columnLength(), COLUMN_RISE), world, state,
              carTurn, bodies, states, connections)
  connections += [
    Contact(CHASSIS, TRACK, *(_STEEL_ON_WOOD + (CHASSIS_SPACING, False))),
    Contact(0, TRACK, *_WALKER_ON_WOOD),
    Contact(0, CHASSIS, *_WALKER_ON_WOOD)]
  connections += [Contact(0, FIRST_CORNER + 6 * c + 3, *_WALKER_ON_RUBBER)
                  for c in range(len(CORNERS))]
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def soapboxCoils(assembly: Assembly) -> tuple:
  """The 'soapboxCoils' function returns how the soapbox's coils are
  drawn ('coilOf': each corner's shock's tube)."""
  return tuple(coilOf(FIRST_CORNER + 6 * c + 4) for c in range(len(CORNERS)))


def soapboxFinishes(assembly: Assembly) -> dict:
  """The 'soapboxFinishes' function returns how the soapbox's bodies are
  drawn, by index: the track and the chassis by their parts, each
  corner's wishbones and knuckle by theirs (mirrored on the right), its
  wheel as the brake bench's (its rim, tyre and disc), its shock's tube
  and rod by their profiles, the rack whole (the steering wheel and
  column: the view's own, 'gui._steeringwheel.columnFinish')."""
  from ._brakes import discRuns
  from ._carcass import rimRuns
  from ._shock import shockRuns
  from ._tyred import tyreRuns
  runs = shockRuns()
  out = {TRACK: trackPieces(), CHASSIS: chassisPieces(), RACK: 'rack'}
  for c, (at, side) in enumerate(CORNERS):
    first = FIRST_CORNER + 6 * c
    out[first] = _sidedPieces(armPieces(True), side, at)
    out[first + 1] = _sidedPieces(armPieces(False), side, at)
    out[first + 2] = _sidedPieces(knucklePieces(), side, at)
    out[first + 3] = rimRuns() + tyreRuns() + discRuns()
    out[first + 4] = runs['tube']
    out[first + 5] = runs['rod']
  return out
