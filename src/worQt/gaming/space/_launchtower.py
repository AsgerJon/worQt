"""
The launch tower beside the rocket on the pad (user, 2026-11-17: "We
*must* have the ability to walk around in the dark before getting in.
Have us start inside a building level with the walkway. There should be
light on. An EXIT sign should point us to a stair case and to an
elevator that can take us to the ground"), Qt-free, in the rocket's own
axes as it stands on the pad (the pad's own, x east, 'PAD_UP' lower):
- the HALL, a lit room at the top, level with the cabin's floor, the
  walkway leaving its east wall for the rocket;
- the STAIR TOWER west of it, from the ground up: its stairwell (two
  lanes of flights, back and forth, a wall between, landings at either
  end: 'FLIGHTS' of them, each a ramp under its steps: Asger's round
  body climbs a slope, not a step's edge), a doorway from its top
  landing into the hall and one from its bottom out to the ground; the
  LIFT's shaft beside it (its car: '_towerlift');
- the YARD round it all: the pad's ground, walkable in the dark, the
  rocket's body, its legs, the tower's legs and the stair tower solid.
Its rooms (each how far inside: 'groundsInside') join the cabin's while
the walkway is at the door ('_walkway'); its solids ('towerSolids') go
into the cabin's world.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._cockpit import FLOOR, capsuleRadius
from ._vessel import LEGS, RADIUS, SIZE
from ._walkway import LEAN, PAD_UP, TUNNEL_FROM, boxInside

#  The ground (the pad's top: the rocket's own z), m.
GROUND = -PAD_UP + 0.02
#  The hall (inside: x from its west wall to its east, y, z), its walls'
#  thickness, m.
HALL = ((-18.5, -3.0, FLOOR), (TUNNEL_FROM, 3.0, FLOOR + 3.0))
WALL = 0.2
#  The stairwell (inside), its lanes' split (y: the wall between, half
#  its thickness), its landings' length (x) at either end; the flights
#  (an odd number: the top landing is the east one, by the hall).
STAIRWELL = ((-24.5, -3.0, GROUND), (-18.7, 0.0, FLOOR + 3.0))
LANES = (-1.5, 0.05)
LANDING = 1.0
FLIGHTS = 21
#  The lift's shaft (inside), the car's floor and roof plates' half
#  thickness and its height inside, m.
SHAFT = ((-20.9, 0.4, GROUND), (-18.7, 2.6, FLOOR + 3.0))
CAR_HIGH = 2.5
PLATE = 0.06
#  The doorways (boxes through the walls): the stairwell's top (into the
#  hall) and bottom (out to the yard, its west wall); the lift's top
#  (into the hall) and bottom (out to the yard, its north wall).
STAIR_TOP = ((-19.3, -2.6, FLOOR), (-17.7, -0.4, FLOOR + 2.2))
STAIR_FOOT = ((-25.4, -2.6, GROUND), (-23.6, -0.4, GROUND + 2.2))
LIFT_TOP = ((-19.4, 0.9, FLOOR), (-17.8, 2.1, FLOOR + 2.2))
LIFT_FOOT = ((-20.3, 2.2, GROUND), (-19.2, 3.6, GROUND + 2.2))
#  The stair tower's walls outside (its footprint, its top), m.
TOWER = ((-24.7, -3.2), (-18.5, 3.2))
TOWER_TOP = FLOOR + 3.2
#  The yard: how far it reaches round the pad (x and y), how high (it
#  stops under the hall's floor), m.
YARD = ((-60.0, -60.0, GROUND), (60.0, 60.0, FLOOR - 1.0))
#  The rocket's body met from the yard: its radius (its tank's, a little
#  more), m.
BODY = RADIUS + 0.05
#  The steel tower's legs under the hall's east end (x, y; half their
#  width), m.
LEG_HALF = 0.18
TOWER_LEGS = ((-17.0, -2.0), (-17.0, 2.0), (-13.0, -2.0), (-13.0, 2.0))
#  Where Asger starts (his soles, the way he faces), and the EXIT sign
#  (its middle on the hall's west wall over the doorways, half its size),
#  m.
START = ((-16.5, 0.0, FLOOR + 0.002), (1.0, 0.0, 0.0))
EXIT_SIGN = ((HALL[0][0] + 0.03, 0.0, FLOOR + 2.55), (0.55, 0.16))


def rise() -> float:
  """Returns how high each flight climbs, m."""
  return (FLOOR - GROUND) / FLIGHTS


def landingLevel(k: int) -> float:
  """Returns the height of landing 'k' (nought the ground, 'FLIGHTS'
  the hall's floor), m."""
  return GROUND + k * rise()


def flightOf(k: int) -> tuple:
  """Returns flight 'k' (from landing 'k' up to 'k' + 1): its lane (y
  from, to), where it starts and ends along x, and its heights there.
  Even flights climb east in the south lane, odd ones west in the
  north."""
  (x0, y0, _), (x1, y1, _) = STAIRWELL
  west, east = x0 + LANDING, x1 - LANDING
  if k % 2 == 0:
    return (y0, LANES[0] - LANES[1]), (west, east), (landingLevel(k),
                                                     landingLevel(k + 1))
  return (LANES[0] + LANES[1], y1), (east, west), (landingLevel(k),
                                                   landingLevel(k + 1))


def bodyOutside(point: tuple) -> float:
  """Returns how far 'point' is outside the rocket's body (its tank and
  capsule, a round column down to the ground), m."""
  x, y, z = point
  radius = BODY if z < FLOOR else capsuleRadius(z) + 0.05
  return (math.hypot(x, y) - radius) * (1.0 if z < FLOOR else LEAN)


def boxOutside(point: tuple, low: tuple, high: tuple) -> float:
  """Returns how far 'point' is outside the box from 'low' to 'high'
  (along the axis it is furthest out by; inside, less than nought)."""
  return -boxInside(point, low, high)


def groundsInside(point: tuple, top: bool, foot: bool) -> float:
  """Returns how far 'point' is inside the tower's rooms: the hall, the
  stairwell, the lift's shaft, the yard (outside the rocket's body and
  the stair tower), the stairwell's doorways, the lift's ('top', 'foot':
  its car there, its door open), m."""
  low, high = TOWER
  tower = ((low[0], low[1], GROUND - 1.0), (high[0], high[1], TOWER_TOP))
  yard = min(boxInside(point, *YARD), bodyOutside(point),
             boxOutside(point, *tower))
  rooms = [boxInside(point, *HALL), boxInside(point, *STAIRWELL),
           boxInside(point, *SHAFT), boxInside(point, *STAIR_TOP),
           boxInside(point, *STAIR_FOOT), yard]
  if top:
    rooms.append(boxInside(point, *LIFT_TOP))
  if foot:
    rooms.append(boxInside(point, *LIFT_FOOT))
  return max(rooms)


@functools.lru_cache(maxsize=1)
def towerSolids() -> tuple:
  """Returns the tower's still solids in the cabin's world (each its
  middle, half sizes, turn (w x y z) and velocity, still): the flights'
  ramps and the landings, the wall between the lanes, the steel tower's
  legs, the rocket's legs and feet."""
  out = []
  run = STAIRWELL[1][0] - STAIRWELL[0][0] - 2.0 * LANDING
  slope = math.atan2(rise(), run)
  long = math.hypot(run, rise())
  thick = 0.15
  for k in range(FLIGHTS):
    (y0, y1), (xa, xb), (za, zb) = flightOf(k)
    sign = 1.0 if xb > xa else -1.0
    angle = sign * slope
    normal = (-math.sin(angle), 0.0, math.cos(angle))
    middle = (0.5 * (xa + xb) - thick * normal[0],
              0.5 * (y0 + y1), 0.5 * (za + zb) - thick * normal[2])
    turn = (math.cos(0.5 * -angle), 0.0, math.sin(0.5 * -angle), 0.0)
    out.append((middle, (0.5 * long + 0.05, 0.5 * (y1 - y0), thick), turn,
                (0.0, 0.0, 0.0)))
  (x0, y0, _), (x1, y1, _) = STAIRWELL
  for k in range(1, FLIGHTS + 1):
    west = k % 2 == 0
    xa, xb = (x0, x0 + LANDING) if west else (x1 - LANDING, x1)
    level = landingLevel(k)
    out.append(((0.5 * (xa + xb), 0.5 * (y0 + y1), level - thick), (
      0.5 * (xb - xa), 0.5 * (y1 - y0), thick), (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0)))
  wall = (x0 + LANDING, x1 - LANDING)
  out.append(((0.5 * sum(wall), LANES[0], 0.5 * (GROUND + FLOOR + 3.0)), (
    0.5 * (wall[1] - wall[0]), LANES[1], 0.5 * (FLOOR + 3.0 - GROUND)),
              (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
  high = 0.5 * (FLOOR - 1.0 - GROUND)
  for x, y in TOWER_LEGS:
    out.append(((x, y, GROUND + high), (LEG_HALF, LEG_HALF, high),
                (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
  out += _rocketLegs()
  return tuple(out)


def _rocketLegs() -> list:
  """Returns the rocket's legs as solids: each strut (from the tank out
  and down to its foot) and its foot."""
  out = []
  low = -PAD_UP
  for foot in LEGS:
    flat = math.hypot(foot[0], foot[1])
    out_ = (foot[0] / flat, foot[1] / flat)
    top = (out_[0] * (RADIUS - 0.05 * SIZE), out_[1] * (RADIUS - 0.05 *
                                                        SIZE),
           low + 2.0 * SIZE + 0.6 * SIZE)
    bottom = (foot[0], foot[1], low + 0.25 * SIZE)
    way = tuple(b - t for b, t in zip(bottom, top))
    long = math.sqrt(sum(w * w for w in way))
    middle = tuple(0.5 * (b + t) for b, t in zip(bottom, top))
    tilt = math.acos(max(-1.0, min(1.0, -way[2] / long)))
    axis = (out_[1], -out_[0], 0.0)
    turn = (math.cos(0.5 * tilt), math.sin(0.5 * tilt) * axis[0],
            math.sin(0.5 * tilt) * axis[1], 0.0)
    out.append((middle, (0.12 * SIZE, 0.12 * SIZE, 0.5 * long), turn,
                (0.0, 0.0, 0.0)))
    out.append(((foot[0], foot[1], low + 0.125 * SIZE), (
      0.32 * SIZE, 0.32 * SIZE, 0.125 * SIZE), (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0)))
  return out
