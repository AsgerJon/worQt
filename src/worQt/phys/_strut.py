"""
The real car's rear corners on Chapman struts (user, 2026-11-15: "the
suspension should go from double wishbone to the same suspension as on
the lotus", "chapman, that's it!", and "computability > historical
accuracy!"): the strut's tube clamped to the upright (one body, its
shape the upright's with the tube's), its rod sliding in it, the coil
and the damper between them, the rod's top in a ball mount on the
chassis; the half shaft, its length fixed by its joints, the lower
link across; a radius rod forward to the chassis and a toe link across
(rigid rods, no bodies: 'Actuator' held strokes). Three bodies a corner
(the upright, the wheel, the rod) where the double wishbones were six;
nothing left free but the wheel's rise and fall.

Points are the left rear corner's, in its frame (x along the car from
the axle, y out, z up from the road), mirrored on the right as the
soapbox's corners are ('_soapbox._sided').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._assembly import Actuator, Damper, DiscBrake, HeldStroke, Slide
from ._assembly import Spring, Tie
from ._body import Body, State
from ._brakes import DISC_AT, DISC_INNER, DISC_OUTER, brakedWheel
from ._rig import HUB_HEIGHT, STEEL, TIE_OUTER, WHEEL_Y
from ._rig import _bar, _box, _padAt
from ._shape import Shape, cylinderShape
from ._shock import BUMP_DAMPING, TOP_OUT, _upTo
from ._turned import Turned
from ._tyred import _loop
from ._soapbox import _joined, _sided, _sidedShape, _sidedTurn, _summed
from ._tyred import tyreOf
from ._vectors import Vector, minus, norm, plus, product, rotated
from ._vectors import scaled, turnAbout

#  The strut: its foot (the tube's lower end, on the upright over the
#  half shaft's outer joint) and its top (the rod's ball mount on the
#  chassis), m; the tube's share of solid steel (hollow, its oil in it);
#  the upright's stuff (cast alloy), kg/m³.
STRUT_FOOT, STRUT_TOP = (-0.02, 0.64, 0.40), (0.12, 0.26, 0.65)
TUBE_SOLID, ALLOY = 0.45, 2800.0
#  The strut as the period's (user, 2026-11-15, the picture
#  previews/Lotus_12_Donington.jpg: "What we have no don't look right"):
#  long and slender, leaning in and forward from the hub to its top under
#  the tail's skin, its coil long round most of it. Its tube's length up
#  from its foot and radius, its rod's length down from its top's eye and
#  radius, its top mount's radius, its coil's seats (how far up the tube,
#  how far down the rod, their radius), the coil's radius, its wire's and
#  its turns, m.
TUBE_LONG, TUBE_ROUND = 0.26, 0.021
ROD_LONG, ROD_ROUND, MOUNT_ROUND = 0.30, 0.009, 0.022
LOWER_AT, UPPER_AT, SEAT_ROUND = 0.06, 0.035, 0.035
COIL_ROUND, WIRE_ROUND, TURNS = 0.03, 0.0045, 13
#  The toe link's inner end, on the frame's tail tube (inside the
#  bodywork), m: on the line from its outer end through the corner's
#  instant centre (where the half shaft's line meets the square to the
#  strut through its top), a touch over it, so the wheel turns in a
#  hair as it rises (user, 2026-11-15: "suspension feels weird"; at
#  0.26 m each rear wheel turned out 0.31 deg every 10 mm it rose: the
#  car steered itself from behind over every bump and in every corner;
#  measured 0.29: 0.12 out, 0.32: 0.10 in).
TOE_INNER = (-0.13, 0.24, 0.31)
#  The rear's toe-in as built, rad (each wheel's front turned in toward
#  the car's middle, by its toe link's length, as a strut car's rear is
#  set, steadying it; standing, its load turns each out ~0.2 deg).
TOE_IN = 0.006
#  The radius rod: its end on the upright (low, inside the rim's dish)
#  and on the chassis (half a metre ahead, at the rail), m.
RADIUS_BACK, RADIUS_FRONT = (0.0, 0.72, 0.17), (0.50, 0.30, 0.22)
#  The upright: its hub's boss about the spindle (inner and outer face,
#  out from the car's middle; its radius), m.
BOSS_IN, BOSS_OUT, BOSS = 0.69, 0.75, 0.055


def strutWay() -> Vector:
  """The 'strutWay' function returns the unit way up the strut, from its
  foot to its top (the left rear corner's)."""
  way = minus(STRUT_TOP, STRUT_FOOT)
  return scaled(way, 1.0 / norm(way))


def _cylinderAlong(start: Vector, end: Vector, radius: float,
                   sides: int) -> Shape:
  """Returns a round cylinder (its round 'sides' corners) of 'radius'
  from 'start' to 'end'."""
  way = minus(end, start)
  length = norm(way)
  middle = tuple(0.5 * (a + b) for a, b in zip(start, end))
  turn = product(_upTo(scaled(way, 1.0 / length)),
                 turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi))
  return cylinderShape(radius, length, sides).moved(middle, turn)


def uprightPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'uprightPieces' function returns the rear upright by its parts,
  in the left rear corner's frame: ('knuckle', its hub's boss about the
  spindle, the spindle out through the wheel's bearing, its leg down to
  the radius rod's eye, the arm back to the toe link, its brace up to
  the strut's foot, the caliper's bracket), ('damper', the strut's
  tube up from its foot, its spring's lower seat), ('caliper', on the
  disc's back, up 45 degrees)."""
  hub = (0.0, BOSS_IN, HUB_HEIGHT)
  boss = _cylinderAlong(hub, (0.0, BOSS_OUT, HUB_HEIGHT), BOSS, 16)
  spindle = _box((-0.016, BOSS_IN, HUB_HEIGHT - 0.016),
                 (0.016, WHEEL_Y + 0.09, HUB_HEIGHT + 0.016))
  leg = _bar((0.0, BOSS_IN + 0.02, HUB_HEIGHT - BOSS + 0.01),
             RADIUS_BACK, 0.03)
  arm = _bar((-0.03, TIE_OUTER[1], HUB_HEIGHT), TIE_OUTER, 0.025)
  brace = _bar((0.0, BOSS_IN + 0.01, HUB_HEIGHT + BOSS - 0.01),
               STRUT_FOOT, 0.035)
  disc = WHEEL_Y + DISC_AT
  pad = _padAt()
  bracket = _bar((-0.01, disc - 0.035, HUB_HEIGHT + 0.01),
                 (pad[0], disc - 0.035, pad[2]), 0.02)
  caliper = _box((pad[0] - 0.035, disc - 0.022, pad[2] - 0.035),
                 (pad[0] + 0.035, disc + 0.022, pad[2] + 0.035))
  way = strutWay()
  top = plus(STRUT_FOOT, scaled(way, TUBE_LONG))
  seat = plus(STRUT_FOOT, scaled(way, LOWER_AT))
  tube = _cylinderAlong(STRUT_FOOT, top, TUBE_ROUND, 16)
  plate = _cylinderAlong(plus(seat, scaled(way, -0.006)), seat,
                         SEAT_ROUND, 24)
  return (('knuckle', _joined((boss, spindle, leg, arm, brace,
                               bracket))),
          ('damper', _joined((tube, plate))), ('caliper', caliper))


def uprightBody(side: float, at: float) -> Body:
  """The 'uprightBody' function returns the rear upright of the corner
  'at' on 'side' with its strut's tube, in the car's frame: cast alloy
  ('ALLOY'), the tube steel 'TUBE_SOLID' of solid."""
  parts = [(_sidedShape(shape, side, at), STEEL * TUBE_SOLID if (
    key == 'damper') else ALLOY) for key, shape in uprightPieces()]
  return _summed(tuple(parts), _joined(tuple(shape for shape, _ in parts)))


def strutRodProfile() -> tuple:
  """The 'strutRodProfile' function returns the strut's rod as a turned
  profile, its own z up the strut, from its top's eye down: the top
  mount, the coil's upper seat, the rod down into the tube."""
  seat = -UPPER_AT
  return _loop([(0.0, 0.0), (MOUNT_ROUND, 0.0),
                (MOUNT_ROUND, seat + 0.006), (SEAT_ROUND, seat + 0.006),
                (SEAT_ROUND, seat), (ROD_ROUND, seat),
                (ROD_ROUND, -ROD_LONG), (0.0, -ROD_LONG)])


def strutRodBody(mass: float) -> Body:
  """The 'strutRodBody' function returns the strut's rod, 'mass' kg (the
  coil's half with it), as its turned shape spreads it."""
  shape = Turned(strutRodProfile(), 24)
  return Body.of(shape, mass / shape.moments()[0])


def toeLinkOf(toe: float) -> float:
  """The 'toeLinkOf' function returns how long the toe link is that sets
  the rear wheel 'toe' rad in past 'TOE_IN' (as '_rig.WheelSetup' sets
  a wheel's toe: its front turned toward the car's middle), the upright
  turned so about its steering axis (from the strut's top's ball to the
  half shaft's outer joint, by the hub: leaning far over, so the upright
  turns about it by the toe over how upright it stands, its wheel's
  heading turning by the toe)."""
  hub = (0.0, BOSS_IN, HUB_HEIGHT)
  axis = minus(STRUT_TOP, hub)
  axis = scaled(axis, 1.0 / norm(axis))
  turn = turnAbout(axis, -(TOE_IN + toe) / axis[2])
  outer = plus(hub, rotated(turn, minus(TIE_OUTER, hub)))
  return norm(minus(outer, TOE_INNER))


def strutCoilOf(upright: int, rod: int, side: float, at: float) -> tuple:
  """The 'strutCoilOf' function returns how the coil of the strut on
  the corner 'at' on 'side' is drawn (as '_shock.coilOf' a shock's):
  its seats' points (on the upright 'upright', in its own frame: the
  car's; on the rod 'rod'), the coil's radius, its wire's, its turns."""
  return (upright, _sided(plus(STRUT_FOOT, scaled(strutWay(), LOWER_AT)),
                          side, at), rod, (0.0, 0.0, -UPPER_AT),
          COIL_ROUND, WIRE_ROUND, TURNS)


def addStrutCorners(corners: tuple, setups: tuple, shock: object,
                    chassis: int, first: int, lines: tuple, world: object,
                    state: object, carTurn: tuple, bodies: list,
                    states: list, connections: list) -> None:
  """The 'addStrutCorners' function adds rear corners on Chapman struts
  ('corners' as '_soapbox.addCorners' takes them, each its 'setups'
  tyre's pressure and toe, 'toeLinkOf'; its camber as built) to
  'bodies', 'states' and
  'connections', three bodies a corner from 'first' (the upright, its
  wheel, its strut's rod): the wheel on the upright's bearing, its disc
  brake on 'lines' (each corner's), its tyre; the strut ('shock' its
  make: its coil between the tube's seat and the rod's, its damper and
  stops between the strut's foot and top, its rod's top in a ball
  mount on body 'chassis'); the radius rod and the toe link from the
  chassis to the upright."""
  axis = (0.0, 0.0, 1.0)
  for c, ((at, side), setup) in enumerate(zip(corners, setups)):
    upright, wheel, rod = first + 3 * c, first + 3 * c + 1, first + 3 * c + 2
    hub = uprightBody(side, at)
    bodies += [hub, brakedWheel()]
    states.append(state(hub.centre))
    turned = _sidedTurn(turnAbout((1.0, 0.0, 0.0), -0.5 * math.pi), side)
    middle = _sided((0.0, WHEEL_Y, HUB_HEIGHT), side, at)
    states.append(State(plus(world(middle), rotated(
      product(carTurn, turned), brakedWheel().centre)),
                        product(carTurn, turned)))
    foot, top = _sided(STRUT_FOOT, side, at), _sided(STRUT_TOP, side, at)
    way = minus(top, foot)
    length = norm(way)
    up = scaled(way, 1.0 / length)
    lean = _upTo(up)
    stem = strutRodBody(shock.rod)
    bodies.append(stem)
    states.append(State(plus(world(top), rotated(product(carTurn, lean),
                                                 stem.centre)),
                        product(carTurn, lean)))
    seat = plus(foot, scaled(up, LOWER_AT))
    connections += [
      Tie(chassis, top, rod, (0.0, 0.0, 0.0)),
      Slide(upright, plus(foot, scaled(up, TUBE_LONG)), up, rod,
            (0.0, 0.0, TUBE_LONG - length), axis),
      Spring(upright, seat, rod, (0.0, 0.0, -UPPER_AT), shock.spring,
             shock.free, 0.0, False, True),
      Damper(upright, foot, chassis, top, shock.bump, shock.rebound),
      Spring(upright, foot, chassis, top, shock.stop, shock.shortest,
             BUMP_DAMPING, False, True),
      Spring(upright, foot, chassis, top, TOP_OUT, shock.longest, 0.0,
             True, False),
      Actuator(chassis, _sided(RADIUS_FRONT, side, at), upright,
               _sided(RADIUS_BACK, side, at), HeldStroke(norm(minus(
                 RADIUS_BACK, RADIUS_FRONT)))),
      Actuator(chassis, _sided(TOE_INNER, side, at), upright,
               _sided(TIE_OUTER, side, at), HeldStroke(toeLinkOf(
                 setup.toe)))]
    for w in (0.02, 0.07):
      connections.append(Tie(upright, plus(middle, (0.0, side * w, 0.0)),
                             wheel, (0.0, 0.0, w)))
    connections.append(DiscBrake(wheel, upright, (0.0, 0.0, DISC_AT), axis,
                                 _sided(_padAt(), side, at), DISC_INNER,
                                 DISC_OUTER, lines[c]))
    connections.append(tyreOf(wheel, setup.pressure))
