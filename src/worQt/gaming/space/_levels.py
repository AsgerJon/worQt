"""
The rocket's three levels (user, 2026-11-19: "Asger starts at level 0
of the rocket where he has his hygge. We then add an empty floor in the
middle, and a top floor at the top. Now, the top floor has four doors in
each direction. On Terra Prime the center room between the spokes is
gone. Instead, the head our rocket insert itself here, so that the
spokes align with the doors to our top floor"): its capsule from the
tank up, in the vessel's own axes (z its nose, m from its middle).
Level 0 is the cabin as it was, under the capsule's cone (its wall
narrows as before) up to its ceiling, where the cone has narrowed to
the head's radius; levels 1 (empty) and 2 (the top floor) in the head,
a round tower 'HEAD' m round over it, a slab between each two with a
round hatch through it on the axis; the head's roof, then its nose's
blunt cone up to the tip. The top floor's four doors face the vessel's
own x, y, -x and -y, round its middle's height ('DOORS_HIGH': docked,
the station's plane runs there, its four shafts out of the doors).
The ladder up the axis through the hatches is '_ladder''s. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._vessel import CAPSULE, CENTRE, RADIUS, SIZE

#  Level 0's floor (the tank's top); how fast the capsule's cone narrows
#  going up (m round a m: as it always did, from the rocket's radius at
#  the floor to 0.45 sizes 10.4 m up); the head's radius (outside); the
#  walls' thickness, m.
FLOOR = CAPSULE[0] - CENTRE
CONE = (RADIUS - 0.45 * SIZE) / (CAPSULE[1] - 0.4 * SIZE - CAPSULE[0])
HEAD = 4.0
WALL = 0.05
#  Level 0's ceiling: where the cone has narrowed to the head's radius;
#  the slabs' thickness, levels 1's and 2's height inside, m; each
#  level's floor and ceiling; the head's roof (over the top floor's
#  ceiling), its nose's tip and the tip's radius.
CEILING = FLOOR + (RADIUS - HEAD) / CONE
SLAB = 0.25
STOREY = 3.0
LEVELS = ((FLOOR, CEILING),
          (CEILING + SLAB, CEILING + SLAB + STOREY),
          (CEILING + 2.0 * SLAB + STOREY,
           CEILING + 2.0 * SLAB + 2.0 * STOREY))
ROOF = LEVELS[2][1] + SLAB
TIP = CAPSULE[1] - CENTRE
TIP_RADIUS = 0.05 * SIZE
#  The hatches through the slabs on the axis, m round.
HATCH = 0.8
#  The top floor's doors: their ways out (the vessel's own x, y, -x, -y;
#  each at 'DOOR_ANGLES' deg round from x toward y), half their span
#  round the wall (deg: its edges on the hull's 2 deg steps, '_cabin'),
#  their middles' height (the top floor's middle: docked, the station's
#  plane) and half their height, m.
DOOR_ANGLES = (0.0, 90.0, 180.0, 270.0)
DOOR_WAYS = tuple((math.cos(math.radians(a)), math.sin(math.radians(a)),
                   0.0) for a in DOOR_ANGLES)
DOOR_HALF_SPAN = 8.0
DOORS_HIGH = 0.5 * (LEVELS[2][0] + LEVELS[2][1])
DOOR_HALF_HIGH = 1.05
TOP_DOORS = tuple(((a - DOOR_HALF_SPAN, a + DOOR_HALF_SPAN), (
  DOORS_HIGH - DOOR_HALF_HIGH, DOORS_HIGH + DOOR_HALF_HIGH))
                  for a in DOOR_ANGLES)


def hullRadius(z: float) -> float:
  """Returns the capsule's outer radius at height 'z' (the vessel's own
  axes; held at the rocket's radius under the floor), m: the cone up to
  level 0's ceiling, the head up to its roof, the nose's cone to its
  tip."""
  if z <= CEILING:
    return RADIUS - CONE * max(0.0, z - FLOOR)
  if z <= ROOF:
    return HEAD
  share = min(1.0, (z - ROOF) / (TIP - ROOF))
  return HEAD + share * (TIP_RADIUS - HEAD)


def hullSlope(z: float) -> float:
  """Returns how fast the capsule's outer radius narrows going up at
  height 'z' (m round a m; at a kink, the part above's)."""
  if z < CEILING:
    return CONE
  if z < ROOF:
    return 0.0
  return (HEAD - TIP_RADIUS) / (TIP - ROOF)


def levelOf(z: float) -> int:
  """Returns the level whose room height 'z' is in (nought, one, two;
  in a slab, the one under it; under level 0, nought; over the top
  floor, two)."""
  for k in (2, 1):
    if z >= LEVELS[k][0]:
      return k
  return 0


def doorMiddle(k: int) -> tuple:
  """Returns the middle of top floor door 'k''s opening in the wall (its
  middle's radius, the vessel's own axes)."""
  way = DOOR_WAYS[k]
  far = HEAD - 0.5 * WALL
  return far * way[0], far * way[1], DOORS_HIGH
