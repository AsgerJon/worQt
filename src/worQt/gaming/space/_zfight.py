"""
Where drawn surfaces fight (user, 2026-11-19: "There are still colliding
geometreis that fight in the renderer which looks awfule. I thought we
had a tool that systematically ensured that no such collissoins
occurred?"; "around the doorways in the tower. Like into the staircase
and the elveator"): two triangles in the same plane (within 'APART'),
facing the same way, sharing some of their area ('LEAST'), are drawn at
the same depth: the renderer picks either from pixel to pixel, frame to
frame (z-fighting). Faces back to back (two boxes meeting) are hidden
inside the solid they make: not a fight. 'fightsOf' finds them among
meshes laid in one frame. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

#  Two planes this near are one to the depth buffer, m (a far plane at
#  50 m in a 24 bit buffer is some 0.1 mm; this is generous).
APART = 0.002
#  Surfaces sharing less than this are not a fight (a seam), m².
LEAST = 1e-4
#  Normals this near parallel are one plane's (the cosine).
PARALLEL = 0.99999


class Fight:
  """
  Fight is two meshes' surfaces drawn in one place: the meshes' names
  ('first', 'second'), the middle of the area they share ('middle', m)
  and its size ('area', m²), the way they face ('facing').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  first: str
  second: str
  middle: tuple
  area: float
  facing: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, first: str, second: str, middle: tuple, area: float,
               facing: tuple) -> None:
    self.first, self.second = first, second
    self.middle, self.area = tuple(middle), float(area)
    self.facing = tuple(facing)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PYTHON SPECIAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    return '%s / %s at (%.3f, %.3f, %.3f), %.4f m² facing %s' % (
      self.first, self.second, *self.middle, self.area,
      tuple(round(x, 3) for x in self.facing))


def fightsOf(meshes: list) -> list:
  """Returns where the meshes fight: 'meshes' each (name, rows, faces)
  (rows of at least x y z, faces three corners a triangle) in one frame;
  each pair of triangles in one plane facing one way sharing at least
  'LEAST' (two of one mesh too: two boxes joined into it)."""
  corners, names, owners = [], [], []
  for k, (name, rows, faces) in enumerate(meshes):
    rows = numpy.asarray(rows, numpy.float64)[:, :3]
    faces = numpy.asarray(faces, numpy.int64).reshape(-1, 3)
    corners.append(rows[faces])
    owners.append(numpy.full(len(faces), k))
    names.append(name)
  if not corners:
    return []
  tri = numpy.concatenate(corners)
  owner = numpy.concatenate(owners)
  cross = numpy.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
  size = numpy.linalg.norm(cross, axis=1)
  keep = size > 1e-12
  tri, owner, cross, size = tri[keep], owner[keep], cross[keep], size[keep]
  normal = cross / size[:, None]
  offset = numpy.einsum('ij,ij->i', normal, tri[:, 0])
  low, high = tri.min(axis=1), tri.max(axis=1)
  buckets = {}
  for t in range(len(tri)):
    key = (tuple(numpy.round(normal[t], 4)), int(math.floor(
      offset[t] / APART)))
    buckets.setdefault(key, []).append(t)
  out = []
  for (way, step), members in buckets.items():
    near = list(members)
    for other in (step - 1, step + 1):
      near += buckets.get((way, other), [])
    first, second = _pairsNear(numpy.array(members, numpy.int64),
                               numpy.array(near, numpy.int64), low, high)
    if not len(first):
      continue
    overlap = (numpy.minimum(high[first], high[second])
               - numpy.maximum(low[first], low[second]))
    keep = ((overlap > -APART).all(axis=1)
            & ((overlap > 1e-6).sum(axis=1) >= 2)
            & (numpy.abs(offset[first] - offset[second]) <= APART)
            & (numpy.einsum('ij,ij->i', normal[first], normal[second])
               >= PARALLEL))
    for i, j in zip(first[keep], second[keep]):
      shared = _shared(tri[i], tri[j], normal[i])
      if shared is None or shared[1] < LEAST:
        continue
      out.append(Fight(names[owner[i]], names[owner[j]], shared[0],
                       shared[1], normal[i]))
  return out


def _pairsNear(members: numpy.ndarray, near: numpy.ndarray,
               low: numpy.ndarray, high: numpy.ndarray) -> tuple:
  """Returns the pairs (each of 'members' with each of 'near' numbered
  after it) whose spans along x come within 'APART' of each other: two
  arrays, the first's and the second's (the rest of the test is the
  caller's). By a sweep along x (each member's partners lie between its
  own span less the widest's and its end), no loop a triangle."""
  order = near[numpy.argsort(low[near, 0], kind='stable')]
  starts = low[order, 0]
  widest = float((high[near, 0] - low[near, 0]).max())
  begin = numpy.searchsorted(starts, low[members, 0] - widest - APART,
                             'left')
  end = numpy.searchsorted(starts, high[members, 0] + APART, 'right')
  counts = end - begin
  total = int(counts.sum())
  if not total:
    return numpy.zeros(0, numpy.int64), numpy.zeros(0, numpy.int64)
  first = numpy.repeat(members, counts)
  steps = numpy.arange(total) - numpy.repeat(numpy.cumsum(counts)
                                             - counts, counts)
  second = order[numpy.repeat(begin, counts) + steps]
  keep = second > first
  return first[keep], second[keep]


def _shared(a: numpy.ndarray, b: numpy.ndarray, normal: numpy.ndarray
            ) -> tuple | None:
  """Returns the middle and the area two triangles in one plane share
  (None: none): triangle 'a' clipped by each edge of 'b', in the
  plane's own two axes."""
  nx, ny, nz = (float(n) for n in normal)
  if abs(nx) < 0.9:
    u = (0.0, nz, -ny)
  else:
    u = (-nz, 0.0, nx)
  size = math.sqrt(u[0] * u[0] + u[1] * u[1] + u[2] * u[2])
  u = (u[0] / size, u[1] / size, u[2] / size)
  v = (ny * u[2] - nz * u[1], nz * u[0] - nx * u[2], nx * u[1] - ny * u[0])

  def flatOf(points: numpy.ndarray) -> list:
    return [(p[0] * u[0] + p[1] * u[1] + p[2] * u[2],
             p[0] * v[0] + p[1] * v[1] + p[2] * v[2])
            for p in points.tolist()]

  flat, clip = flatOf(a), flatOf(b)
  if _signed(clip) < 0.0:
    clip.reverse()
  if _signed(flat) < 0.0:
    flat.reverse()
  for k in range(3):
    (px, py), (qx, qy) = clip[k], clip[(k + 1) % 3]
    ex, ey = qx - px, qy - py

    def inside(point: tuple) -> float:
      return ex * (point[1] - py) - ey * (point[0] - px)

    kept = []
    for m in range(len(flat)):
      s, e = flat[m], flat[(m + 1) % len(flat)]
      si, ei = inside(s), inside(e)
      if si >= 0.0:
        kept.append(s)
      if (si >= 0.0) != (ei >= 0.0):
        t = si / (si - ei)
        kept.append((s[0] + t * (e[0] - s[0]), s[1] + t * (e[1] - s[1])))
    flat = kept
    if len(flat) < 3:
      return None
  area = _signed(flat)
  if area <= 0.0:
    return None
  cu = sum(p[0] for p in flat) / len(flat)
  cv = sum(p[1] for p in flat) / len(flat)
  depth = float(a[0] @ normal)
  middle = tuple(cu * x + cv * y + depth * n for x, y, n in zip(
    u, v, (nx, ny, nz)))
  return middle, area


def _signed(points: list) -> float:
  """Returns a polygon's area, positive wound counterclockwise."""
  total = 0.0
  for k in range(len(points)):
    (x0, y0), (x1, y1) = points[k], points[(k + 1) % len(points)]
    total += x0 * y1 - x1 * y0
  return 0.5 * total
