"""
The launch tower, its walkway and the door's meshes (user, 2026-11-17:
"The door out of the rocket should be connected to a retractable walk
way"; '_walkway'), Qt-free, rows of eight (place, normal, where on a
picture), each by its look:
- 'towerParts': the tower on the pad (the pad's own axes: x east, y
  north, z up from the ground): four red steel legs braced every storey
  up to the platform at the cabin's floor, its grating, the cage round
  it (open to the walkway, the lift's door at its back), floodlights on
  its posts;
- 'armParts': the walkway in its own axes (from its pivot at the
  tower's platform, x out to the rocket): a glazed tunnel on a grating
  floor, a lamp along its roof, the rubber hood round the door, the
  door's panel on its wall by the door ('OUTSIDE_PANEL');
- 'leafRows': the door's leaf in the rocket's own axes, closed (it
  slides round the axis into the wall);
- 'insideParts': by the door inside, the panel with its keys
  ('INSIDE_KEYS') and the warning placard ('PLACARD').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._cockpit import FLOOR, WALL, capsuleRadius
from ._shapes import UNTURNED, boxRows, joined, quadRows
from ._walkway import DOOR_HIGH, DOOR_SPAN, PAD_UP, PLATFORM_FAR
from ._walkway import PLATFORM_HALF, SLOPE, TUNNEL_FROM, TUNNEL_HALF
from ._walkway import TUNNEL_HIGH

#  The platform's height over the ground (the cabin's floor), m.
DECK = FLOOR + PAD_UP
#  The tower's legs (half their thickness), its storeys (m), its braces'
#  half thickness, how far its posts rise over the platform, m.
LEG = 0.18
STOREY = 4.0
BRACE = 0.06
POSTS = 3.0
#  The cage round the platform: its bars' spacing and height, m.
BAR_EVERY = 0.25
CAGE_HIGH = 2.3
#  The walkway: how far it reaches from its pivot to the hull (the skin
#  at the floor), its walls' thickness, its windows' sill and head over
#  its floor, the mullions' spacing, m.
ARM_LONG = TUNNEL_FROM * -1.0 - capsuleRadius(FLOOR)
SKIN = 0.06
SILL, HEAD = 0.9, 2.0
MULLION_EVERY = 1.0
#  The door's panel outside, on the walkway's left wall by the door (its
#  middle in the rocket's own axes; its half sizes), the panel inside by
#  the door (the wall's angle (deg), height over the floor) and its keys
#  (name, key, action, across the panel from its middle, m), the warning
#  placard (the wall's angle, height of its middle, half its sizes), m.
OUTSIDE_PANEL = ((TUNNEL_FROM + ARM_LONG - 1.0, TUNNEL_HALF - 0.02,
                  FLOOR + 1.2), (0.12, 0.16, 0.02))
INSIDE_AT = (168.0, 1.25)
INSIDE_KEYS = (('DOOR', 'E', 'door', -0.08),
               ('LOCK', 'E', 'lock', 0.0),
               ('WALKWAY', 'E', 'walkway', 0.08))
KEY_HALF = (0.025, 0.025, 0.012)
PLACARD = (160.5, 1.5, (0.21, 0.297))


@functools.lru_cache(maxsize=1)
def towerParts() -> dict:
  """Returns the tower's meshes by look (the pad's own axes)."""
  parts = {}

  def put(look: str, mesh: tuple) -> None:
    """Adds 'mesh' to 'look''s."""
    parts.setdefault(look, []).append(mesh)

  x0, x1, half = PLATFORM_FAR, TUNNEL_FROM, PLATFORM_HALF
  corners = ((x0, -half), (x0, half), (x1, -half), (x1, half))
  top = DECK + POSTS
  for x, y in corners:
    put('tower', boxRows((x, y, 0.5 * top), (LEG, LEG, 0.5 * top),
                         UNTURNED))
  sides = (((x0, -half), (x1, -half)), ((x0, half), (x1, half)),
           ((x0, -half), (x0, half)), ((x1, -half), (x1, half)))
  storeys = int(DECK // STOREY)
  for k in range(storeys + 1):
    z = min(DECK - 0.4, STOREY * (k + 1))
    for (ax, ay), (bx, by) in sides:
      put('tower', _beam((ax, ay, z), (bx, by, z), BRACE + 0.02))
      if k < storeys:
        low = z - STOREY if k else 0.3
        a, b = ((ax, ay, low), (bx, by, z)) if k % 2 else (
          (bx, by, low), (ax, ay, z))
        put('tower', _beam(a, b, BRACE))
  put('grating', boxRows((0.5 * (x0 + x1), 0.0, DECK - 0.075),
                         (0.5 * (x1 - x0) + 0.1, half + 0.1, 0.075),
                         UNTURNED))
  _cage(put, x0, x1, half)
  for y in (-half, half):
    put('lamp body', boxRows((x1, y, top + 0.25), (0.25, 0.35, 0.25),
                             UNTURNED))
    put('lamp', quadRows((x1 + 0.252, y, top + 0.25), ((0.0, 1.0, 0.0),
                                                       (0.0, 0.0, 1.0),
                                                       (1.0, 0.0, 0.0)),
                         (0.3, 0.2)))
  put('lift', boxRows((x0 - 0.05, 0.0, DECK + 1.05), (0.04, 0.55, 1.05),
                      UNTURNED))
  return {look: joined(meshes) for look, meshes in parts.items()}


def floodlights() -> tuple:
  """Returns where the tower's floodlights are (the pad's own axes)."""
  return tuple((TUNNEL_FROM + 0.3, y, DECK + POSTS + 0.25)
               for y in (-PLATFORM_HALF, PLATFORM_HALF))


def platformLight() -> tuple:
  """Returns where the light over the platform and in the walkway is (the
  rocket's own axes, the walkway at the door)."""
  return 0.5 * (TUNNEL_FROM + PLATFORM_FAR), 0.0, FLOOR + 2.6


def armPivot() -> tuple:
  """Returns the walkway's pivot (the pad's own axes)."""
  return TUNNEL_FROM, 0.0, DECK


@functools.lru_cache(maxsize=1)
def armParts() -> dict:
  """Returns the walkway's meshes by look, in its own axes (its pivot at
  the platform's edge, x out to the rocket, z up from its floor)."""
  parts = {}

  def put(look: str, mesh: tuple) -> None:
    """Adds 'mesh' to 'look''s."""
    parts.setdefault(look, []).append(mesh)

  long, wide = ARM_LONG, TUNNEL_HALF + SKIN
  middle = 0.5 * long
  put('grating', boxRows((middle, 0.0, -0.1), (middle, wide, 0.1),
                         UNTURNED))
  put('tunnel', boxRows((middle, 0.0, TUNNEL_HIGH + 0.05),
                        (middle, wide, 0.05), UNTURNED))
  for side in (-1.0, 1.0):
    y = side * (TUNNEL_HALF + 0.5 * SKIN)
    put('tunnel', boxRows((middle, y, 0.5 * SILL), (middle, 0.5 * SKIN,
                                                    0.5 * SILL), UNTURNED))
    put('tunnel', boxRows((middle, y, 0.5 * (HEAD + TUNNEL_HIGH)), (
      middle, 0.5 * SKIN, 0.5 * (TUNNEL_HIGH - HEAD)), UNTURNED))
    count = int(long // MULLION_EVERY)
    for k in range(count + 1):
      x = min(long - 0.05, k * MULLION_EVERY + 0.05)
      put('tunnel', boxRows((x, y, 0.5 * (SILL + HEAD)), (
        0.05, 0.5 * SKIN, 0.5 * (HEAD - SILL)), UNTURNED))
    put('glass', boxRows((middle, y, 0.5 * (SILL + HEAD)), (
      middle, 0.005, 0.5 * (HEAD - SILL)), UNTURNED))
    put('rubber', boxRows((long - 0.1, side * (TUNNEL_HALF + 0.05),
                           0.5 * TUNNEL_HIGH), (0.12, 0.05,
                                                0.5 * TUNNEL_HIGH),
                          UNTURNED))
  hood = DOOR_HIGH - FLOOR
  inward = -SLOPE * hood
  put('rubber', _beam((long - 0.05, -wide, TUNNEL_HIGH + 0.05),
                      (long + inward, -wide, hood + 0.05), 0.05,
                      (0.0, 1.0, 0.0)))
  put('rubber', _beam((long - 0.05, wide, TUNNEL_HIGH + 0.05),
                      (long + inward, wide, hood + 0.05), 0.05,
                      (0.0, 1.0, 0.0)))
  put('tunnel', quadRows((long + 0.5 * inward - 0.02, 0.0,
                          0.5 * (TUNNEL_HIGH + hood) + 0.05), (
    (0.0, 1.0, 0.0), _unit((inward + 0.05, 0.0, hood - TUNNEL_HIGH)),
    _unit((TUNNEL_HIGH - hood, 0.0, inward + 0.05))), (
    wide, 0.5 * math.hypot(inward + 0.05, TUNNEL_HIGH - hood))))
  put('lamp', boxRows((middle, 0.0, TUNNEL_HIGH - 0.02), (
    middle - 0.5, 0.06, 0.02), UNTURNED))
  for side in (-1.0, 1.0):
    put('tower', _beam((0.3, side * wide, -0.25), (long - 0.3, side * wide,
                                                    -0.25), 0.12))
  (x, y, z), half = OUTSIDE_PANEL
  axes = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
  local = (x - TUNNEL_FROM, y, z - FLOOR)
  put('panel', boxRows(local, half, axes))
  put('key green', boxRows((local[0], local[1] - half[2] - 0.006,
                            local[2]), (0.04, 0.04, 0.006), axes))
  return {look: joined(meshes) for look, meshes in parts.items()}


def outsideKey() -> tuple:
  """Returns the door's key outside: its middle and axes (right, up,
  out of the walkway's wall) and half sizes, the rocket's own axes (the
  walkway at the door)."""
  (x, y, z), half = OUTSIDE_PANEL
  axes = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
  return (x, y - half[2] - 0.006, z), axes, (0.06, 0.06, 0.03)


@functools.lru_cache(maxsize=1)
def leafRows() -> tuple:
  """Returns the door's leaf closed, in the wall's cut (the rocket's own
  axes; it turns about the axis): its outer face, inner face and edges,
  in steps round."""
  a0, a1 = (math.radians(a) for a in DOOR_SPAN)
  steps = 6
  angles = [a0 + (a1 - a0) * k / steps for k in range(steps + 1)]
  parts = []
  for out, sign in ((0.003, 1.0), (WALL - 0.003, -1.0)):
    for b0, b1 in zip(angles[:-1], angles[1:]):
      corners = [_onWall(b, z, out) for b, z in (
        (b0, FLOOR + 0.004), (b1, FLOOR + 0.004), (b1, DOOR_HIGH - 0.004),
        (b0, DOOR_HIGH - 0.004))]
      parts.append(_quadOf(corners, sign))
  for b, sign in ((a0, -1.0), (a1, 1.0)):
    corners = [_onWall(b, z, out) for z, out in (
      (FLOOR + 0.004, 0.003), (FLOOR + 0.004, WALL - 0.003),
      (DOOR_HIGH - 0.004, WALL - 0.003), (DOOR_HIGH - 0.004, 0.003))]
    parts.append(_quadOf(corners, sign))
  return joined(parts)


@functools.lru_cache(maxsize=1)
def insideParts() -> dict:
  """Returns the panel inside by the door (its plate, its keys: amber,
  red, green) and the placard's frame, by look (the rocket's own
  axes)."""
  parts = {}
  middle, axes = wallFrame(*INSIDE_AT, 0.012)
  parts['panel'] = [boxRows(middle, (0.14, 0.07, 0.012), axes)]
  for (_, _, _, across), look in zip(INSIDE_KEYS, ('key amber', 'key red',
                                                   'key green')):
    key, keyAxes = insideKey(across)
    parts.setdefault(look, []).append(boxRows(key, KEY_HALF, keyAxes))
  angle, high, half = PLACARD
  middle, axes = wallFrame(angle, high, 0.006)
  parts.setdefault('panel', []).append(boxRows(
    middle, (half[0] + 0.012, half[1] + 0.012, 0.006), axes))
  return {look: joined(meshes) for look, meshes in parts.items()}


def insideKey(across: float) -> tuple:
  """Returns a key of the panel inside, 'across' it from its middle: its
  middle and axes (right, up, out into the cabin)."""
  middle, axes = wallFrame(*INSIDE_AT, 0.024 + KEY_HALF[2])
  return tuple(m + across * r for m, r in zip(middle, axes[0])), axes


def placardRows() -> tuple:
  """Returns the warning placard's face (its picture across it)."""
  angle, high, half = PLACARD
  middle, axes = wallFrame(angle, high, 0.0125)
  return quadRows(middle, axes, half)


def placardBox() -> tuple:
  """Returns the placard as a box to look at: its middle, axes and half
  sizes."""
  angle, high, half = PLACARD
  middle, axes = wallFrame(angle, high, 0.0125)
  return middle, axes, (half[0], half[1], 0.02)


def wallFrame(angle: float, high: float, out: float) -> tuple:
  """Returns a place on the cabin's inner wall at 'angle' (deg) and
  'high' over the floor, 'out' m from it into the cabin, and the wall's
  axes there (right as one faces it, up it, out of it into the
  cabin)."""
  a = math.radians(angle)
  z = FLOOR + high
  inward = (-math.cos(a), -math.sin(a), 0.0)
  up = _unit((-SLOPE * inward[0], -SLOPE * inward[1], 1.0))
  normal = _unit((inward[0], inward[1], SLOPE))
  right = _cross(up, normal)
  r = capsuleRadius(z) - WALL
  place = (r * math.cos(a) + out * normal[0],
           r * math.sin(a) + out * normal[1], z + out * normal[2])
  return place, (right, up, normal)


def _onWall(angle: float, z: float, depth: float) -> tuple:
  """Returns the point on the cone 'depth' m in from the skin at 'angle'
  (rad) and 'z'."""
  r = capsuleRadius(z) - depth
  return r * math.cos(angle), r * math.sin(angle), z


def _quadOf(corners: list, sign: float) -> tuple:
  """Returns a quad through four 'corners', facing the way their winding
  gives (times 'sign')."""
  a, b, c = corners[0], corners[1], corners[2]
  normal = _unit(_cross(tuple(q - p for p, q in zip(a, b)),
                        tuple(q - p for p, q in zip(a, c))))
  normal = tuple(sign * n for n in normal)
  rows = [tuple(corner) + normal + (0.0, 0.0) for corner in corners]
  faces = (0, 1, 2, 0, 2, 3) if sign > 0 else (0, 2, 1, 0, 3, 2)
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _beam(a: tuple, b: tuple, half: float, side: tuple = None) -> tuple:
  """Returns a square beam from 'a' to 'b', 'half' its thickness."""
  along = tuple(q - p for p, q in zip(a, b))
  long = math.sqrt(sum(x * x for x in along))
  along = tuple(x / long for x in along)
  if side is None:
    side = (0.0, 0.0, 1.0) if abs(along[2]) < 0.9 else (1.0, 0.0, 0.0)
  out = _unit(_cross(along, side))
  up = _cross(out, along)
  middle = tuple(0.5 * (p + q) for p, q in zip(a, b))
  return boxRows(middle, (0.5 * long, half, half), (along, up, out))


def _cage(put: object, x0: float, x1: float, half: float) -> None:
  """Adds the cage round the platform: bars and rails along its back and
  sides, and its front either side of the walkway."""
  z0, z1 = DECK, DECK + CAGE_HIGH
  runs = (((x0, -half), (x0, half)), ((x0, -half), (x1, -half)),
          ((x0, half), (x1, half)), ((x1, -half), (x1, -TUNNEL_HALF - 0.1)),
          ((x1, TUNNEL_HALF + 0.1), (x1, half)))
  for (ax, ay), (bx, by) in runs:
    long = math.hypot(bx - ax, by - ay)
    count = max(1, int(long // BAR_EVERY))
    for k in range(count + 1):
      t = k / count
      x, y = ax + t * (bx - ax), ay + t * (by - ay)
      put('rail', boxRows((x, y, 0.5 * (z0 + z1)), (0.012, 0.012,
                                                    0.5 * CAGE_HIGH),
                          UNTURNED))
    for z in (z0 + 0.1, z0 + 1.1, z1):
      put('rail', _beam((ax, ay, z), (bx, by, z), 0.025))


def _unit(v: tuple) -> tuple:
  """Returns 'v' made a unit."""
  size = math.sqrt(sum(x * x for x in v))
  return tuple(x / size for x in v)


def _cross(a: tuple, b: tuple) -> tuple:
  """Returns 'a' across 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])
