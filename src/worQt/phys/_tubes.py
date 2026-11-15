"""
Round parts as they are drawn (user, 2026-11-15: "make it look proper,
not these blocky things"): tubes and balls as rows of eight a corner
(place, m, its normal, its picture's two coordinates), every triangle's
corners in turn, as '_meshes.finishedRows' takes them ('rows'), smooth
shaded, wound outward. Qt-free, numpy. A part's physics keeps its
simple convex pieces ('_rig._bar', '_box'): only its drawing is round.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

#  How many faces round a tube, and how many bands a ball from pole to
#  pole.
SIDES, BANDS = 16, 10


def _square(way: numpy.ndarray) -> tuple:
  """Returns two units square to 'way' (a unit) and to each other."""
  helper = numpy.array((0.0, 0.0, 1.0)) if abs(way[2]) < 0.9 else (
    numpy.array((1.0, 0.0, 0.0)))
  u = numpy.cross(way, helper)
  u /= numpy.linalg.norm(u)
  return u, numpy.cross(way, u)


def _triangles(places: list, normals: list) -> numpy.ndarray:
  """Returns triangles' corners (places, normals: each (n, 3, 3)) as
  rows, the picture's coordinates nought."""
  place = numpy.concatenate(places).reshape(-1, 3)
  normal = numpy.concatenate(normals).reshape(-1, 3)
  rows = numpy.zeros((len(place), 8))
  rows[:, :3], rows[:, 3:6] = place, normal
  return rows


def tubeRows(start: tuple, end: tuple, radius: float,
             ends: tuple = (True, True), far: float = None,
             sides: int = SIDES) -> numpy.ndarray:
  """The 'tubeRows' function returns a round tube from 'start' to 'end'
  ('radius' at its start, 'far' at its end: None, the same; a taper) as
  rows, its ends capped where 'ends' says (start, end)."""
  a, b = numpy.array(start, float), numpy.array(end, float)
  way = b - a
  length = numpy.linalg.norm(way)
  if length <= 0.0:
    return numpy.zeros((0, 8))
  way /= length
  u, v = _square(way)
  far = radius if far is None else far
  angles = numpy.linspace(0.0, 2.0 * math.pi, sides + 1)
  round_ = (numpy.cos(angles)[:, None] * u + numpy.sin(angles)[:, None]
            * v)
  slope = (radius - far) / length
  normal = round_ + slope * way
  normal /= numpy.linalg.norm(normal, axis=1, keepdims=True)
  low, high = a + radius * round_, b + far * round_
  places, normals = [], []
  for k in range(sides):
    j = k + 1
    places.append(numpy.array(((low[k], low[j], high[j]),
                               (low[k], high[j], high[k]))))
    normals.append(numpy.array(((normal[k], normal[j], normal[j]),
                                (normal[k], normal[j], normal[k]))))
  for capped, middle, rim, facing in ((ends[0], a, low, -way),
                                      (ends[1], b, high, way)):
    if not capped:
      continue
    for k in range(sides):
      j = k + 1
      corners = (middle, rim[k], rim[j]) if facing @ way > 0.0 else (
        middle, rim[j], rim[k])
      places.append(numpy.array((corners,)))
      normals.append(numpy.array(((facing, facing, facing),)))
  return _triangles(places, normals)


def ballRows(middle: tuple, radius: float,
             bands: int = BANDS) -> numpy.ndarray:
  """The 'ballRows' function returns a ball of 'radius' about 'middle' as
  rows."""
  c = numpy.array(middle, float)
  theta = numpy.linspace(0.0, math.pi, bands + 1)
  phi = numpy.linspace(0.0, 2.0 * math.pi, 2 * bands + 1)
  grid = numpy.stack((numpy.sin(theta)[:, None] * numpy.cos(phi),
                      numpy.sin(theta)[:, None] * numpy.sin(phi),
                      numpy.cos(theta)[:, None] * numpy.ones_like(phi)), -1)
  places, normals = [], []
  for i in range(bands):
    for j in range(2 * bands):
      p00, p01 = grid[i, j], grid[i, j + 1]
      p10, p11 = grid[i + 1, j], grid[i + 1, j + 1]
      for tri in ((p00, p10, p11), (p00, p11, p01)):
        places.append(numpy.array((tuple(c + radius * p for p in tri),)))
        normals.append(numpy.array((tri,)))
  return _triangles(places, normals)


def joinedRows(*parts: numpy.ndarray) -> numpy.ndarray:
  """The 'joinedRows' function returns 'parts' (rows each) as one."""
  return numpy.concatenate([part for part in parts if len(part)])
