"""
The lamps up the rocket's head and in Terra Prime's cages (user,
2026-11-19: "we must have lamps in the center of the Terra Prime and in
each of the four elevators"; "I can't see it because of the darkness";
then the three levels: "the head our rocket insert itself here"): a
ring of lamps under each of the head's two levels' ceilings, round the
hatch and the pole (level 2 is the station's middle, docked: the doors
open there), and a lamp bar under each cage's roof on its inside
(riding with its cage). The rings' places in the rocket's own axes, the
cages' in the docked rocket's; their meshes about their middles.
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._elevator import CAR_HALF, CAR_HIGH
from ._levels import LEVELS
from ._shapes import UNTURNED, boxRows, joined
from ._stationinterior import PLANE
from ._turns import cross

#  A level's lamp ring: its lamps this far from the axis, this many
#  round, each this long round it, this thick, just under the ceiling
#  (their middles this far under it); its light on the axis this far
#  under the ceiling.
RING_OUT = 2.4
RING_LAMPS = 12
RING_LAMP_LONG = 0.9
RING_LAMP_THICK = 0.08
RING_DOWN = 0.05
RING_LIGHT_DOWN = 0.6
#  A cage's lamp bar: under its roof (this far from the roof's plane),
#  on the cage's inside across it (this far in from the plate across at
#  the axis's low side), along the ring this long, this thick; its light
#  this far from the roof's plane in the cage's middle.
CAGE_LAMP_DOWN = 0.2
CAGE_LAMP_IN = 0.1
CAGE_LAMP_LONG = 2.0
CAGE_LAMP_THICK = 0.08
CAGE_LIGHT_DOWN = 0.9


def ringAt(level: int) -> tuple:
  """Returns level 'level''s (one, two) lamp ring's middle, the rocket's
  own axes."""
  return 0.0, 0.0, LEVELS[level][1] - RING_DOWN


def ringLightAt(level: int) -> tuple:
  """Returns where level 'level''s lamp ring's light shines from (on the
  axis under the ring), the rocket's own axes."""
  return 0.0, 0.0, LEVELS[level][1] - RING_LIGHT_DOWN


def cageLampOf(floor: float, way: tuple) -> tuple:
  """Returns a cage's lamp bar's middle and its light's place (the
  docked rocket's own axes), its floor 'floor' m off the axis along a
  shaft out 'way' (its turn is the cage's, '_elevator.boxesOf')."""
  up = (0.0, 0.0, 1.0)
  side = cross(up, way)
  roof = floor - CAR_HIGH
  axial = -(CAR_HALF - CAGE_LAMP_IN)

  def at(out: float, along: float, high: float) -> tuple:
    return tuple(out * w + along * s + high * u for w, s, u in zip(
      way, side, up))

  bar = at(roof + CAGE_LAMP_DOWN, 0.0, axial)
  light = at(roof + CAGE_LIGHT_DOWN, 0.0, 0.0)
  return ((bar[0], bar[1], bar[2] + PLANE),
          (light[0], light[1], light[2] + PLANE))


def ringLampRows() -> tuple:
  """Returns a level's lamp ring about its middle: 'RING_LAMPS' bars round
  the axis, 'RING_OUT' m out."""
  half = (0.5 * RING_LAMP_LONG, 0.5 * RING_LAMP_THICK,
          0.5 * RING_LAMP_THICK)
  parts = []
  for k in range(RING_LAMPS):
    a = 2.0 * math.pi * (k + 0.5) / RING_LAMPS
    radial = (math.cos(a), math.sin(a), 0.0)
    round_ = (-math.sin(a), math.cos(a), 0.0)
    middle = tuple(RING_OUT * r for r in radial)
    parts.append(boxRows(middle, half, (round_, radial, (0.0, 0.0, 1.0))))
  return joined(parts)


def cageLampRows() -> tuple:
  """Returns a cage's lamp bar about its middle, in the cage's axes
  (along the ring, along the axis, out)."""
  return boxRows((0.0, 0.0, 0.0), (0.5 * CAGE_LAMP_LONG, 0.5
                                   * CAGE_LAMP_THICK, 0.5
                                   * CAGE_LAMP_THICK), UNTURNED)
