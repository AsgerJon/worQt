"""
Stone is one stone of an aggregate: a convex polyhedron, turned at
random.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple, TYPE_CHECKING

import numpy
import torch
from scipy.spatial import ConvexHull

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from numpy.random import Generator

_CORNERS = 14  # points drawn about the ellipsoid; their hull is the stone
_WIDE = (0.65, 0.9)  # how wide a stone is, of how long
_THICK = (0.6, 0.9)  # how thick a stone is, of how wide
_JITTER = 0.08  # how far a corner strays from the ellipsoid, of its reach


def randomTurns(rng: Generator, count: int) -> numpy.ndarray:
  """The 'randomTurns' function returns 'count' rotations drawn evenly
  from all rotations, as matrices: Shoemake's unit quaternions of three
  draws each."""
  draws = rng.random((count, 3))
  low, high = numpy.sqrt(1.0 - draws[:, 0]), numpy.sqrt(draws[:, 0])
  x = low * numpy.sin(2 * math.pi * draws[:, 1])
  y = low * numpy.cos(2 * math.pi * draws[:, 1])
  z = high * numpy.sin(2 * math.pi * draws[:, 2])
  w = high * numpy.cos(2 * math.pi * draws[:, 2])
  rows = [
    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
  ]
  return numpy.stack([numpy.stack(row, 1) for row in rows], 1)


class Stone(NamedTuple):
  """
  Stone is one stone of an aggregate, in mm: a convex polyhedron, its
  'vertices' about its 'centre', the mean of them, its triangular 'faces'
  with their outward unit 'normals' and 'offsets', a point x about the
  centre inside where every n . x is within its offset, and its 'edges'.
  'random' makes one: corners drawn at random about an ellipsoid longer
  than it is wide and wider than it is thick, as stones are, their hull
  turned at random and made as large by 'volume' as the sphere of its
  'size'. 'outer' is how far its farthest corner is from the centre,
  'inner' how far its nearest face.

  'corners' are its vertices where it is; 'moved' is the stone put
  elsewhere; 'section' is the convex polygon a plane at a depth z cuts
  from it, its corners counter-clockwise, or 'None' where the plane
  misses it.
  """

  centre: torch.Tensor
  vertices: torch.Tensor
  faces: torch.Tensor
  normals: torch.Tensor
  offsets: torch.Tensor
  edges: torch.Tensor
  size: float
  volume: float
  outer: float
  inner: float

  @property
  def corners(self, ) -> torch.Tensor:
    """The vertices where the stone is."""
    return self.vertices + self.centre

  def moved(self, centre: torch.Tensor) -> Stone:
    """The stone put at 'centre'."""
    return Stone(centre.clone(), *self[1:])

  def section(self, depth: float) -> torch.Tensor | None:
    """The polygon the plane at 'depth' cuts from the stone, its corners
    counter-clockwise, or 'None' if the plane misses it."""
    corners = self.corners
    above = corners[:, 2] - depth
    one, two = self.edges[:, 0], self.edges[:, 1]
    first, second = above[one], above[two]
    cut = first * second < 0
    if int(cut.sum()) < 3:
      return None
    start, stop = corners[one[cut]], corners[two[cut]]
    share = (first[cut] / (first[cut] - second[cut]))[:, None]
    points = (start + share * (stop - start))[:, :2]
    middle = points.mean(0)
    angles = torch.atan2(points[:, 1] - middle[1], points[:, 0] - middle[0])
    return points[torch.argsort(angles)]

  @classmethod
  def random(cls, rng: Generator, size: float) -> Stone:
    """
    A stone of 'size' at the origin, drawn by 'rng': the hull of corners
    drawn about an ellipsoid, found once; moving, scaling and turning it
    to its centre, its volume and its turn leave its faces the same.
    """
    wide = rng.uniform(*_WIDE)
    reach = numpy.array([1.0, wide, wide * rng.uniform(*_THICK)])
    ways = rng.normal(0.0, 1.0, (_CORNERS, 3))
    ways /= numpy.linalg.norm(ways, 2, 1, True)
    strays = rng.uniform(1.0 - _JITTER, 1.0 + _JITTER, (_CORNERS, 1))
    points = ways * reach * strays
    hull = ConvexHull(points)
    place = numpy.full(len(points), -1)
    place[hull.vertices] = numpy.arange(len(hull.vertices))
    corners = points[hull.vertices]
    centre = corners.mean(0)
    normals = hull.equations[:, :3]
    offsets = -hull.equations[:, 3] - normals @ centre
    volume = math.pi / 6 * size ** 3
    scale = (volume / hull.volume) ** (1.0 / 3.0)
    turn = randomTurns(rng, 1)[0]
    corners = ((corners - centre) * scale) @ turn.T
    normals = normals @ turn.T
    faces = torch.from_numpy(place[hull.simplices].astype(numpy.int64))
    sides = torch.cat([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    edges = torch.unique(torch.sort(sides, 1).values, True, False, False, 0)
    vertices = torch.from_numpy(numpy.ascontiguousarray(corners))
    offsets = torch.from_numpy(numpy.ascontiguousarray(offsets * scale))
    outer = vertices.norm(2, 1).max().item()
    return cls(
      torch.zeros(3).double(), vertices, faces,
      torch.from_numpy(numpy.ascontiguousarray(normals)), offsets,
      edges, float(size), float(hull.volume * scale ** 3), outer,
      offsets.min().item()
      )
