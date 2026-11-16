"""
The real car's speedometer on its dash (user, 2026-11-15: "let's add a
speedometer. both a virtual one on the GUI and a diegetic one next to
the steering wheel"): a round dial in the cockpit right of the steering
wheel, behind the dash hoop, facing the driver's eyes; drawn with the
chassis (its face, 'faceRows', the dial's picture laid on it; its can
and bezel, 'bezelRows'; the needle's hub; the stalk it stands on), its
needle turned for the car's speed each frame ('needleOf'). In the car's
frame, m; Qt-free.

The dial's picture ('gui._dials.dialPicture') is the window's
speedometer's too: its sweep and its scale are here ('SWEEP',
'TOP_SPEED'), 0 km/h at 'SWEEP' left of upright, the top as far right.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._tubes import joinedRows, tubeRows
from ._vectors import Vector, cross, minus, norm, plus, scaled

#  The dial's middle (right of the steering wheel's rim by 4 cm, behind
#  the dash hoop's bar), the driver's eyes it faces (the walker's in the
#  seat), its face's radius, the bezel's, how deep its can is, m.
MIDDLE = (-1.44, -0.15, 0.62)
EYES = (-1.69, 0.0, 1.017)
FACE, BEZEL, CAN = 0.045, 0.05, 0.03
#  The needle's sweep each way of upright, rad (0 km/h at its left, the
#  top at its right), the dial's top, km/h, the needle's reach and tail
#  from the middle and its half thickness, how far over the face it
#  lies, m.
SWEEP = math.radians(135.0)
TOP_SPEED = 240.0
REACH, TAIL, HALF, OVER = 0.038, 0.009, 0.0011, 0.003
#  Where the stalk holding the dial meets the dash hoop's bar, m.
STALK = (-1.385, -0.15, 0.575)


@functools.lru_cache(maxsize=1)
def frameOf() -> tuple[Vector, Vector, Vector, Vector]:
  """The 'frameOf' function returns the dial's middle and its ways: out
  of its face (toward the driver's eyes), up it and right along it (as
  the driver sees it)."""
  out = minus(EYES, MIDDLE)
  out = scaled(out, 1.0 / norm(out))
  up = minus((0.0, 0.0, 1.0), scaled(out, out[2]))
  up = scaled(up, 1.0 / norm(up))
  return MIDDLE, out, up, cross(up, out)


def angleOf(speed: float) -> float:
  """The 'angleOf' function returns how far right of upright the needle
  points at 'speed' km/h, rad (held at the dial's ends)."""
  share = min(max(abs(speed) / TOP_SPEED, 0.0), 1.0)
  return -SWEEP + 2.0 * SWEEP * share


def needleOf(speed: float) -> tuple[Vector, Vector]:
  """The 'needleOf' function returns the needle's tail and tip at
  'speed' km/h, in the car's frame."""
  middle, out, up, right = frameOf()
  angle = angleOf(speed)
  way = plus(scaled(up, math.cos(angle)), scaled(right, math.sin(angle)))
  hub = plus(middle, scaled(out, OVER))
  return plus(hub, scaled(way, -TAIL)), plus(hub, scaled(way, REACH))


@functools.lru_cache(maxsize=1)
def faceRows() -> numpy.ndarray:
  """The 'faceRows' function returns the dial's face as rows (a disc
  facing the driver, the dial's picture laid on it: its picture's first
  way along the dial's right, its second up it, as the steering wheel's
  badge has it)."""
  middle, out, up, right = frameOf()
  sides = 64
  rows = []
  for k in range(sides):
    corners = [(0.0, 0.0)] + [
      (math.cos(a), math.sin(a)) for a in (2.0 * math.pi * k / sides,
                                           2.0 * math.pi * (k + 1) / sides)]
    for x, y in corners:
      place = plus(middle, plus(scaled(right, FACE * x),
                                scaled(up, FACE * y)))
      rows.append(tuple(place) + tuple(out) + (0.5 + 0.5 * x,
                                               0.5 + 0.5 * y))
  return numpy.array(rows)


@functools.lru_cache(maxsize=1)
def bezelRows() -> numpy.ndarray:
  """The 'bezelRows' function returns the dial's can and chrome bezel
  round its face (open in front: the face shows through), the needle's
  hub, and the stalk from the can's back to the dash hoop, as rows."""
  middle, out, _, _ = frameOf()
  back = plus(middle, scaled(out, -CAN))
  return joinedRows(
    tubeRows(back, plus(middle, scaled(out, 0.004)), BEZEL, (True, False),
             None, 48),
    tubeRows(middle, plus(middle, scaled(out, OVER + 0.001)), 0.004),
    tubeRows(back, STALK, 0.006))
