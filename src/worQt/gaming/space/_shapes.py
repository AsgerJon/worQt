"""
Mesh shapes as rows of eight numbers a corner (place, normal, where on a
picture) and their triangles, Qt-free: boxes, quads, discs, rings,
cylinders, frustums, balls, rounded slabs and panes, joined into one
mesh or taken about a point. The dashboard, the cabin's furnishings and
the like are made of them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

TAU = 2.0 * math.pi

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  SHAPES   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

UNTURNED = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
#  Where on a picture a face with none lies (its corner).
_NO_PICTURE = (0.002, 0.002)
#  A box's faces: the normal in its own axes and its corners (each -1 or
#  1 along right, up, out), seen from outside counter-clockwise.
_FACES = (
  ((0, 0, 1), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))),
  ((0, 0, -1), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1))),
  ((1, 0, 0), ((1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1))),
  ((-1, 0, 0), ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1))),
  ((0, 1, 0), ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1))),
  ((0, -1, 0), ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1))))


def pointAlong(point: tuple, axis: tuple, far: float) -> tuple:
  """Returns 'point' moved 'far' along 'axis'."""
  return tuple(p + far * a for p, a in zip(point, axis))


def boxRows(middle: tuple, half: tuple, axes: tuple, cell: tuple = None,
            about: tuple = None) -> tuple:
  """Returns a box's rows and triangles: its 'middle', 'half' sizes along
  its 'axes' (right, up, out); its front (out) face laid over 'cell' of
  a picture (u0, v0, u1, v1), its other faces on no picture; its places
  from 'about' (None: as they are)."""
  rows, faces = [], []
  for normal, corners in _FACES:
    first = len(rows)
    direction = tuple(normal[0] * a + normal[1] * b + normal[2] * n
                      for a, b, n in zip(*axes))
    for k, corner in enumerate(corners):
      place = tuple(m + corner[0] * half[0] * a + corner[1] * half[1] * b
                    + corner[2] * half[2] * n for m, a, b, n in zip(
        middle, *axes))
      if cell is not None and normal == (0, 0, 1):
        uv = (cell[0] + (cell[2] - cell[0]) * (0.5 + 0.5 * corner[0]),
              cell[1] + (cell[3] - cell[1]) * (0.5 + 0.5 * corner[1]))
      else:
        uv = _NO_PICTURE
      rows.append(place + direction + uv)
    faces.extend((first, first + 1, first + 2, first, first + 2,
                  first + 3))
  return (rowsAbout(numpy.array(rows), about),
          numpy.array(faces, numpy.uint32))


def quadRows(middle: tuple, axes: tuple, half: tuple,
             cell: tuple = None) -> tuple:
  """Returns a quad facing out of its 'axes' (right, up, out), 'half' its
  size, laid over 'cell' of a picture (None: none)."""
  right, up, out = axes
  cell = cell or (0.0, 0.0, 1.0, 1.0)
  rows = []
  for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
    place = tuple(m + (2 * u - 1) * half[0] * r + (2 * v - 1) * half[1] * w
                  for m, r, w in zip(middle, right, up))
    rows.append(place + tuple(out) + (cell[0] + u * (cell[2] - cell[0]),
                                      cell[1] + v * (cell[3] - cell[1])))
  return numpy.array(rows), numpy.array((0, 1, 2, 0, 2, 3), numpy.uint32)


def discRows(middle: tuple, axes: tuple, radius: float, sides: int,
             cell: tuple = None) -> tuple:
  """Returns a disc facing out of its 'axes', laid over 'cell' of a
  picture (its square: u0, v0, u1, v1; None: none)."""
  right, up, out = axes
  rows = [tuple(middle) + tuple(out) + _cellAt(cell, 0.5, 0.5)]
  for k in range(sides + 1):
    a = TAU * k / sides
    c, s = math.cos(a), math.sin(a)
    place = tuple(m + radius * (c * r + s * w) for m, r, w in zip(
      middle, right, up))
    rows.append(place + tuple(out) + _cellAt(cell, 0.5 + 0.5 * c,
                                             0.5 + 0.5 * s))
  faces = []
  for k in range(sides):
    faces.extend((0, 1 + k, 2 + k))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def ringRows(middle: tuple, axes: tuple, inner: float, outer: float,
             high: float) -> tuple:
  """Returns a bezel: a flat ring from 'inner' to 'outer' radius 'high'
  out of the face, and its outer edge down to the face."""
  right, up, out = axes
  rows, faces = [], []
  sides = 40
  for k in range(sides + 1):
    a = TAU * k / sides
    c, s = math.cos(a), math.sin(a)
    way = tuple(c * r + s * w for r, w in zip(right, up))
    for radius, lift, normal in ((inner, high, out), (outer, high, out),
                                 (outer, high, way), (outer, 0.0, way)):
      place = tuple(m + radius * x + lift * n for m, x, n in zip(
        middle, way, out))
      rows.append(place + tuple(normal) + _NO_PICTURE)
  for k in range(sides):
    a, b = 4 * k, 4 * (k + 1)
    faces.extend((a, a + 1, b + 1, a, b + 1, b))
    faces.extend((a + 2, a + 3, b + 3, a + 2, b + 3, b + 2))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def cylinderRows(base: tuple, axis: tuple, radius: float, length: float,
                 sides: int) -> tuple:
  """Returns a closed cylinder from 'base' 'length' along 'axis'."""
  return frustumRows(base, axis, radius, radius, length, sides)


def frustumRows(base: tuple, axis: tuple, low: float, high: float,
                length: float, sides: int) -> tuple:
  """Returns a closed frustum from 'base' ('low' its radius) 'length'
  along 'axis' (its far end 'high' round)."""
  axis = numpy.array(axis, numpy.float64)
  axis /= numpy.linalg.norm(axis)
  other = numpy.array((0.0, 0.0, 1.0)) if abs(axis[2]) < 0.9 else (
    numpy.array((1.0, 0.0, 0.0)))
  right = numpy.cross(axis, other)
  right /= numpy.linalg.norm(right)
  up = numpy.cross(axis, right)
  base = numpy.array(base, numpy.float64)
  top = base + length * axis
  slope = (low - high) / length
  rows, faces = [], []
  for k in range(sides + 1):
    a = TAU * k / sides
    way = math.cos(a) * right + math.sin(a) * up
    normal = way + slope * axis
    normal /= numpy.linalg.norm(normal)
    rows.append(tuple(base + low * way) + tuple(normal) + _NO_PICTURE)
    rows.append(tuple(top + high * way) + tuple(normal) + _NO_PICTURE)
  for k in range(sides):
    a, b = 2 * k, 2 * k + 2
    faces.extend((a, b, b + 1, a, b + 1, a + 1))
  for centre, radius, normal in ((base, low, -axis), (top, high, axis)):
    middle = len(rows)
    rows.append(tuple(centre) + tuple(normal) + _NO_PICTURE)
    for k in range(sides + 1):
      a = TAU * k / sides
      way = math.cos(a) * right + math.sin(a) * up
      rows.append(tuple(centre + radius * way) + tuple(normal)
                  + _NO_PICTURE)
    for k in range(sides):
      faces.extend((middle, middle + 1 + k, middle + 2 + k))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def ballRows(middle: tuple, radius: float, sides: int) -> tuple:
  """Returns a ball: 'sides' round and half as many from pole to pole,
  on no picture."""
  rows, faces = [], []
  rings = max(2, sides // 2)
  for i in range(rings + 1):
    polar = math.pi * i / rings
    for k in range(sides + 1):
      a = TAU * k / sides
      way = (math.sin(polar) * math.cos(a), math.sin(polar) * math.sin(a),
             math.cos(polar))
      rows.append(tuple(m + radius * w for m, w in zip(middle, way))
                  + way + _NO_PICTURE)
  for i in range(rings):
    for k in range(sides):
      a, b = i * (sides + 1) + k, (i + 1) * (sides + 1) + k
      faces.extend((a, b, b + 1, a, b + 1, a + 1))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def roundedOutline(half: tuple, radius: float, steps: int) -> list:
  """Returns a rounded rectangle's outline, 'half' its size, its corners
  'radius' round in 'steps' each, counter-clockwise from its right
  edge's foot: each point as its corner's middle and its way out from
  it (a unit pair)."""
  out = []
  for k, (sx, sy) in enumerate(((1, -1), (1, 1), (-1, 1), (-1, -1))):
    middle = (sx * (half[0] - radius), sy * (half[1] - radius))
    for j in range(steps + 1):
      a = 0.5 * math.pi * (k - 1 + j / steps)
      out.append((middle, (math.cos(a), math.sin(a))))
  return out


def roundedSlabRows(base: tuple, axes: tuple, half: tuple, depth: float,
                    radius: float, edge: float, cell: tuple = None) -> tuple:
  """Returns a rounded slab standing 'depth' out of 'base' along its
  'axes' (right, up, out): 'half' its size, its corners 'radius' round,
  its front edge rounded 'edge' (at most 'radius'), its back open; laid
  over 'cell' of a picture as seen from the front (None: none)."""
  right, up, out = (numpy.array(a, numpy.float64) for a in axes)
  base = numpy.array(base, numpy.float64)
  outline = roundedOutline(half, radius, 8)
  bends = [0.5 * math.pi * j / 4 for j in range(5)]
  profile = [(radius - edge + edge * math.sin(t),
              depth - edge * (1.0 - math.cos(t)), math.cos(t),
              math.sin(t)) for t in bends] + [(radius, 0.0, 0.0, 1.0)]
  rows = [tuple(base + depth * out) + tuple(out) + _cellAt(cell, 0.5,
                                                           0.5)]
  for reach, lift, forward, sideways in profile:
    for (cx, cy), (c, s) in outline:
      x, y = cx + reach * c, cy + reach * s
      normal = forward * out + sideways * (c * right + s * up)
      rows.append(tuple(base + x * right + y * up + lift * out)
                  + tuple(normal) + _cellAt(cell, 0.5 + 0.5 * x / half[0],
                                            0.5 + 0.5 * y / half[1]))
  return numpy.array(rows), _ringFaces(len(outline), len(profile))


def roundedPaneRows(middle: tuple, axes: tuple, half: tuple,
                    radius: float, bulge: float, cell: tuple = None) -> (
    tuple):
  """Returns a rounded pane facing out of its 'axes' (right, up, out):
  'half' its size, its corners 'radius' round, its middle bulging
  'bulge' out (a picture tube's face); laid over 'cell' of a picture
  (None: none)."""
  right, up, out = (numpy.array(a, numpy.float64) for a in axes)
  middle = numpy.array(middle, numpy.float64)
  outline = roundedOutline(half, radius, 8)
  shares = (0.25, 0.5, 0.75, 1.0)
  rows = [tuple(middle + bulge * out) + tuple(out) + _cellAt(cell, 0.5,
                                                             0.5)]
  for share in shares:
    for (cx, cy), (c, s) in outline:
      ex, ey = cx + radius * c, cy + radius * s
      reach = math.hypot(ex, ey)
      x, y = share * ex, share * ey
      normal = out + 2.0 * bulge * share / reach * (
        ex * right + ey * up) / reach
      normal /= numpy.linalg.norm(normal)
      rows.append(tuple(middle + x * right + y * up + bulge * (
        1.0 - share * share) * out) + tuple(normal) + _cellAt(
        cell, 0.5 + 0.5 * x / half[0], 0.5 + 0.5 * y / half[1]))
  return numpy.array(rows), _ringFaces(len(outline), len(shares))


def _ringFaces(count: int, rings: int) -> numpy.ndarray:
  """Returns the triangles of a fan round row 0 to the first of 'rings'
  rings of 'count' rows each (rows 1 on), and between each ring and the
  next, every one facing the way the rings run out from the fan."""
  faces = []
  for k in range(count):
    faces.extend((0, 1 + k, 1 + (k + 1) % count))
  for i in range(rings - 1):
    a, b = 1 + i * count, 1 + (i + 1) * count
    for k in range(count):
      n = (k + 1) % count
      faces.extend((a + k, b + k, b + n, a + k, b + n, a + n))
  return numpy.array(faces, numpy.uint32)


def joined(parts: list, about: tuple = None) -> tuple:
  """Returns the rows and triangles of 'parts' as one mesh, its places
  from 'about' (None: as they are)."""
  rows, faces, count = [], [], 0
  for part, indices in parts:
    rows.append(part)
    faces.append(indices + count)
    count += len(part)
  return rowsAbout(numpy.concatenate(rows), about), numpy.concatenate(
    faces).astype(numpy.uint32)


def rowsAbout(rows: numpy.ndarray, about: tuple) -> numpy.ndarray:
  """Returns 'rows' with their places taken from 'about' (None: as they
  are)."""
  if about is None:
    return rows
  out = numpy.array(rows, numpy.float64)
  out[:, :3] -= numpy.array(about)
  return out


def _cellAt(cell: tuple, u: float, v: float) -> tuple:
  """Returns where on a picture the share 'u', 'v' of 'cell' lies (no
  cell: the picture's corner)."""
  if cell is None:
    return _NO_PICTURE
  return (cell[0] + u * (cell[2] - cell[0]), cell[1] + v * (cell[3]
                                                           - cell[1]))
