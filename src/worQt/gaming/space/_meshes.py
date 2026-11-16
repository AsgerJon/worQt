"""
The space package's meshes as rows ('sandbox._mesh.Mesh' takes them):
a heavenly body's sphere (its look laid over it, the prime meridian
down the picture's middle), a cap of the ground round a point (fine
near it, coarse far out: what is drawn under the camera), the pad, the
creative rocket's parts and Saturn's rings. Qt-free; numpy, float64
until handed over.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._cabin import capsuleShell
from ._looks import RING_INNER, RING_OUTER
from ._vessel import CAPSULE, CENTRE, LEGS, PLUG, RADIUS, SIZE, TANK

TAU = 2.0 * math.pi
#  The ground's cap: how far round it reaches (rad: ~1900 km on Terra),
#  its nearest ring (rad: ~6 m) and its rings and spokes.
CAP_REACH = 0.3
CAP_NEAREST = 1e-6
CAP_RINGS = 72
CAP_SPOKES = 96
#  The pad: its radius and thickness, m.
PAD_RADIUS = 18.0
PAD_THICK = 0.6
#  Its top, m over the ground: the legs stand on the ground (a sphere),
#  the pad drawn a little over it so the two do not flicker; the legs'
#  feet hide the 2 cm.
PAD_TOP = 0.02


def sphereRows(spokes: int, rings: int) -> tuple:
  """Returns a unit sphere's rows (place, normal, where on the picture)
  and triangles: its own z north, x the prime meridian; the picture's
  middle column on the prime meridian, its seam on the far side."""
  lat = numpy.linspace(-0.5 * math.pi, 0.5 * math.pi, rings + 1)
  lon = numpy.linspace(-math.pi, math.pi, spokes + 1)
  la, lo = numpy.meshgrid(lat, lon, indexing='ij')
  place = numpy.stack([numpy.cos(la) * numpy.cos(lo),
                       numpy.cos(la) * numpy.sin(lo), numpy.sin(la)], -1)
  u = (lo + math.pi) / TAU
  v = (la + 0.5 * math.pi) / math.pi
  rows = numpy.concatenate([place, place, u[..., None], v[..., None]], -1)
  return rows.reshape(-1, 8), _gridIndices(rings, spokes)


def capRows(centre: tuple, radius: float) -> tuple:
  """Returns the rows and triangles of the ground's cap round 'centre'
  (a unit vector in a body's own axes) on a body 'radius' m round: its
  places from the ground's point at 'centre' (m, the body's own axes:
  small near it), its normals, where it lies on the body's picture."""
  c = numpy.array(centre, numpy.float64)
  c /= numpy.linalg.norm(c)
  pole = numpy.array([0.0, 0.0, 1.0])
  east = numpy.cross(pole, c)
  if numpy.linalg.norm(east) < 1e-9:
    east = numpy.array([0.0, 1.0, 0.0])
  east /= numpy.linalg.norm(east)
  north = numpy.cross(c, east)
  angles = numpy.concatenate([[0.0], numpy.geomspace(
    CAP_NEAREST, CAP_REACH, CAP_RINGS)])
  ways = numpy.linspace(0.0, TAU, CAP_SPOKES + 1)
  phi, beta = numpy.meshgrid(angles, ways, indexing='ij')
  across = numpy.cos(beta)[..., None] * east + numpy.sin(beta)[
    ..., None] * north
  way = numpy.cos(phi)[..., None] * c + numpy.sin(phi)[..., None] * across
  place = radius * numpy.sin(phi)[..., None] * across - (
    2.0 * radius * numpy.sin(0.5 * phi) ** 2)[..., None] * c
  lon = numpy.arctan2(way[..., 1], way[..., 0])
  middle = math.atan2(c[1], c[0])
  lon = middle + (lon - middle + math.pi) % TAU - math.pi
  lat = numpy.arcsin(numpy.clip(way[..., 2], -1.0, 1.0))
  u = (lon + math.pi) / TAU
  v = (lat + 0.5 * math.pi) / math.pi
  rows = numpy.concatenate([place, way, u[..., None], v[..., None]], -1)
  return rows.reshape(-1, 8), _gridIndices(CAP_RINGS, CAP_SPOKES, True)


def padRows() -> tuple:
  """Returns the pad's rows and triangles: a concrete disc in its own
  frame (x east, y north, z up), its top 'PAD_TOP' over the ground."""
  return _frustum(PAD_TOP - PAD_THICK, PAD_RADIUS, PAD_TOP, PAD_RADIUS, 48,
                  False, True)


def rocketParts() -> dict:
  """Returns the creative rocket's parts by look, each its rows and
  triangles about its centre of mass (its own axes, z its nose): the
  aerospike's plug, the tank, the capsule's skin (its windows cut: the
  cabin inside, '_cabin') and its nose, the legs."""
  low = -CENTRE
  out = {}
  out['plug'] = _joined([
    _frustum(low + PLUG[0], 0.35 * SIZE, low + PLUG[1], RADIUS * 0.9, 32,
             True, False)])
  out['tank'] = _joined([
    _frustum(low + TANK[0], RADIUS, low + TANK[1], RADIUS, 40, True,
             True)])
  out['capsule'] = capsuleShell(False)
  legs = []
  for foot in LEGS:
    out_ = numpy.array([foot[0], foot[1], 0.0]) / math.hypot(foot[0],
                                                              foot[1])
    top = out_ * (RADIUS - 0.05 * SIZE) + numpy.array(
      [0.0, 0.0, low + TANK[0] + 0.6 * SIZE])
    bottom = numpy.array(foot, numpy.float64) + numpy.array(
      [0.0, 0.0, 0.25 * SIZE])
    legs.append(_strut(top, bottom, 0.12 * SIZE))
    legs.append(_frustum(foot[2], 0.45 * SIZE, foot[2] + 0.25 * SIZE,
                         0.3 * SIZE, 16, True, True, (foot[0], foot[1])))
  out['legs'] = _joined(legs)
  return out


def ringRows() -> tuple:
  """Returns Saturn's rings' rows and triangles: a flat annulus in its
  equator's plane, its radii its planet's (a unit planet), where on the
  rings' strip each lies (across from the inside out), both faces."""
  spokes = 128
  ways = numpy.linspace(0.0, TAU, spokes + 1)
  rows, faces = [], []
  for up in (1.0, -1.0):
    first = len(rows)
    for way in ways:
      for r, u in ((RING_INNER, 0.0), (RING_OUTER, 1.0)):
        rows.append((r * math.cos(way), r * math.sin(way), 0.0, 0.0, 0.0,
                     up, u, 0.5))
    for k in range(spokes):
      a, b, c, d = (first + 2 * k, first + 2 * k + 1, first + 2 * k + 3,
                    first + 2 * k + 2)
      faces.extend((a, b, c, a, c, d) if up > 0 else (a, c, b, a, d, c))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _gridIndices(rows: int, columns: int,
                 turned: bool = False) -> numpy.ndarray:
  """Returns the triangles of a grid of (rows + 1) x (columns + 1)
  corners, row by row, its faces outward: counter-clockwise seen from
  outside with the columns going right and the rows up (a sphere's
  longitudes and latitudes), or, 'turned', the rows right and the
  columns up (a cap's rings outward and spokes round)."""
  out = []
  wide = columns + 1
  for r in range(rows):
    for c in range(columns):
      a, b = r * wide + c, r * wide + c + 1
      d, e = (r + 1) * wide + c, (r + 1) * wide + c + 1
      out.extend((a, d, e, a, e, b) if turned else (a, b, e, a, e, d))
  return numpy.array(out, numpy.uint32)


def _frustum(z0: float, r0: float, z1: float, r1: float, sides: int,
             bottom: bool, top: bool, at: tuple = (0.0, 0.0)) -> tuple:
  """Returns the rows (place, normal) and triangles of a frustum along
  z from 'z0' (radius 'r0') to 'z1' ('r1') about 'at', with its bottom
  and top closed if asked."""
  rows, faces = [], []
  slope = (r0 - r1) / (z1 - z0)
  for k in range(sides + 1):
    way = TAU * k / sides
    cos, sin = math.cos(way), math.sin(way)
    size = math.sqrt(1.0 + slope * slope)
    normal = (cos / size, sin / size, slope / size)
    for z, r in ((z0, r0), (z1, r1)):
      rows.append((at[0] + r * cos, at[1] + r * sin, z) + normal)
  for k in range(sides):
    a, b, c, d = 2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1
    faces.extend((a, b, c, a, c, d))
  for closed, z, r, up in ((bottom, z0, r0, -1.0), (top, z1, r1, 1.0)):
    if not closed:
      continue
    middle = len(rows)
    rows.append((at[0], at[1], z, 0.0, 0.0, up))
    for k in range(sides + 1):
      way = TAU * k / sides
      rows.append((at[0] + r * math.cos(way), at[1] + r * math.sin(way),
                   z, 0.0, 0.0, up))
    for k in range(sides):
      one, two = middle + 1 + k, middle + 2 + k
      faces.extend((middle, one, two) if up > 0 else (middle, two, one))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _strut(one: numpy.ndarray, two: numpy.ndarray, half: float) -> tuple:
  """Returns a square strut's rows and triangles from 'one' to 'two',
  'half' m from its line each way."""
  along = two - one
  along = along / numpy.linalg.norm(along)
  side = numpy.cross(along, numpy.array([0.0, 0.0, 1.0]))
  if numpy.linalg.norm(side) < 1e-9:
    side = numpy.array([1.0, 0.0, 0.0])
  side = side / numpy.linalg.norm(side)
  other = numpy.cross(along, side)
  corners = [side * a + other * b for a, b in ((1, 1), (-1, 1), (-1, -1),
                                               (1, -1))]
  rows, faces = [], []
  for k in range(4):
    p, q = corners[k] * half, corners[(k + 1) % 4] * half
    normal = (p + q) / numpy.linalg.norm(p + q)
    first = len(rows)
    for corner in (one + p, two + p, two + q, one + q):
      rows.append(tuple(corner) + tuple(normal))
    faces.extend((first, first + 2, first + 1, first, first + 3,
                  first + 2))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _joined(parts: list) -> tuple:
  """Returns the rows and triangles of 'parts' as one mesh."""
  rows, faces, count = [], [], 0
  for part, indices in parts:
    rows.append(part)
    faces.append(indices + count)
    count += len(part)
  return numpy.concatenate(rows), numpy.concatenate(faces).astype(
    numpy.uint32)
