"""
The spokes' terminals in Terra Prime's ring (user, 2026-11-19: "the
spokes are not pressurized. Only the elevators are They are large
girder structures. The spoke-elevators end on the inside of the ring in
a special extra structure. Once there, Asger will get up and *walk* out
of the elevator down some stairs and in to the ring"): under each
spoke, inside the ring's tube, a square tube of walls guides the cage
down from the ring's ceiling to its landing 'RISE' m over the deck
('LANDING': the cage's floor there, its stop); a platform before its
opening side (along the ring, the turning's way) at the landing's
height, railed, and stairs from the platform down to the deck, each
step laid round the ring where it is. Their parts in the station's own
axes (each its look, middle, half sizes, axes: along the ring, along
the axis, out; whether it is a solid); their solids in the docked
rocket's ('terminalSolids'); their meshes by look ('terminalMeshes').
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._shapes import boxRows, joined
from ._stationinterior import DECK, TUBE_INSIDE, stationPoint, stationWay
from ._stationmeshes import SPOKES, TUBE_MIDDLE
from ._turns import quaternionOf

#  The landing: this high over the deck, m (the cage's floor there: its
#  stop, '_elevator.DECK_STOP'); the guide tube round the cage's way
#  (half its width inside, both ways; its walls' half thickness), from
#  the ring's ceiling down to the landing, m.
RISE = 4.0
LANDING = DECK - RISE
GUIDE_HALF = 1.95
GUIDE_WALL = 0.08
CEILING_OUT = TUBE_MIDDLE - TUBE_INSIDE
#  The cage's height, its opening's (its side along the ring), m.
OPENING_HIGH = 3.0
#  The platform before the opening: how deep along the ring, half its
#  width along the axis, half its thickness, m.
PLATFORM_DEEP = 3.0
PLATFORM_HALF = 1.6
PLATFORM_THICK = 0.12
#  The stairs from the platform's far edge down to the deck: each step
#  this high and this deep, m; the railings' height, half thickness, m.
STEP_RISE = 0.2
STEP_RUN = 0.3
STEPS = int(round(RISE / STEP_RISE))
RAIL_HIGH = 1.0
RAIL_HALF = 0.03


def spokeAngles() -> tuple:
  """Returns the spokes' angles round the station's axis, rad."""
  count = SPOKES[0]
  return tuple(2.0 * math.pi * k / count for k in range(count))


def _axesAt(angle: float) -> tuple:
  """Returns the axes at 'angle' round the station's axis: along the
  ring (the turning's way), along the axis, out from it."""
  c, s = math.cos(angle), math.sin(angle)
  return (-s, c, 0.0), (0.0, 0.0, 1.0), (c, s, 0.0)


def _placed(angle: float, along: float, axial: float,
            out: float) -> tuple:
  """Returns the point 'along' m round the ring (on the arc 'out' m from
  the axis) from 'angle', 'axial' m along the axis, and its axes there
  (the arc's: along it, the axis, out)."""
  turned = angle + along / out
  c, s = math.cos(turned), math.sin(turned)
  return (out * c, out * s, axial), _axesAt(turned)


def _box(parts: list, look: str, angle: float, along: float,
         axial: float, out: float, half: tuple, solid: bool) -> None:
  """Adds a box: its middle 'along' m round the ring at 'out' m from the
  axis, 'axial' along it; 'half' its half sizes along the ring, the
  axis, out."""
  middle, axes = _placed(angle, along, axial, out)
  parts.append((look, middle, tuple(half), axes, solid))


@functools.lru_cache(maxsize=1)
def terminalParts() -> tuple:
  """Returns every terminal's parts (the station's own axes): each its
  look, middle, half sizes, axes (along the ring, the axis, out) and
  whether it is a solid."""
  parts = []
  span = LANDING - CEILING_OUT
  middle = CEILING_OUT + 0.5 * span
  wall = GUIDE_HALF + GUIDE_WALL
  for angle in spokeAngles():
    for side in (1.0, -1.0):
      _box(parts, 'terminal', angle, 0.0, side * wall, middle,
           (wall + GUIDE_WALL, GUIDE_WALL, 0.5 * span), True)
    _box(parts, 'terminal', angle, -wall, 0.0, middle,
         (GUIDE_WALL, GUIDE_HALF, 0.5 * span), True)
    high = span - OPENING_HIGH
    _box(parts, 'terminal', angle, wall, 0.0, CEILING_OUT + 0.5 * high,
         (GUIDE_WALL, GUIDE_HALF, 0.5 * high), True)
    floor = LANDING + PLATFORM_THICK
    front = wall + GUIDE_WALL
    _box(parts, 'stairs', angle, front + 0.5 * PLATFORM_DEEP, 0.0, floor,
         (0.5 * PLATFORM_DEEP, PLATFORM_HALF, PLATFORM_THICK), True)
    for k in range(STEPS - 1):
      top = LANDING + STEP_RISE * (k + 1)
      deep = 0.5 * (DECK - top)
      along = front + PLATFORM_DEEP + STEP_RUN * (k + 0.5)
      _box(parts, 'stairs', angle, along, 0.0, top + deep,
           (0.5 * STEP_RUN, PLATFORM_HALF, deep), True)
    for side in (1.0, -1.0):
      _box(parts, 'railing', angle, front + 0.5 * PLATFORM_DEEP,
           side * (PLATFORM_HALF - RAIL_HALF), LANDING - RAIL_HIGH,
           (0.5 * PLATFORM_DEEP, RAIL_HALF, RAIL_HALF), False)
      run = STEP_RUN * STEPS
      slope = math.atan2(RISE, run)
      along = front + PLATFORM_DEEP + 0.5 * run
      out = LANDING + 0.5 * RISE - RAIL_HIGH
      centre, axes = _placed(angle, along, side * (
        PLATFORM_HALF - RAIL_HALF), out)
      way, axial, outward = axes
      c, s = math.cos(slope), math.sin(slope)
      tilted = (tuple(c * w + s * o for w, o in zip(way, outward)), axial,
                tuple(-s * w + c * o for w, o in zip(way, outward)))
      parts.append(('railing', centre, (0.5 * math.hypot(run, RISE),
                                        RAIL_HALF, RAIL_HALF), tilted,
                    False))
  return tuple(parts)


def terminalSolids(relative: tuple) -> tuple:
  """Returns the terminals' solids in the docked rocket's own axes
  ('relative': its axes in the station's): each its middle, half sizes,
  turn (w x y z) and velocity (still)."""
  out = []
  for _, middle, half, axes, solid in terminalParts():
    if not solid:
      continue
    columns = tuple(stationWay(a, relative) for a in axes)
    turn = quaternionOf(tuple((columns[0][k], columns[1][k], columns[2][k])
                              for k in range(3)))
    out.append((stationPoint(middle, relative), half, turn,
                (0.0, 0.0, 0.0)))
  return tuple(out)


@functools.lru_cache(maxsize=1)
def terminalMeshes() -> dict:
  """Returns the terminals' meshes by look ('terminal', 'stairs',
  'railing'; the station's own axes)."""
  out = {}
  for look, middle, half, axes, _ in terminalParts():
    out.setdefault(look, []).append(boxRows(middle, half, axes))
  return {look: joined(parts) for look, parts in out.items()}
