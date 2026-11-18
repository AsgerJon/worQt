"""
The station's solids and the rocket's hull as the flight kernel meets
them (user, 2026-11-17: the station, "Get the docking!"; a bad approach
passed straight through it): the station as simple solids in its own
axes (the ring a torus, the hub and its two ports cylinders on its axis,
the spokes, antennas and beacons capsules and balls; the port's collar, the
windows and the elevators' shafts left out: thin, or inside), the
rocket as a chain of balls along its hull (the plug, the tank, the
capsule's cone and nose) and its feet. How far a point is from a solid
('solidDistance', the kernel's line for line) and the least it could be
however the station has turned ('sweptDistance': a frame's quick look
which solids are near). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import FLOOR, NOSE
from ._stationmeshes import ANTENNA, BEACON, FLOOR_RADIUS, HUB, HULL, PORT
from ._stationmeshes import SPOKES, TUBE, TUBE_MIDDLE, beaconTips
from ._vessel import CENTRE, LEGS, PLUG, RADIUS, SIZE, TANK

#  The solids' kinds: a torus round the own z (its middle's radius in a's
#  x), a cylinder along the own z (from a's z to b's z), a capsule from
#  a to b (a ball where they meet).
TORUS, CYLINDER, CAPSULE = 0, 1, 2
#  The hull's balls: the plug's at these shares of its height (each
#  touching its cone); along the tank every 'TANK_STEP' m; up the capsule's
#  cone and its nose (its tip 'TIP' over the capsule's top, its radius
#  there 'TIP_RADIUS' m) every 'CONE_STEP' m, none smaller than
#  'SMALLEST' m.
PLUG_SHARES = (0.2, 0.5, 0.8)
TANK_STEP = 2.0
TIP = 0.4 * SIZE
TIP_RADIUS = 0.05 * SIZE
CONE_STEP = 1.0
SMALLEST = 0.3
#  The feet's balls' radius, m, and how far over the feet they sit.
FOOT = 0.3 * SIZE
FOOT_UP = 0.15 * SIZE


def stationSolids() -> tuple:
  """Returns the station's solids, its own axes: (kind, a, b, radius)
  each, at most 32 (a frame's near ones are bits of an int)."""
  half = 0.5 * HUB[1]
  solids = [(TORUS, (TUBE_MIDDLE, 0.0, 0.0), (0.0, 0.0, 0.0), TUBE),
            (CYLINDER, (0.0, 0.0, -half), (0.0, 0.0, half), HUB[0]),
            (CYLINDER, (0.0, 0.0, half), (0.0, 0.0, half + PORT[1]),
             PORT[0]),
            (CYLINDER, (0.0, 0.0, -half - PORT[1]), (0.0, 0.0, -half),
             PORT[0])]
  count, thick = SPOKES
  for k in range(count):
    a = 2.0 * math.pi * k / count
    way = (math.cos(a), math.sin(a), 0.0)
    solids.append((CAPSULE, tuple(0.5 * HUB[0] * w for w in way), tuple(
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
  up the capsule's cone and nose (each touching the cone, never past it
  nor past the tip), the four feet's."""
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
  wall = math.atan((RADIUS - _coneRadius(NOSE)) / (NOSE - FLOOR))
  slope = (_coneRadius(NOSE) - TIP_RADIUS) / TIP
  z = FLOOR
  while True:
    side = (RADIUS - (z - FLOOR) * math.tan(wall)) * math.cos(wall)
    nose = (_coneRadius(NOSE) - (z - NOSE) * slope) * math.cos(
      math.atan(slope))
    radius = min(side, nose)
    if radius < SMALLEST or z + radius > NOSE + TIP:
      break
    balls.append((0.0, 0.0, z, radius))
    z += CONE_STEP
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
  if kind == CYLINDER:
    across = math.hypot(x, y) - radius
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


def _coneRadius(z: float) -> float:
  """Returns the capsule cone's outer radius at height 'z' (the vessel's
  own axes; the cockpit's 'capsuleRadius'), m."""
  from ._cockpit import capsuleRadius
  return capsuleRadius(z)
