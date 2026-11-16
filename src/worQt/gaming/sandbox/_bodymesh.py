"""
The sandbox's meshes, Qt-free: a body's shape as triangles for the GPU
to draw ('bodyRows'), and quads made in the world as triangles
('quadRows'). Every mesh is rows of six numbers a corner (its place, m,
and its normal, along the world's axes) and the triangles' corners by
row.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys._shape import Sphere
from worQt.phys._turned import Turned

#  A ball is drawn this many bands from pole to pole, twice as many
#  round.
BANDS = 12


def bodyRows(body: object) -> tuple[numpy.ndarray, numpy.ndarray]:
  """The 'bodyRows' function returns 'body''s shape as triangles about its
  centre of mass, in its own frame: a ball smooth, any other solid flat
  faced (a turned solid as its 'mesh')."""
  shape = body.shape
  if shape is None:
    return numpy.zeros((0, 6), numpy.float32), numpy.zeros(0, numpy.uint32)
  if isinstance(shape, Sphere):
    rows, indices = _ballRows(shape.radius)
  else:
    if isinstance(shape, Turned):
      shape = shape.mesh()
    rows, indices = _faceRows(shape)
  rows[:, :3] -= numpy.array(body.centre, numpy.float32)
  return rows, indices


def quadRows(quads: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray]:
  """The 'quadRows' function returns quads (n, 4, 6: each corner's place
  and normal) as rows, two triangles a quad."""
  rows = numpy.ascontiguousarray(quads.reshape(-1, 6), numpy.float32)
  first = 4 * numpy.arange(len(quads), dtype=numpy.uint32)[:, None]
  corners = numpy.array((0, 1, 2, 0, 2, 3), numpy.uint32)
  return rows, (first + corners).ravel()


def _faceRows(shape: object) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Returns a closed surface of triangles (a 'Shape') as rows, three a
  face, each corner with its face's normal (flat)."""
  points = numpy.array(shape.points, numpy.float64)
  faces = numpy.array(shape.faces, numpy.int64)
  corners = points[faces]
  normals = numpy.cross(corners[:, 1] - corners[:, 0],
                        corners[:, 2] - corners[:, 0])
  sizes = numpy.linalg.norm(normals, axis=1)
  normals /= numpy.where(sizes > 0.0, sizes, 1.0)[:, None]
  rows = numpy.empty((len(faces), 3, 6), numpy.float32)
  rows[:, :, :3] = corners
  rows[:, :, 3:] = normals[:, None, :]
  return rows.reshape(-1, 6), numpy.arange(3 * len(faces),
                                           dtype=numpy.uint32)


def _ballRows(radius: float) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Returns a ball of 'radius' as rows, 'BANDS' from pole to pole, each
  corner's normal its way from the middle (smooth)."""
  rows = []
  for i in range(BANDS + 1):
    down = math.pi * i / BANDS
    for j in range(2 * BANDS + 1):
      round_ = math.pi * j / BANDS
      way = (math.sin(down) * math.cos(round_),
             math.sin(down) * math.sin(round_), math.cos(down))
      rows.append(tuple(radius * x for x in way) + way)
  indices, wide = [], 2 * BANDS + 1
  for i in range(BANDS):
    for j in range(2 * BANDS):
      a, b = i * wide + j, (i + 1) * wide + j
      indices += (a, b, b + 1, a, b + 1, a + 1)
  return (numpy.array(rows, numpy.float32),
          numpy.array(indices, numpy.uint32))
