"""
The trains' own dress (Qt-free): what a car is drawn as when its shape
is not enough (user, 2026-11-16: walk through the train, "put some
memes on the inside walls"): boxes as quads, wound outward ('boxQuads',
upright or turned), pictures on walls ('posterRows': a cell of a
picture, the right way up for whoever faces it), and the lot gathered
into a body's parts, one mesh a look, about its centre ('partsOf').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

#  The boxes' faces: each its axis and which way (outward).
_FACES = ((0, 1.0), (0, -1.0), (1, 1.0), (1, -1.0), (2, 1.0), (2, -1.0))


def boxQuads(low: tuple, high: tuple, turn: numpy.ndarray = None,
             at: tuple = (0.0, 0.0, 0.0)) -> numpy.ndarray:
  """The 'boxQuads' function returns the box from 'low' to 'high' (m) as
  six quads (6, 4, 6: each corner's place and normal), each wound
  anticlockwise seen from outside; turned by 'turn' (a 3 x 3 matrix,
  None: not) about the origin, then moved by 'at'."""
  low, high = numpy.array(low, float), numpy.array(high, float)
  middle, half = 0.5 * (low + high), 0.5 * (high - low)
  out = numpy.empty((6, 4, 6))
  for k, (axis, way) in enumerate(_FACES):
    normal = numpy.zeros(3)
    normal[axis] = way
    up = numpy.array((0.0, 1.0, 0.0) if axis == 2 else (0.0, 0.0, 1.0))
    right = numpy.cross(-normal, up)
    across = abs(float(right @ half))
    tall = abs(float(up @ half))
    face = middle + normal * half[axis]
    corners = (face - right * across - up * tall,
               face + right * across - up * tall,
               face + right * across + up * tall,
               face - right * across + up * tall)
    for j, corner in enumerate(corners):
      out[k, j, :3], out[k, j, 3:] = corner, normal
  if turn is not None:
    out[:, :, :3] = out[:, :, :3] @ numpy.asarray(turn).T
    out[:, :, 3:] = out[:, :, 3:] @ numpy.asarray(turn).T
  out[:, :, :3] += numpy.array(at, float)
  return out


def posterRows(middle: tuple, normal: tuple, right: tuple, wide: float,
               high: float, cell: tuple) -> numpy.ndarray:
  """The 'posterRows' function returns a picture on a wall as four rows
  of eight (place, normal, where on the picture, from its bottom left):
  'wide' by 'high' m about 'middle', facing 'normal', its right along
  'right' as one facing it sees it; showing the picture's 'cell' (from
  u, from v, to u, to v)."""
  middle, normal = numpy.array(middle, float), numpy.array(normal, float)
  right = numpy.array(right, float)
  up = numpy.cross(right, -normal)
  u0, v0, u1, v1 = cell
  out = numpy.empty((4, 8))
  for j, (x, y, u, v) in enumerate(((-1, -1, u0, v0), (1, -1, u1, v0),
                                    (1, 1, u1, v1), (-1, 1, u0, v1))):
    out[j, :3] = middle + right * (0.5 * wide * x) + up * (0.5 * high * y)
    out[j, 3:6], out[j, 6:] = normal, (u, v)
  return out


def partsOf(groups: dict, centre: tuple) -> tuple:
  """The 'partsOf' function returns 'groups' ({look: quads, each (4, 6)
  or (4, 8) corners}) as a body's parts ('World.dressedWith'): one mesh
  a look, its rows about the body's 'centre' (float32), two triangles a
  quad."""
  out = []
  for look, quads in groups.items():
    if not len(quads):
      continue
    quads = numpy.array(quads, numpy.float64)
    quads[:, :, :3] -= numpy.array(centre, float)
    rows = numpy.ascontiguousarray(quads.reshape(-1, quads.shape[2]),
                                   numpy.float32)
    first = 4 * numpy.arange(len(quads), dtype=numpy.uint32)[:, None]
    corners = numpy.array((0, 1, 2, 0, 2, 3), numpy.uint32)
    out.append((rows, (first + corners).ravel(), look))
  return tuple(out)
