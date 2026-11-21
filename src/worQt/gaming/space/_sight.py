"""
The Grav-Gun's line of sight (user, 2026-11-17: "the gravgun should not
be able to grab bolts through walls"; then "the fucking gravity gun
still works through walls"): the straight way from his eyes to what it
aims at, up to a hair before it, must run through the rooms the whole
way and through no solid. The rooms are walked by how deep in them each
point is (never further in a step than that, nor less than 'LEAST':
no wall is stepped over, however thin); the solids are boxes, each met
exactly (its slabs). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

#  The way is looked at up to this short of what it aims at (it sits on
#  a wall, or rests on something), m; the least step along it, m (the
#  thinnest wall, the hull's, is 5 cm).
SHORT = 0.2
LEAST = 0.01
#  A room's depth is trusted this far as a step (the cabin's is had
#  across, not square to its wall: its cone leans 17 degrees in).
TRUST = 0.9


def inSight(eye: tuple, there: tuple, inside: object,
            boxes: tuple) -> bool:
  """Returns whether the way from 'eye' to 'there' (up to 'SHORT'
  before it) runs through the rooms ('inside': a point's depth in them,
  m, nought or less out of them) and through none of 'boxes' (their
  middles, half sizes and axes as columns, numpy arrays (n, 3), (n, 3),
  (n, 3, 3); empty: none)."""
  off = numpy.asarray(there, numpy.float64) - numpy.asarray(eye,
                                                            numpy.float64)
  far = float(numpy.linalg.norm(off))
  reach = far - SHORT
  if reach <= 0.0:
    return True
  way = off / far
  start = numpy.asarray(eye, numpy.float64)
  gone = 0.0
  while gone < reach:
    depth = inside(tuple(start + gone * way))
    if depth <= 0.0:
      return False
    gone += max(LEAST, TRUST * depth)
  return not _boxMet(start, way, reach, boxes)


def _boxMet(start: numpy.ndarray, way: numpy.ndarray, reach: float,
            boxes: tuple) -> bool:
  """Returns whether the way from 'start' along 'way' (unit) meets any
  of 'boxes' within 'reach' m (each box's slabs, in its own axes)."""
  middles, halves, axes = boxes
  if len(middles) == 0:
    return False
  rel = start[None, :] - middles
  local = numpy.einsum('nij,ni->nj', axes, rel)
  turned = numpy.einsum('nij,i->nj', axes, way)
  low = numpy.zeros(len(middles))
  high = numpy.full(len(middles), reach)
  for k in range(3):
    o, d, h = local[:, k], turned[:, k], halves[:, k]
    still = numpy.abs(d) < 1e-12
    inside = numpy.abs(o) <= h
    safe = numpy.where(still, 1.0, d)
    a = (-h - o) / safe
    b = (h - o) / safe
    near = numpy.minimum(a, b)
    far = numpy.maximum(a, b)
    low = numpy.where(still, numpy.where(inside, low, math.inf),
                      numpy.maximum(low, near))
    high = numpy.where(still, numpy.where(inside, high, -math.inf),
                       numpy.minimum(high, far))
  return bool(numpy.any(low <= high))


def boxGap(point: tuple, boxes: tuple) -> float:
  """Returns how far 'point' is from the nearest of 'boxes' (as
  'inSight' takes them), m: less than nought inside one (as deep as it
  is in it); none, infinite."""
  middles, halves, axes = boxes
  if len(middles) == 0:
    return math.inf
  rel = numpy.asarray(point, numpy.float64)[None, :] - middles
  local = numpy.abs(numpy.einsum('nij,ni->nj', axes, rel)) - halves
  out = numpy.linalg.norm(numpy.maximum(local, 0.0), axis=1)
  return float(numpy.min(out + numpy.minimum(local.max(1), 0.0)))
