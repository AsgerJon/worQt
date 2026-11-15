"""
The steering bench (user, 2026-11-14: "The steering wheel shall be
designated as a point that can receive rotational input through the
fourth wall. From the steering wheel, follow the traditional and real
implementation"): a car's front axle on a rig, steered as cars are.
The steering wheel and its column one body, turning in the column's
bearings (a 'Hinge' to the rig), the player's hands on it ('TurnPoint',
a fourth wall point); the pinion at the column's foot meshing with the
rack ('RackAndPinion': 7.96 mm, 540 degrees of wheel a 75 mm of rack),
the rack sliding in its housing ('Slide'), its travel ended by a strap
('Spring', pulling only, 75 mm either way); tie rods with ball joints at
both ends (held rods: 'Actuator', 'HeldStroke') out to the steering
arms on the knuckles (behind the axle, aimed at the rear axle's middle
2.5 m back: Ackermann), the knuckles turning on their kingpins
('Hinge'), the Soufflé wheels with their discs ('brakedWheel') on their
bearings (two ties each) on the knuckles, their brakes' calipers on the
knuckles ('DiscBrake', one line: the brake, a fourth wall point too),
their tyres on the ground. The car points along +x, its left along +y;
the walker sits in the driver's place, behind the wheel (Denmark's
side: the left).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._assembly import Actuator, Assembly, BrakeLine, Contact, DiscBrake
from ._assembly import Fixed, FourthWall, HeldStroke, Hinge
from ._assembly import RackAndPinion, Slide, Spring, Tie, TurnPoint
from ._body import Body, State
from ._brakes import DISC_AT, DISC_INNER, DISC_OUTER, PAD_RADIUS
from ._brakes import brakedWheel
from ._carcass import TYRE_PRESSURE
from ._shape import Shape, boxShape, cylinderShape
from ._turned import Turned
from ._tyred import _WALKER_ON_RUBBER, _loop, tyreOf
from ._vectors import Vector, minus, norm, plus, rotated, scaled
from ._vectors import turnAbout

#  The axle: the kingpins' places across (y), the wheels' middles (y),
#  the rack's line behind the axle (x) and its ends' (y), the steering
#  arms' length and the wheelbase they aim by; the axle's height (the
#  tyre's radius, 2 mm in).
KINGPIN_Y, WHEEL_Y = 0.68, 0.78
RACK_X, RACK_END = -0.135, 0.40
ARM_LENGTH, WHEELBASE = 0.14, 2.5
AXLE_HEIGHT = tyreOf(1, TYRE_PRESSURE).radius - 0.002
#  The steering: the pinion's pitch radius (75 mm of rack in one and a
#  half turns), the rack's travel either way, the strap's stiffness (the
#  hands' most, 7.5 kN at the rack, stretch it 1.5 mm); the
#  column from the pinion (at the rack, the driver's side) up and back to
#  the wheel's middle; the hands (stiffness, damping, most).
PINION = 0.075 / (3.0 * math.pi)
TRAVEL, STRAP = 0.075, 5e6
DRIVER_Y = 0.35
WHEEL_AT = (-1.0, DRIVER_Y, 0.85)
HANDS = (2000.0, 20.0, 60.0)
#  The steering wheel: its rim's radius (to the grip's middle), the
#  flat bottom's height under its middle, its grip's thickness; the
#  column's radius.
RIM, FLAT, GRIP = 0.175, 0.13, 0.016
COLUMN = 0.0125
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)


def _box(low: Vector, high: Vector) -> Shape:
  """Returns a box from corner 'low' to corner 'high'."""
  middle = tuple(0.5 * (a + b) for a, b in zip(low, high))
  return boxShape(*(b - a for a, b in zip(low, high))).moved(
    middle, (1.0, 0.0, 0.0, 0.0))


def _joined(pieces: tuple) -> Shape:
  """Returns 'pieces' as one shape."""
  shape = pieces[0]
  for piece in pieces[1:]:
    shape = shape.joined(piece)
  return shape


def _summed(parts: tuple, shape: object) -> Body:
  """Returns 'parts' (bodies in one frame) as one body of 'shape':
  masses and moments summed (parallel axes)."""
  mass = sum(part.mass for part in parts)
  centre = tuple(sum(part.mass * part.centre[i] for part in parts) / mass
                 for i in range(3))
  inertia = [[0.0] * 3 for _ in range(3)]
  for part in parts:
    d = tuple(a - b for a, b in zip(part.centre, centre))
    dd = sum(x * x for x in d)
    for i in range(3):
      for j in range(3):
        inertia[i][j] += part.inertia[i][j] + part.mass * (
          (dd if i == j else 0.0) - d[i] * d[j])
  return Body(mass, centre, tuple(tuple(row) for row in inertia), shape)


def columnLength() -> float:
  """The 'columnLength' function returns how far the steering wheel's
  middle is from the pinion's, m."""
  return norm(minus(WHEEL_AT, (RACK_X, DRIVER_Y, AXLE_HEIGHT)))


def columnTurn() -> tuple:
  """The 'columnTurn' function returns how the column body lies: its
  own z up the column toward the driver, its own y the wheel's top
  (up, square to it), its own x the driver's right."""
  way = minus(WHEEL_AT, (RACK_X, DRIVER_Y, AXLE_HEIGHT))
  return _frame((0.0, -1.0, 0.0), _unit((way[2], 0.0, -way[0])),
                _unit(way))


def _unit(v: Vector) -> Vector:
  """Returns 'v' a unit long."""
  return scaled(v, 1.0 / norm(v))


def _frame(x: Vector, y: Vector, z: Vector) -> tuple:
  """Returns the turn whose own x, y, z lie along 'x', 'y', 'z' (units,
  square, right handed)."""
  from ._vectors import turnOf
  return turnOf(((x[0], y[0], z[0]), (x[1], y[1], z[1]),
                 (x[2], y[2], z[2])))


@functools.lru_cache(maxsize=4)
def columnBody(length: float = None) -> Body:
  """The 'columnBody' function returns the steering wheel and its column
  as one body, in its own frame (the wheel's middle at the origin, its
  face toward +z, its top +y, the column down -z to the pinion): the
  rim (a ring of leather over steel, 1.1 kg), the hub and spokes (0.6
  kg), the column (a steel shaft, its pinion at its foot), 'length' m
  from the wheel's middle to the pinion's (None: the steering bench's,
  'columnLength')."""
  length = columnLength() if length is None else length
  ring = Turned(_loop([(RIM - GRIP, -0.013), (RIM + GRIP, -0.013),
                       (RIM + GRIP, 0.013), (RIM - GRIP, 0.013)]), 48)
  rim = Body.of(ring, 1.1 / ring.moments()[0])
  dish = Turned(_loop([(0.0, -0.05), (0.06, -0.05), (0.06, 0.008),
                       (0.0, 0.008)]), 24)
  hub = Body.of(dish, 0.6 / dish.moments()[0])
  shaft = Body.of(Turned(_loop([(0.0, -length - 0.04),
                                (COLUMN, -length - 0.04),
                                (COLUMN, -0.05), (0.0, -0.05)]), 24),
                  7850.0)
  shape = _joined((cylinderShape(RIM + GRIP, 0.026, 24).moved(
    (0.0, 0.0, 0.0), turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)),
    _box((-COLUMN, -COLUMN, -length - 0.04), (COLUMN, COLUMN, -0.05))))
  return _summed((rim, hub, shaft), shape)


def knucklePieces(side: float) -> tuple[tuple[str, Shape], ...]:
  """The 'knucklePieces' function returns the knuckle on the 'side'
  (+1 left, -1 right) by its parts, in its own frame (the world's axes,
  from the kingpin's foot at the axle's height): ('knuckle', its boss on
  the kingpin, the spindle out through the wheel's bearings, the
  steering arm back to the tie rod), ('caliper', on its bracket at the
  disc's back)."""
  out = side * (WHEEL_Y - KINGPIN_Y)
  disc = side * (WHEEL_Y + DISC_AT - KINGPIN_Y)
  tip = armTip(side)
  boss = _box((-0.03, -0.03, -0.12), (0.03, 0.03, 0.12))
  spindle = _box((-0.016, min(0.0, out + side * 0.09),
                  -0.016), (0.016, max(0.0, out + side * 0.09), 0.016))
  arm = _bar2((0.0, 0.0, 0.0), (tip[0], tip[1] - side * KINGPIN_Y, 0.0))
  short = disc - side * 0.024
  bracket = _box((-0.13, min(0.0, short), -0.02),
                 (-0.02, max(0.0, short), 0.02))
  caliper = _box((-PAD_RADIUS - 0.035, disc - 0.022, -0.035),
                 (-PAD_RADIUS + 0.035, disc + 0.022, 0.035))
  return (('knuckle', _joined((boss, spindle, arm, bracket))),
          ('caliper', caliper))


def _bar2(start: Vector, end: Vector) -> Shape:
  """Returns a flat bar 30 x 20 mm from 'start' to 'end' (level)."""
  dx, dy = end[0] - start[0], end[1] - start[1]
  middle = tuple(0.5 * (a + b) for a, b in zip(start, end))
  return boxShape(math.hypot(dx, dy), 0.03, 0.02).moved(
    middle, turnAbout((0.0, 0.0, 1.0), math.atan2(dy, dx)))


def armTip(side: float) -> Vector:
  """The 'armTip' function returns where the steering arm on the 'side'
  ends (its tie rod's outer ball joint), in the world (the rig's
  frame): 'ARM_LENGTH' back from the kingpin, aimed at the rear axle's
  middle (Ackermann)."""
  way = _unit((-WHEELBASE, -side * KINGPIN_Y, 0.0))
  return plus((0.0, side * KINGPIN_Y, AXLE_HEIGHT), scaled(way, ARM_LENGTH))


@functools.lru_cache(maxsize=2)
def knuckleBody(side: float) -> Body:
  """The 'knuckleBody' function returns a knuckle, steel."""
  return Body.of(_joined(tuple(shape for _, shape in knucklePieces(side))),
                 7850.0)


def rackBody() -> Body:
  """The 'rackBody' function returns the rack, a steel bar 25 mm square
  between its ends' ball joints, along its own y."""
  return Body.of(boxShape(0.025, 2.0 * RACK_END, 0.025), 7850.0)


def rigPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'rigPieces' function returns the rig by its parts, in its own
  frame (the world's): ('frame', its base and the kingpins' and rack's
  posts), ('bracket', the kingpins' forks, the rack's housing, the
  column's bearing housings)."""
  height = AXLE_HEIGHT
  frame = [_box((-1.0, -0.55, 0.0), (0.2, 0.55, 0.03))]
  brackets = []
  for side in (-1.0, 1.0):
    y = side * KINGPIN_Y
    frame.append(_box((-0.05, y - side * 0.12 - 0.03, 0.03),
                      (0.05, y - side * 0.12 + 0.03, height + 0.20)))
    for z in (height - 0.15, height + 0.15):
      low, high = sorted((y, y - side * 0.12))
      brackets.append(_box((-0.035, low - 0.03, z - 0.015),
                           (0.035, high + 0.03, z + 0.015)))
  brackets.append(_box((RACK_X - 0.025, -0.33, height - 0.025),
                       (RACK_X + 0.025, 0.33, height + 0.025)))
  frame.append(_box((RACK_X - 0.03, -0.03, 0.03),
                    (RACK_X + 0.03, 0.03, height - 0.025)))
  turn = columnTurn()
  start = (RACK_X, DRIVER_Y, AXLE_HEIGHT)
  for share in (0.3, 0.85):
    middle = plus(start, scaled(minus(WHEEL_AT, start), share))
    brackets.append(boxShape(0.06, 0.06, 0.12).moved(middle, turn))
    frame.append(_box((middle[0] - 0.02, middle[1] - 0.02, 0.03),
                      (middle[0] + 0.02, middle[1] + 0.02,
                       middle[2] - 0.03)))
  return ('frame', _joined(tuple(frame))), ('bracket',
                                            _joined(tuple(brackets)))


@functools.lru_cache(maxsize=1)
def rigBody() -> Body:
  """The 'rigBody' function returns the rig (part of the world)."""
  return Body.of(_joined(tuple(shape for _, shape in rigPieces())),
                 7850.0)


def steeringBench(wall: FourthWall,
                  line: BrakeLine) -> tuple[Assembly, tuple[State, ...]]:
  """The 'steeringBench' function returns the front axle, steered by
  'wall' (the player's hands: the steering wheel's angle, rad, left
  positive) and braked by 'line': the walker (body 0) in the driver's
  place behind the wheel, the rig (1, part of the world), the steering
  wheel and column (2), the rack (3), the knuckles (4 left, 5 right),
  the wheels (6 left, 7 right), straight ahead and still."""
  from ._scenes import WALKER
  column, rack = columnBody(), rackBody()
  turn = columnTurn()
  length = columnLength()
  axis = (0.0, 0.0, 1.0)
  states = [State((WHEEL_AT[0] - 0.75, DRIVER_Y, WALKER.radius)),
            State(rigBody().centre),
            State(plus(WHEEL_AT, rotated(turn, columnBody().centre)), turn),
            State((RACK_X, 0.0, AXLE_HEIGHT))]
  bodies = [WALKER.body(), rigBody(), column, rack]
  connections = [
    Fixed(1),
    Hinge(1, WHEEL_AT, rotated(turn, axis), 2, (0.0, 0.0, 0.0), axis),
    Slide(1, (RACK_X, 0.0, AXLE_HEIGHT), (0.0, 1.0, 0.0), 3,
          (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    RackAndPinion(2, axis, 3, (0.0, -1.0, 0.0), 1, PINION),
    Spring(1, (RACK_X, 0.0, AXLE_HEIGHT), 3, (0.0, 0.0, 0.0), STRAP,
           TRAVEL, 2000.0, True, False),
    TurnPoint(2, 1, axis, wall, *HANDS)]
  left = turnAbout((1.0, 0.0, 0.0), -0.5 * math.pi)
  right = turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)
  for index, (side, upright) in enumerate(((1.0, left), (-1.0, right))):
    knuckle, wheel = 4 + index, 6 + index
    pin = (0.0, side * KINGPIN_Y, AXLE_HEIGHT)
    body = knuckleBody(side)
    bodies.insert(knuckle, body)
    states.insert(knuckle, State(plus(pin, body.centre)))
    connections.append(Hinge(1, pin, (0.0, 0.0, 1.0), knuckle,
                             (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
    tip = armTip(side)
    connections.append(Actuator(3, (0.0, side * RACK_END, 0.0), knuckle,
                                minus(tip, pin), HeldStroke(norm(minus(
                                  tip, (RACK_X, side * RACK_END,
                                        AXLE_HEIGHT))))))
  for index, (side, upright) in enumerate(((1.0, left), (-1.0, right))):
    knuckle, wheel = 4 + index, 6 + index
    pin = (0.0, side * KINGPIN_Y, AXLE_HEIGHT)
    middle = (0.0, side * WHEEL_Y, AXLE_HEIGHT)
    body = brakedWheel()
    bodies.append(body)
    states.append(State(plus(middle, rotated(upright, body.centre)),
                        upright))
    for w in (0.02, 0.07):
      connections.append(Tie(knuckle, minus(plus(middle, (0.0, side * w,
                                                          0.0)), pin),
                             wheel, (0.0, 0.0, w)))
    connections.append(DiscBrake(wheel, knuckle, (0.0, 0.0, DISC_AT),
                                 (0.0, 0.0, 1.0),
                                 (-PAD_RADIUS, side * (WHEEL_Y + DISC_AT
                                                       - KINGPIN_Y), 0.0),
                                 DISC_INNER, DISC_OUTER, line))
    connections.append(tyreOf(wheel, TYRE_PRESSURE))
  connections += [Contact(0, k, *(_WALKER_ON_RUBBER if k >= 6 else
                                  _WALKER_ON_STEEL))
                  for k in (1, 4, 5, 6, 7)]
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)
