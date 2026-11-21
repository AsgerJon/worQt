"""
The station's solids and the rocket's hull as the flight kernel meets
them (user, 2026-11-17: the station, "Get the docking!"; a bad approach
passed straight through it): the station as simple solids in its own
axes (the ring a torus, the drum on its axis a round block with the
socket's hole through it (2026-11-19: a docked rocket's head is in
it), the spokes, antennas and beacons capsules and balls; the collars,
the windows and the elevators' shafts left out: thin, or inside), the
rocket as a chain of balls along its hull (the plug, the tank, the
capsule's cone, its head and nose) and its feet. How far a point is
from a solid ('solidDistance', the kernel's line for line) and the
least it could be however the station has turned ('sweptDistance': a
frame's quick look which solids are near). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._levels import CEILING, FLOOR, HEAD, ROOF, TIP, TIP_RADIUS
from ._stationmeshes import ANTENNA, BEACON, DRUM, DRUM_HALF, FLOOR_RADIUS
from ._stationmeshes import HULL, SOCKET, SPOKES, TUBE, TUBE_MIDDLE
from ._stationmeshes import beaconTips
from ._vessel import CENTRE, LEGS, PLUG, RADIUS, SIZE, TANK

#  The solids' kinds: a torus round the own z (its middle's radius in a's
#  x), a cylinder along the own z (from a's z to b's z), a capsule from
#  a to b (a ball where they meet), a hollow cylinder along the own z
#  (its hole's radius in a's x; from a's z to b's z: the drum).
TORUS, CYLINDER, CAPSULE, HOLLOW = 0, 1, 2, 3
#  The hull's balls: the plug's at these shares of its height (each
#  touching its cone); along the tank every 'TANK_STEP' m; up the
#  capsule (its cone, its head, its nose to the tip) every 'CONE_STEP'
#  m, each as big as fits in it there, none smaller than 'SMALLEST' m.
PLUG_SHARES = (0.2, 0.5, 0.8)
TANK_STEP = 2.0
CONE_STEP = 0.5
SMALLEST = 0.3
#  The head's round edge under its roof (the balls up the axis are
#  narrowed by the nose's cone there): a ring of 'RIM_BALLS' balls, each
#  'RIM' m round, touching the head's wall and its roof.
RIM_BALLS = 8
RIM = 1.0
#  The capsule's outline up its side (out from the axis, up it), m.
OUTLINE = ((RADIUS, FLOOR), (HEAD, CEILING), (HEAD, ROOF),
           (TIP_RADIUS, TIP), (0.0, TIP))
#  The feet's balls' radius, m, and how far over the feet they sit.
FOOT = 0.3 * SIZE
FOOT_UP = 0.15 * SIZE


def stationSolids() -> tuple:
  """Returns the station's solids, its own axes: (kind, a, b, radius)
  each, at most 32 (a frame's near ones are bits of an int)."""
  solids = [(TORUS, (TUBE_MIDDLE, 0.0, 0.0), (0.0, 0.0, 0.0), TUBE),
            (HOLLOW, (SOCKET, 0.0, -DRUM_HALF), (0.0, 0.0, DRUM_HALF),
             DRUM)]
  count, thick = SPOKES
  for k in range(count):
    a = 2.0 * math.pi * k / count
    way = (math.cos(a), math.sin(a), 0.0)
    solids.append((CAPSULE, tuple(DRUM * w for w in way), tuple(
      (TUBE_MIDDLE - 0.5 * TUBE) * w for w in way), thick))
  long, radius = ANTENNA
  out = FLOOR_RADIUS + HULL
  for k in range(count):
    a = 2.0 * math.pi * (k + 0.5) / count
    way = (math.cos(a), math.sin(a), 0.0)
    solids.append((CAPSULE, tuple(out * w for w in way), tuple(
      (out + long) * w for w in way), radius))
  for tip in beaconTips():
    solids.append((CAPSULE, tip, tip, BEACON))
  return tuple(solids)


def hullBalls() -> tuple:
  """Returns the rocket's hull as balls (x, y, z, radius; its own axes,
  m from its middle): the plug's two, the tank's every 'TANK_STEP' m,
  up the capsule's cone, head and nose (each as big as fits inside the
  outline there, 'OUTLINE'), a ring round the head's edge under its roof,
  the four feet's."""
  low = -CENTRE
  balls = []
  slope = math.atan((0.9 * RADIUS - 0.35 * SIZE) / (PLUG[1] - PLUG[0]))
  for share in PLUG_SHARES:
    z = low + PLUG[0] + share * (PLUG[1] - PLUG[0])
    balls.append((0.0, 0.0, z, (0.35 * SIZE + share * (
      0.9 * RADIUS - 0.35 * SIZE)) * math.cos(slope)))
  z = low + TANK[0] + TANK_STEP
  while z <= low + TANK[1] - TANK_STEP + 1e-9:
    balls.append((0.0, 0.0, z, RADIUS))
    z += TANK_STEP
  z = FLOOR
  while z < TIP:
    radius = min(_toSegment(z, one, two) for one, two in zip(
      OUTLINE[:-1], OUTLINE[1:]))
    if radius < SMALLEST:
      break
    balls.append((0.0, 0.0, z, radius))
    z += CONE_STEP
  out = HEAD - RIM
  for k in range(RIM_BALLS):
    a = 2.0 * math.pi * k / RIM_BALLS
    balls.append((out * math.cos(a), out * math.sin(a), ROOF - RIM, RIM))
  for x, y, z in LEGS:
    balls.append((x, y, z + FOOT_UP, FOOT))
  return tuple(balls)


def hullReach() -> float:
  """Returns how far the hull reaches from the rocket's middle, m."""
  return max(math.sqrt(x * x + y * y + z * z) + r
             for x, y, z, r in hullBalls())


def solidDistance(solid: tuple, point: tuple) -> float:
  """Returns how far 'point' (the station's own axes) is out of 'solid'
  (less than nought: inside), m."""
  kind, a, b, radius = solid
  x, y, z = point
  if kind == TORUS:
    return math.hypot(math.hypot(x, y) - a[0], z) - radius
  if kind in (CYLINDER, HOLLOW):
    flat = math.hypot(x, y)
    across = flat - radius
    if kind == HOLLOW:
      across = max(across, a[0] - flat)
    along = max(a[2] - z, z - b[2])
    return min(max(across, along), 0.0) + math.hypot(max(across, 0.0),
                                                     max(along, 0.0))
  return math.dist(point, _nearestOn(a, b, point)) - radius


def sweptDistance(solid: tuple, point: tuple) -> float:
  """Returns the least 'solidDistance' could be however the station has
  turned about its own z, m: how far 'point' is in its distance from the
  axis and along it from what the solid sweeps."""
  kind, a, b, radius = solid
  x, y, z = point
  if kind != CAPSULE:
    return solidDistance(solid, point)
  flat = (math.hypot(x, y), z, 0.0)
  return solidDistance((CAPSULE, (math.hypot(a[0], a[1]), a[2], 0.0), (
    math.hypot(b[0], b[1]), b[2], 0.0), radius), flat)


def _nearestOn(a: tuple, b: tuple, point: tuple) -> tuple:
  """Returns the point of the segment 'a' 'b' nearest 'point'."""
  ab = tuple(q - p for p, q in zip(a, b))
  long2 = sum(c * c for c in ab)
  share = 0.0
  if long2 > 0.0:
    share = min(1.0, max(0.0, sum((p - q) * c for p, q, c in zip(
      point, a, ab)) / long2))
  return tuple(p + share * c for p, c in zip(a, ab))


def _toSegment(z: float, one: tuple, two: tuple) -> float:
  """Returns how far the axis's point at height 'z' is from the
  outline's piece from 'one' to 'two' (each out, up), m."""
  (r0, z0), (r1, z1) = one, two
  dr, dz = r1 - r0, z1 - z0
  long2 = dr * dr + dz * dz
  share = 0.0
  if long2 > 0.0:
    share = min(1.0, max(0.0, ((0.0 - r0) * dr + (z - z0) * dz) / long2))
  return math.hypot(r0 + share * dr, z0 + share * dz - z)
