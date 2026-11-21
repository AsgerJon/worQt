"""
The rocket's rooms and the space station's, as Asger goes up and
aboard (user, 2026-11-17: "all aboard Asger's kolonihave i rummet!";
2026-11-19: "Asger starts at level 0 of the rocket where he has his
hygge. We then add an empty floor in the middle, and a top floor at the
top. Now, the top floor has four doors in each direction. On Terra Prime
the center room between the spokes is gone. Instead, the head our
rocket insert itself here, so that the spokes align with the doors to
our top floor"): their rooms in the docked rocket's own axes. Docked,
the rocket's head is in the station's drum on its axis (nose down it),
its top floor's doors facing the four shafts, so the rocket and the
station turn as one: Asger's world stays the rocket's, only larger,
and what he feels there (its turning: the station's) is the station's
gravity by itself, nothing added.

Each room says how far a point is inside it ('insideOf' a room: less
than nought, outside); the rooms joined ('roomsInside') are inside as
far as the room it is deepest in. The rocket's: the cabin (level 0, the
capsule's frustum, as the kernel has it), levels 1 and 2 (round rooms
in the head), the hatches through the slabs between them; docked also
the top floor's four doorways (through its wall, over the gap to the
drum's hole, into the shafts' mouths: the doors' leaves are solids,
'_shaftdoor'), each shaft's cage's inside where the cage is (the spokes
are open girders in vacuum, user 2026-11-19: "Only the elevators are"
pressurised: 'cages', each from, to along its shaft) and the ring (its
tube's inside, under its deck). The rocket's own z runs up its
nose: the station's plane lies 'PLANE' up it (the top floor's middle),
the station's z down it. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._levels import CEILING, CONE, DOOR_HALF_HIGH, DOOR_HALF_SPAN
from ._levels import DOOR_WAYS, DOORS_HIGH, FLOOR, HATCH, HEAD, LEVELS
from ._levels import WALL
from ._stationmeshes import FLOOR_RADIUS, SHAFT, SOCKET, SPOKES, TUBE
from ._stationmeshes import TUBE_MIDDLE

#  The station's plane up the rocket's own z when docked (the top
#  floor's middle: its doors face the shafts), m; the station's z is
#  'PLANE' less the rocket's.
PLANE = DOORS_HIGH
#  Two rooms meeting at a plane are nought deep there (his box rising up
#  the axis stopped dead on it, the user's let's play, 2026-11-18): each
#  room joining another reaches 'SEAM' m into it, m.
SEAM = 1.0
#  The station's walls inside, m: its hull's thickness.
HULL_WALL = 1.0
#  The rooms' sizes inside (m): the head's levels (radius), the hatches
#  through the slabs (from a little under each, to a little over it);
#  the top floor's doorways (each half as wide as its door, half as
#  high; from inside the head's wall out over the gap into its shaft's
#  mouth, along its door's way); the shafts (radius, from the drum's
#  hole to the deck), the ring's tube (radius), the deck (its distance
#  from the axis: one g at the station's turn).
LEVEL_INSIDE = HEAD - WALL
HATCHES = tuple((LEVELS[k][1] - SEAM, LEVELS[k + 1][0] + SEAM)
                for k in range(len(LEVELS) - 1))
DOORWAY_HALF = (LEVEL_INSIDE * math.sin(math.radians(DOOR_HALF_SPAN)),
                DOOR_HALF_HIGH)
DOORWAY = (LEVEL_INSIDE - SEAM, SOCKET + SEAM)
SHAFT_INSIDE = SHAFT
SHAFT_FROM = SOCKET
TUBE_INSIDE = TUBE - HULL_WALL
DECK = FLOOR_RADIUS
#  The cabin's inside, as the kernel has it.
CABIN_LOW = HEAD + CONE * (CEILING - FLOOR) - WALL
CABIN_SLOPE = -CONE


def shaftWays(relative: tuple) -> tuple:
  """Returns the four shafts' ways out from the axis in the docked
  rocket's own axes ('relative': its own axes in the station's,
  '_dockingport.DockingPort.relative')."""
  count = SPOKES[0]
  return tuple(stationWay((math.cos(2.0 * math.pi * k / count), math.sin(
    2.0 * math.pi * k / count), 0.0), relative) for k in range(count))


def cabinInside(point: tuple) -> float:
  """Returns how far 'point' is inside the cabin (level 0: its floor,
  its ceiling, its cone of a wall), m."""
  x, y, z = point
  across = math.hypot(x, y)
  inner = CABIN_LOW + CABIN_SLOPE * min(max(z - FLOOR, 0.0),
                                        CEILING - FLOOR)
  lean = 1.0 / math.sqrt(1.0 + CABIN_SLOPE * CABIN_SLOPE)
  return min(z - FLOOR, CEILING - z, (inner - across) * lean)


def tubeInside(point: tuple, radius: float, low: float,
               high: float) -> float:
  """Returns how far 'point' is inside a round room on the axis
  ('radius', from 'low' to 'high' up it), m."""
  x, y, z = point
  return min(radius - math.hypot(x, y), z - low, high - z)


def shaftDoorwayInside(point: tuple, way: tuple) -> float:
  """Returns how far 'point' is inside the top floor's doorway out
  along 'way' (one of '_levels.DOOR_WAYS': a box along it), m."""
  x, y, z = point
  out = x * way[0] + y * way[1]
  side = -x * way[1] + y * way[0]
  return min(out - DOORWAY[0], DOORWAY[1] - out,
             DOORWAY_HALF[0] - abs(side),
             DOORWAY_HALF[1] - abs(z - DOORS_HIGH))


def shaftInside(point: tuple, way: tuple, span: tuple) -> float:
  """Returns how far 'point' is inside the shaft out along 'way' where
  its cage is ('span': from, to along it; never nearer than the drum's
  hole, 'SHAFT_FROM'), m."""
  x, y, z = point
  low, high = max(SHAFT_FROM, span[0]), span[1]
  out = x * way[0] + y * way[1]
  along = min(max(out, low), max(low, high))
  across = math.dist(point, (along * way[0], along * way[1], PLANE))
  return min(SHAFT_INSIDE - across, out - low, high - out)


def ringInside(point: tuple) -> float:
  """Returns how far 'point' is inside the ring's tube over its deck,
  m."""
  x, y, z = point
  across = math.hypot(x, y)
  return min(TUBE_INSIDE - math.hypot(across - TUBE_MIDDLE, z - PLANE),
             DECK - across)


def rocketInside(point: tuple) -> float:
  """Returns how far 'point' is inside the rocket's rooms (its three
  levels and the hatches between them; not the doorways), m."""
  inside = cabinInside(point)
  for low, high in LEVELS[1:]:
    inside = max(inside, tubeInside(point, LEVEL_INSIDE, low, high))
  for low, high in HATCHES:
    inside = max(inside, tubeInside(point, HATCH, low, high))
  return inside


def roomsInside(point: tuple, docked: bool, ways: tuple,
                cages: tuple) -> float:
  """Returns how far 'point' is inside the rooms Asger may be in: the
  rocket's, and docked the top floor's doorways, the cages' insides
  along the shafts out along 'ways' ('cages': each from, to along its
  shaft) and the ring (as far as the room it is deepest in), m."""
  inside = rocketInside(point)
  if not docked:
    return inside
  inside = max(inside, ringInside(point))
  for way in DOOR_WAYS:
    inside = max(inside, shaftDoorwayInside(point, way))
  for way, span in zip(ways, cages):
    inside = max(inside, shaftInside(point, way, span))
  return inside


def roomOf(point: tuple, ways: tuple, cages: tuple) -> str:
  """Returns the room 'point' is deepest in, docked: 'cabin', 'level 1',
  'level 2', 'hatch', 'doorway', 'shaft' (a cage's inside: 'cages' as
  'roomsInside'), 'ring' ('' none)."""
  rooms = [('cabin', cabinInside(point))]
  rooms += [('level %d' % k, tubeInside(point, LEVEL_INSIDE, low, high))
            for k, (low, high) in enumerate(LEVELS) if k > 0]
  rooms += [('hatch', tubeInside(point, HATCH, low, high))
            for low, high in HATCHES]
  rooms += [('doorway', shaftDoorwayInside(point, way)) for way in DOOR_WAYS]
  rooms += [('ring', ringInside(point))]
  rooms += [('shaft', shaftInside(point, way, span))
            for way, span in zip(ways, cages)]
  name, inside = max(rooms, key=lambda pair: pair[1])
  return name if inside > 0.0 else ''


def stationPoint(point: tuple, relative: tuple) -> tuple:
  """Returns 'point' (the station's own axes, m from its middle) in the
  docked rocket's own axes ('relative': its axes in the station's; the
  rocket's middle lies on the station's axis 'PLANE' from it, against
  its own z: docked from either side, the station's middle is 'PLANE'
  up the rocket's z)."""
  middle = tuple(-PLANE * z for z in relative[2])
  return stationWay(tuple(p - m for p, m in zip(point, middle)), relative)


def stationWay(way: tuple, relative: tuple) -> tuple:
  """Returns 'way' (the station's own axes) in the docked rocket's own
  axes ('relative': its axes in the station's)."""
  return tuple(sum(a * b for a, b in zip(way, column))
               for column in relative)
