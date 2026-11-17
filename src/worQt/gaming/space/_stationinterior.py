"""
The space station's inside, as Asger goes aboard (user, 2026-11-17:
"all aboard Asger's kolonihave i rummet!"; the plan: up out of the
cabin through a hatch in the nose, the docking port, the hub weightless
on the axis, an elevator down each spoke, the ring's deck at one g):
its rooms in the docked rocket's own axes. Docked, the rocket's nose is
in the port and its axis is the station's (nose down it), so the rocket
and the station turn as one: Asger's world stays the rocket's, only
larger, and what he feels there (its turning: the station's) is the
station's gravity by itself, nothing added.

Each room says how far a point is inside it ('insideOf' a room: less
than nought, outside); the rooms joined ('roomsInside') are inside as
far as the room it is deepest in. The cabin (the capsule's frustum, as
the kernel has it); docked also the hatch through the nose, the port,
the hub, the four shafts (the spokes: their elevators) and the ring (its
tube's inside, under its deck). The rocket's own z runs up its nose: the
station's plane lies 'PLANE' up it, the station's z down it. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import FLOOR, NOSE, WALL, capsuleRadius
from ._dockingport import NOSE_PORT
from ._stationmeshes import FLOOR_RADIUS, HUB, PORT, SPOKES, TUBE
from ._stationmeshes import TUBE_MIDDLE, portTip

#  The station's walls inside, m: its hull's thickness; the hatch's
#  radius through the rocket's nose (from a little inside the cabin to a
#  little into the port).
HULL_WALL = 1.0
HATCH = 0.8
HATCH_LOW = NOSE - 1.0
HATCH_HIGH = NOSE_PORT[2] + 1.0
#  The station's plane up the rocket's own z when docked (its nose tip in
#  the port's mouth), m; the station's z is 'PLANE' less the rocket's.
PLANE = NOSE_PORT[2] + portTip()[2]
#  The rooms' sizes inside (m): the port, the hub (radius; from its end
#  by the port to its far end, up the rocket's z), the shafts (radius,
#  from 'SHAFT_FROM' off the axis to the deck), the ring's tube (radius),
#  the deck (its distance from the axis: one g at the station's turn).
PORT_INSIDE = PORT[0] - HULL_WALL
PORT_LOW, PORT_HIGH = NOSE_PORT[2], PLANE - 0.5 * HUB[1] + HULL_WALL
HUB_INSIDE = HUB[0] - HULL_WALL
HUB_LOW = PLANE - 0.5 * HUB[1] + HULL_WALL
HUB_HIGH = PLANE + 0.5 * HUB[1] - HULL_WALL
SHAFT_INSIDE = SPOKES[1] - HULL_WALL
SHAFT_FROM = 0.5 * HUB[0]
TUBE_INSIDE = TUBE - HULL_WALL
DECK = FLOOR_RADIUS
#  The cabin's inside, as the kernel has it.
CABIN_LOW = capsuleRadius(FLOOR) - WALL
CABIN_SLOPE = (capsuleRadius(NOSE) - capsuleRadius(FLOOR)) / (NOSE - FLOOR)


def shaftWays(relative: tuple) -> tuple:
  """Returns the four shafts' ways out from the axis in the docked
  rocket's own axes ('relative': its own axes in the station's,
  '_dockingport.DockingPort.relative')."""
  count = SPOKES[0]
  return tuple(stationWay((math.cos(2.0 * math.pi * k / count), math.sin(
    2.0 * math.pi * k / count), 0.0), relative) for k in range(count))


def cabinInside(point: tuple) -> float:
  """Returns how far 'point' is inside the cabin (its floor, its
  ceiling, its cone of a wall), m."""
  x, y, z = point
  across = math.hypot(x, y)
  inner = CABIN_LOW + CABIN_SLOPE * min(max(z - FLOOR, 0.0), NOSE - FLOOR)
  lean = 1.0 / math.sqrt(1.0 + CABIN_SLOPE * CABIN_SLOPE)
  return min(z - FLOOR, NOSE - z, (inner - across) * lean)


def tubeInside(point: tuple, radius: float, low: float,
               high: float) -> float:
  """Returns how far 'point' is inside a round room on the axis
  ('radius', from 'low' to 'high' up it), m."""
  x, y, z = point
  return min(radius - math.hypot(x, y), z - low, high - z)


def shaftInside(point: tuple, way: tuple) -> float:
  """Returns how far 'point' is inside the shaft out along 'way' (from
  'SHAFT_FROM' to the deck), m."""
  x, y, z = point
  out = x * way[0] + y * way[1]
  along = min(max(out, SHAFT_FROM), DECK)
  across = math.dist(point, (along * way[0], along * way[1], PLANE))
  return min(SHAFT_INSIDE - across, DECK - math.hypot(x, y))


def ringInside(point: tuple) -> float:
  """Returns how far 'point' is inside the ring's tube over its deck,
  m."""
  x, y, z = point
  across = math.hypot(x, y)
  return min(TUBE_INSIDE - math.hypot(across - TUBE_MIDDLE, z - PLANE),
             DECK - across)


def roomsInside(point: tuple, docked: bool, ways: tuple) -> float:
  """Returns how far 'point' is inside the rooms Asger may be in: the
  cabin, and docked the hatch, the port, the hub, the shafts out along
  'ways' and the ring (as far as the room it is deepest in), m."""
  inside = cabinInside(point)
  if not docked:
    return inside
  inside = max(inside, tubeInside(point, HATCH, HATCH_LOW, HATCH_HIGH),
               tubeInside(point, PORT_INSIDE, PORT_LOW, PORT_HIGH),
               tubeInside(point, HUB_INSIDE, HUB_LOW, HUB_HIGH),
               ringInside(point))
  for way in ways:
    inside = max(inside, shaftInside(point, way))
  return inside


def roomOf(point: tuple, ways: tuple) -> str:
  """Returns the room 'point' is deepest in, docked: 'cabin', 'hatch',
  'port', 'hub', 'shaft', 'ring' ('' none)."""
  rooms = [('cabin', cabinInside(point)),
           ('hatch', tubeInside(point, HATCH, HATCH_LOW, HATCH_HIGH)),
           ('port', tubeInside(point, PORT_INSIDE, PORT_LOW, PORT_HIGH)),
           ('hub', tubeInside(point, HUB_INSIDE, HUB_LOW, HUB_HIGH)),
           ('ring', ringInside(point))]
  rooms += [('shaft', shaftInside(point, way)) for way in ways]
  name, inside = max(rooms, key=lambda pair: pair[1])
  return name if inside > 0.0 else ''


def stationPoint(point: tuple, relative: tuple) -> tuple:
  """Returns 'point' (the station's own axes, m from its middle) in the
  docked rocket's own axes ('relative': its axes in the station's; the
  rocket's middle lies on the station's axis 'PLANE' up it)."""
  return stationWay((point[0], point[1], point[2] - PLANE), relative)


def stationWay(way: tuple, relative: tuple) -> tuple:
  """Returns 'way' (the station's own axes) in the docked rocket's own
  axes ('relative': its axes in the station's)."""
  return tuple(sum(a * b for a, b in zip(way, column))
               for column in relative)
