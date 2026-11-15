"""
The tyre rig (user, 2026-11-14: "You attached the wheel and it's
suspension to the end of a long rod. The rod attaches to ground through
ball joint. An actuator then presses the arm such as to force the wheel
into another simulated driving road. A threadmill basically. this setup
can then put force on the wheel and different speeds. We can then
observe breaking at different weights. Further, the rod can also
introduce 'bumps' in the road"; then "the 'belt' could be a flat disc
spinning about the vertical perpendicular to the ground?"; then "We need
steering now ... a two direction hinge still preventing roll ... the
tire can steer its position on the disc ... it's gonna look like a damn
record player"): a front corner of the new car built whole of its parts
on the end of a steel boom; the boom's foot ahead of the wheel on a
yoke (it pitches in the yoke's clevis and the yoke slews on the floor:
a Cardan joint; no roll: a ball joint let it roll about its own length,
one wheel cannot hold it up both ways it can tip), so the wheel steered
rolls across the deck, the boom swinging after it as a record player's
arm, stops on the yoke keeping it on the deck; the steering box on the
boom (the Soufflé steering wheel lying level on its column, the player's
hands on it: 'TurnPoint'; its pinion sliding a rack, 'RackAndPinion',
the tie rod from the rack); pressed down by a hydraulic ram ('Ram': the
operator's load, a fourth wall point) hung from a frame over it; its
wheel on a
turntable, a steel deck 7 m across turning on a post in its middle,
its motor in a housing on the post holding the speed asked (a servo:
'Drive'), humps to bolt across the deck ('Humps'). The corner: a double
wishbone, unequal arms in rubber bushings ('Bush'), the knuckle on two
ball joints ('Tie'), its toe held by the tie rod ('HeldStroke') to the
rack, the shock absorber ('_shock') from the lower
arm up to the boom, the Soufflé wheel and its disc ('brakedWheel') on
its bearing (two ties), the brake's caliper on the knuckle
('DiscBrake'), the tyre ('tyreOf') on the deck. Weight plates on the
boom's end make it a quarter car's to the wheel (about 200 kg on it,
2.3 kN); the ram adds load, not mass. The wheel runs round a circle
on the deck, 'PATH' from its middle: the tread's inner edge is carried
a little slower than its outer (3 % either way: as cornering on that
circle). The car's frame: x forward (the deck runs back under the
wheel), y left (the deck's middle on the wheel's left: a left front
corner), z up from the deck's top.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._assembly import Actuator, Assembly, BrakeLine, Bush, Contact
from ._assembly import DiscBrake, Drive, Fixed, FourthWall, HeldStroke
from ._assembly import Hinge, Hump, Humps, Motor, RackAndPinion, Ram
from ._assembly import Slide, Spring, Tie, TurnPoint
from ._axle import HANDS, PINION, STRAP, columnBody, columnLength
from ._body import Body, State
from ._brakes import DISC_AT, DISC_INNER, DISC_OUTER, PAD_RADIUS
from ._brakes import brakedWheel
from ._carcass import TYRE_PRESSURE, TYRE_YARD, _sector
from ._gears import prismOf
from ._shape import Shape, boxShape, cylinderShape
from ._shock import Shock, coilOf, shockOf
from ._turned import Turned
from ._tyred import _WALKER_ON_RUBBER, _loop, tyreOf
from ._vectors import Vector, minus, norm, plus, product, rotated
from ._vectors import scaled, turnAbout

#  The turntable: its deck's radius, its bore (round the post), how
#  thick it is and how high its top stands over the floor, m; steel; how
#  far from its middle the wheel runs, m; its motor's servo, N m s (a
#  tenth of a second to come to the speed asked, the deck's 37 t m²;
#  the brake at 2 kN slows it 0.05 m/s at the wheel), and its
#  most, N m (from still to 50 m/s at the wheel in about 6 s).
TABLE_RADIUS, TABLE_BORE = 3.5, 0.4
TABLE_DECK, TABLE_TOP = 0.02, 0.06
PATH = 3.0
TABLE_SERVO, TABLE_MOST = 3.7e5, 1e5
STEEL = 7850.0
#  The corner, in the car's frame (m): the wheel's middle out from the
#  car's middle, its axle's height (the tyre's radius, 9 mm pressed in
#  by the corner's load); the ball joints; the wishbones' pivots in the
#  boom (lower along x either side of nought, upper either side of the
#  upper ball joint's x), the tie rod's ends, the shock's eyes (top in
#  the boom, foot on the lower arm). Kingpin 5.5 degrees in, caster 3.7
#  back, scrub radius 25 mm.
WHEEL_Y = 0.78
HUB_HEIGHT = tyreOf(1, TYRE_PRESSURE).radius - 0.009
LOWER_BALL, UPPER_BALL = (0.0, 0.74, 0.16), (-0.02, 0.71, 0.47)
LOWER_PIVOT_Y, LOWER_SPREAD = 0.26, 0.17
UPPER_PIVOT_Y, UPPER_SPREAD = 0.40, 0.13
TIE_INNER, TIE_OUTER = (-0.13, 0.323, 0.30), (-0.13, 0.726, 0.30)
SHOCK_TOP, SHOCK_FOOT = (-0.02, 0.50, 0.51), (-0.02, 0.60, 0.175)
#  The boom: its foot (on the floor, outside the deck) AHEAD of the
#  corner, so the wheel trails it as a trailer its hitch (behind it, the
#  leading wheel would swing round), on a yoke slewing about the upright,
#  the boom pitching in its clevis (user, 2026-11-14: "a two direction
#  hinge still preventing roll": a Cardan joint, its axes meeting at the
#  foot); the weight plates' block (a corner, its size), the ram's eye
#  on them and its top in the frame over it; the yoke's stops: how far
#  from the foot along the boom they bear, how far it may swing out
#  toward the deck's rim (the wheel 0.36 m out: kept on the deck) and in
#  toward its middle (1.5 m in), m, their rubber's rate, N/m, how far it
#  is from the boom when it first bears, m, and its damping, N s/m.
BOOM_FOOT = (3.0, 0.20, 0.10)
WEIGHT_LOW, WEIGHT_SIZE = (0.32, 0.05, 0.30), (0.30, 0.30, 0.135)
RAM_FOOT = (0.47, 0.20, WEIGHT_LOW[2] + WEIGHT_SIZE[2])
RAM_TOP = (0.47, 0.20, 1.75)
STOP_AT, STOP_OUT, STOP_IN = 0.5, 0.06, 0.25
STOP, STOP_REST, STOP_DAMPING = 2e5, 0.05, 2000.0
#  The steering box on the boom (user, 2026-11-14: "We need steering
#  now ... the tire can steer its position on the disc"): the rack's
#  middle and half its length (its outer end the tie rod's inner), its
#  travel either way (the road wheel 24 degrees), the column upright from
#  its pinion beside the rack ('_axle.PINION': a turn of the steering
#  wheel a lock) to the Soufflé steering wheel lying level on top
#  ('_axle.columnBody'), the player's hands on it ('_axle.HANDS').
RACK_MIDDLE = (TIE_INNER[0], 0.2015, TIE_INNER[2])
RACK_HALF = TIE_INNER[1] - RACK_MIDDLE[1]
RACK_TRAVEL = 0.05
COLUMN_FOOT = (TIE_INNER[0] - 0.025, 0.10, TIE_INNER[2])
COLUMN_TOP = plus(COLUMN_FOOT, (0.0, 0.0, columnLength()))
#  The shock's make here: a coil of 80 kN/m (the wheel's rate about 33
#  kN/m on the tyre: 2 Hz under the boom's 200 kg), its free length set
#  so the corner rides as built under 'LOAD' (measured), its damper a
#  quarter of critical in bump, 0.55 in rebound.
SHOCK = Shock(8e4, 0.2597, 2800.0, 6200.0)
#  The ram's load the operator starts at, N, and the most it gives.
LOAD, LOAD_MOST = 1500.0, 5000.0
#  The tyre on the deck (a road's grip: its steel is gritted as a
#  tester's is), the walker on steel.
_TYRE_ON_DECK = (1e5, 1.0, TYRE_YARD.grip, 1e5, 300.0)
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)
#  How many sides round the deck is drawn, and its sectors (painted
#  alike in turn, so it is seen to turn), and the lane the wheel runs
#  in, m either side of its path.
TABLE_SIDES, TABLE_SECTORS, LANE = 120, 72, 0.16


class WheelSetup(NamedTuple):
  """
  WheelSetup is a wheel's tune-up (user, 2026-11-14: "a tune-up menu where
  the tire pressure of each wheel can be adjusted. Along with camber,
  toe"): its tyre's air, 'pressure' Pa over the outside's (its spring's
  stiffness: 'Tyre'); its 'camber' (rad, its top leaning out positive:
  set by shims moving the upper wishbone's pivots in or out); its 'toe'
  (rad, its front turned in toward the car's middle positive: set by its
  tie rod's length), each as set standing as built (its load and the
  rubber then give a little).
  """

  pressure: float = TYRE_PRESSURE
  camber: float = 0.0
  toe: float = 0.0


class TuneUp:
  """
  TuneUp is the tune-up menu's setting of every wheel, 'wheels' (a tuple
  of 'WheelSetup', the car's corners in order; the tyre rig's one), set
  from outside between builds as a mechanic sets a car up stopped.
  """

  __slots__ = ('wheels',)

  def __init__(self, wheels: tuple = (WheelSetup(),)) -> None:
    self.wheels = tuple(wheels)


class RigControls(NamedTuple):
  """
  RigControls are what the rig's operator works: the turntable's motor
  ('drive': a servo toward the speed asked), the ram's load ('load', N:
  a fourth wall point), the humps bolted on ('humps'), the brake's line
  ('line'), the steering wheel ('steer': the hands on it, rad, left
  positive), the wheel's tune-up ('tune', a 'TuneUp'; None: as built);
  and where things are: the table's body, the wheel's, the wheel's path
  as built, m from the table's middle, the knuckle's.
  """

  drive: Drive
  load: FourthWall
  humps: Humps
  line: BrakeLine
  steer: FourthWall
  tune: TuneUp = None
  table: int = 2
  wheel: int = 7
  path: float = PATH
  knuckle: int = 6

  def setSpeed(self, speed: float) -> None:
    """The 'setSpeed' method asks the turntable's motor for the deck to
    run 'speed' m/s under the wheel (backward, the car going forward:
    the deck turns clockwise seen from above)."""
    drive = self.drive
    drive.damping, drive.most = TABLE_SERVO, TABLE_MOST
    drive.torque = -TABLE_SERVO * speed / self.path


def _about(point: Vector, at: Vector, turn: tuple) -> Vector:
  """Returns 'point' turned by 'turn' about 'at'."""
  return plus(at, rotated(turn, minus(point, at)))


def tunedCorner(setup: WheelSetup) -> tuple:
  """The 'tunedCorner' function returns the corner as 'setup' sets it
  up, in the car's frame: the turn of the knuckle (and the wheel on it)
  about the lower ball joint (tilted about the car's length for the
  camber, then turned about the kingpin, through both ball joints, for
  the toe), the upper wishbone's shim (how far its pivots move across,
  m) and its turn about its pivots' line (to meet the knuckle's ball
  joint), and the tie rod's length (to the steering arm where it is
  now): (knuckle turn, shim, arm turn, tie rod length)."""
  tilt = turnAbout((1.0, 0.0, 0.0), -setup.camber)
  upper = _about(UPPER_BALL, LOWER_BALL, tilt)
  reach = UPPER_BALL[1] - UPPER_PIVOT_Y
  lift = max(-1.0, min(1.0, (upper[2] - UPPER_BALL[2]) / reach))
  swing = math.asin(lift)
  shim = upper[1] - UPPER_PIVOT_Y - reach * math.cos(swing)
  kingpin = minus(upper, LOWER_BALL)
  kingpin = scaled(kingpin, 1.0 / norm(kingpin))
  turn = product(turnAbout(kingpin, -setup.toe), tilt)
  outer = _about(TIE_OUTER, LOWER_BALL, turn)
  return (turn, shim, turnAbout((1.0, 0.0, 0.0), swing),
          norm(minus(outer, TIE_INNER)))


def rigOf(point: Vector) -> Vector:
  """The 'rigOf' function returns 'point' (in the car's frame) in the
  rig's (the world's: the table's middle on the floor at nought)."""
  return plus(point, (0.0, -(PATH + WHEEL_Y), TABLE_TOP))


def _box(low: Vector, high: Vector) -> Shape:
  """Returns a box from corner 'low' to corner 'high'."""
  middle = tuple(0.5 * (a + b) for a, b in zip(low, high))
  return boxShape(*(b - a for a, b in zip(low, high))).moved(
    middle, (1.0, 0.0, 0.0, 0.0))


def _bar(start: Vector, end: Vector, thick: float) -> Shape:
  """Returns a square bar 'thick' across from 'start' to 'end'."""
  way = minus(end, start)
  length = norm(way)
  middle = tuple(0.5 * (a + b) for a, b in zip(start, end))
  level = math.hypot(way[0], way[1])
  turn = turnAbout((0.0, 0.0, 1.0), math.atan2(way[1], way[0]))
  pitch = turnAbout(rotated(turn, (0.0, 1.0, 0.0)), math.atan2(-way[2],
                                                                level))
  from ._vectors import product
  return boxShape(length, thick, thick).moved(middle, product(pitch, turn))


def _joined(pieces: tuple) -> Shape:
  """Returns 'pieces' as one shape."""
  shape = pieces[0]
  for piece in pieces[1:]:
    shape = shape.joined(piece)
  return shape


def _bodyOf(pieces: tuple) -> Body:
  """Returns the steel body of 'pieces' ((key, shape), ...)."""
  return Body.of(_joined(tuple(shape for _, shape in pieces)), STEEL)


def tableProfile() -> tuple:
  """The 'tableProfile' function returns the deck as a turned profile in
  its own frame (the world's: its axis the table's middle, upright):
  a ring from its bore to its rim, its top 'TABLE_TOP' over the floor."""
  low = TABLE_TOP - TABLE_DECK
  return _loop([(TABLE_BORE, low), (TABLE_RADIUS, low),
                (TABLE_RADIUS, TABLE_TOP), (TABLE_BORE, TABLE_TOP)])


@functools.lru_cache(maxsize=1)
def tableBody() -> Body:
  """The 'tableBody' function returns the turntable's deck, steel (6 t,
  37 t m² about its axis)."""
  return Body.of(Turned(tableProfile(), TABLE_SIDES), STEEL)


def tablePieces() -> tuple[tuple[str, Shape], ...]:
  """The 'tablePieces' function returns the deck as it is drawn, in its
  own frame: its sectors in turn ('deck', 'stripe') in from the lane
  and out from it, and the lane the wheel runs in ('lane')."""
  low = TABLE_TOP - TABLE_DECK
  out = []
  bands = ((TABLE_BORE, PATH - LANE), (PATH + LANE, TABLE_RADIUS))
  for k in range(TABLE_SECTORS):
    a0 = 2.0 * math.pi * k / TABLE_SECTORS
    a1 = 2.0 * math.pi * (k + 1) / TABLE_SECTORS
    key = 'stripe' if k % 6 == 0 else 'deck'
    for inner, outer in bands:
      out.append((key, prismOf(_sector(inner, outer, a0, a1), low,
                               TABLE_TOP)))
    out.append(('lane', prismOf(_sector(PATH - LANE, PATH + LANE, a0, a1),
                                low, TABLE_TOP)))
  return tuple(out)


def framePieces() -> tuple[tuple[str, Shape], ...]:
  """The 'framePieces' function returns the rig's frame by its parts, in
  the world: ('frame', the floor plate the boom's yoke slews on, the
  yoke's stops' posts, the post and arm the ram hangs from, the table's
  post), ('housing', the table's motor on its post)."""
  foot = rigOf(BOOM_FOOT)
  top = rigOf(RAM_TOP)
  post = (top[0], foot[1] - 0.60)
  stops = tuple(_box((at[0] - 0.04, at[1] - 0.015, 0.0),
                     (at[0] + 0.04, at[1] + 0.015, at[2] + 0.06))
                for at in (rigOf(point) for point in _stopsAt()))
  frame = (_box((foot[0] - 0.18, foot[1] - 0.18, 0.0),
                (foot[0] + 0.18, foot[1] + 0.18, 0.01)),) + stops + (
           _box((post[0] - 0.2, post[1] - 0.2, 0.0),
                (post[0] + 0.2, post[1] + 0.2, 0.04)),
           _box((post[0] - 0.05, post[1] - 0.05, 0.04),
                (post[0] + 0.05, post[1] + 0.05, top[2] + 0.12)),
           _box((post[0] - 0.05, post[1] - 0.05, top[2] + 0.02),
                (post[0] + 0.05, top[1] + 0.08, top[2] + 0.12)),
           _box((-0.12, -0.12, 0.0), (0.12, 0.12, TABLE_TOP)))
  housing = cylinderShape(0.34, 0.45, 32).moved(
    (0.0, 0.0, TABLE_TOP + 0.225), turnAbout((1.0, 0.0, 0.0),
                                             0.5 * math.pi))
  return ('frame', _joined(frame)), ('housing', housing)


def boomPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'boomPieces' function returns the boom by its parts, in the
  car's frame: ('boom', the beam from its foot, the chassis' side at its
  end, the wishbones' brackets, the shock's tower, the tie rod's
  bracket), ('weight', its plates)."""
  rail = _box((-0.30, 0.17, 0.08), (0.25, 0.20, 0.62))
  beam = _bar(BOOM_FOOT, (0.25, 0.20, 0.32), 0.07)
  x, y = COLUMN_FOOT[0], COLUMN_FOOT[1]
  tower = _box((x - 0.03, 0.14, 0.60),
               (x + 0.03, 0.17, COLUMN_TOP[2] - 0.12))
  collars = tuple(_box((x - 0.03, y - 0.03, z - 0.02),
                       (x + 0.03, 0.14, z + 0.02))
                  for z in (0.62, COLUMN_TOP[2] - 0.14))
  housing = _box((TIE_INNER[0] - 0.02, RACK_MIDDLE[1] - RACK_HALF - 0.02,
                  TIE_INNER[2] - 0.02),
                 (TIE_INNER[0] + 0.02, 0.24, TIE_INNER[2] + 0.02))
  pieces = [beam, rail, tower, housing] + list(collars)
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
  weight = _box(WEIGHT_LOW, plus(WEIGHT_LOW, WEIGHT_SIZE))
  return ('boom', _joined(tuple(pieces))), ('weight', weight)


def _stopsAt() -> tuple[Vector, Vector, Vector]:
  """Returns where the yoke's stops are, in the car's frame: the
  boom's point they bear on ('STOP_AT' from its foot), the stop outside
  it (toward the deck's rim) and the one inside, each 'STOP_REST' from
  where the boom first touches it."""
  on = (BOOM_FOOT[0] - STOP_AT, BOOM_FOOT[1], 0.14)
  return (on, (on[0], on[1] - STOP_OUT - STOP_REST, on[2]),
          (on[0], on[1] + STOP_IN + STOP_REST, on[2]))


def yokePieces() -> tuple[tuple[str, Shape], ...]:
  """The 'yokePieces' function returns the boom's yoke, in the car's
  frame: ('yoke', its turntable on the floor plate, 2 mm clear of it,
  and the clevis' ears either side of the boom's foot)."""
  foot, floor = BOOM_FOOT, -TABLE_TOP + 0.012
  base = _box((foot[0] - 0.15, foot[1] - 0.15, floor),
              (foot[0] + 0.15, foot[1] + 0.15, floor + 0.03))
  ears = tuple(_box((foot[0] - 0.06, foot[1] + side * 0.045 - 0.015,
                     floor + 0.03),
                    (foot[0] + 0.06, foot[1] + side * 0.045 + 0.015,
                     foot[2] + 0.06)) for side in (-1.0, 1.0))
  return (('yoke', _joined((base,) + ears)),)


def rackShape() -> Shape:
  """The 'rackShape' function returns the steering's rack, a steel bar
  22 mm square across the car, in the car's frame."""
  low = minus(RACK_MIDDLE, (0.011, RACK_HALF, 0.011))
  return _box(low, plus(RACK_MIDDLE, (0.011, RACK_HALF, 0.011)))


def armPieces(lower: bool) -> tuple[tuple[str, Shape], ...]:
  """The 'armPieces' function returns a wishbone by its parts, in the
  car's frame: ('arm', its two legs from its pivots to its ball joint
  and, the lower, the shock's lug), ('rubber', its bushings on its
  pivots)."""
  if lower:
    ball, y, x0, spread = LOWER_BALL, LOWER_PIVOT_Y, 0.0, LOWER_SPREAD
  else:
    ball, y, x0, spread = UPPER_BALL, UPPER_PIVOT_Y, UPPER_BALL[0], (
      UPPER_SPREAD)
  legs = [_bar((x0 + side * spread, y, ball[2]), ball, 0.025)
          for side in (-1.0, 1.0)]
  legs.append(_box((ball[0] - 0.025, ball[1] - 0.025, ball[2] - 0.025),
                   (ball[0] + 0.025, ball[1] + 0.025, ball[2] + 0.025)))
  if lower:
    legs.append(_box((SHOCK_FOOT[0] - 0.02, SHOCK_FOOT[1] - 0.10,
                      ball[2] - 0.01), (SHOCK_FOOT[0] + 0.02,
                                        SHOCK_FOOT[1] + 0.02,
                                        SHOCK_FOOT[2] + 0.015)))
  bushes = tuple(_box((x0 + side * spread - 0.03, y - 0.022,
                       ball[2] - 0.022),
                      (x0 + side * spread + 0.03, y + 0.022,
                       ball[2] + 0.022)) for side in (-1.0, 1.0))
  return ('arm', _joined(tuple(legs))), ('rubber', _joined(bushes))


def knucklePieces() -> tuple[tuple[str, Shape], ...]:
  """The 'knucklePieces' function returns the knuckle by its parts, in
  the car's frame: ('knuckle', its upright from ball joint to ball
  joint, the spindle out through the wheel's bearing, the steering arm
  back to the tie rod, the caliper's bracket), ('caliper', on the
  disc's back, up 45 degrees)."""
  upright = _bar(LOWER_BALL, UPPER_BALL, 0.04)
  spindle = _box((-0.016, LOWER_BALL[1] - 0.03, HUB_HEIGHT - 0.016),
                 (0.016, WHEEL_Y + 0.09, HUB_HEIGHT + 0.016))
  arm = _bar((-0.005, TIE_OUTER[1], TIE_OUTER[2]), TIE_OUTER, 0.025)
  disc = WHEEL_Y + DISC_AT
  pad = _padAt()
  bracket = _bar((-0.01, disc - 0.035, HUB_HEIGHT + 0.01),
                 (pad[0], disc - 0.035, pad[2]), 0.02)
  caliper = _box((pad[0] - 0.035, disc - 0.022, pad[2] - 0.035),
                 (pad[0] + 0.035, disc + 0.022, pad[2] + 0.035))
  return (('knuckle', _joined((upright, spindle, arm, bracket))),
          ('caliper', caliper))


def _padAt() -> Vector:
  """Returns where the brake's pads press the disc, in the car's frame:
  on its middle plane, half way across its swept ring, up and back."""
  lean = math.radians(45.0)
  return (-PAD_RADIUS * math.cos(lean), WHEEL_Y + DISC_AT,
          HUB_HEIGHT + PAD_RADIUS * math.sin(lean))


@functools.lru_cache(maxsize=1)
def boomBody() -> Body:
  """The 'boomBody' function returns the boom, steel, in the car's frame
  (about 300 kg; its moment about its foot over the wheel's distance
  squared about 200 kg)."""
  return _bodyOf(boomPieces())


@functools.lru_cache(maxsize=2)
def armBody(lower: bool) -> Body:
  """The 'armBody' function returns a wishbone, steel, in the car's
  frame."""
  return _bodyOf(armPieces(lower))


@functools.lru_cache(maxsize=1)
def knuckleBody() -> Body:
  """The 'knuckleBody' function returns the knuckle, steel, in the car's
  frame."""
  return _bodyOf(knucklePieces())


@functools.lru_cache(maxsize=1)
def yokeBody() -> Body:
  """The 'yokeBody' function returns the boom's yoke, steel, in the
  car's frame."""
  return _bodyOf(yokePieces())


@functools.lru_cache(maxsize=1)
def rackBody() -> Body:
  """The 'rackBody' function returns the steering's rack, steel, in the
  car's frame."""
  return Body.of(rackShape(), STEEL)


@functools.lru_cache(maxsize=1)
def frameBody() -> Body:
  """The 'frameBody' function returns the rig's frame (part of the
  world), in the world."""
  return _bodyOf(framePieces())


def tyreRig(controls: RigControls,
            humps: tuple = ()) -> tuple[Assembly, tuple[State, ...]]:
  """The 'tyreRig' function returns the rig worked by 'controls': the
  walker (body 0) on the floor before it, the frame (1, part of the
  world), the turntable (2, still), the boom (3), the lower wishbone
  (4), the upper (5), the knuckle (6), the wheel (7), the shock's tube
  (8) and rod (9), the boom's yoke (10), the steering's rack (11) and
  its column and steering wheel (12), all as built (and as its tune-up
  sets the corner: 'tunedCorner'), still, straight ahead; 'humps' bolted
  on to start."""
  from ._scenes import WALKER
  controls.humps.humps = tuple(humps)
  setup = WheelSetup() if controls.tune is None else (
    controls.tune.wheels[0])
  turn, shim, swing, rod = tunedCorner(setup)
  across = (0.0, shim, 0.0)
  pivots = (UPPER_BALL[0], UPPER_PIVOT_Y + shim, UPPER_BALL[2])
  column = columnBody()
  bodies = [WALKER.body(), frameBody(), tableBody(), boomBody(),
            armBody(True), armBody(False), knuckleBody(), brakedWheel()]
  states = [State(rigOf((-1.0, -2.4, -TABLE_TOP + WALKER.radius))),
            State(frameBody().centre), State(tableBody().centre)]
  for body in bodies[3:5]:
    states.append(State(rigOf(body.centre)))
  states.append(State(rigOf(_about(plus(armBody(False).centre, across),
                                   pivots, swing)), swing))
  states.append(State(rigOf(_about(knuckleBody().centre, LOWER_BALL,
                                   turn)), turn))
  upright = product(turn, turnAbout((1.0, 0.0, 0.0), -0.5 * math.pi))
  middle = (0.0, WHEEL_Y, HUB_HEIGHT)
  states.append(State(plus(rigOf(_about(middle, LOWER_BALL, turn)),
                           rotated(upright, brakedWheel().centre)),
                      upright))
  axis = (0.0, 0.0, 1.0)
  x, y = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
  hub = tableBody().centre
  yoke, rack, steering = 10, 11, 12
  connections = [Fixed(1),
                 Hinge(None, hub, axis, 2, hub, axis),
                 Motor(None, 2, axis, controls.drive),
                 Hinge(None, rigOf(BOOM_FOOT), axis, yoke, BOOM_FOOT, axis),
                 Hinge(yoke, BOOM_FOOT, y, 3, BOOM_FOOT, y)]
  on, outside, inside = _stopsAt()
  for stop in (outside, inside):
    connections.append(Spring(None, rigOf(stop), 3, on, STOP, STOP_REST,
                              STOP_DAMPING, False, True))
  for arm, ball, pivotY, x0, spread in (
      (4, LOWER_BALL, LOWER_PIVOT_Y, 0.0, LOWER_SPREAD),
      (5, UPPER_BALL, UPPER_PIVOT_Y, UPPER_BALL[0], UPPER_SPREAD)):
    for side in (-1.0, 1.0):
      pivot = (x0 + side * spread, pivotY, ball[2])
      inBoom = plus(pivot, across) if arm == 5 else pivot
      connections.append(Hinge(3, inBoom, x, arm, pivot, x, Bush()))
    connections.append(Tie(arm, ball, 6, ball))
  connections += [
    Slide(3, RACK_MIDDLE, y, rack, RACK_MIDDLE, y),
    Spring(3, RACK_MIDDLE, rack, RACK_MIDDLE, STRAP, RACK_TRAVEL, 2000.0,
           True, False),
    Hinge(3, COLUMN_TOP, axis, steering, (0.0, 0.0, 0.0), axis),
    RackAndPinion(steering, axis, rack, (0.0, -1.0, 0.0), 3, PINION),
    TurnPoint(steering, 3, axis, controls.steer, *HANDS),
    Actuator(rack, TIE_INNER, 6, TIE_OUTER, HeldStroke(rod))]
  for w in (0.02, 0.07):
    connections.append(Tie(6, plus(middle, (0.0, w, 0.0)), 7,
                           (0.0, 0.0, w)))
  connections.append(DiscBrake(7, 6, (0.0, 0.0, DISC_AT), axis, _padAt(),
                               DISC_INNER, DISC_OUTER, controls.line))
  connections.append(tyreOf(7, setup.pressure))
  connections.append(Contact(7, 2, *_TYRE_ON_DECK))
  shocked, shockStates, parts = shockOf(SHOCK, 3, SHOCK_TOP, 4,
                                        SHOCK_FOOT, 8, rigOf(SHOCK_TOP),
                                        rigOf(SHOCK_FOOT))
  bodies += list(shocked) + [yokeBody(), rackBody(), column]
  states += list(shockStates) + [
    State(rigOf(yokeBody().centre)), State(rigOf(rackBody().centre)),
    State(plus(rigOf(COLUMN_TOP), column.centre))]
  connections += list(parts)
  connections.append(Ram(None, rigOf(RAM_TOP), 3, RAM_FOOT, controls.load))
  connections.append(controls.humps)
  connections += [Contact(0, k, *(_WALKER_ON_RUBBER if k == 7 else
                                  _WALKER_ON_STEEL))
                  for k in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)]
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def rigHumps(count: int) -> tuple[Hump, ...]:
  """The 'rigHumps' function returns 'count' humps bolted across the
  wheel's lane, evenly round the deck (each 'Hump()': 40 cm across, 3
  cm high), from a metre out from its middle to its rim (wherever the
  wheel is steered)."""
  return tuple(Hump(2.0 * math.pi * (k + 0.5) / count, 1.0,
                    TABLE_RADIUS - 0.05) for k in range(count))


def rigCoils(assembly: Assembly) -> tuple:
  """The 'rigCoils' function returns how the rig's coil is drawn
  ('coilOf': its shock's tube is body 8)."""
  return (coilOf(8),)


def rigFinishes(assembly: Assembly) -> dict:
  """The 'rigFinishes' function returns how the rig's bodies are drawn,
  by index: the frame, the deck, the boom, the wishbones and the
  knuckle and the yoke by their parts, the wheel as the brake bench's
  (its rim, tyre and disc), the shock's tube and rod by their profiles,
  the rack whole (the steering wheel and column: the view's own,
  'gui._steeringwheel.columnFinish')."""
  from ._brakes import discRuns
  from ._carcass import rimRuns
  from ._shock import shockRuns
  from ._tyred import tyreRuns
  runs = shockRuns()
  return {1: framePieces(), 2: tablePieces(), 3: boomPieces(),
          4: armPieces(True), 5: armPieces(False), 6: knucklePieces(),
          7: rimRuns() + tyreRuns() + discRuns(), 8: runs['tube'],
          9: runs['rod'], 10: yokePieces(), 11: 'rack'}
